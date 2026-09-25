---
title: "MCP Tool Schema Export Policy"
area: mcp
tags:
  - mcp
  - tool-schema
  - export-policy
related:
---
# MCP Tool Schema Export Policy

## Standard Export Name: `TOOL_LIST`

All MCP server tool schema modules (`scripts/mcp_servers/<server_name>/<server_name>_tools.py`) must export the standard tool list as `TOOL_LIST`.

Related: [04_mcp_03_02_tool-registry.md](04_mcp_03_02_tool-registry.md) — describes the ownership and routing roles of `ToolRegistry` (different from the schema export role described in this document).

### Rationale

- `TOOL_LIST` is a prefix-less public name, clearly indicating it is the primary export.
- GitHub MCP already uses `TOOL_LIST` as its standard name (see `scripts/mcp_servers/github/github_tools.py`).

### Migration History

All MCP servers have completed migration to `TOOL_LIST`. The migration was performed in the following order:

1. **git** — `scripts/mcp_servers/git/git_tools.py`, `scripts/mcp_servers/git/git_server.py`
2. **mdq** — `scripts/mcp_servers/mdq/mdq_tools.py`, `scripts/mcp_servers/mdq/mdq_server.py`
3. **rag_pipeline** — `scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
4. **shell** — `scripts/mcp_servers/shell/shell_tools.py`, `scripts/mcp_servers/shell/shell_server.py`
5. **cicd** — `scripts/mcp_servers/cicd/cicd_tools.py`, `scripts/mcp_servers/cicd/cicd_server.py`
6. **web_search** — `scripts/mcp_servers/web_search/web_search_tools.py`, `scripts/mcp_servers/web_search/web_search_server.py`
7. **file_read** — `scripts/mcp_servers/file/read_tools.py`, `scripts/mcp_servers/file/read_server.py`
8. **file_write** — `scripts/mcp_servers/file/write_tools.py`, `scripts/mcp_servers/file/write_server.py`
9. **file_delete** — `scripts/mcp_servers/file/delete_tools.py`, `scripts/mcp_servers/file/delete_server.py`

Note: In some servers, there was a period where both bare names (`tools.py`/`server.py`) and renamed files (`<server>_tools.py`/`<server>_server.py`) coexisted. This is being tracked in issues/20260719-193357_risks.md.

### Verification

After all migrations are complete:
- Run: `pytest tests/test_<name>_mcp_service.py -v`
- Run: `pytest tests/test_mcp_tool_schema_exports.py -v` — verifies that all active MCP tool schema modules export `TOOL_LIST` as a non-empty list of dictionaries containing a `"name"` key, and ensures no modules are still using the legacy `_MCP_TOOLS`.

### Implementation Notes (Current behavior)

- `tests/test_mcp_tool_schema_exports.py` lists all 9 modules (`shell`, `cicd`, `git`, `rag_pipeline`, `web_search`, `mdq`, `github`, `file.read_tools`, `file.write_tools`, `file.delete_tools`) in `_TOOL_MODULES`, mechanically verifying that each module exports `TOOL_LIST` as a non-empty list and does not contain `_MCP_TOOLS`. As far as implementation can be confirmed, migration to `TOOL_LIST` has been completed for all modules including `file.delete_tools`. (Basis: Explicit in code)
- Only `mdq/mdq_tools.py` explicitly defines the element type of `TOOL_LIST` as `MCPToolSchema` (`TypedDict` with `status` and optional fields like `is_write`/`requires_serial`/`resource_scope_kind`/`resource_scope_keys`). In `mdq/mdq_server.py`, it is assigned to `MCPServer.mcp_tools` (`list[dict[str, Any]]`) via `mcp_tools = cast(list[dict[str, Any]], TOOL_LIST)`. Although `TypedDict` allows `NotRequired`, actual `TOOL_LIST` entries for all tools explicitly declare these 4 fields, making them mandatory under the Schema 2.0 contract at the point of discovery by `agent/services/mcp_tool_discovery.py` (missing fields cause individual tools to be excluded from the registry). Other servers use `list[dict[str, Any]]` or `list[dict]` at the time of `TOOL_LIST` declaration and do not require casting. (Basis: Explicit in code)
- Each server's `server.py` imports `TOOL_LIST` from `tools.py` and assigns it to the `mcp_tools` class attribute of the `MCPServer` subclass. `MCPServer.list_tools()` returns a list of tool names for the agent, while `list_tools_with_server_key()` returns tool definitions with an added `server_key`; the latter is used for the `/v1/tools` endpoint and tool discovery during startup (`scripts/mcp_servers/server.py`). Some `server.py` files for `file.read_tools`, `file.write_tools`, and `file.delete_tools` convert `TOOL_LIST` directly to include the `server_key` within the `/v1/tools` handler instead of using `list_tools_with_server_key()` (e.g., `scripts/mcp_servers/file/read_server.py`). (Basis: Explicit in code)
- The `description` and `input_schema` fields of `ToolDefinition` in `shared/tool_registry.py` are reserved for future use and are explicitly not set in `_populate_default_registry()`. It is explicitly stated in code comments that LLM tool schemas (description, inputSchema) originate from the `TOOL_LIST` in each server's `tools.py`, not from this registry. This is consistent with this document. (Basis: Explicit in code)

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_02_tool-registry.md`

## Keywords

mcp
tool-schema
export
policy
