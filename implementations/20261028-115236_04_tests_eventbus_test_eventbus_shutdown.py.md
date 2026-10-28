# Procedure: add the deterministic queued-worker regression test and the lifecycle tests

## Goal

Write the failing queued-worker test and the in-flight, cleared-state and second-lifecycle tests with explicit synchronization (Plan REQ-004).

## Scope

- Modify only `tests/eventbus/test_eventbus_shutdown.py`.
- Test-only change; no source file is edited.

## Assumptions

- Ordering note: this row's tests are written before rows 1 and 3 are applied (Plan Phase 1); the plan table fixes `seq`, so run this row first by hand and confirm the red result.
- Overlap (compatible): `plans/20261028-094217_ebmetrics006_correct-db-timing-health.md` also targets `scripts/eventbus/route_helpers.py` (timing statements around the lock acquisition) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Metrics section); `plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (archived) targeted `scripts/eventbus/app.py` (ACK/NACK wiring only). This procedure edits the shutdown re-check, the shutdown state and the Shutdown section.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/eventbus/test_eventbus_shutdown.py`

### Procedure

- Add `test_queued_worker_refuses_sql_after_shutdown_began` (new): replace `eventbus.db.get_db_lock` through `monkeypatch` with a `threading.Lock` wrapper whose `__enter__` sets a `threading.Event` before acquiring; hold the real lock in the test, start `run_with_db_lock(func)` as a task, wait on the event, call `set_shutdown_flag()`, release the lock and await the task; assert `RuntimeError` and that `func` was never called.
- Add `test_inflight_request_completes_before_connection_close` (new): run a worker that holds the lock until a `threading.Event` is set, start `_shutdown_lifespan`, release the worker, and assert the worker finished before the connection closed.
- Add `test_shutdown_clears_app_state_db` (new): after `_shutdown_lifespan`, assert `app.state.db is None` and that `app_get_db(app)` raises `RuntimeError`.
- Add `test_second_lifecycle_does_not_inherit_shutdown_flag` (new): enter and exit the app lifespan twice (the existing sweep test shows the `load_config` and schema monkeypatching) and assert `run_with_db_lock` works inside the second context.
- Bound every wait with a timeout; use no sleeps.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Apply this row first (the Plan's Phase 1 is tests first) even though its `seq` follows the source rows; confirm the queued-worker test fails on the unmodified code before applying the guard.
- The conftest autouse fixture `_reset_db_conn_state` restores the flag and the counter after each test.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_shutdown.py tests/eventbus/test_eventbus_health.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_shutdown.py`; `uv run ruff check tests/eventbus/test_eventbus_shutdown.py` | No finding |

## Completion criteria

- The queued-worker test fails on the pre-change code and passes after row 1.
- The in-flight sweep, lock-timeout and pre-check tests still pass.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-004 (regression test first; in-flight and second-lifecycle cases)
- **Source issue**: issues/20261027-155845_ebshutdown002_close-shutdown-admission-race.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115236
- **Related target files**: tests/eventbus/test_eventbus_shutdown.py
