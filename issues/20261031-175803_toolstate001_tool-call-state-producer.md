# Wire the agent-side tool_call_state producer into the tool execution path

## Priority
Medium

## Summary
`tool_call_state` (workflow.sqlite, toolexec001 row 06) has readers (turn-entry replay detection,
row 08) and helpers (row 07) but no writer yet: nothing records a pending row when the agent
issues a tool call or finalizes it on completion/failure. Until a producer lands,
`WorkflowEngine.build_turn_control_message` and `StateStore.classify_stale_pending` stay inert
(no rows -> no control message; existing behavior unchanged, REQ-010 holds).
This issue wires that producer into the agent tool execution path.

## Background
Source: owner decision 2026-10-31 during the toolexec001 row 07-09 implementation cycles
(option B: land detection/injection, defer the producer to a separate procedure). Facts:

- Rows 07-09 landed: `scripts/agent/workflow/tool_call_state_ops.py` (record/finalize/pending/
  classify helpers + facade methods on `StateStore`), `WorkflowEngine.build_turn_control_message`,
  `LlmTurnExecutor.handle_llm_turn(control_message=...)`, `LLMTurnRunner.run(control_message=...)`.
  (Explicit in code)
- The only site that simultaneously knows task context, tool name, arguments, and outcome is
  `scripts/agent/tool_runner.py` `_recorded_call` / `_execute_prepared_call` (`_idempotency_key`
  composition, audit call site). It is NOT in the toolexec001 frozen target table. (Explicit in code)
- Key mismatch to resolve: `tool_runner._idempotency_key` composes
  `{workflow_id}:{task_id}:{turn_id}:{call_id}` (turn-scoped), while the dispatcher-side dedup
  key is the deterministic `shared.http_transport.derive_idempotency_key("call_tool", name, args,
  uid)` with `uid = transport session_id` (stable across turns and restarts, row 01). The
  `tool_call_state.idempotency_key` must be the deterministic transport key for replay to match
  dedup rows; plumbing the transport uid (or re-deriving with the same uid) into the agent
  record point is the core design decision. (Explicit in code)
- `StateStore` is held by the orchestrator/adapter, not on `AgentContext`; a producer in
  `tool_runner` needs store access (ctx service reference or a per-turn recorder). (Explicit in code)
- Record-before-call is required for the kill-mid-call scenario (row pending at crash ->
  `classify_stale_pending` flips to interrupted at a later turn -> replay control message).
  Current tests inject rows manually (`tests/agent/workflow/test_workflow_engine.py`,
  `TestBuildTurnControlMessage`). (Verified by test)

## Problem
REQ-008's end-to-end staging check (plan Phase 6: "kill mid-call and confirm next-turn replay")
cannot run against production paths because no pending rows are ever written.

## Reason for Change
The toolexec001 rows 07-09 cycle deliberately deferred the producer (option B), so the replay
detection machinery is inert in production. Until this producer lands, the REQ-008 interrupted-call
replay guarantee cannot be validated end to end, and the feature shipped in rows 06-09 remains
unverifiable against real tool-execution paths.

## Implementation Intent
Resolve two design decisions first (in the issue-to-plan cycle): the producer site (directly in
`tool_runner` vs a recorder injected via `AgentContext`) and the key-identity plumbing (plumb the
transport uid into the agent record point, or re-derive with the same uid). Then add
record(pending)-before-call and finalize(completed/failed)-after-call around the existing tool
execution path, reusing the `tool_call_state_ops` helpers and `StateStore` facade methods.
Preserve existing behavior: readers stay backward compatible, and REQ-010 preserved behavior holds.

## Target Files or Areas
- `scripts/agent/tool_runner.py` (producer site candidate)
- `scripts/agent/workflow/tool_call_state_ops.py` and `scripts/agent/workflow/state_store.py`
  (existing helpers/facade methods to reuse)
- `scripts/shared/http_transport.py` (`derive_idempotency_key`, key-identity reference only)
- `tests/agent/` (producer coverage + end-to-end replay case)
- Final producer site: `Unknown` (design decision, see Unresolved Questions)

## Required Changes
- Decide the producer site (`tool_runner.py` vs a recorder injected via `AgentContext`) and the
  key-identity plumbing (deterministic transport key vs agent composite key).
- Implement record(pending)-before-call and finalize(completed/failed)-after-call with the same
  connection discipline as other workflow ops.
- Extend `tests/agent/` with producer coverage and an end-to-end interrupted->replayed case.

## Constraints
- `tool_call_state.idempotency_key` must equal the deterministic transport key from
  `derive_idempotency_key("call_tool", name, args, uid)` so replay detection matches dedup rows.
- Record must happen before the call executes (kill-mid-call leaves a pending row for
  `classify_stale_pending`).
- Reuse the connection discipline of the existing `tool_call_state_ops` helpers.
- `StateStore` is not on `AgentContext`; the producer needs a store-access route that does not
  bypass existing ownership boundaries.
- REQ-010 preserved behavior (caller-supplied keys, dispatcher auth/authz flow) must not change.
- `scripts/agent/tool_runner.py` is not in the toolexec001 frozen target table; adding it is a
  scope decision of this issue, not a deviation from that plan.

## Acceptance Criteria
- A real agent tool call writes a pending `tool_call_state` row before execution and finalizes it
  to completed/failed after the call returns.
- The recorded `idempotency_key` matches the dispatcher-side dedup key derived from the same
  transport uid.
- An end-to-end test shows a pending row flipped to `interrupted` by `classify_stale_pending` and
  replayed as a next-turn control message (REQ-008).
- Existing behavior is unchanged for flows not using tool-call state (REQ-010), and the full test
  suite plus validation gates pass.

## Testing Expectations
- Unit tests in `tests/agent/` for the producer: pending row recorded before execution, finalized
  on success and on failure.
- An end-to-end interrupted->replayed case replacing manual row injection with the production
  write path (keeping the existing `TestBuildTurnControlMessage` coverage).
- Regression: the inert-readers behavior of rows 07-09 stays intact; REQ-010 flows unchanged.
- Lint/type gates via `tools/run_validation_gates.py`.

## Documentation Impact
The producer makes `tool_call_state` behavior observable in production paths. Any required doc
updates (intent, boundaries, failure behavior of the interrupted-call replay flow) should be
scoped during the plan against `docs/00_index.md`'s task-scope mapping; exact documents: Needs
confirmation.

## Out of Scope
- Dispatcher-side dedup and auth/authz flow (`scripts/shared/http_transport.py` key derivation
  itself, toolexec001 row 01).
- `tool_call_state` schema changes.
- `WorkflowEngine.build_turn_control_message` / `LlmTurnExecutor` injection paths (rows 08-09,
  already landed).
- Caller-supplied idempotency key behavior.

## Dependencies
- `plans/done/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` — depends on rows 06-09
  (schema, helpers, detection/injection), already landed.
- `implementations/done/20261030-102825_07_scripts_agent_workflow_state_store.py.md` (Blocker Log) —
  depends on the row 07 helpers.
- `implementations/done/20261030-102825_08_scripts_agent_workflow_workflow_engine.py.md` (Blocker
  Log) — depends on the row 08 detection path.
- Sibling check: no open issues or in-flight plans touch `tool_call_state` beyond these.

## Unresolved Questions
- Producer site: directly in `tool_runner.py` vs a recorder service injected via `AgentContext`.
  Needs confirmation during issue-to-plan.
- Key plumbing: propagate the transport session uid into the agent record point vs re-derive the
  deterministic key there with the same uid. Needs confirmation.
- Store-access route for `StateStore` from `tool_runner` without bypassing orchestrator/adapter
  ownership. Needs confirmation.
- Whether docs need updating and which ones (see Documentation Impact). Needs confirmation.

## AI Implementation Instruction
Resolve the producer-site and key-identity decisions in the plan before coding; do not start
implementation while they are open. Do not modify `scripts/shared/http_transport.py` key
derivation, the `tool_call_state` schema, or the already-landed detection/injection paths. Reuse
the existing `tool_call_state_ops` helpers and `StateStore` facade methods; do not duplicate them.
Keep changes minimal and preserve REQ-010 behavior. Stop and report if the uid plumbing requires
touching an out-of-scope file.

## Traceability
- **Workflow phase**: `issue-creator` (completed a manually filed draft into the canonical template)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: `implementations/done/20261030-102825_07_scripts_agent_workflow_state_store.py.md`, `implementations/done/20261030-102825_08_scripts_agent_workflow_workflow_engine.py.md`
- **Generated at**: 20261031-175803
- **Related target files**: `scripts/agent/tool_runner.py`, `scripts/agent/workflow/tool_call_state_ops.py`, `scripts/agent/workflow/state_store.py`, `scripts/shared/http_transport.py`, `tests/agent/`
