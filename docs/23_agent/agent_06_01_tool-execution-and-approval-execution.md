---
title: "Agent Tool Execution and Approval - Execution"
area: agent
tags:
  - agent
  - tool-execution
related:
  - agent_00_document-guide.md
  - agent_06_02_tool-execution-and-approval-approval.md
  - agent_06_03_tool-execution-and-approval-concurrency-safety.md
  - agent_06_04_tool-execution-and-approval-canonical.md
  - agent_04_01_state-and-persistence-state-model.md
  - security_02_high-risk-tool-common-policy.md
  - agent_03_01_turn-processing-flow-overview.md
  - mcp_03_01_dispatch-and-routing.md
---

# Agent Tool Execution and Approval

- Turn Flow → [agent_03_01_turn-processing-flow-overview.md](agent_03_01_turn-processing-flow-overview.md)
- MCP Routing → [mcp_03_01_dispatch-and-routing.md](../22_mcp/mcp_03_01_dispatch-and-routing.md)
- GitHub Change Approval/GitOps Control → [agent_06_02_tool-execution-and-approval-approval.md](agent_06_02_tool-execution-and-approval-approval.md)

## Purpose

Documents the responsibility division of `ToolExecutor`, design decisions for parallel/sequential execution, and DAG scheduling.

## Design Intent

### ToolExecutor Responsibility Division

Dispatch path of `ToolExecutor.execute(tool_name, args)` (single path, no fallback chain):
1. MCP server dispatch via `ToolRouteResolver.resolve()` → `McpServerHealthRegistry` → `LifecycleProtocol.ensure_ready()` → `HttpTransport`

### Parallel vs Sequential Execution

`execute_all_tool_calls()` always delegates to a single execution path (`agent/tool_runner.py::_execute_with_dag()`). `ctx.cfg.tool.serial_tool_calls` does not select an engine; it is passed as the `force_serial` input to `agent/tool_scheduler.py::build_execution_groups()`, so `True` yields individual serial phases in calling order and `False` uses phase construction plus the conflict graph.

### DAG Tool Scheduler Design Decisions

#### Rules (Traverse calls in input order to construct phases)

1. **`requires_serial=True`** — An in-place barrier. Closes all currently accumulated phases, issues a single serial phase at the original position of the current call, and starts a new phase for subsequent calls (does not pull up to the start of the batch).
2. **Calls with overlapping `resource_scopes` (where at least one is `is_write=True`)** — Grouped as connected components within the same phase, and serialization occurs within that group (in addition to exact matches, filesystem scopes are considered overlapping if they have ancestor/descendant relationships. See `shared/resource_scope.py::_scopes_conflict()`).
3. **`resource_scopes` is empty AND `is_write=True`** — Treated as a synthetic scope `("global:write",)` and joins the same conflict graph as Rule 2. Non-scoped writes also detect conflicts and are serialized (unless they do not conflict with other calls, in which case they are pooled into a normal parallel execution group).
4. **Calls not matching rules 1–3 within the same phase** — Pooled into a single parallel execution group.
5. **`force_serial=True`** (supplied from `ctx.cfg.tool.serial_tool_calls`) — Bypasses all the above and generates individual serial phases in calling order.

Grouping is performed by `agent/tool_scheduler.py::build_execution_groups()` using `call_id` as the key for each `ToolSpec` (constructed per call via `agent/tool_runner.py::_execute_with_dag()`'s `RuntimeToolRegistry.tool_spec_for_call()`) — not on a per-tool-name basis. Even different calls to the same tool name can be executed in parallel within the same batch if their `resource_scopes` do not overlap.

#### Execution Order

`build_execution_groups()` returns an execution plan of batches plus serialization events. Batches run sequentially; groups within a batch run in parallel, and calls within a `sequential` group run in order.

### Argument Validation

Argument parsing, resolution, and validation are performed collectively in a dedicated preparation phase before the approval phase (via `agent/tool_preparation.py::prepare_tool_calls()` within `execute_all_tool_calls()` before `_run_approval_gate()`).

For each call, the following steps are performed in order; failure in any step results in a fail-closed outcome (no `PreparedToolCall` is created, preventing it from reaching approval, scheduling, or execution, and returning a composite error immediately):
- Existence check for `id`/`function.name`
- JSON parsing of `arguments` (once only) and dict type check
- Resolution via `RuntimeToolRegistry` — rejected without fallback if disconnected or if the target tool is unregistered
- For registered tools: schema validation via `agent/tool_arg_validator.py::validate_tool_arguments()` + custom hooks
- Metadata construction via `RuntimeToolRegistry.tool_spec_for_call()`

Only calls that pass the preparation phase are passed to approval, execution, and scheduling as a `PreparedToolCall` (`call_id`/`name`/`args`/`spec`/`original_call`). `execute_one_tool_call()` and `_execute_with_dag()` only reference the `PreparedToolCall.spec` (resolved during the preparation phase) and do not perform their own argument validation or registry lookups.

A preparation rejection is answered, not fatal: the rejected call contributes one `tool` message at its batch position carrying the rejection reason (a missing or empty `id` is answered with `tool_call_id == ""`), and the round completes for the remaining calls. A malformed provider tool call never aborts a turn.

### Result Reflection in History

Uses verified methods via `ConversationState.append_message()` / `extend_messages()`.

A round answers every `tool_call_id` the assistant message declared: when `execute_all_tool_calls()` ends, normally or by raising, history and the saved batch hold exactly one `role='tool'` row per declared id, in the original call order. A call the round did not execute is answered by a synthesized row that says it was not executed, for one of two reasons (`ToolCallStopReason`): the round was stopped by a loop guard, or the round did not complete. A synthesized row changes neither `ctx.stats` nor `out_failed_keys`, and it is never fed to the empty-result guard. The exception that ended a failing round still propagates unchanged.

### Dynamic Availability Hints and the Unavailable-Repeat Bound

A tool result from MCP transport that signals server unavailability may carry a dynamic availability hint: a normalized reason code, the circuit breaker state, and an optional retry-after time in seconds (the same vocabulary as [Health Reasons and Error Kinds](../22_mcp/mcp_06_10_health-reasons-and-error-kinds.md)). The hint is advisory metadata, never a routing input: it changes neither tool registration nor LLM tool visibility nor static availability, and it never changes the tool definitions presented to the LLM (ADR-003 Decision 17). The hint is constructed only from runtime health state; server-supplied free text is not part of the bounded-hint signal.

Repeated selection of tools returning the same server-unavailable hint within one turn is bounded by the existing empty-result repeat configuration (`tool_empty_result_max_repeats`); the bound is off when that configuration is 0 (the repository default). At the bound the turn ends with an observable system hint. A result that does not carry a server-unavailable hint — including a successful call to that server — clears the accumulated count, so recovery requires no explicit removal.

## Responsibility Boundary

- **Source of Truth**: `shared/tool_executor.py`, `agent/tool_scheduler.py`, `agent/tool_preparation.py` (including preparation phase with argument validation/registry resolution)
- **Routing Authority**: `ToolRouteResolver.resolve()` ([04_mcp Routing Source of Truth](../22_mcp/mcp_03_01_dispatch-and-routing.md))

## Key Constraints

- `_execute_with_dag()` is the only execution path; `serial_tool_calls=True` only changes the scheduler input and never selects another engine.
- A trip of the empty-result guard observed while a round runs ends the remaining calls of the sequential group and the remaining batches of the plan; those ids are answered by synthesized rows, and the post-round check remains the only place that records the guard hint.
- Preparation phase is fail-closed: if any issue exists (missing id, invalid JSON, unregistered tool, registry disconnected, schema violation, metadata construction failure), it is rejected before reaching approval, execution, or scheduling.

## Known Limitations

- Structurally invalid schemas from MCP servers may raise `jsonschema.SchemaError`, which `_check_type_validation()` does not catch.
- A result whose `tool_call_id` is empty can only be paired positionally: it is matched to the batch entry lacking an id in declared order.
- Repeated `tool_call_id` values in one assistant message collapse to a single answered row: a second call sharing a real id produces no second result row.

## Keywords

- ToolExecutor
- parallel vs sequential execution
- DAG tool scheduler
- tool argument validation
- tool call preparation phase
- PreparedToolCall
- fail-closed
- validated history append/extend
- ExecutionPlan
- ScheduledGroup
- force_serial
- global:write scope
- dynamic availability hint
- unavailable-repeat bound
- retry_after
