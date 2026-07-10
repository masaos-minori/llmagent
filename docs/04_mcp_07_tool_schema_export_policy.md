---
title: "MCP Tool Schema Export Policy"
category: mcp
tags:
  - mcp
  - mcp
  - tool-schema
  - export
  - policy
related:
  - 04_mcp_00_document-guide.md
---

# MCP Tool Schema Export Naming Policy

## Canonical Export: `TOOL_LIST`

All MCP server tool schema modules (`mcp/<name>/tools.py`) must export the canonical tool list as `TOOL_LIST`.

### Rationale

- `TOOL_LIST` is a public, non-prefixed name that clearly indicates this is the main export.
- GitHub MCP already uses `TOOL_LIST` as canonical (see `mcp/github/tools.py`).

### Migration History

All MCP servers have been migrated to `TOOL_LIST`. The migration was completed in the following order:

1. **git** — `scripts/mcp_servers/git/tools.py`, `scripts/mcp_servers/git/server.py`
2. **mdq** — `scripts/mcp_servers/mdq/tools.py`, `scripts/mcp_servers/mdq/server.py`
3. **rag_pipeline** — `scripts/mcp_servers/rag_pipeline/tools.py`, `scripts/mcp_servers/rag_pipeline/server.py`
4. **shell** — `scripts/mcp_servers/shell/tools.py`, `scripts/mcp_servers/shell/server.py`
5. **cicd** — `scripts/mcp_servers/cicd/tools.py`, `scripts/mcp_servers/cicd/server.py`
6. **web_search** — `scripts/mcp_servers/web_search/tools.py`, `scripts/mcp_servers/web_search/server.py`
7. **file_read** — `scripts/mcp_servers/file/read_tools.py`, `scripts/mcp_servers/file/read_server.py`
8. **file_write** — `scripts/mcp_servers/file/write_tools.py`, `scripts/mcp_servers/file/write_server.py`
9. **file_delete** — `scripts/mcp_servers/file/delete_tools.py`, `scripts/mcp_servers/file/delete_server.py`

### Validation

After all migrations:
- Run: `pytest tests/test_<name>_mcp_service.py -v`
- Run: `pytest tests/test_mcp_tool_schema_exports.py -v` — asserts every active MCP tool schema module exports TOOL_LIST as a non-empty list of dicts with "name" key, and no module uses the legacy _MCP_TOOLS name.

## Related Documents

- `mcp`
- `tool-schema`
- `export`

## Keywords

mcp
tool-schema
export
policy
