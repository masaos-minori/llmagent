# A failed or cancelled turn is recorded as `completed` in the workflow task table

## Priority
High

## Summary
Stop the adapter's `finally` from overwriting the task status the workflow engine already wrote, so
`tasks.status` reflects what actually happened.

## Background
`WorkflowEngine.run` records the outcome before re-raising: `halted` for
`WorkflowHaltError`/`WorkflowTimeoutError`, `failed` for any other `Exception`
(`scripts/agent/workflow/workflow_engine.py:124-133`). `WorkflowEngineAdapter.execute_turn` then runs a
`finally` block (`scripts/agent/workflow_engine_adapter.py:186-201`) that writes a status whenever
`engine_status_handled` is false: `"failed"` if `error_kind is not None`, otherwise `"completed"`.

## Problem
- A non-retryable stage (`plan`, `verify`) or an `execute_fn` that raises: the engine writes `failed`
  and re-raises a plain exception; the adapter's `except (WorkflowHaltError, WorkflowTimeoutError)` does
  not match it, so `engine_status_handled` stays `False` and `error_kind` is still `None` — the
  `finally` overwrites the row with `completed`.
- A cancelled turn (the REPL cancelling an in-flight dispatch): `asyncio.CancelledError` is not
  `Exception`, so the engine does not write a status at all, and the adapter's `finally` writes
  `completed`.
- Only the `WorkflowHaltError`/`WorkflowTimeoutError` paths are protected by
  `engine_status_handled`; every other failure ends up recorded as success.
The write is additionally best-effort (`except Exception` → `logger.warning`, `:200-201`), so a status
mismatch is not reported.

## Reason for Change
`tasks.status` is the record the system relies on for resumed/halted work and for `/stats`-style
inspection. Recording failures as `completed` removes the only durable signal that a turn did not
finish.

## Implementation Intent
Write the status once, in one owner. Either let the engine's transitions stand and have the adapter fill
in only what the engine could not know, or make the adapter compute the final status from the propagated
exception type instead of from `error_kind` alone.

## Target Files or Areas
- `scripts/agent/workflow_engine_adapter.py` (`execute_turn` `finally`, `_handle_workflow_halt`)
- `scripts/agent/workflow/workflow_engine.py` (status transitions, reference)

## Required Changes
- Make the adapter's `finally` non-destructive: never replace `halted`/`failed` already written by the
  engine.
- Derive the final status from the exit reason (exception type, `CancelledError`, normal return), not
  from `error_kind` alone.
- Handle `CancelledError` explicitly so a cancelled turn is not recorded as `completed`.
- Surface a failed best-effort status write as an observable error rather than only a warning.

## Constraints
- The engine's `halted` semantics and `WorkflowHaltError` handling must not change.
- `_handle_workflow_halt` (`workflow_engine_adapter.py:311-321`) currently leaves `error_kind` unset;
  whatever is chosen must keep the REPL-visible behavior for halts unchanged.
- `tasks.status` values are an existing schema contract (`scripts/db/schema_sql.py`); do not invent new
  status strings without a schema decision.

## Acceptance Criteria
- A turn whose `verify` stage raises leaves `tasks.status = 'failed'`.
- A turn whose dispatch is cancelled leaves a status that is not `completed`.
- A successfully completed turn still records `completed`.
- A test asserts the status transitions for: success, retry-exhausted halt, timeout, plain exception,
  cancellation.

## Testing Expectations
- Regression tests at the adapter level with a real `StateStore` on a `tmp_path` DB, asserting the row's
  `status` after each failure mode.
- Mutation check: removing the overwrite must not break any existing test that asserts `completed`.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document the status state machine (who writes which status and when) in the workflow docs, including the
`cancelled`/`halted`/`failed`/`completed` distinction and that status writes are best-effort.

## Out of Scope
- Retry policy values and stage semantics.
- Turn audit events (`turn004`) and task identity (`turn001`).

## Dependencies
- After `turn001` (a task row must exist for any status) and before/independent of `turn004`.
- `turn002` changes what the `execute` stage does; sequence after it to keep the failure taxonomy valid.

## Unresolved Questions
- Is a cancelled turn `halted`, `failed`, or a distinct status? Needs a decision before implementation.
- Should `_handle_workflow_halt` set `error_kind` so the REPL can distinguish a halted turn? Needs
  confirmation.

## AI Implementation Instruction
One writer per state transition. Make the exit reason explicit in code instead of inferring it from
`error_kind`, and cover every exit path with a test.

## Traceability
- **Workflow phase**: `python-code-review` (turn orchestration review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`,
  `scripts/agent/workflow/workflow_engine.py`, `scripts/db/schema_sql.py`
