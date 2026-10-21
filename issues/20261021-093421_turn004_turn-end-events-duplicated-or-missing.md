# Turn audit events are duplicated on success and missing on failure, and `elapsed_ms` is meaningless

## Priority
High

## Summary
Emit exactly one `turn_end` audit event per turn, with a real elapsed time, and clear turn state on
every exit path.

## Background
Turn lifecycle events are produced from two places: `AuditEventEmitter.emit_turn_start`/`emit_turn_end`
(`scripts/agent/audit_event_emitter.py:76`, `:127-145`) called by `Orchestrator._execute_turn`
(`scripts/agent/orchestrator.py:165-172`), and `WorkflowEngineAdapter._handle_turn_end`
(`scripts/agent/workflow_engine_adapter.py:369-385`) called from the `verify` stage (`:178-183`).

## Problem
- Duplicated event: on a successful turn, `_handle_turn_end` writes a `turn_end` event and sets
  `ctx.turn.current_turn_id = None` (`:385`); `Orchestrator._execute_turn` then calls
  `emit_turn_end(...)` (`orchestrator.py:170-172`), which writes a second `turn_end` event whose
  `task_id` is `""` because the id was already cleared (`audit_event_emitter.py:94`, `:145`).
- Missing event: `Orchestrator._execute_turn` has no `try/finally`. If `_process_turn` raises, the
  `verify` stage never runs and `emit_turn_end` is not called either — no `turn_end` event at all, and
  `ctx.turn.current_turn_id` stays set until the next `emit_turn_start` overwrites it
  (`audit_event_emitter.py:76`). Tool audit rows and session persistence that stamp the current turn id
  therefore read a stale id across a failed turn.
- Invalid metric: `orchestrator.py:167-172` passes the literal `0.0` as `turn_started_at`, and
  `workflow_engine_adapter.py:167` and `:379` compute
  `elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)`. With `turn_started_at == 0.0`
  that is the process uptime in milliseconds, not the turn duration, in both `turn_end` events and
  `audit_stage_completed`.
- Dead state: `TurnState.last_error_kind`, `TurnState.tool_calls`, `TurnState.add_tool_call`,
  `TurnState.get_tool_calls` (`scripts/agent/context.py:194-216`) have no assignment or call sites
  anywhere under `scripts/` (verified by grep), so per-turn error kind and tool-call counts are never
  recorded.

## Reason for Change
`audit.log` is the primary observability surface for turns. Right now successful turns are double
counted, failed turns are absent, and every duration value in it is unusable.

## Implementation Intent
Make one component own the turn lifecycle bracket: emit `turn_start`/`turn_end` once, in a
`try/finally` that runs on every exit path, with a real monotonic start captured once at turn entry and
passed through the workflow adapter instead of `0.0`.

## Target Files or Areas
- `scripts/agent/orchestrator.py` (`_execute_turn`)
- `scripts/agent/audit_event_emitter.py` (`emit_turn_end`, `build_turn_end_*`)
- `scripts/agent/workflow_engine_adapter.py` (`_handle_turn_end`, `audit_stage_completed` call sites)
- `scripts/agent/context.py` (`TurnState` fields)

## Required Changes
- Remove one of the two `turn_end` emission paths; keep a single owner.
- Capture `turn_started_at` once at turn entry and pass the real value through
  `execute_turn(line, turn_started_at, session_id)` instead of `0.0`.
- Bracket the turn with `try/finally` so `turn_end` and turn-state clearing run on success, exception,
  cancellation, and halt.
- Either populate `TurnState.last_error_kind`/`tool_calls` from the turn or delete them; do not leave
  declared-but-unused state on the shared context.

## Constraints
- The audit event schema (`event`, `task_id`, `workflow_id`, `session_id`, `elapsed_ms`,
  `error_kind`, `is_partial`, LLM stats) must stay parseable by existing consumers of `audit.log`.
- `emit_turn_end`'s `on_turn_end` callback hook (`audit_event_emitter.py:143-144`) must keep working.
- Do not change `elapsed_ms` units.

## Acceptance Criteria
- Exactly one `turn_end` event per turn for all four exit paths (success, exception, cancel, halt), with
  a non-empty `task_id`.
- `elapsed_ms` for a stubbed 100 ms turn is within a sane range of 100 ms and is not process uptime.
- `ctx.turn.current_turn_id` is `None` after a failed turn.
- No `TurnState` field remains declared with no producer and no consumer.

## Testing Expectations
- Test that counts `turn_end` events written for a real `AuditLogger` (or a capturing handler) across
  each exit path, asserting one event and a non-empty `task_id`.
- Test asserting `elapsed_ms` is bounded by the stubbed turn duration.
- Mutation check: deleting the second emitter must not break tests; keeping both must fail a new test.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document the turn bracket (who emits, when, and what is guaranteed on failure) in the
operations/observability docs, and state that `elapsed_ms` is measured from turn entry. Mark any
historical `elapsed_ms` data in `audit.log` as unreliable in Known Issues.

## Out of Scope
- Workflow task status semantics (`turn003`).
- Background task tracking (`turn005`).
- LLM token accounting changes.

## Dependencies
- Shares `Orchestrator._execute_turn` and the `execute_turn(...)` signature with `turn001`; change the
  signature once, coherently.
- `turn005` depends on the same `try/finally` bracket for background-task cleanup.

## Unresolved Questions
- Which component is the intended owner of the turn bracket — `Orchestrator` or the workflow adapter's
  `verify` stage? Needs confirmation.
- Is a separate `turn_failed` event wanted instead of `turn_end` with `error_kind`? Needs a decision.

## AI Implementation Instruction
One bracket, one start timestamp, one `turn_end`. Prove the guarantee with tests for failure paths, not
only the success path.

## Traceability
- **Workflow phase**: `python-code-review` (turn orchestration review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/orchestrator.py`, `scripts/agent/audit_event_emitter.py`,
  `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/context.py`
