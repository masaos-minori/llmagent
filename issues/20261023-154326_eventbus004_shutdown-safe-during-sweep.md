# Make EventBus shutdown safe while a background sweep is in flight

## Priority
High

## Summary
Give shutdown explicit ownership of the DLQ sweep worker so the shared SQLite connection is never closed while another worker may use it, and make the regression test assert that invariant.

## Background
Confirmed against HEAD (adversarial re-verification):
- The lifespan in `scripts/eventbus/app.py` cancels the DLQ asyncio task, then acquires the global DB lock with `asyncio.to_thread(lock.acquire, timeout=_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS)` (5.0 s) and calls `app.state.db.close()` in a `finally` even when the lock was not acquired; the fallback only logs `db lock not acquired ... closing db anyway (a sweep thread may still be using it)`.
- Waiting for an in-flight sweep is therefore already implemented and covered by `test_shutdown_waits_for_inflight_sweep_before_closing_db` in `tests/eventbus/test_eventbus_shutdown.py`. The unsafe part is only the timeout fallback, which `test_shutdown_logs_warning_when_lock_timeout_exceeded` explicitly requires ("still close the DB").
- `tests/eventbus/test_eventbus_app_isolation.py` replaces `_dlq_loop` with a no-op coroutine (`_noop_dlq_loop`) to avoid the segfault; the memo's path `tests/test_eventbus_app_isolation.py` does not exist.
- Additional race not named in the memo: cancelling the loop task does not cancel a worker thread that is still queued on the lock inside `run_with_db_lock`. After shutdown releases the lock, that thread can acquire it and run SQL on the closed connection (a `sqlite3.ProgrammingError`, swallowed or logged as `dlq_loop error`). Route handlers and SSE tasks that use `run_with_db_lock` have the same exposure if the server shuts down with requests in flight.

## Problem
A lock-acquisition timeout is evidence that another worker may still own the connection, yet the current fallback closes it anyway, which can crash inside SQLite or interrupt an active transaction. The timeout test enforces that unsafe behavior.

## Reason for Change
Controlled restart and WAL checkpoint procedures depend on orderly connection shutdown, and a regression test must enforce the safety invariant.

## Implementation Intent
Track the underlying sweep worker or future, stop scheduling new sweeps when shutdown starts, observe or join the in-flight worker, and close the connection only when exclusive ownership is proven. If shutdown must be bounded, choose and document a policy (process termination or connection isolation) that does not close a connection another worker owns.

## Target Files or Areas
`scripts/eventbus/app.py` (lifespan, `_dlq_loop`), `scripts/eventbus/route_helpers.py` (`run_with_db_lock`), `tests/eventbus/test_eventbus_shutdown.py`, `tests/eventbus/test_eventbus_app_isolation.py`, the EventBus service unit and process-manager stop policy (location not confirmed), `docs/24_eventbus/` and `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`.

## Required Changes
- Track the sweep worker or future explicitly and stop scheduling new cycles when shutdown starts.
- Wait for the active sweep before closing the shared connection; never close it when the lock was not acquired.
- Choose and document a safe bounded-shutdown policy.
- Update the timeout regression test to assert safe behavior and remove the no-op DLQ-loop workaround from the app-isolation tests.
- Use one cleanup helper in production and tests.

## Constraints
The shutdown bound must stay compatible with the process manager's stop timeout. No new thread leak.

## Acceptance Criteria
- The shared connection is never closed while another worker may use it.
- Real DLQ-loop shutdown tests pass without replacing the loop with a no-op and the timeout test no longer requires close-on-timeout.
- Repeated full-suite runs complete without a SQLite crash, and production and tests use the same lifecycle sequence.
- A sweep or request thread that is still queued on the database lock when shutdown starts cannot run SQL on the closed connection.

## Testing Expectations
Normal shutdown; sweep completed within the timeout; sweep exceeding the timeout; sweep exception; repeated full EventBus test-suite runs. Then ruff and mypy.

## Documentation Impact
Yes: the shutdown sequence, the connection-ownership rule and the bounded-shutdown policy.

## Out of Scope
The DLQ sweep logic itself; the WAL checkpoint step of the agent shutdown.
- Lazy loading of the Step 0 mandatory-load set — no action required: the fixed load is absorbed by the prompt cache (user decision 2026-10-24).

## Dependencies
Related memo tasks H-01 and H-05 (same connection and lock model). No open issue under `issues/` overlaps.

## Unresolved Questions
- The safe bounded-shutdown policy (wait indefinitely, terminate the process, or isolate the connection and leave it to process exit) is an owner decision.
- Does the process manager's stop timeout leave room for a longer wait than the current 5.0 s? The service unit location is not confirmed in this review.
- Should a shutdown flag make `run_with_db_lock` callers fail fast after shutdown starts (closing the queued-thread race and the in-flight-request exposure), or is draining enough? Needs confirmation.

## AI Implementation Instruction
- Read the listed implementation, tests, and design documents before editing; keep changes minimal and do not rewrite unrelated files.
- Preserve the existing public contract unless this issue explicitly names a contract change; an unresolved owner decision is reported, not guessed.
- Do not resolve an implementation defect by changing documentation alone.
- Keep transaction, locking, authorization, durability and fail-closed boundaries explicit.
- Add or update automated tests for every acceptance criterion; do not implement out-of-scope items.

## Traceability
- **Workflow phase**: `issue-creator` (converted from `memo-issue.md`, task `H-04`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-154326
- **Related target files**: `scripts/eventbus/app.py`, `tests/eventbus/test_eventbus_shutdown.py`, `tests/test_eventbus_app_isolation.py`
