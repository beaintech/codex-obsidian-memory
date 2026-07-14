from __future__ import annotations

from pathlib import Path
from typing import Any

from .index import read_note as read_note_file
from .index import search_index


def create_server(vault: Path, db_path: Path):
    """Create the optional MCP server without making MCP a core dependency."""

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as error:
        raise RuntimeError(
            'MCP support is not installed. Run: pip install -e ".[mcp]"'
        ) from error

    vault = vault.expanduser().resolve()
    db_path = db_path.expanduser().resolve()
    server = FastMCP(
        "Obsidian Memory",
        instructions=(
            "Read-only retrieval over the configured Obsidian vault. "
            "Use search_memory before read_note. Cite path and heading from results. "
            "Never claim that retrieved notes are current external facts."
        ),
    )

    @server.tool()
    def search_memory(query: str, limit: int = 5) -> dict[str, Any]:
        """Search the Obsidian index and return source-cited Markdown chunks."""

        return {
            "query": query,
            "results": search_index(db_path=db_path, query=query, limit=limit),
        }

    @server.tool()
    def read_note(path: str, max_chars: int = 20_000) -> dict[str, Any]:
        """Read one Markdown note by its vault-relative path."""

        return read_note_file(vault=vault, relative_path=path, max_chars=max_chars)

    return server


def run_server(vault: Path, db_path: Path) -> None:
    create_server(vault=vault, db_path=db_path).run(transport="stdio")
