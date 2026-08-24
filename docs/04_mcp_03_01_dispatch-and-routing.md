---
title: "Tool Call Dispatch Flow and Routing Resolution"
area: mcp
tags:
  - mcp
  - routing
  - lifecycle
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_02_tool-registry.md
  - 04_mcp_03_03_transport-and-health.md
  - 04_mcp_03_04_tool-call-tracing-and-watchdog.md
  - 04_mcp_03_05_lifecycle-and-new-server.md
---

# MCP Tool Call Dispatch Flow and Routing Resolution

- System Overview → [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md)

## Purpose

To document tool routing, server startup/shutdown lifecycles, the internal structure of `ToolExecutor`, watchdog behavior, idle timeouts, and procedures for adding new servers.

---

## Tool Call Dispatch Flow

The agent sets the `server_key` and `tool_name` in the dispatch log context. The `X-Request-Id` (retrieved from the serverless response header) correlates the agent's dispatch logs with transport and server audit logs.

``` text
LLM returns tool_call
   → ToolRouteResolver.resolve(tool_name) → server_key
   → ToolExecutor.execute(tool_name, args)
        1. Cache check (TTL + LRU)             — returns cached result if hit; no HealthRegistry update
           (cache miss: aggregates concurrent execution of the same key with an inflight future — stampede protection)
        2. MCP server dispatch (internal dispatch)
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

- On cache miss, concurrent calls to the same `cache_key` (`tool_name:json(args)`) share an `asyncio.Future`, ensuring the actual processing is executed only once (stampede protection). If the caller raises an exception, that exception is propagated to all waiting callers. (Explicit in code)
- Tool calls to a server with `startup_mode=none` return an error immediately before attempting health checks or lifecycle activation. (Explicit in code)
- If the health registry returns a `HALF_OPEN` state, the block by `is_unavailable` is skipped to allow one trial dispatch (circuit breaker half-open attempt). (Explicit in code)
- `ToolTransportInvoker.invoke()` exists as a separate general-purpose method providing health checks, lifecycle activation, and semaphore control similar to internal dispatch, but it does not include the `startup_mode` gate. (Explicit in code)

---

## Tool resolution and LLM visibility (corrected)

A single stage does the real filtering: `RuntimeToolRegistry.llm_tool_definitions()` returns only tools with `enabled_for_llm=True`, and that is the set of function definitions actually sent to the LLM. Disabled tools (per the owning server's `enabled`/`disabled_reason`) are excluded here, before the LLM ever sees them — not at a later "runtime routability" stage.

`LLMTurnRunner._filter_disabled_tool_definitions()` exists in code but is not a second filtering stage: it builds `visible_names` from the exact same `registry.llm_tool_definitions()` call and then filters against that self-referential set, so it removes nothing beyond what Stage 1 already removed (the function body's own comment notes `visible_names is redundant here`). Treat this as dead-code-shaped, not as an independent routability check — see `04_mcp_03_06_tool-runtime-availability-metadata.md` sections 6a/6b for the concepts this area actually needs (static vs. dynamic availability, approval).

Once a tool call reaches `ToolRouteResolver.resolve()`/`RuntimeToolRegistry`, routing succeeds as long as the tool is *owned* by a server — `enabled_for_llm`/`disabled_reason` are not re-checked at this layer. A disabled tool that somehow reaches this point (e.g., a stale LLM response referencing a tool disabled after the definitions were generated) is not rejected by the agent-side router; enforcement of "disabled tools must not execute" then depends on the owning MCP server's own `/v1/call_tool` gate, which only 4 of 8 server categories implement (`git`, `file_read`/`file_write`/`file_delete`, `github`, `web_search` — see `04_mcp_03_06_tool-runtime-availability-metadata.md`).

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

Resolves `tool_name → server_key` using `RuntimeToolRegistry`. See [ADR-003](adr/ADR-003-runtime-tool-registry-routing-authority.md) for rationale and invariants.

| Tool Set | Server Key |
|---|---|
| `READ_TOOLS` (9 tools: list_directory, read_text_file, etc.) | `file_read` |
| `WRITE_TOOLS` (write_file, edit_file, create_directory, move_file) | `file_write` |
| `DELETE_TOOLS` (delete_file, delete_directory) | `file_delete` |
| `shell_run` | `shell` |
| `WEB_SEARCH_TOOLS` (search_web, browser_fetch) | `web_search` |
| `GITHUB_TOOLS` (github_search_repositories, github_get_file_contents) | `github` |
| `RAG_TOOLS` (rag_run_pipeline, rag_debug_pipeline) | `rag_pipeline` |
| `CICD_TOOLS` (trigger_workflow, get_workflow_runs, get_workflow_status, get_workflow_logs) | `cicd` |
| `MDQ_TOOLS` (search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs) | `mdq` |
| No Match | `ValueError` |

For diagnosis guidance, see [MCP Failure Diagnosis](04_mcp_06_09_mcp-failure-diagnosis.md#llm-called-a-tool-but-execution-failed-with-unknown-tool).

```python
resolver = ToolRouteResolver(server_configs)
server_key = resolver.resolve("read_text_file")  # → "file_read"
```

**Four-layer responsibility of MDQ tool definitions:** MDQ (`mdq`) tool definitions are spread across four independent files, each having a single responsibility. Changing any one of them requires updating the other three synchronously (`tests/test_mdq_tool_layer_consistency.py` verifies this consistency).

| Layer | File/Symbol | Responsibility |
|---|---|---|
| Schema Definition | `scripts/mcp_servers/mdq/mdq_tools.py::TOOL_LIST` | Tool names, input schemas, and status exposed to LLM |
| Runtime Dispatch | `scripts/mcp_servers/mdq/mdq_server.py::_DISPATCH_TABLE` | Mapping of tool name → handler function |
| Registry Registration | `shared/tool_constants.py::MDQ_TOOLS` | Canonical set for registering tools in `ToolRegistry` |
| Deployment Allowlist | `[mcp_servers.mdq].tool_names` in `config/agent.toml` | List of tools actually allowed to start and be used |

**Generalization to all 8 servers:** The above 4-layer consistency guardrails were specific to MDQ, but `tests/test_tool_server_layer_consistency.py` generalizes this verification to all 8 MCP servers (mdq, github, shell, git, cicd, rag_pipeline, file[read/write/delete], web_search). Dispatch table implementations follow two patterns:

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
                       `shared/tool_executor_helpers.py::is_side_effect()` is now used only for bypassing TTL cache in `shared/tool_executor.py`, which is a completely unrelated mechanism.
⑤ Risk Classification & Approval `agent/tool_policy.py::classify_operation_type()` / `classify_risk()` — Priority: `approval_risk_rules` → `tool_safety_tiers` → `tool_constants.py` classification
⑥ Audit Logging           `agent/tool_audit.py` — Records `classify_operation_type()` result as `operation_type`
```

**Layers ③–⑤ reference different sources.** ③ is registry registration (ownership), ④ is batch execution parallel/serial control, and ⑤ is approval risk assessment and audit classification; all three refer to the `shared/tool_constants.py` frozenset, but missing a reference can cause each layer to drift individually. `agent/tool_policy.py::classify_operation_type()` previously only referenced `WRITE_TOOLS`/`DELETE_TOOLS`/GitHub sets, misclassifying tools in `MDQ_WRITE_TOOLS, RAG_WRITE_TOOLS, CICD_WRITE_TOOLS, GIT_WRITE_TOOLS (e.g., `index_paths`, `refresh_index`, `rag_delete_document`, `trigger_workflow`, `git_add`, etc.) as `read`. (This has been fixed). `tests/test_tool_policy_comprehensive.py` and `tests/test_tool_approval_risk.py` verify this classification regression.

### Serialization mechanism integrated into a single scheduler

Previously, there were two separate mechanisms: batch-level downgrade ("if any tool in a batch is a write tool, serialize the whole batch") via standard execution path (`agent/tool_runner.py::_execute_standard()`, effective when `serial_tool_calls=True`) and tool-specific mandatory serialization via `ToolSpec.requires_serial`. `_execute_standard()` was removed, and `agent/tool_runner.py::_execute_with_dag()` became the sole execution path, unifying serialization decision making into `agent/tool_scheduler.py::build_execution_groups()` (phase construction + conflict graph + `force_serial` input):

| Source | Behavior |
|---|---|
| `ToolSpec.requires_serial` (individual tools. e.g., MDQ's `index_paths`/`refresh_index`, shell's `shell_run`) | Forms a solo serial phase as an in-place barrier |
| Overlapping `resource_scopes` (where at least one is `is_write=True`; unscoped writes use synthetic `"global:write"` scope) | Grouped as connected components in the conflict graph and serialized within the group |
| `ctx.cfg.tool.serial_tool_calls=True` → `force_serial=True` (batch-level input) | Bypasses all the above and forces individual serial phases for each call in order |

`shared/tool_executor_helpers.py::is_side_effect()` no longer participates in this decision — it is now used only for bypassing the TTL cache in `shared/tool_executor.py`, which is a completely unrelated mechanism.

---

## Reliable Sources for Routing

See [ADR-003](adr/ADR-003-runtime-tool-registry-routing-authority.md) for rationale and invariants.

---

## Tool Registry (`shared/tool_registry.py`)

Drift detection only; not used for routing. See [ADR-003](adr/ADR-003-runtime-tool-registry-routing-authority.md) for the distinction between routing authority and drift detection.

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_02_tool-registry.md`
- `04_mcp_03_03_transport-and-health.md`
- `04_mcp_03_04_tool-call-tracing-and-watchdog.md`
- `04_mcp_03_05_lifecycle-and-new-server.md`
- [ADR-003](../adr/ADR-003-runtime-tool-registry-routing-authority.md) — RuntimeToolRegistryを唯一のルーティング権威とする
- [ADR-004](../adr/ADR-004-environment-profile-fail-fast-fail-open.md) — Environment Profile別障害方針 — Fail-Fast/Fail-Open

## Keywords

mcp
routing
lifecycle
ToolRouteResolver
ToolRegistry
tool dispatch
routing drift
stampede protection
startup_mode gate
HALF_OPEN trial dispatch
