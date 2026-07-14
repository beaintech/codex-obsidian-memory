# RAG v0 architecture

This first release deliberately starts with reliable local retrieval instead of a remote vector service.

```text
Obsidian Markdown -> heading chunks -> SQLite FTS5 -> MCP tools -> Codex
```

## What it does

- Recursively indexes Markdown notes.
- Ignores `.obsidian`, `.git`, `.rag`, virtual environments, and common generated folders.
- Splits notes at Markdown headings and preserves file/heading citations.
- Builds the database atomically under `.rag/index.sqlite3`.
- Exposes read-only `search_memory` and `read_note` MCP tools.
- Requires no API key and sends no note content to an embedding provider.

## What it does not do yet

- Semantic/vector retrieval
- OCR or PDF ingestion
- Automatic filesystem watching
- Reranking
- Automatic note mutation

These are intentional v0 boundaries. The SQLite database is a derived cache and can always be deleted and rebuilt from Markdown.

## Privacy model

The vault is the source of truth. The generated index remains local and is ignored by Git. Do not place passwords, tokens, private keys, recovery codes, or unnecessary sensitive data in the vault.

For real company operations, use a private vault repository. Keep this public repository limited to code, templates, and fictional examples.
