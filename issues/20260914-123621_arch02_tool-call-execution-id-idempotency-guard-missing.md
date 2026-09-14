# Add a Tool Call-level idempotency guard; make the existing per-request ID survive retries and link to WorkflowEngine's Attempt ID

## Priority
Medium

## Summary
Every MCP HTTP request already receives a unique `request_id` (`scripts/mcp_servers/server.py` `_auth_middleware`, `uuid.uuid4()`) that is propagated to `ToolExecEvent.mcp_request_id` for audit purposes (`scripts/agent/tool_audit.py`). However, this ID is trace-only: (1) no component checks whether the same logical Tool Call has already run and rejects/short-circuits a duplicate, (2) a retried Tool Call gets a brand-new UUID each time rather than a stable identifier for "this logical attempt," and (3) `mcp_request_id` is never linked to WorkflowEngine's own `task_id`/`attempt_id` (`scripts/agent/workflow/workflow_engine.py`), so the two identifier spaces cannot be cross-referenced during an incident investigation.

## Background
This issue follows a design review requested in this session covering six Agent/Workflow design questions (memo2.md): stage-level idempotency keys, a unique execution ID per Tool Call, duplicate-execution prevention for the same side-effecting operation, execute/verify success separation, unique retry ownership, and a Workflow/Agent/MCP timeout hierarchy. Two independent fork investigations covered the Tool Call ID question and the duplicate-execution-prevention question; both converged on the same gap, so they are filed together here. Stage-level idempotency (a related but distinct concern — one event_id per `{task_id}:{stage_id}:{attempt}`) is already implemented via `idempotency_ops.begin_stage_if_new()` and is now recorded as ADR-001 INV-08/INV-026 — that part required no new issue.

## Problem
Confirmed by direct reading:
- `scripts/mcp_servers/server.py` `_auth_middleware`: generates a fresh `uuid.uuid4()` per HTTP request and returns it as `X-Request-Id`; this happens unconditionally on every request, including retries of the same logical call.
- `scripts/agent/tool_runner.py` `execute_one_tool_call()` (lines ~90-115): reads `result.request_id`, passes it to `audit_tool_exec(..., mcp_request_id=...)` — purely for audit-trail recording.
- `scripts/agent/tool_audit.py` `audit_tool_exec()`: builds a `ToolExecEvent` whose `task_id` field is `ctx.turn.current_turn_id` — a different identifier space from WorkflowEngine's `TaskRecord.task_id`/`attempt_id`.
- No dispatch-layer or MCP-server-layer code (`scripts/mcp_servers/dispatch.py`, `scripts/mcp_servers/server.py`) checks an incoming `request_id` (or any other field) against previously-processed requests before executing a side-effecting tool.
- Consequence: if a Tool Call with side effects (file write, git operation, external API call) is retried — whether by `WorkflowEngine`'s stage retry, `ToolLoopGuard`'s own retry counter, or a transport-level reconnect — nothing prevents the underlying operation from actually running twice; only the audit log records two distinct request IDs after the fact.

## Reason for Change
An audit-only identifier gives the illusion of traceable, idempotent Tool Call execution without the substance: a postmortem can see "two calls happened" but the system itself never had the chance to say "this is the same logical attempt, do not run it again." Given this project's existing stage-level idempotency guard (`begin_stage_if_new()`) already established the pattern (deterministic key + check-then-insert), the same pattern applies naturally one level down, at the Tool Call.

## Implementation Intent
Introduce a Tool Call-level idempotency key derived from the enclosing WorkflowEngine attempt (e.g. `{task_id}:{stage_id}:{attempt}:{tool_call_index}` or similar, to be finalized during implementation against the actual call-site data available at the MCP dispatch boundary) that: (a) is stable across retries of the same logical Tool Call rather than freshly randomized per HTTP request, (b) is checked by the MCP server or dispatch layer before executing a side-effecting tool, rejecting or short-circuiting an exact duplicate, and (c) is recorded in the audit log alongside (not instead of) the existing per-request trace ID, with an explicit link to WorkflowEngine's `task_id`/`attempt_id`.

## Target Files or Areas
- `scripts/mcp_servers/server.py`
- `scripts/mcp_servers/dispatch.py`
- `scripts/agent/tool_runner.py`
- `scripts/agent/tool_audit.py`
- `scripts/agent/workflow/idempotency_ops.py` (as a possible existing-pattern reference, not necessarily a shared implementation)

## Required Changes
- Design and implement a stable, retry-invariant Tool Call identifier that is distinct from the per-HTTP-request `uuid.uuid4()` trace ID (keep the latter for transport-level tracing; add the former for idempotency).
- Add a duplicate-check step before side-effecting tool execution in the MCP server or dispatch layer, using the stable identifier; define the rejection/short-circuit behavior for a detected duplicate (e.g. return the prior result if cached, or reject with a distinct error kind).
- Link the new identifier (or the existing `mcp_request_id`) to `WorkflowEngine`'s `task_id`/`attempt_id` in the audit event so the two identifier spaces are cross-referenceable.
- Scope the duplicate-check to side-effecting tools only (per this project's existing risk-tiering used elsewhere, e.g. `tool_validators.py`'s high-risk tool list) — do not add overhead to read-only tool calls unless a reviewer determines it is warranted.

## Constraints
Do not change the existing per-HTTP-request `X-Request-Id`/`uuid.uuid4()` trace ID's behavior — it serves a distinct, already-working transport-tracing purpose; add the idempotency key alongside it, not as a replacement.

## Acceptance Criteria
- A side-effecting Tool Call that is retried with the same stable idempotency key is detected and does not execute the underlying operation twice.
- The audit log records both the transport trace ID and the new stable idempotency key, with a field linking to the enclosing WorkflowEngine `task_id`/`attempt_id`.
- Existing MCP server test suites (`tests/mcp_servers/`) still pass; new tests cover the duplicate-detection behavior.

## Testing Expectations
Add unit tests for the duplicate-check logic (e.g. same key submitted twice → second call short-circuited or rejected) and an integration test exercising a retried side-effecting tool call end-to-end. Run `tests/mcp_servers/` and `tests/agent/` after the change.

## Documentation Impact
Update `docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md` (or the nearest equivalent operational doc) to describe the new idempotency key and its relationship to `mcp_request_id` and WorkflowEngine's `task_id`/`attempt_id`. Consider whether ADR-014 (Agent control-plane responsibility boundaries) should gain a Known Deviation or Review Trigger entry noting this was an identified gap at ADR-014's Accepted date.

## Out of Scope
- Stage-level idempotency (`begin_stage_if_new()`) — already implemented and now documented as ADR-001 INV-08/INV-026; not part of this issue.
- Redesigning the retry-ownership model across WorkflowEngine/ToolLoopGuard/LLM transport layers — tracked separately (see related issue on retry ownership from the same design review).
- The Workflow/Agent/MCP timeout hierarchy — tracked separately (see related issue on timeout hierarchy from the same design review).

## Dependencies
N/A: none — can be implemented independently, though it shares call-site context with the timeout-hierarchy and retry-ownership issues filed from the same review.

## Unresolved Questions
The exact shape of the stable idempotency key (what data is available at the MCP dispatch boundary to derive it deterministically from the enclosing WorkflowEngine attempt) needs to be resolved during implementation by reading the actual call path from `WorkflowEngineAdapter.execute_turn()` through to the MCP server's tool dispatch, since a Tool Call is not a WorkflowEngine stage — a single stage's `execute_fn` can issue multiple Tool Calls in one LLM turn.

## AI Implementation Instruction
Read `scripts/agent/workflow/idempotency_ops.py` and `scripts/agent/workflow/workflow_engine.py::_run_stage()` first to understand the existing stage-level idempotency pattern (deterministic key + check-then-insert via `begin_stage_if_new()`) before designing the Tool Call-level equivalent — reuse the same design pattern rather than inventing a different one, but do not literally reuse `begin_stage_if_new()` itself, since it is scoped to stage records, not Tool Call records.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-123621
- **Related target files**: scripts/mcp_servers/server.py, scripts/mcp_servers/dispatch.py, scripts/agent/tool_runner.py, scripts/agent/tool_audit.py
