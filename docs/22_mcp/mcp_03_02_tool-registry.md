---
title: "Tool Registry: Drift Verification, Adding Tools, Cache and Concurrency"
area: mcp
tags:
  - mcp
  - routing
  - tool-registry
related:
  - mcp_00_document-guide.md
  - mcp_03_01_dispatch-and-routing.md
  - mcp_03_03_transport-and-health.md
  - mcp_03_04_tool-call-tracing-and-lifecycle.md
  - mcp_03_05_lifecycle-and-new-server.md
  - mcp_03_06_tool-runtime-availability-metadata.md
  - mcp_07_tool_schema_export_policy.md
  - mcp_06_09_startup-validation-behavior-tool_definitions_strict.md
---

# Tool Registry: Drift Verification, Adding Tools, Cache and Concurrency

The responsibility of `ToolRegistry` is to manage the ownership relationship from tools to servers, not as a schema registry. Runtime routing is exclusively authorized by `RuntimeToolRegistry`, and `ToolRegistry` is NOT used for routing decisions (see the "`RuntimeToolRegistry` and Live Discovery" section at the end of this document for details). `ToolRegistry` has one production use: input data for `McpToolDiscoveryService`'s drift detection. This use is a formalized architectural decision — see ADR-003 Decision Detail #15 / INV-04. `agent/tool_policy.py::classify_operation_type()` checks the `tool_constants.py` frozensets first for the WRITE/DELETE/EXECUTE/API_WRITE categories, and consults `RuntimeToolRegistry` to separate WRITE (a registered write tool), READ (any other registered tool) and UNKNOWN (unregistered), per ADR-003 Decision Detail #8 and INV-03. `ToolDefinition.description` / `input_schema` are reserved and unused here. The canonical source for the schemas of tools visible to the LLM is each server's `TOOL_LIST` ([mcp_07_tool_schema_export_policy.md](mcp_07_tool_schema_export_policy.md)).

## Drift Verification

### Drift validation

Three comparison functions (defined in `shared/tool_routing_validation.py`) detect configuration drift.

| Function | Comparison Target | When Called |
|---|---|---|
| `validate_routing_against_config()` | config's `tool_names` vs. Registry | At startup (`agent/services/routing_drift.py::check_routing_drift()`, called from `startup_validation`) |
| `validate_routing_against_live()` | live `/v1/tools` vs. Registry | At startup (`McpToolDiscoveryService` drift verification) |

> **Startup Verification Semantics** — The aforementioned `validate_routing_against_config()` and `validate_routing_against_live()` functions compare the live `/v1/tools` against the internal routing registry. This is distinct from the tool definition check performed by `McpToolDiscoveryService`, which compares configured `tool_definitions` (from `agent.toml`) against live `/v1/tools`. For behavior upon startup failure due to `tool_definitions_strict`, see [mcp_06 Startup Validation Behavior](mcp_06_09_startup-validation-behavior-tool_definitions_strict.md#startup-validation-behavior-tool_definitions_strict).

Drift warnings are displayed during agent startup.

``` text
WARNING Routing drift [file_read]: [file_read] tool 'read_multiple_files' in registry but not in config
```

To resolve a drift warning, update `tool_names` under `[mcp_servers.<key>]` in `config/agent.toml`, or the static registry source (`shared/tool_constants.py`). (Explicit in code — `scripts/shared/mcp_config.py::McpServerConfig.tool_names`)

A registered tool listed in `CONFIG_GATED_TOOLS` is exempt from the registry-versus-config and registry-versus-live absence checks, because its server withholds it until a config prerequisite is met. Currently this is `browser_fetch`, which web-search-mcp withholds while `browser_allowed_domains` is empty. The absence of any other registered tool, and any config or live tool name that is not in the registry, is still drift. (Explicit in code — `scripts/shared/tool_constants.py::CONFIG_GATED_TOOLS`, `scripts/shared/tool_registry.py::ToolRegistry.validate_tool_names_match`)

### Adding a New Tool

For detailed procedures, refer to [Adding a new tool](mcp_03_05_lifecycle-and-new-server.md#adding-a-new-tool). Note that `tool_names` is not an input for routing, but metadata for drift verification.

### Verification

After registration is complete:

```bash
uv run pytest tests/test_tool_constants.py tests/test_route_resolver.py -v
```

Expected result: All routing tests pass. If `tool_definitions_strict = true`, restart the agent and verify that no `Routing drift` warnings appear in the startup logs.

### Main APIs

```python
from shared.tool_registry import get_registry

registry = get_registry()
server_key = registry.get_server_for_tool("read_text_file")  # → "file_read"
tool_names = registry.get_tool_names("file_read")  # → ["read_text_file", ...]
all_tools = registry.get_all_tool_names()  # → frozenset of all tool names
```

```python
executor = ToolExecutor(
    http=httpx.AsyncClient(...),
    server_configs=server_configs,
    concurrency_limits={"file_write": 1},
    lifecycle=lifecycle_router,
)
result = await executor.execute("read_text_file", {"path": "/opt/llm/..."})
# result: ToolCallResult(output, is_error, request_id, server_key)
```

### Concurrency Limits

`concurrency_limits={"server_key": N}` limits concurrent calls per server to `N`. Implemented as lazily generated `asyncio.Semaphore`. If an unknown key is provided, only a warning log is output.

### Side-effect Detection

Batch execution parallel/serial determination is delegated to `agent/tool_runner.py::_execute_with_dag()` via `agent/tool_scheduler.py::build_execution_groups()`, which references `PreparedToolCall.spec.is_write` (resolved via `RuntimeToolRegistry` in `agent/tool_preparation.py::prepare_tool_calls()` before the approval phase) to determine parallel/serial execution (unregistered tools or calls without a connection to `RuntimeToolRegistry` are rejected in the preparation phase via fail-closed, so they never reach scheduling or execution). `serial_tool_calls` is not a branch to another execution engine, but is passed to the scheduler as `force_serial` input to `build_execution_groups()`; if `True`, it bypasses phase construction/conflict graph construction and forces individual serial phases for each call in order.

### Safety Tier Verification

- `check_tool_safety_tiers()`: Warns about registered tools not declared in `tool_safety_tiers`. Called from `agent/services/routing_drift.py` during startup (Explicit in code).
- `check_unknown_tool_safety_tiers()`: Detects when a key in `tool_safety_tiers` is unregistered (e.g., specifying a server key instead of an individual tool name). Called from `agent/production_config_validator.py` (Explicit in code).
- Both functions return an empty list if `tool_safety_tiers` is empty/unset (skipping checks).

### Implementation Notes (Current behavior): ToolSpec

- `shared/tool_spec.py`'s `ToolSpec` (frozen dataclass) holds execution metadata for a single approved tool call (`call_id`, `name`, `args`, `resource_scopes` (tuple of strings with kind prefixes), `requires_serial`, `is_write`). `agent/tool_runner.py::_execute_with_dag()` constructs it for every call via `RuntimeToolRegistry.tool_spec_for_call(call_id, name, args)` (which internally calls `shared/resource_scope.py::resolve_resource_scopes()` to resolve `resource_scopes`) and passes it to `agent/tool_scheduler.py::build_execution_groups()` as a `dict[str, ToolSpec]` keyed by `call_id`, which is then used for parallel/serial determination as a single `ExecutionPlan` (`batches`/`ScheduledGroup`/`SerializationEvent`). (Explicit in code)

### `RuntimeToolRegistry` and Live Discovery

`shared/runtime_tool.py` (`RuntimeTool`, `build_runtime_tool()`) and `shared/runtime_tool_registry.py` (`RuntimeToolRegistry`) are additional modules separate from the existing `shared.tool_registry.ToolRegistry` described in this document. `agent/services/mcp_tool_discovery.py`'s `McpToolDiscoveryService` (`async def discover_all() -> DiscoveryResult`) fetches `/v1/tools` live from each HTTP transport MCP server and validates the response shape; the round-trip itself and its response- and entry-level validation are implemented in `agent/services/mcp_tool_discovery_fetch.py`, which the service calls. In addition to `name`/`description`/`inputSchema`, four fields—`is_write`/`requires_serial`/`resource_scope_kind`/`resource_scope_keys`—are **mandatory** under the schema-2.0 contract (with `shared/resource_scope.py::validate_tool_schema_v2()` verifying type, known kinds, and presence of `resource_scope_keys` within `inputSchema.properties`); any individual tool with missing or invalid fields is excluded from the registry (silent default application is not allowed). `status`/`resource_scope` (legacy singular form)/`enabled` are validated only if present. Tools with duplicate names across servers are excluded from the registry and a `FATAL` `StartupCheckOutcome` is returned regardless of `strict` or `required` settings (explicitly implemented in `_dedupe_and_build()`, which with `_detect_duplicates()` and `_build_runtime_tools()` forms the registry-building layer in `agent/services/mcp_tool_discovery_registry.py`). Startup pipelines propagate `FATAL` via `pipeline.add_fatal()`, causing startup to abort.

**(Explicit in code)** `McpToolDiscoveryService` is called from `startup.py`. `ToolExecutor.set_runtime_registry(runtime_reg)` connects the `RuntimeToolRegistry`. `ToolRouteResolver.resolve()` refers only to `RuntimeToolRegistry` for resolution. `ToolRegistry` is NOT used for routing decisions—it functions solely as drift detection data for the `tool_constants.py` frozenset (see the explanation at the beginning of this document; `agent/tool_policy.py::classify_operation_type()` does not consult `ToolRegistry` — see ADR-003 Decision Detail #8).

## Keywords

- mcp
- routing
- ToolRegistry
- ToolSpec
- concurrency limits
- side effect detection
- routing drift
- tool safety tiers
- RuntimeToolRegistry
- McpToolDiscoveryService
