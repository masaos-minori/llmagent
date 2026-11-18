# WorkflowEngineAdapter.execute_turn bundles the exit-reason state machine, per-attempt stage closures, and turn-entry prep in one ~110-line method

## Priority
Medium

## Summary
Split `WorkflowEngineAdapter.execute_turn` (`scripts/agent/workflow_engine_adapter.py`) so the turn-entry preparation, the engine invocation with its three per-stage closures, and the exit-status bookkeeping each live in their own small method. The goal is a method whose control flow a reader can follow without holding six `exit_reason` branches, three nonlocal-mutating closures, and two separate status-writers in memory at once.

## Background
`execute_turn` is the single entry point that runs one LLM turn through the workflow engine. It was shaped by repeated wiring changes (ADR-014 adapter, the AC-5/AC-6 execute-stage failure contract, the turn-entry replay-control message, and the `_owns_state_store` close-on-exit lifecycle). Each added concern appended another branch or closure rather than extracting a helper. The adjacent retry-path cleanup in `issues/done/20261107-203227_wfaudit014_retry-loop-dead-parameters.md` removed one dead parameter but left the overall method structure intact.

## Problem
`execute_turn` is ~111 lines (L115-226) and mixes four unrelated responsibilities in one control-flow graph:

- Task init and workflow activation (L130-142),
- Three nested async closures (`plan_fn`, `execute_fn`, `verify_fn`) that mutate three `nonlocal` values (`answer`, `error_kind`, `is_partial`) and read `self._ctx.turn.attempt_side_effect` (L144-184),
- Turn-entry preparation inside the same `with self._tool_override(...)` scope as `engine.run` (L185-201),
- A six-branch `try/except/finally` whose `exit_reason` variable is resolved by `_status_for_exit` + `_record_exit_status` into a status the adapter may or may not write (L202-226).

The `exit_reason` threading is the fragile part: `execute_turn` sets `exit_reason` in six places, `_status_for_exit` returns `None` for every branch except `"cancelled"`, and `_record_exit_status` writes nothing when the engine already recorded the terminal status. A change that adds a new exit path (a new exception type, a new early return) can silently leave a task status unwritten because the author assumed the engine covered it. The per-attempt side-effect guard (`self._ctx.turn.attempt_side_effect = False` reset inside `execute_fn`) is also easy to misread as turn-scoped when it is actually attempt-scoped, which is exactly what makes retries safe.

## Reason for Change
The execute-stage retry/halt contract (AC-5/AC-6) and the turn-entry replay path are both subtle; burying them in a 110-line method with a shared `exit_reason` state machine raises the cost of the next correct change. Extracting the three responsibilities into small, named methods makes each independently reviewable and testable without loading the whole turn lifecycle.

## Implementation Intent
Extract by responsibility, preserving behavior exactly:

- Move turn-entry preparation (clear ephemeral messages, memory injection, mode classification, user-message append, history compression) plus its `WorkflowHaltError`/`WorkflowTimeoutError` re-route into a `_run_turn_entry(line, ctx)` method that raises `WorkflowHaltError` on failure, matching the current halt-handler routing.
- Extract the three closures' shared setup (task creation/activation is already `_init_workflow_task`/`_activate_workflow`) and keep `execute_fn` focused on the per-attempt side-effect reset + `WorkflowStageFailure` conversion (AC-5/AC-6). Consider whether `verify_fn`'s no-op needs to exist as a closure at all, or can be a module-level no-op callback.
- Replace the inline `exit_reason` string threaded through six branches with a single small function that maps an engine outcome enum (or the returned typed tuple) directly to the status the adapter writes. The adapter already owns only the `"cancelled"` -> `"halted"` write; make that the sole adapter-owned branch explicit rather than a `None`-return convention.

Describe the extraction in terms of responsibility boundaries, not line numbers, unless a boundary itself is the decision.

## Target Files or Areas
- `scripts/agent/workflow_engine_adapter.py`
- `tests/agent/workflow/test_adapter_guards.py`, `tests/agent/workflow/test_adapter_store_ownership.py`

## Required Changes
- Extract turn-entry preparation into its own async method with the existing halt-routes preserved.
- Narrow `execute_fn` so the per-attempt `attempt_side_effect` reset and the `WorkflowStageFailure` conversion are visually grouped, and confirm the reset is attempt-scoped, not turn-scoped.
- Replace the `exit_reason` string + `_status_for_exit`/`_record_exit_status` `None`-return convention with one explicit adapter-owned status write; keep the engine's own terminal writes as the only other writer.
- Preserve the `_owns_state_store` close-on-exit behavior in the `finally`.

## Constraints
- Behavior must be byte-for-byte identical: same task statuses written on every exit path, same `answer`/`error_kind`/`is_partial` tuple, same `on_error`/`_handle_workflow_halt` routing.
- Do not change the engine's status writes, the retry loop, or the `attempt_side_effect` semantics.
- Public adapter surface (`execute_turn`, `deactivate_workflow`) signatures unchanged.

## Acceptance Criteria
- `execute_turn` no longer exceeds ~60 lines of control flow; the four responsibilities each live in a named method.
- Every existing exit-path test (`test_adapter_guards.py`, `test_adapter_store_ownership.py`) passes unchanged, asserting the same task statuses and returned tuples.
- No exit path leaves a task status unwritten that the current code writes.

## Testing Expectations
- Retarget existing adapter tests to the extracted methods; suites green.
- Add a regression test that a new early-exit path (e.g. a fresh exception type raised after `engine.run` starts) still produces the correct task status, so the state machine cannot silently drop a write again.
- Ruff/mypy clean on the touched file.

## Documentation Impact
If `docs/` describes the adapter's turn-execution flow or task-status ownership, confirm the extracted methods match. Prefer compressing any per-branch description into the responsibility boundary; do not add implementation-step detail.

## Out of Scope
- Changing the execute-stage retry/halt semantics (AC-5/AC-6).
- Changing the engine, `state_store.py`, or `orchestrator.py`.
- Renaming public adapter methods or changing `execute_turn`'s signature.

## Dependencies
- Related (same adapter, prior cleanup): `issues/done/20261107-203227_wfaudit014_retry-loop-dead-parameters.md` (removed a dead exit-path parameter; this addresses the remaining structural complexity).
- Context: `issues/done/20261107-203228_wfaudit015_state-store-facade-bypass.md` (facade routing in the same class pair); avoid conflicting refactors in the same pass.

## Unresolved Questions
- Should `verify_fn` remain a closure, or become a module-level no-op callback? The verify stage is required by the loader but the turn-end work now lives in the Orchestrator bracket, so the closure does nothing today. (Needs confirmation.)
- 不明: whether the owner wants the adapter's sole status write (`"cancelled"` -> `"halted"`) made explicit via an outcome enum, or kept as the current `None`-return convention.

## AI Implementation Instruction
Refactor only; do not change behavior. Extract the three responsibilities into named methods, keep the `_owns_state_store` close-on-exit in the `finally`, and preserve every task-status write on every exit path. Verify with the existing adapter tests plus one new early-exit regression test. Do not touch the engine or store.

## Traceability
- **Workflow phase**: `python-code-review` (review of `scripts/agent/workflow/` and the `workflow_engine_adapter.py` integration), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-221314
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`, `tests/agent/workflow/test_adapter_guards.py`, `tests/agent/workflow/test_adapter_store_ownership.py`
