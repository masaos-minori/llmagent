---
title: "Agent Tool Execution and Approval - Execution"
category: agent
tags:
  - agent
  - tool-execution
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_06_01_tool-execution-and-approval-execution.md
---

# Agent Tool Execution and Approval

- Turn Flow → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCP Routing → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)
- GitHub Change Approval/GitOps Control → [05_agent_06_02_tool-execution-and-approval-approval.md](05_agent_06_02_tool-execution-and-approval-approval.md)

## Purpose

Documents the responsibility division of `ToolExecutor`, design decisions for parallel/sequential execution, and DAG scheduling.

## Design Intent

### ToolExecutor Responsibility Division

Dispatch priority of `ToolExecutor.execute(tool_name, args)`:
1. TTL cache
2. MCP server dispatch via `ToolRouteResolver.resolve()` → `McpServerHealthRegistry` → `LifecycleProtocol.ensure_ready()` → `HttpTransport`

### Parallel vs Sequential Execution

`execute_all_tool_calls()` always delegates processing to `agent/tool_runner.py::_execute_with_dag()` (a single execution path). The second execution engine called `_execute_standard()` has been deprecated. `ctx.cfg.tool.serial_tool_calls` is no longer a flag to select an execution engine; instead, it is passed as the `force_serial` input to `agent/tool_scheduler.py::build_execution_groups()`:

| Condition | Execution |
|---|---|
| `serial_tool_calls=False` (default) | DAG Scheduling (Phase construction + conflict graph) |
| `serial_tool_calls=True` | `force_serial=True` — Bypasses phase/conflict graph construction entirely and generates individual serial phases in calling order |

**Design judgment**: `_execute_with_dag()` is the only execution path; there is no implementation-level switch back to "legacy behavior (standard execution)". While `serial_tool_calls=True` still executes all calls sequentially, this is achieved through input to a single scheduler rather than branching to a different function.

### DAG Tool Scheduler Design Decisions

#### Rules (Traverse calls in input order to construct phases)

1. **`requires_serial=True`** — An in-place barrier. Closes all currently accumulated phases, issues a single serial phase at the original position of the current call, and starts a new phase for subsequent calls (does not pull up to the start of the batch).
2. **Calls with overlapping `resource_scopes` (where at least one is `is_write=True`)** — Grouped as connected components within the same phase, and serialization occurs within that group (in addition to exact matches, filesystem scopes are considered overlapping if they have ancestor/descendant relationships. See `shared/resource_scope.py::_scopes_conflict()`).
3. **`resource_scopes` is empty AND `is_write=True`** — Treated as a synthetic scope `("global:write",)` and joins the same conflict graph as Rule 2. A dedicated `write_first` bucket was deprecated; non-scoped writes now also detect conflicts and are serialized (unless they do not conflict with other calls, in which case they are pooled into a normal parallel execution group).
4. **Calls not matching rules 1–3 within the same phase** — Pooled into a single parallel execution group.
5. **`force_serial=True`** (supplied from `ctx.cfg.tool.serial_tool_calls`) — Bypasses all the above and generates individual serial phases in calling order.

Grouping is performed by `agent/tool_scheduler.py::build_execution_groups()` using `call_id` as the key for each `ToolSpec` (constructed per call via `agent/tool_runner.py::_execute_with_dag()`'s `RuntimeToolRegistry.tool_spec_for_call()`) — not on a per-tool-name basis. Even different calls to the same tool name can be executed in parallel within the same batch if their `resource_scopes` do not overlap.

#### ExecutionPlan Structure (batches / ScheduledGroup)

`build_execution_groups()` returns a single `ExecutionPlan` (`batches: tuple[ScheduledBatch, ...], serialization_events: tuple[SerializationEvent, ...]`). The old two-value tuple format `tuple[list[list[dict]], _GroupMetadata]` plus a parallel array of `serialize_flags` has been deprecated.

- Each **batch** is executed sequentially relative to other batches.
- Within a **batch**, `ScheduledGroup`s are executed in parallel via `asyncio.gather()`; if a group's `sequential` flag is `True`, calls within that group are executed in order.
- `scheduling_mode`: `"dag_concurrent"` / `"dag_sequential"`

### Argument Validation

Argument parsing, resolution, and validation are performed collectively in a dedicated preparation phase before the approval phase (via `agent/tool_preparation.py::prepare_tool_calls()` within `execute_all_tool_calls()` before `_run_approval_gate()`).

For each call, the following steps are performed in order; failure in any step results in a fail-closed outcome (no `PreparedToolCall` is created, preventing it from reaching approval, scheduling, or execution, and returning a composite error immediately):
- Existence check for `id`/`function.name`
- JSON parsing of `arguments` (once only) and dict type check
- Resolution via `RuntimeToolRegistry` — rejected without fallback if disconnected or if the target tool is unregistered
- For registered tools: schema validation via `agent/tool_arg_validator.py::validate_tool_arguments()` + custom hooks
- Metadata construction via `RuntimeToolRegistry.tool_spec_for_call()`

Only calls that pass the preparation phase are passed to approval, execution, and scheduling as a `PreparedToolCall` (`call_id`/`name`/`args`/`spec`/`original_call`). `execute_one_tool_call()` and `_execute_with_dag()` only reference the `PreparedToolCall.spec` (resolved during the preparation phase) and do not perform their own argument validation or registry lookups.

### Result Reflection in History

Uses verified methods via `ConversationState.append_message()` / `extend_messages()`.

## Responsibility Boundary

- **Source of Truth**: `shared/tool_executor.py`, `agent/tool_scheduler.py`, `agent/tool_preparation.py` (including preparation phase with argument validation/registry resolution)
- **Routing Authority**: `ToolRouteResolver.resolve()` ([04_mcp Routing Source of Truth](04_mcp_03_01_dispatch-and-routing.md))

## Key Constraints

- `_execute_with_dag()` is the only execution path. `serial_tool_calls=True` does not switch to a different engine but acts as the `force_serial` input to `build_execution_groups()`.
- Multiple calls to write tools with overlapping `resource_scopes` are serialized within the same group.
- Preparation phase is fail-closed: if any issue exists (missing id, invalid JSON, unregistered tool, registry disconnected, schema violation, metadata construction failure), it is rejected before reaching approval, execution, or scheduling.

## Operational Notes

- Unknown

## Known Limitations

- Structurally invalid schemas from MCP servers may raise `jsonschema.SchemaError`, which `_check_type_validation()` does not catch.

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_06_02_tool-execution-and-approval-approval.md`
- `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`
- `05_agent_06_04_tool-execution-and-approval-canonical.md`
- `05_agent_04_01_state-and-persistence-state-model.md`
- `00_security_02_high-risk-tool-common-policy.md` — High-risk MCP tool common policy (Approval-Risk Tier Mapping)

## Keywords

ToolExecutor
parallel vs sequential execution
DAG tool scheduler
tool argument validation
tool call preparation phase
PreparedToolCall
fail-closed
validated history append/extend
ExecutionPlan
ScheduledGroup
force_serial
global:write scope
