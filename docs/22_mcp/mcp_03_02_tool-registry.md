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

Two comparison functions (`shared/tool_routing_validation.py`) detect configuration drift.

| Function | Comparison Target | When Called |
|---|---|---|
| `validate_routing_against_config()` | config's `tool_names` vs. Registry | At startup (`agent/services/routing_drift.py::check_routing_drift()`, called from `startup_validation`) |
| `validate_routing_against_live()` | live `/v1/tools` vs. Registry | At startup (`McpToolDiscoveryService` drift verification) |

> **Startup Verification Semantics** — The aforementioned `validate_routing_against_config()` and `validate_routing_against_live()` functions compare the live `/v1/tools` against the internal routing registry. This is distinct from the tool definition check performed by `McpToolDiscoveryService`, which compares configured `tool_definitions` (from `agent.toml`) against live `/v1/tools`. For behavior upon startup failure due to `tool_definitions_strict`, see [mcp_06 Startup Validation Behavior](mcp_06_09_startup-validation-behavior-tool_definitions_strict.md#startup-validation-behavior-tool_definitions_strict).

Drift warnings are displayed during agent startup.

To resolve a drift warning, update `tool_names` under `[mcp_servers.<key>]` in `config/agent.toml`, or the static registry source (`shared/tool_constants.py`).

A registered tool listed in `CONFIG_GATED_TOOLS` is exempt from the registry-versus-config and registry-versus-live absence checks, because its server withholds it until a config prerequisite is met. Currently this is `browser_fetch`, which web-search-mcp withholds while `browser_allowed_domains` is empty. The absence of any other registered tool, and any config or live tool name that is not in the registry, is still drift. (`CONFIG_GATED_TOOLS` in `scripts/shared/tool_constants.py`)

### Adding a New Tool

For detailed procedures, refer to [Adding a new tool](mcp_03_05_lifecycle-and-new-server.md#adding-a-new-tool). Note that `tool_names` is not an input for routing, but metadata for drift verification.

### Verification

After registration is complete, run the routing tests (`tests/shared/test_tool_constants.py`, `tests/shared/test_route_resolver.py`); all must pass. If `tool_definitions_strict = true`, restart the agent and verify that no `Routing drift` warnings appear in the startup logs.

### Concurrency Limits

`concurrency_limits={"server_key": N}` limits concurrent calls per server to `N`. Implemented as lazily generated `asyncio.Semaphore`. If an unknown key is provided, only a warning log is output.

### Side-effect Detection

Parallel/serial determination is owned by the DAG scheduler and reads `PreparedToolCall.spec.is_write`, resolved via `RuntimeToolRegistry` before the approval phase. Unregistered tools, or calls without a `RuntimeToolRegistry` connection, are rejected in the preparation phase (fail-closed) and never reach scheduling. `serial_tool_calls` is passed to the scheduler as `force_serial` rather than selecting another engine. Details: [mcp_03_01](mcp_03_01_dispatch-and-routing.md#serialization-mechanism-integrated-into-a-single-scheduler).

### Safety Tier Verification

- `check_tool_safety_tiers()`: Warns about registered tools not declared in `tool_safety_tiers`. Called at startup from `agent/services/routing_drift.py`.
- `check_unknown_tool_safety_tiers()`: Detects when a key in `tool_safety_tiers` is unregistered (e.g., specifying a server key instead of an individual tool name). Called from `agent/production_config_validator.py`.
- Both functions return an empty list if `tool_safety_tiers` is empty/unset (skipping checks).

### ToolSpec

`ToolSpec` (`shared/tool_spec.py`, frozen) carries the execution metadata of one approved tool call: `call_id`, `name`, `args`, kind-prefixed `resource_scopes`, `requires_serial`, `is_write`. It is built per call by `RuntimeToolRegistry.tool_spec_for_call()` and consumed by the scheduler as a `dict[str, ToolSpec]` keyed by `call_id`; see [mcp_03_01](mcp_03_01_dispatch-and-routing.md#data-source-for-dag-scheduling).

### `RuntimeToolRegistry` and Live Discovery

`RuntimeToolRegistry` (`shared/runtime_tool_registry.py`) is separate from `ToolRegistry`. `McpToolDiscoveryService` (`agent/services/mcp_tool_discovery.py`) fetches `/v1/tools` live from each HTTP MCP server and validates the response shape; the fetch and response/entry validation live in `agent/services/mcp_tool_discovery_fetch.py`, and registry building in `mcp_tool_discovery_registry.py`. In addition to `name`/`description`/`inputSchema`, four fields (`is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys`) are **mandatory** under the schema-2.0 contract (`shared/resource_scope.py::validate_tool_schema_v2()` verifies type, known kinds, and that `resource_scope_keys` exist in `inputSchema.properties`). A tool with missing or invalid fields is excluded from the registry; silent default application is not allowed. `status`, legacy singular `resource_scope`, and `enabled` are validated only if present. Tools with duplicate names across servers are excluded and a `FATAL` `StartupCheckOutcome` is returned regardless of `strict` or `required`; startup propagates it via `pipeline.add_fatal()` and aborts.

Discovery runs at startup and the result is connected through `ToolExecutor.set_runtime_registry()`. `ToolRouteResolver.resolve()` refers only to `RuntimeToolRegistry`. `ToolRegistry` is NOT used for routing decisions—it functions solely as drift detection data for the `tool_constants.py` frozenset (see the explanation at the beginning of this document; `agent/tool_policy.py::classify_operation_type()` does not consult `ToolRegistry` — see ADR-003 Decision Detail #8).

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
