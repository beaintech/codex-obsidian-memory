# Connect the local memory server to Codex

## 1. Install

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[mcp]'
```

## 2. Build the index

```bash
obsidian-rag index --vault /absolute/path/to/your/vault
```

The generated database is `/absolute/path/to/your/vault/.rag/index.sqlite3`.

## 3. Test retrieval

```bash
obsidian-rag search --vault /absolute/path/to/your/vault "customer follow-up"
obsidian-rag read --vault /absolute/path/to/your/vault "Customers/Acme.md"
```

## 4. Add the MCP server

Add a local STDIO server in Codex settings, or add this to `~/.codex/config.toml`:

```toml
[mcp_servers.obsidian_memory]
command = "/absolute/path/to/repository/.venv/bin/python"
args = [
  "-m",
  "obsidian_rag",
  "serve",
  "--vault",
  "/absolute/path/to/your/vault",
]
enabled = true
required = false
enabled_tools = ["search_memory", "read_note"]
default_tools_approval_mode = "auto"
```

Restart Codex after saving. Then ask:

> List the `obsidian_memory` tools without running them.

Next, test retrieval:

> Search my Obsidian memory for the lead qualification workflow. Cite the source path and heading.

## 5. Refresh after note changes

Rerun the index command whenever important notes change:

```bash
obsidian-rag index --vault /absolute/path/to/your/vault
```
