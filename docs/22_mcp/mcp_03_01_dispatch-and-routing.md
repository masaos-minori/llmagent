---
title: "Tool Call Dispatch Flow and Routing Resolution"
area: mcp
tags:
  - mcp
  - routing
  - lifecycle
related:
  - mcp_00_document-guide.md
  - mcp_03_02_tool-registry.md
  - mcp_03_03_transport-and-health.md
  - mcp_03_04_tool-call-tracing-and-lifecycle.md
  - mcp_03_05_lifecycle-and-new-server.md
---

# MCP Tool Call Dispatch Flow and Routing Resolution

- System Overview → [mcp_01_system_overview.md](mcp_01_system_overview.md)

## Purpose

To document tool routing, server startup/shutdown lifecycles, the internal structure of `ToolExecutor`, on-demand restart behavior (there is no background watchdog), idle timeouts, and procedures for adding new servers.

---

## Tool Call Dispatch Flow

The agent sets the `server_key` and `tool_name` in the dispatch log context. The `X-Request-Id` (returned in the HTTP response header of the MCP server) correlates the agent's dispatch logs with transport and server audit logs.

``` text
LLM returns tool_call
   → ToolRouteResolver.resolve(tool_name) → server_key
   → ToolExecutor.execute(tool_name, args)
         1. MCP server dispatch (internal dispatch)
             → startup_mode==none gate → immediate error ("disabled (startup_mode=none)")
             → McpServerHealthRegistry: is_unavailable? → return error immediately (no attempt made)
               (if HALF_OPEN, allow as a trial dispatch)
             → LifecycleProtocol.ensure_ready(server_key)
             → concurrency semaphore acquire (if configured)
             → HttpTransport.call()
             → HealthRegistry.record_success() on success / record_failure() on transport error
             → return ToolCallResult(output, is_error, request_id, server_key)
```

### Implementation Notes (Current behavior)

- Tool calls to a server with `startup_mode=none` return an error immediately before attempting health checks or lifecycle activation. (Explicit in code)
- If the health registry returns a `HALF_OPEN` state, the block by `is_unavailable` is skipped to allow one trial dispatch (circuit breaker half-open attempt). (Explicit in code)
- `ToolTransportInvoker.invoke()` exists as a separate general-purpose method providing health checks, lifecycle activation, and semaphore control similar to internal dispatch, but it does not include the `startup_mode` gate. (Explicit in code)

---

## Tool resolution and LLM visibility

A single stage does the real filtering: `RuntimeToolRegistry.llm_tool_definitions()` returns only tools with `enabled_for_llm=True`, and that is the set of function definitions actually sent to the LLM. Disabled tools (per the owning server's `enabled`/`disabled_reason`) are excluded here, before the LLM ever sees them — not at a later "runtime routability" stage.

`LlmTurnExecutor` has no second filtering stage. `LlmTurnExecutor._stream_llm()` calls `registry.llm_tool_definitions()` directly (falling back to `ctx.cfg.tool.tool_definitions` only when no registry is available), so Stage 1 above is the sole filtering stage — see ADR-003 for the distinction between static availability, dynamic health, and approval, and `mcp_03_06_tool-runtime-availability-metadata.md` for the availability metadata.

Once a tool call reaches `ToolRouteResolver.resolve()`/`RuntimeToolRegistry`, routing succeeds as long as the tool is *owned* by a server — `enabled_for_llm`/`disabled_reason` are not re-checked at this layer. A disabled tool that somehow reaches this point (e.g., a stale LLM response referencing a tool disabled after the definitions were generated) is not rejected by the agent-side router; enforcement of "disabled tools must not execute" then depends on the owning MCP server's own `/v1/call_tool` gate, which every server except `mdq` implements (`git`, `file_read`/`file_write`/`file_delete`, `github`, `web_search`, `shell`, `cicd`, `rag_pipeline` — see `mcp_03_06_tool-runtime-availability-metadata.md`).

**Critical failure mode:** If `RuntimeToolRegistry` is missing entirely, the LLM sees no tools at all, resulting in "Unknown tool" errors even when tools exist in the system.

## Data source for DAG scheduling

The DAG scheduler reads its metadata from `RuntimeToolRegistry`, the same registry that backs routing and LLM visibility. For each approved call, `agent/tool_runner.py::_execute_with_dag()` builds a call-id-keyed `ToolSpec` via `RuntimeToolRegistry.tool_spec_for_call(call_id, name, args)` (`shared/runtime_tool_registry.py`), which resolves per-call resource scopes from the tool's declared `resource_scope_kind`/`resource_scope_keys` and the call's actual arguments (`shared/resource_scope.py::resolve_resource_scopes()`). `agent/tool_scheduler.py::build_execution_groups()` consumes this `dict[str, ToolSpec]` keyed by `call_id` (not tool name) and raises `MissingToolSpecError` if a call's `call_id` has no entry, instead of silently defaulting.

### Fields used by the DAG scheduler

The following `ToolSpec` fields (resolved per call from the tool's `/v1/tools` schema-2.0 declaration) drive scheduling:

- `requires_serial`: Controls whether the tool requires serialized execution (forms a solo serial-barrier group)
- `resource_scopes`: Tuple of kind-prefixed resource-scope strings (e.g. `"filesystem:/a/b.txt"`) the call occupies; conflicting scopes across calls form a serialized conflict-graph group (`shared/resource_scope.py::_scopes_conflict()` — exact match, or ancestor/descendant for `"filesystem:"` scopes)
- `is_write`: Indicates whether the tool performs write operations (a write tool with no resolved scope is treated as occupying the synthetic `"global:write"` scope, so it still participates in — and can conflict within — the same resource-scope conflict graph as scoped writes; there is no separate `write_first` bucket)

### Key distinction

- **RuntimeToolRegistry**: Sole authority for both routing/LLM visibility (`/v1/tools`) AND DAG scheduling metadata (`ToolSpec` via `tool_spec_for_call()`).
- **config/agent.toml `[[tool_definitions]]`**: Only the LLM-facing function-calling schema (name/description/parameters) exposed to the model; carries no scheduling metadata of its own.

There is a single data source for scheduling metadata today: a tool's `/v1/tools` schema-2.0 declaration (`is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys`). Updating `config/agent.toml`'s tool definitions does not affect DAG scheduling.

---

## ToolRouteResolver (`shared/route_resolver.py`)

Resolves `tool_name → server_key` using `RuntimeToolRegistry`. See [ADR-003](../10_adr/ADR-003-runtime-tool-registry-routing-authority.md) for rationale and invariants.

| Static tool group (`shared/tool_constants.py`) | Owning server key |
|---|---|
| `READ_TOOLS` | `file_read` |
| `WRITE_TOOLS` | `file_write` |
| `DELETE_TOOLS` | `file_delete` |
| `SHELL_TOOLS` | `shell` |
| `WEB_SEARCH_TOOLS` | `web_search` |
| `GITHUB_TOOLS` (`GITHUB_READ_TOOLS`, `GITHUB_WRITE_TOOLS`, `GITHUB_DANGEROUS_TOOLS`) | `github` |
| `GIT_TOOLS` (`GIT_READ_TOOLS`, `GIT_WRITE_TOOLS`) | `git` |
| `RAG_TOOLS` (`RAG_READ_TOOLS`, `RAG_WRITE_TOOLS`) | `rag_pipeline` |
| `CICD_TOOLS` (`CICD_READ_TOOLS`, `CICD_WRITE_TOOLS`) | `cicd` |
| `MDQ_TOOLS` (`MDQ_WRITE_TOOLS` is its write subset) | `mdq` |
| No Match | `ValueError` |

For diagnosis guidance, see [MCP Failure Diagnosis](mcp_06_07_mcp-failure-diagnosis.md#llm-called-a-tool-but-execution-failed-with-unknown-tool).

```python
resolver = ToolRouteResolver()
resolver.set_runtime_registry(registry)
server_key = resolver.resolve("read_text_file")  # → "file_read"
```

**Not to be confused with `ToolExecutor.server_configs`:** `ToolRouteResolver`'s constructor has no `server_configs` parameter — it accepts only `warn_on_missing`, `strict_mode`, and `runtime_registry` (see [Agent Reference API](../23_agent/agent_12_reference-api.md) for the full parameter list). `ToolExecutor.server_configs` (`shared/tool_executor.py`) is a separate, current, active configuration: a `dict[str, McpServerConfig]` used for MCP server transport and startup-mode checks (`self._server_configs.get(server_key)`), unrelated to tool-name routing.

**Four-layer responsibility of MDQ tool definitions:** MDQ (`mdq`) tool definitions are spread across four independent files, each having a single responsibility. Changing any one of them requires updating the other three synchronously (`tests/test_mdq_tool_layer_consistency.py` verifies this consistency).

| Layer | File/Symbol | Responsibility |
|---|---|---|
| Schema Definition | `scripts/mcp_servers/mdq/mdq_tools.py::TOOL_LIST` | Tool names, input schemas, and status exposed to LLM |
| Runtime Dispatch | `scripts/mcp_servers/mdq/mdq_server.py::_DISPATCH_TABLE` | Mapping of tool name → handler function |
| Registry Registration | `shared/tool_constants.py::MDQ_TOOLS` | Canonical set for registering tools in `ToolRegistry` |
| Deployment Allowlist | `[mcp_servers.mdq].tool_names` in `config/agent.toml` | List of tools actually allowed to start and be used |

**Generalization to all MCP servers:** The above 4-layer consistency guardrails were specific to MDQ, but `tests/test_tool_server_layer_consistency.py` generalizes this verification to all MCP servers (mdq, github, shell, git, cicd, rag_pipeline, file[read/write/delete], web_search). Dispatch table implementations follow two patterns:

| Dispatch Pattern | Applicable Servers |
|---|---|
| Module-level dictionary (`_DISPATCH_TABLE` equivalent) | `mdq` (`server.py::_DISPATCH_TABLE`), `web_search` (`formatters.py::_WEB_DISPATCH`) |
| Service instance's `get_dispatch_table()` | `github`, `shell`, `git`, `cicd`, `rag_pipeline`, `file_read`, `file_write`, `file_delete` |

---

## Tool Lifecycle Overview (schema → dispatch → registry → side-effect → risk → audit)

Every MCP tool passes through these layers consistently from invocation to audit logging. Updating only one layer while leaving others unchanged causes drift (inconsistency between layers).

``` text
① Schema Definition        Each server's `tools.py::TOOL_LIST` — Names and input schemas exposed to LLM
② Runtime Dispatch        `server.py`'s `_DISPATCH_TABLE` or `service.get_dispatch_table()`
③ Registry Registration    `shared/tool_constants.py`'s frozenset → `shared/tool_registry.py` (for drift detection); routing relies solely on `RuntimeToolRegistry` in `shared/runtime_tool_registry.py`
④ Side-effect Detection     Only execution path `agent/tool_runner.py::_execute_with_dag()` delegates to `agent/tool_scheduler.py::build_execution_groups()` and references `RuntimeToolRegistry`-registered `is_write` (PreparedToolCall.spec) to determine parallel/serial execution (unregistered tools are rejected in the preparation phase via fail-closed)
⑤ Risk Classification & Approval `agent/tool_policy.py::classify_operation_type()` / `classify_risk()` — Priority: `approval_risk_rules` → `tool_safety_tiers` → operation-type classification (`tool_constants.py` frozensets first, then `RuntimeToolRegistry` for READ vs UNKNOWN)
⑥ Audit Logging           `agent/tool_audit.py` — Records `classify_operation_type()` result as `operation_type`
```

**Layers ③–⑤ reference different sources.** ③ is registry registration (ownership; drift detection only), ④ is batch execution parallel/serial control (`RuntimeToolRegistry` `is_write`), and ⑤ is approval risk assessment and audit classification. Missing a reference can cause each layer to drift individually. `agent/tool_policy.py::classify_operation_type()` evaluates in this order: (1) the `shared/tool_constants.py` frozensets `WRITE_TOOLS`, `MDQ_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `CICD_WRITE_TOOLS`, `GIT_WRITE_TOOLS` give WRITE; (2) `DELETE_TOOLS` gives DELETE; (3) the shell execution tool set gives EXECUTE; (4) `GITHUB_WRITE_TOOLS` and `GITHUB_DANGEROUS_TOOLS` give API_WRITE; (5) any other tool is looked up in `RuntimeToolRegistry`: a registered tool gives READ, and an unregistered tool or a missing registry gives UNKNOWN (fail closed, no static-registry fallback; ADR-003 Decision Detail #6/#8). (Explicit in code — `scripts/agent/tool_policy.py::classify_operation_type`) `tests/test_tool_policy_comprehensive.py` and `tests/test_tool_approval_risk.py` verify this classification.

### Serialization mechanism integrated into a single scheduler

`agent/tool_runner.py::_execute_with_dag()` is the sole execution path, and all serialization decisions (tool-specific mandatory serialization via `ToolSpec.requires_serial`, resource-scope conflicts, and the batch-level `serial_tool_calls` setting) are made in `agent/tool_scheduler.py::build_execution_groups()` (phase construction + conflict graph + `force_serial` input):

| Source | Behavior |
|---|---|
| `ToolSpec.requires_serial` (individual tools. e.g., MDQ's `index_paths`/`refresh_index`, shell's `shell_run`) | Forms a solo serial phase as an in-place barrier |
| Overlapping `resource_scopes` (where at least one is `is_write=True`; unscoped writes use synthetic `"global:write"` scope) | Grouped as connected components in the conflict graph and serialized within the group |
| `ctx.cfg.tool.serial_tool_calls=True` → `force_serial=True` (batch-level input) | Bypasses all the above and forces individual serial phases for each call in order |

`shared/tool_executor_helpers.py::is_side_effect()` is not referenced by the execution path; parallel/serial determination relies solely on `PreparedToolCall.spec.is_write`.

---

## Reliable Sources for Routing

See [ADR-003](../10_adr/ADR-003-runtime-tool-registry-routing-authority.md) for rationale and invariants.

---

## Tool Registry (`shared/tool_registry.py`)

Drift detection only; not used for routing. See [ADR-003](../10_adr/ADR-003-runtime-tool-registry-routing-authority.md) for the distinction between routing authority and drift detection.

## Keywords

- mcp
- routing
- lifecycle
- ToolRouteResolver
- ToolRegistry
- tool dispatch
- routing drift
- startup_mode gate
- HALF_OPEN trial dispatch
