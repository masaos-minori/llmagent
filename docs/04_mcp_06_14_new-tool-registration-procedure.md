---
title: "New Tool Registration Procedure"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# New Tool Registration Procedure

## New Tool Registration Procedure

### /v1/tools Requirements

Before registering a new tool, ensure your MCP server responds to `/v1/tools` requests with the correct format. See [endpoints-and-transport.md](./04_mcp_02_01_endpoints-and-transport.md) for the complete field specification.

#### Required fields

- `name`: Unique tool identifier
- `description`: Human-readable description of the tool
- `inputSchema`: JSON Schema defining the tool's input parameters
- `is_write`: Whether the tool performs write operations (schema-2.0 contract)
- `requires_serial`: Whether the tool requires serialized execution (schema-2.0 contract)
- `resource_scope_kind`: Scope-kind prefix used for conflict detection, e.g. `"filesystem"`, `"git_repo"`, or `""` for unscoped (schema-2.0 contract)
- `resource_scope_keys`: Argument-dict keys whose values are resolved into the call's actual scope strings (schema-2.0 contract; each key must exist in `inputSchema.properties`)

These four schema-2.0 fields are validated by `shared/resource_scope.py::validate_tool_schema_v2()`
and enforced by `agent/services/mcp_tool_discovery.py::McpToolDiscoveryService`. A tool entry
missing any of them, or failing validation, is rejected and excluded from the built
`RuntimeToolRegistry` — it is never silently defaulted.

#### Optional fields

- `status`: Tool status (e.g., "available", "degraded")
- `resource_scope`: legacy singular scope field; type-checked only if present, not required
- `enabled`: Whether the tool is enabled for LLM use
- `capabilities`: Tool capabilities object
- `server_key`: Identifier for the MCP server providing the tool
- `config_dependent`: Whether the tool depends on configuration
- `disabled_reason`: Reason why the tool is disabled (if applicable)

#### Deferred fields

The following fields are deferred and may not be supported yet:

- `disabled_code`: Structured error code for disabled tools (deferred)

When adding a new tool to an **existing** MCP server:

| Step | Action | Required? |
|---|---|---|
| 1 | Add the tool name to the corresponding `frozenset` in `shared/tool_constants.py` (e.g., add to `READ_TOOLS`, `WRITE_TOOLS`, or create a new `<SERVER>_TOOLS` frozenset and add it to `get_all_mcp_tool_names()`) | **[Required]** |
| 2 | The registry is automatically built from these frozensets upon import — manual editing of the registry is not required | (Automatic) |
| 3 | Implement the `dispatch()` handler in the owner MCP server (`scripts/mcp_servers/<name>/server.py`) | **[Required]** |
| 4 | Expose the tool via the `/v1/tools` endpoint (return a tool definition including the `server_key` field) | **[Recommended]** — enables drift validation at startup but does not affect routing |
| 5 | Add the LLM schema to `[[tool_definitions]]` in `config/agent.toml` (OpenAI function-calling format) | **[Required]** — if the tool is to be visible to the LLM |
| 6 | Add an entry for the new tool to `tool_safety_tiers` in `config/agent.toml` | **[Required]** — all tools must declare their safety tier |
| 7 | Add the tool name to the `tool_names` section of `[mcp_servers.<key>]` in `config/<key>_mcp_server.toml` | **[Optional]** — only enables drift validation at startup; not required for routing |

**Note**: All tools must be explicitly registered in the `ToolRegistry`. Prefix-based routing does not exist.

### Verification

After registration is complete:

```bash
uv run pytest tests/test_tool_constants.py tests/test_route_resolver.py -v
```

**Expected results:** All routing tests pass. If `tool_definitions_strict = true`, restart the agent and verify that `"Routing: N/N tools mapped"` is displayed in the startup logs without unmapped warnings.

---

					

## Metadata update paths

`/v1/tools` is now the single source of tool metadata for both runtime availability and DAG
scheduling:

- **LLM visibility / routing**: `RuntimeToolRegistry` (built by `McpToolDiscoveryService` from
  live `/v1/tools` discovery) is the sole routing authority.
- **DAG scheduling**: `agent/tool_runner.py::_execute_with_dag()` builds a per-call `ToolSpec`
  via `RuntimeToolRegistry.tool_spec_for_call()`, which reads the same tool's `is_write`,
  `requires_serial`, `resource_scope_kind`, and `resource_scope_keys` declared in `/v1/tools`.

Updating a tool's `/v1/tools` declaration (its `TOOL_LIST` entry in the owning MCP server)
therefore changes both what the LLM sees/routes to and how the tool is scheduled in the DAG —
there is no separate `config/agent.toml`-driven scheduling metadata path. `config/agent.toml`'s
`[[tool_definitions]]` only supplies the LLM-facing function-calling schema (name, description,
parameters) and carries no scheduling metadata.

See [dispatch-and-routing.md](./04_mcp_03_01_dispatch-and-routing.md#data-source-for-dag-scheduling) for details.

---



## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
