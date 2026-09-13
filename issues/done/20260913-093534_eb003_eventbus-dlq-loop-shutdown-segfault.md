# EventBus process crashes with Segmentation Fault on shutdown due to `_dlq_loop` background-thread race

## Priority
High

## Summary
The Event Bus app's background DLQ-sweep loop can still be running its SQLite work in
a worker thread when the FastAPI `lifespan` shutdown path closes the database
connection, causing a native-level Segmentation Fault that crashes the whole process
(observed via a `pytest` run, but this is a process-lifecycle bug, not a test-only
artifact).

## Background
N/A: covered by Summary

## Problem
`scripts/eventbus/app.py`'s `lifespan()` starts `app.state.dlq_task =
asyncio.create_task(_dlq_loop(app))` on startup. `_dlq_loop()` calls `sweep_orphans()`
(via `run_with_db_lock()`, which runs the actual work through `asyncio.to_thread()` —
`scripts/eventbus/route_helpers.py`). On shutdown, `lifespan()` calls
`app.state.dlq_task.cancel()`, awaits it, then immediately calls `app.state.db.close()`.

`asyncio.Task.cancel()` only delivers `CancelledError` at the next `await` point inside
the coroutine — it cannot stop a `concurrent.futures.Future` that is already running in
a worker thread (a well-known `asyncio.to_thread`/executor limitation: once a thread has
started executing, cancelling the wrapping coroutine does not stop the thread itself).
So if `_dlq_loop`'s background thread is mid-execution of `sweep_orphans()` ->
`_shared_promote()` (`scripts/eventbus/dlq.py`) when shutdown begins, `await
app.state.dlq_task` can return (via `CancelledError`) while that thread is still
running — and the very next line, `app.state.db.close()`, closes the SQLite connection
out from under it. `EventBusConfig`'s connection is opened with
`check_same_thread=False` specifically to allow this kind of cross-thread access, but
that setting does not protect against a connection being closed while another thread is
using it.

## Reason for Change
Confirmed by repository evidence: a `pytest tests/eventbus/` run produced `Fatal Python
error: Segmentation fault`, with the crashing thread's stack at the moment of the crash
showing `scripts/eventbus/dlq.py:50 in _shared_promote` (a `db.execute(...)` call) ->
`sweep_orphans` -> `app.py:110 in _sweep` -> `route_helpers.py:99 in _locked`, while a
second thread's stack simultaneously showed `starlette/testclient.py:713 in __exit__`
(the `TestClient` context-manager exit, which triggers `lifespan` shutdown) inside the
test file's `client` fixture teardown. This is a process crash, not a normal exception
— it is not caught by any `except` clause and takes down the entire interpreter. In
production this would crash the live Event Bus service, not just a test run.

## Implementation Intent
Ensure shutdown genuinely waits for any in-flight `run_with_db_lock`-wrapped work to
finish (not just for the wrapping asyncio coroutine to observe cancellation) before
closing the database connection — e.g. by having the sweep loop check a shutdown
signal cooperatively between iterations and only closing the DB after the underlying
thread has actually returned, rather than relying on `asyncio.Task.cancel()` alone to
guarantee that.

## Target Files or Areas
- `scripts/eventbus/app.py` (`lifespan()`, `_dlq_loop()`)
- `scripts/eventbus/route_helpers.py` (`run_with_db_lock()`)

## Required Changes
- Change the shutdown sequence so `app.state.db.close()` is not reached until any
  in-progress `_dlq_loop` sweep (including its background-thread work) has actually
  finished, not merely until the wrapping asyncio task acknowledges cancellation.
- Consider whether `run_with_db_lock`/`_dlq_loop` need a cooperative shutdown signal
  (e.g. checked between sweep iterations) in addition to or instead of
  `asyncio.Task.cancel()`, given that `cancel()` cannot interrupt an already-running
  thread.

## Constraints
The fix must not introduce a shutdown hang: if the sweep is stuck, shutdown must still
have a bounded wait, not block forever. Preserve `check_same_thread=False`'s intended
cross-thread access pattern rather than serializing all DB access onto one thread,
unless the chosen fix specifically requires that trade-off.

## Acceptance Criteria
- Repeated full `tests/eventbus/` runs (e.g. 10+ consecutive runs, since this is a
  timing-dependent race) do not reproduce the Segmentation Fault.
- The DLQ sweep's own correctness (orphan promotion behavior, verified by `tests/
  eventbus/test_eventbus_dlq*.py`) is unaffected.
- Shutdown completes within a bounded time in the normal (no stuck thread) case.

## Testing Expectations
Add a regression test that reliably forces the race (e.g. injecting a delay into
`sweep_orphans`/`_shared_promote` so a sweep is guaranteed to be mid-flight when
shutdown is triggered) and asserts shutdown completes cleanly without crashing. Run
the full `tests/eventbus/` suite multiple times afterward to build confidence the
crash no longer reproduces (a single clean run is not sufficient evidence for a
timing-dependent bug).

## Documentation Impact
State whether `scripts/eventbus/`'s shutdown/lifecycle behavior is described anywhere
under `docs/06_eventbus_*.md`; if so, update it to describe the corrected shutdown
sequence's failure/operational behavior (per `skills/DESIGN.md` Docs content policy —
retain), not implementation detail.

## Out of Scope
- The `/events/{event_id}/ack` routing 403 issue (tracked separately).
- The per-role token validation issue (tracked separately).
- The `/nack` endpoint's `consumer_id` dependency-injection issue (tracked separately).

## Dependencies
N/A: none

## Unresolved Questions
- Whether this race is reachable in the actual production deployment (where shutdown
  is presumably less frequent than in a test suite running many short-lived
  `TestClient` instances back-to-back) is `Needs confirmation` — the risk is real
  regardless of frequency, but the operational likelihood is not yet measured.

## AI Implementation Instruction
This is the highest-severity of the four eventbus issues filed from this
investigation (process crash, not just incorrect behavior) — prioritize it
accordingly. Change only the shutdown/background-task lifecycle in the files listed
above; do not touch the DLQ promotion logic's correctness, the auth routing map, the
per-role token validation, or the `/nack` consumer_id handling — each has its own
tracked issue. Reproduce the crash first (or the timing-dependent regression test)
before considering the fix validated — do not rely on a single passing run.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-093534
- **Related target files**: scripts/eventbus/app.py, scripts/eventbus/route_helpers.py
