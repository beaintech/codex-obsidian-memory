from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from typing import Any, Iterable

from .chunking import MarkdownChunk, chunk_markdown


SCHEMA_VERSION = "1"
DEFAULT_IGNORED_DIRS = {
    ".git",
    ".obsidian",
    ".rag",
    ".trash",
    ".venv",
    "node_modules",
    "__pycache__",
}
TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def default_db_path(vault: Path) -> Path:
    return vault / ".rag" / "index.sqlite3"


def iter_markdown_files(
    vault: Path, ignored_dirs: set[str] | None = None
) -> Iterable[Path]:
    ignored = ignored_dirs or DEFAULT_IGNORED_DIRS
    for root, dirs, files in os.walk(vault):
        dirs[:] = sorted(directory for directory in dirs if directory not in ignored)
        for filename in sorted(files):
            if filename.lower().endswith(".md"):
                yield Path(root) / filename


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode = DELETE;
        PRAGMA foreign_keys = ON;

        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL,
            title TEXT NOT NULL,
            heading TEXT NOT NULL,
            content TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            content_sha256 TEXT NOT NULL,
            modified_ns INTEGER NOT NULL,
            UNIQUE(path, ordinal)
        );

        CREATE VIRTUAL TABLE chunks_fts USING fts5(
            path UNINDEXED,
            title,
            heading,
            content,
            tokenize = 'unicode61 remove_diacritics 2'
        );
        """
    )


def index_vault(vault: Path, db_path: Path | None = None) -> dict[str, Any]:
    """Build a complete index in a temporary database, then replace atomically."""

    vault = vault.expanduser().resolve()
    if not vault.is_dir():
        raise ValueError(f"Vault does not exist or is not a directory: {vault}")
    db_path = (db_path or default_db_path(vault)).expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    file_count = 0
    chunk_count = 0
    with tempfile.NamedTemporaryFile(
        prefix="obsidian-rag-", suffix=".sqlite3", dir=db_path.parent, delete=False
    ) as handle:
        temporary_path = Path(handle.name)

    try:
        connection = _connect(temporary_path)
        try:
            _create_schema(connection)
            for markdown_path in iter_markdown_files(vault):
                file_count += 1
                modified_ns = markdown_path.stat().st_mtime_ns
                for chunk in chunk_markdown(markdown_path, vault):
                    digest = hashlib.sha256(chunk.content.encode("utf-8")).hexdigest()
                    cursor = connection.execute(
                        """
                        INSERT INTO chunks(
                            path, title, heading, content, ordinal,
                            content_sha256, modified_ns
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            chunk.path,
                            chunk.title,
                            chunk.heading,
                            chunk.content,
                            chunk.ordinal,
                            digest,
                            modified_ns,
                        ),
                    )
                    connection.execute(
                        """
                        INSERT INTO chunks_fts(rowid, path, title, heading, content)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            cursor.lastrowid,
                            chunk.path,
                            chunk.title,
                            chunk.heading,
                            chunk.content,
                        ),
                    )
                    chunk_count += 1

            metadata = {
                "schema_version": SCHEMA_VERSION,
                "vault": str(vault),
                "indexed_at": datetime.now(timezone.utc).isoformat(),
                "file_count": str(file_count),
                "chunk_count": str(chunk_count),
            }
            connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)", metadata.items()
            )
            connection.commit()
        finally:
            connection.close()
        temporary_path.replace(db_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return {
        "vault": str(vault),
        "database": str(db_path),
        "files": file_count,
        "chunks": chunk_count,
    }


def _fts_query(query: str) -> str:
    tokens = TOKEN_RE.findall(query)
    return " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)


def search_index(db_path: Path, query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search indexed chunks and return source-aware results."""

    if not query.strip():
        raise ValueError("Search query must not be empty")
    if limit < 1 or limit > 20:
        raise ValueError("limit must be between 1 and 20")
    db_path = db_path.expanduser().resolve()
    if not db_path.is_file():
        raise ValueError(f"Index does not exist: {db_path}. Run the index command first.")

    match_query = _fts_query(query)
    if not match_query:
        return []
    connection = _connect(db_path)
    try:
        rows = connection.execute(
            """
            SELECT
                c.path,
                c.title,
                c.heading,
                c.content,
                c.modified_ns,
                bm25(chunks_fts, 0.0, 5.0, 3.0, 1.0) AS rank,
                snippet(chunks_fts, 3, '**', '**', ' … ', 28) AS snippet
            FROM chunks_fts
            JOIN chunks AS c ON c.id = chunks_fts.rowid
            WHERE chunks_fts MATCH ?
            ORDER BY rank ASC, c.path ASC, c.ordinal ASC
            LIMIT ?
            """,
            (match_query, limit),
        ).fetchall()
    finally:
        connection.close()

    results = []
    for row in rows:
        results.append(
            {
                "path": row["path"],
                "title": row["title"],
                "heading": row["heading"],
                "snippet": row["snippet"],
                "content": row["content"],
                "modified_at": datetime.fromtimestamp(
                    row["modified_ns"] / 1_000_000_000, timezone.utc
                ).isoformat(),
                "score": round(-float(row["rank"]), 6),
                "citation": f'{row["path"]}#{row["heading"]}',
            }
        )
    return results


def read_note(vault: Path, relative_path: str, max_chars: int = 20_000) -> dict[str, Any]:
    """Read one Markdown note while preventing path traversal."""

    if max_chars < 1 or max_chars > 100_000:
        raise ValueError("max_chars must be between 1 and 100000")
    vault = vault.expanduser().resolve()
    requested = Path(relative_path)
    if requested.is_absolute():
        raise ValueError("path must be relative to the vault")
    resolved = (vault / requested).resolve()
    try:
        normalized = resolved.relative_to(vault)
    except ValueError as error:
        raise ValueError("path escapes the vault") from error
    if any(part in DEFAULT_IGNORED_DIRS for part in normalized.parts):
        raise ValueError("path is inside an excluded vault directory")
    if resolved.suffix.lower() != ".md" or not resolved.is_file():
        raise ValueError("path must identify an existing Markdown note")
    content = resolved.read_text(encoding="utf-8")
    truncated = len(content) > max_chars
    return {
        "path": normalized.as_posix(),
        "content": content[:max_chars],
        "truncated": truncated,
        "characters": len(content),
    }


def index_status(db_path: Path) -> dict[str, str]:
    db_path = db_path.expanduser().resolve()
    if not db_path.is_file():
        return {"status": "missing", "database": str(db_path)}
    connection = _connect(db_path)
    try:
        rows = connection.execute("SELECT key, value FROM metadata ORDER BY key").fetchall()
    finally:
        connection.close()
    status = {row["key"]: row["value"] for row in rows}
    status["status"] = "ready"
    status["database"] = str(db_path)
    return status
