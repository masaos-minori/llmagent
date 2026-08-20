---
title: "Tool Registry: Drift Verification, Adding Tools, Cache and Concurrency"
category: mcp
tags:
  - mcp
  - routing
  - tool-registry
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_01_dispatch-and-routing.md
  - 04_mcp_03_03_transport-and-health.md
  - 04_mcp_03_04_tool-call-tracing-and-watchdog.md
  - 04_mcp_03_05_lifecycle-and-new-server.md
  - 04_mcp_07_tool_schema_export_policy.md
---

# Tool Registry: Drift Verification, Adding Tools, Cache and Concurrency

The responsibility of `ToolRegistry` is to manage the ownership relationship from tools to servers, not as a schema registry. Runtime routing is exclusively authorized by `RuntimeToolRegistry`, and `ToolRegistry` is NOT used for routing decisions (see the "`RuntimeToolRegistry` and Live Discovery" section at the end of this document for details). `ToolRegistry` is still maintained for two production uses: (a) input data for `McpToolDiscoveryService`'s drift detection, and (b) the fail-safe membership check that `agent/tool_policy.py::classify_operation_type()` (`tool_policy.py:69`) references via `get_all_tool_names()` to determine whether a tool is known at all. `ToolDefinition.description` / `input_schema` are reserved and unused here. The canonical source for the schemas of tools visible to the LLM is each server's `TOOL_LIST` ([04_mcp_07_tool_schema_export_policy.md](04_mcp_07_tool_schema_export_policy.md)).

## Drift Verification

### Drift validation

Three comparison functions detect configuration drift.

| Function | Comparison Target | When Called |
|---|---|---|
| `validate_routing_against_config()` | config's `tool_names` vs. Registry | At startup (`McpToolDiscoveryService` drift verification) |
| `validate_routing_against_live()` | live `/v1/tools` vs. Registry | At startup (`McpToolDiscoveryService` drift verification) |
| `validate_all_routing()` | Combination of both above | Not yet implemented (future support) |

> **Startup Verification Semantics** — The aforementioned `validate_routing_against_live()` and `validate_all_routing()` functions compare the live `/v1/tools` against the internal routing registry. This is distinct from the tool definition check performed by `McpToolDiscoveryService`, which compares configured `tool_definitions` (from `agent.toml`) against live `/v1/tools`. For behavior upon startup failure due to `tool_definitions_strict`, see [04_mcp_06 §Startup Validation Behavior](04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md#startup-validation-behavior-tool_definitions_strict).

Drift warnings are displayed during agent startup.

``` text
WARNING Routing drift [file_read]: [file_read] tool 'read_multiple_files' in registry but not in config. Update file_read_mcp_server.toml [mcp_servers.file_read] tool_names or the registry to resolve.
```

### Adding a New Tool

For detailed procedures, refer to [Adding a new tool](docs/04_mcp_03_05_lifecycle-and-new-server.md#adding-a-new-tool). Note that `tool_names` is not an input for routing, but metadata for drift verification.

### Verification

After registration is complete:

```bash
uv run pytest tests/test_tool_constants.py tests/test_route_resolver.py -v
```

Expected result: All routing tests pass. If `tool_definitions_strict = true`, restart the agent and verify that `"Routing: N/N tools mapped"` appears in the startup logs with no unmapped warnings.

### Main APIs

```python
from shared.tool_registry import get_registry, validate_all_routing

registry = get_registry()
server_key = registry.get_server_for_tool("read_text_file")  # → "file_read"
tool_names = registry.get_tool_names("file_read")  # → ["read_text_file", ...]
all_tools = registry.get_all_tool_names()  # → frozenset of all tool names
mismatches = validate_all_routing(server_configs, live_tool_lists)  # → dict[str, list[str]]
```

```python
executor = ToolExecutor(
    http=httpx.AsyncClient(...),
    cache_ttl=300.0,
    server_configs=server_configs,
    cache_max_size=200,
    concurrency_limits={"file_write": 1},
    lifecycle=lifecycle_router,
)
result = await executor.execute("read_text_file", {"path": "/opt/llm/..."})
# result: ToolCallResult(output, is_error, request_id, server_key)
```

### Cache Behavior

- Only results with `is_error=False` are cached.
- Cache key: `"tool_name:args_json"` (plain string; not MD5).
- Entries expire after `cache_ttl` seconds.
- If `cache_max_size > 0`, entries are removed via LRU (0 = unlimited).
- On cache hit: `request_id=""` (no live request is made).
- Statistics: `stat_cache_hits: int`

### Concurrency Limits

`concurrency_limits={"server_key": N}` limits concurrent calls per server to `N`. Implemented as lazily generated `asyncio.Semaphore`. If an unknown key is provided, only a warning log is output.

### Side-effect Detection

```python
_SIDE_EFFECT_TOOLS = (
    WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
    | GIT_WRITE_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
    | CICD_WRITE_TOOLS | RAG_WRITE_TOOLS | MDQ_WRITE_TOOLS
)
is_side_effect(tool_name: str) -> bool
```

`is_side_effect()`/`_SIDE_EFFECT_TOOLS` (`shared/tool_executor_helpers.py`) is currently used only for bypassing the TTL cache in `shared/tool_executor.py`. Batch execution parallel/serial determination is delegated to `agent/tool_runner.py::_execute_with_dag()` via `agent/tool_scheduler.py::build_execution_groups()`, which references `PreparedToolCall.spec.is_write` (resolved via `RuntimeToolRegistry` in `agent/tool_preparation.py::prepare_tool_calls()` before the approval phase) to determine parallel/serial execution (unregistered tools or calls without a connection to `RuntimeToolRegistry` are rejected in the preparation phase via fail-closed, so they never reach scheduling or execution ("fallback to treating everything as having side effects" has been deprecated). `serial_tool_calls` is not a branch to another execution engine, but is passed to the scheduler as `force_serial` input to `build_execution_groups()`; if `True`, it bypasses phase construction/conflict graph construction and forces individual serial phases for each call in order.

### Safety Tier Verification

- `check_tool_safety_tiers()`: Warns about registered tools not declared in `tool_safety_tiers`. Called from `agent/repl_health.py` during startup (Explicit in code).
- `check_unknown_tool_safety_tiers()`: Detects when a key in `tool_safety_tiers` is unregistered (e.g., specifying a server key instead of an individual tool name). Called from `shared/production_config_validator.py` (Explicit in code).
- Both functions return an empty list if `tool_safety_tiers` is empty/unset (skipping checks).

### Implementation Notes (Current behavior): tool_cache.py and ToolSpec

- `shared/tool_cache.py`'s `ToolResultCache` (LRU + TTL) is currently not used by `ToolExecutor`. `ToolExecutor` uses its own `OrderedDict`-based cache (see "Cache Behavior" section above), which is tightly coupled with stampede protection (inflight future sharing); it is used instead. `ToolResultCache` is not deprecated, but remains a standalone utility for future users who do not require stampede protection. (Explicit in code: `shared/tool_cache.py` module docstring)
- `shared/tool_spec.py`'s `ToolSpec` (frozen dataclass) holds execution metadata for a single approved tool call (`call_id`, `name`, `args`, `resource_scopes` (tuple of strings with kind prefixes), `requires_serial`, `is_write`). `agent/tool_runner.py::_execute_with_dag()` constructs it for every call via `RuntimeToolRegistry.tool_spec_for_call(call_id, name, args)` (which internally calls `shared/resource_scope.py::resolve_resource_scopes()` to resolve `resource_scopes`) and passes it to `agent/tool_scheduler.py::build_execution_groups()` as a `dict[str, ToolSpec]` keyed by `call_id`, which is then used for parallel/serial determination as a single `ExecutionPlan` (`batches`/`ScheduledGroup`/`SerializationEvent`). (Explicit in code)

### `RuntimeToolRegistry` and Live Discovery (Implemented)

`shared/runtime_tool.py` (`RuntimeTool`, `build_runtime_tool()`) and `shared/runtime_tool_registry.py` (`RuntimeToolRegistry`) are additional modules separate from the existing `shared.tool_registry.ToolRegistry` described in this document. `agent/services/mcp_tool_discovery.py`'s `McpToolDiscoveryService` (`async def discover_all() -> DiscoveryResult`) fetches `/v1/tools` live from each HTTP transport MCP server and validates the response shape. In addition to `name`/`description`/`inputSchema`, four fields—`is_write`/`requires_serial`/`resource_scope_kind`/`resource_scope_keys`—are **mandatory** under the schema-2.0 contract (with `shared/resource_scope.py::validate_tool_schema_v2()` verifying type, known kinds, and presence of `resource_scope_keys` within `inputSchema.properties`); any individual tool with missing or invalid fields is excluded from the registry (silent default application is not allowed). `status`/`resource_scope` (legacy singular form)/`enabled` are validated only if present. Tools with duplicate names across servers are excluded from the registry and a `FATAL` `StartupCheckOutcome` is returned regardless of `security_profile` (production/local) or `strict` settings (explicitly implemented in `_dedupe_and_build()`). Startup pipelines propagate `FATAL` via `pipeline.add_fatal()`, causing startup to abort.

**[Explicit in code]** `McpToolDiscoveryService` is called from `startup.py`. `ToolExecutor.set_runtime_registry(runtime_reg)` connects the `RuntimeToolRegistry`. `ToolRouteResolver.resolve()` refers only to `RuntimeToolRegistry` for resolution. `ToolRegistry` is NOT used for routing decisions—it functions solely as drift detection data for the `tool_constants.py` frozenset, and as the fail-safe membership check for `agent/tool_policy.py::classify_operation_type()` (`tool_policy.py:69`) (see the explanation at the beginning of this document).

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_01_dispatch-and-routing.md`
- `04_mcp_03_03_transport-and-health.md`
- `04_mcp_03_04_tool-call-tracing-and-watchdog.md`
- `04_mcp_03_05_lifecycle-and-new-server.md`
- `04_mcp_07_tool_schema_export_policy.md`

## Keywords

mcp
routing
ToolRegistry
tool cache
ToolResultCache
ToolSpec
concurrency limits
side effect detection
routing drift
tool safety tiers
RuntimeToolRegistry
McpToolDiscoveryService
