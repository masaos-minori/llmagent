# MCP Tool Schema Export Naming Policy

## Canonical Export: `TOOL_LIST`

All MCP server tool schema modules (`mcp/<name>/tools.py`) must export the canonical tool list as `TOOL_LIST`.

### Rationale

- `TOOL_LIST` is a public, non-prefixed name that clearly indicates this is the main export.
- GitHub MCP already uses `TOOL_LIST` as canonical (see `mcp/github/tools.py`).

### Migration History

All MCP servers have been migrated to `TOOL_LIST`. The migration was completed in the following order:

1. **git** — `scripts/mcp/git/tools.py`, `scripts/mcp/git/server.py`
2. **mdq** — `scripts/mcp/mdq/tools.py`, `scripts/mcp/mdq/server.py`
3. **rag_pipeline** — `scripts/mcp/rag_pipeline/tools.py`, `scripts/mcp/rag_pipeline/server.py`
4. **shell** — `scripts/mcp/shell/tools.py`, `scripts/mcp/shell/server.py`
5. **cicd** — `scripts/mcp/cicd/tools.py`, `scripts/mcp/cicd/server.py`
6. **web_search** — `scripts/mcp/web_search/tools.py`, `scripts/mcp/web_search/server.py`
7. **file_read** — `scripts/mcp/file/read_tools.py`, `scripts/mcp/file/read_server.py`
8. **file_write** — `scripts/mcp/file/write_tools.py`, `scripts/mcp/file/write_server.py`
9. **file_delete** — `scripts/mcp/file/delete_tools.py`, `scripts/mcp/file/delete_server.py`

### Validation

After all migrations:
- Run: `pytest tests/test_<name>_mcp_service.py -v`
