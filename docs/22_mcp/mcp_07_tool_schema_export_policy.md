---
title: "MCP Tool Schema Export Policy"
area: mcp
tags:
  - mcp
  - tool-schema
  - export-policy
related:
  - mcp_00_document-guide.md
  - mcp_03_02_tool-registry.md
---
# MCP Tool Schema Export Policy

## Standard Export Name: `TOOL_LIST`

All MCP server tool schema modules (`scripts/mcp_servers/<server_name>/<server_name>_tools.py`) must export the standard tool list as `TOOL_LIST`.

Related: [mcp_03_02_tool-registry.md](mcp_03_02_tool-registry.md) — describes the ownership and routing roles of `ToolRegistry` (different from the schema export role described in this document).

### Rationale

- `TOOL_LIST` is a prefix-less public name, clearly indicating it is the primary export.
- GitHub MCP already uses `TOOL_LIST` as its standard name (see `scripts/mcp_servers/github/github_tools.py`).

### Verification

`tests/mcp_servers/test_mcp_tool_schema_exports.py` mechanically verifies that every active MCP tool schema module exports `TOOL_LIST` as a non-empty list of dictionaries with a `"name"` key and that no module still uses the legacy `_MCP_TOOLS`. Per-server service tests are `tests/test_<name>_mcp_service.py`.

### Design Constraints

- Under the Schema 2.0 contract every `TOOL_LIST` entry declares `is_write`, `requires_serial`, `resource_scope_kind`, and `resource_scope_keys`; discovery excludes a tool missing any of them (`agent/services/mcp_tool_discovery.py`).
- Each server assigns its `TOOL_LIST` to the `mcp_tools` attribute of its `MCPServer` subclass. `MCPServer.list_tools()` is an introspection helper with no production call site: each server's `/v1/tools` route annotates its own `TOOL_LIST` and returns it through `build_tools_response()`, and startup discovery reads those HTTP responses.
- LLM tool schemas (description, inputSchema) originate from each server's `TOOL_LIST`, not from `shared/tool_registry.py`; the `description` and `input_schema` fields of `ToolDefinition` there are reserved and unset.

## Keywords

- mcp
- tool-schema
- export
- policy
