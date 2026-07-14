from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from .index import default_db_path, index_status, index_vault, read_note, search_index
from .server import run_server


def _vault(value: str | None) -> Path:
    return Path(value or os.environ.get("OBSIDIAN_VAULT", Path.cwd())).expanduser().resolve()


def _database(value: str | None, vault: Path) -> Path:
    return Path(value).expanduser().resolve() if value else default_db_path(vault)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="obsidian-rag",
        description="Local-first retrieval and MCP tools for Obsidian Markdown.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("index", "search", "read", "status", "serve"):
        command = subparsers.add_parser(name)
        command.add_argument("--vault", help="Obsidian vault path (default: cwd)")
        command.add_argument("--db", help="Index path (default: VAULT/.rag/index.sqlite3)")

    search = subparsers.choices["search"]
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)

    read = subparsers.choices["read"]
    read.add_argument("path", help="Vault-relative Markdown path")
    read.add_argument("--max-chars", type=int, default=20_000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    vault = _vault(args.vault)
    database = _database(args.db, vault)
    try:
        if args.command == "index":
            result = index_vault(vault=vault, db_path=database)
        elif args.command == "search":
            result = {
                "query": args.query,
                "results": search_index(database, args.query, args.limit),
            }
        elif args.command == "read":
            result = read_note(vault, args.path, args.max_chars)
        elif args.command == "status":
            result = index_status(database)
        elif args.command == "serve":
            run_server(vault=vault, db_path=database)
            return 0
        else:  # pragma: no cover
            raise AssertionError(f"Unhandled command: {args.command}")
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
