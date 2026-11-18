# Round completion runs async work inside the BaseException/cancellation handler of `execute_all_tool_calls`

## Priority
Low

## Summary
Bound the best-effort round completion in `execute_all_tool_calls` so it neither extends
the shutdown window nor risks replacing the original exception with a second
`BaseException` raised while completing a cancelled round.

## Background
`tool_runner.py::execute_all_tool_calls` wraps DAG execution in `except BaseException:`
and calls `await finish(ToolCallStopReason.ROUND_NOT_COMPLETED)` — which runs
`complete_round` (appends tool results to history and persists them) — before re-raising.
This is intentional best-effort persistence of whatever already ran during a round that
did not complete (e.g. a `asyncio.CancelledError`).

## Problem
Two related concerns:
- During cancellation, awaiting `finish()` performs additional DB/history writes before the
  exception propagates, extending the time before the process can honor a shutdown signal.
- If `finish()` raises a second `BaseException` (e.g. another `CancelledError`), the inner
  `except Exception` guard does not catch it; it propagates out of the handler and replaces
  the original exception in the chain. Both are cancellation-related, so the observable
  outcome (turn aborted) is unchanged, but the surfaced exception is no longer the one that
  started the unwind.

## Reason for Change
The current behavior is defensible (best-effort persistence), but a graceful shutdown that
must be fast pays the full round-completion cost, and the exception-replacement edge case
makes debugging the true origin harder. Non-blocking; the fix is optional and gated.

## Implementation Intent
Guard the completion call so it only runs when the task is not already cancelled, e.g.
`if not asyncio.current_task().cancelled(): await finish(...)`. This preserves the
best-effort persistence for a genuine mid-round failure while skipping the write when the
task is being cancelled. Alternatively bound `finish()` with `asyncio.wait_for` and a
short timeout. Preserve the final bare `raise` so the original unwinding exception still
propagates. Do not change the per-call `Exception`-to-error-row conversion or the
`CancelledError` propagation contract (AC-5).

## Target Files or Areas
- `scripts/agent/tool_runner.py` (`execute_all_tool_calls`, `except BaseException` branch)

## Required Changes
- Skip or bound `finish()` when the current task is cancelled.
- Ensure the original exception is still re-raised after the guarded completion.

## Constraints
- Must not change AC-5: a `CancelledError` (or any `BaseException`) must still propagate out
  of `execute_all_tool_calls`.
- Must not swallow a genuine (non-cancellation) failure: a round that truly did not
  complete must still attempt best-effort completion.
- Do not change `_recorded_call`'s per-call exception handling.

## Acceptance Criteria
- On a real mid-round failure (not a cancellation), the round is still completed
  best-effort.
- On cancellation, `finish()` is skipped or bounded and the original `CancelledError`
  propagates unchanged.

## Testing Expectations
- Unit test: a round interrupted by `CancelledError` re-raises the same exception type and
  does not perform the completion writes (or completes within a bound).
- Unit test: a round interrupted by a plain `Exception` still attempts best-effort
  completion.
- `ruff` and `mypy --no-namespace-packages` on `tool_runner.py`; existing tool-execution
  tests pass unchanged.

## Documentation Impact
Not required unless docs describe the cancellation/shutdown completion contract; if so,
note the guarded skip.

## Out of Scope
- Changing how cancelled tool-call state rows are cleaned up (stale-pending detection).
- Changing the per-call error-row conversion or DAG scheduling.

## Dependencies
N/A: none.

## Unresolved Questions
- Whether graceful-shutdown latency is ever measurable here (不明); gate the change on a
  confirmed shutdown-time concern rather than speculatively.

## AI Implementation Instruction
In `scripts/agent/tool_runner.py`, guard the `finish()` call in `execute_all_tool_calls`
so it is skipped or time-bounded when `asyncio.current_task().cancelled()` is True, and
keep the final bare `raise`. Do not alter AC-5 propagation or the per-call exception
handling. Add tests for both the cancelled and genuine-failure paths.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-141420
- **Related target files**: scripts/agent/tool_runner.py
