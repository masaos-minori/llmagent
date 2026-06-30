# MCP Tool Schema Export Naming Policy

## Canonical Export: `TOOL_LIST`

All MCP server tool schema modules (`mcp/<name>/tools.py`) must export the canonical tool list as `TOOL_LIST`, not `_MCP_TOOLS`.

### Rationale

- `TOOL_LIST` is a public, non-prefixed name that clearly indicates this is the main export.
- `_MCP_TOOLS` implies internal/compatibility use and creates ambiguity about which is the canonical export.
- GitHub MCP already uses `TOOL_LIST` as canonical (see `mcp/github/tools.py`).

### Migration Plan

The following MCP servers need to migrate from `_MCP_TOOLS` to `TOOL_LIST`:

1. **git** — `scripts/mcp/git/tools.py`, `scripts/mcp/git/server.py`
2. **web_search** — `scripts/mcp/web_search/tools.py`, `scripts/mcp/web_search/server.py`
3. **shell** — `scripts/mcp/shell/tools.py`, `scripts/mcp/shell/server.py`
4. **rag_pipeline** — `scripts/mcp/rag_pipeline/tools.py`, `scripts/mcp/rag_pipeline/server.py`
5. **cicd** — `scripts/mcp/cicd/tools.py`, `scripts/mcp/cicd/server.py`
6. **mdq** — `scripts/mcp/mdq/tools.py`, `scripts/mcp/mdq/server.py`

### Migration Steps per MCP Server

1. Rename `_MCP_TOOLS` → `TOOL_LIST` in `tools.py`
2. Update import in `server.py`: `from mcp.<name>.tools import TOOL_LIST`
3. Update any other references to `_MCP_TOOLS` within the MCP server module
4. Update tests that reference `_MCP_TOOLS` for this MCP server
5. Remove any `_MCP_TOOLS` compatibility alias if present

### Implementation Order (Recommended)

1. git — smallest scope, fewest cross-references
2. web_search — single tool, low risk
3. shell — single tool, low risk
4. cicd — 4 tools, moderate scope
5. rag_pipeline — 4 tools, high usage (needs careful testing)
6. mdq — 9 tools, largest scope

### Validation

After each migration:
- Run: `rg -n "_MCP_TOOLS" scripts/mcp/<name>/` — should return no results
- Run: `pytest tests/test_<name>_mcp_service.py -v`
- Run: `python scripts/checks/check_no_compat.py`
