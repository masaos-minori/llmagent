# Close the EventBus shutdown admission race for workers queued on the database lock

## Priority
Medium

## Summary
Make the shutdown check and SQL execution atomic so that a request admitted before shutdown but still queued on the database lock cannot run SQL on the shared connection after shutdown closed it.

## Background
Source: `memo-issue.md` Issue 02, re-verified against current source on 2026-10-27. The memo rated it High; Phase 7 tie-breaking assigns Medium because the only demonstrated effect is a request failing during shutdown (see Reason for Change).

- `set_shutdown_flag()` in `scripts/eventbus/db_conn.py` documents that it makes `run_with_db_lock()` "refuse new work for any thread still queued on the lock (REQ-004)". `Explicit in code`.
- `run_with_db_lock()` in `scripts/eventbus/route_helpers.py` checks `is_shutting_down()` once, before `asyncio.to_thread(_locked)`. The inner `_locked()` takes `get_db_lock()` and calls `func()` without checking the flag again. `Explicit in code`.
- `_shutdown_lifespan()` in `scripts/eventbus/app.py` sets the flag, cancels the DLQ task, acquires the same lock, closes `app.state.db`, and releases the lock. It raises when the lock cannot be acquired within the timeout. `Explicit in code`.
- `bump_active_db_user()` / `release_active_db_user()` maintain a counter that shutdown does not read. `Explicit in code`.
- Interleaving that follows from the above: a request passes the pre-check, its worker waits on the lock, shutdown takes the lock and closes the connection, then the worker acquires the lock and executes SQL on the closed connection. `Strongly implied by code` (no test reproduces it).
- Prior work: `plans/done/20261025-113939_eventbus004_shutdown-safe-during-sweep.md` (REQ-004) intended to cover queued workers but implemented the flag as a pre-check only.
- The memo calls this `EVENTBUS-022`. The eventbus004 plan assigns EVENTBUS-022 to deployment readiness checks, and `docs/` currently lists no EVENTBUS-019 to 023 entries, so no ledger entry is referenced here.

## Problem
A worker that was admitted before the shutdown flag but acquires the lock after shutdown closed the connection runs SQL against a closed SQLite connection, contradicting the REQ-004 contract in the `set_shutdown_flag()` docstring.

## Reason for Change
The effect is bounded to requests in flight at shutdown (a `sqlite3.ProgrammingError` or a failed request), so it is Medium. It is still a contract violation that the eventbus004 work already tried to close, and the guard is cheap.

## Implementation Intent
Re-evaluate the shutdown state after the lock is acquired, inside the same critical section that registers the active user and runs SQL, so a worker admitted earlier exits without executing SQL once shutdown began. Decide whether the active-user counter has a role in shutdown or should be removed. Keep the refuse-to-close behavior on lock timeout unchanged.

## Target Files or Areas
- `scripts/eventbus/route_helpers.py` (`run_with_db_lock`)
- `scripts/eventbus/db_conn.py` (shutdown flag and active-user counter)
- `scripts/eventbus/app.py` (`_shutdown_lifespan`)
- `tests/eventbus/test_eventbus_shutdown.py` and related lifecycle tests

## Required Changes
- Recheck the shutdown flag after acquiring the DB lock and refuse to execute `func()` when set.
- Define the role of the active-user counter (use it in shutdown, or remove it).
- Make a worker that was queued before shutdown exit with the documented shutdown error and no SQL.
- Ensure later access to `app.state.db` after close fails explicitly (clear or replace the reference) if this does not change lifecycle behavior elsewhere.
- Add a deterministic regression test that forces the interleaving described in Background.

## Constraints
- Do not change the DLQ sweep logic or the bounded lock-acquire timeout behavior from eventbus004.
- Tests must use explicit synchronization (events, barriers), not sleeps.

## Acceptance Criteria
- A worker admitted before shutdown and acquiring the lock after close does not execute SQL.
- The queued-worker case, the in-flight sweep case and the in-flight request case all have deterministic tests.
- A second app lifecycle does not inherit stale shutdown state.
- The `set_shutdown_flag()` docstring matches the implemented behavior.

## Testing Expectations
- `uv run pytest tests/eventbus -q`, including the new deterministic test; confirm the new test fails on the current code.
- mypy and ruff on changed files; `tools/check_mock_patch_targets.py` if mocks are added.

## Documentation Impact
Only if the shutdown sequence text in the EventBus ops doc or ADR-006 states the queued-worker behavior; align it with the implementation (current behavior only). Otherwise none.

## Out of Scope
- Connection pooling or per-worker connections.
- Deployment readiness checks (EVENTBUS-022 as defined by the eventbus004 plan).
- Changing sweep scheduling.

## Dependencies
N/A: none open. `plans/20261027-120858_ebcompat002_decide-eventbus-db-facade.md` migrates the `route_helpers.py` imports; coordinate ordering if both are implemented (the `from eventbus.db import get_db_lock` import in `run_with_db_lock` is in scope of that plan).

## Unresolved Questions
- Is the active-user counter intended to gate shutdown? `Needs confirmation`.
- Whether any existing test already covers the queued-worker interleaving: `Needs confirmation` (search `tests/eventbus/test_eventbus_shutdown.py`).

## AI Implementation Instruction
Make the smallest change that closes the race in `run_with_db_lock`; do not refactor the lifespan or the facade. Write the failing deterministic test first. If the counter's intended role is unclear, stop and report instead of removing it.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-155845
- **Related target files**: `scripts/eventbus/route_helpers.py`, `scripts/eventbus/db_conn.py`, `scripts/eventbus/app.py`, `tests/eventbus/test_eventbus_shutdown.py`
