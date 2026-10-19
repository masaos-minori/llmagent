## Goal
- Add coordinator tests for concurrent termination, signal-before-wait, interruption, and preserved failure handling with several servers (`REQ-005` (tests for the coordinator behavior), covering `REQ-002`, `REQ-003`, and `REQ-004`).

## Scope
- In scope: `tests/agent/test_http_lifecycle_shutdown_coordinator.py` only.
- Out of scope: the coordinator source, the terminator tests, and every other file (each has its own procedure document).

## Assumptions
- The coordinator change (concurrent termination) is applied before these tests are expected to pass; the concurrency and signal-order tests fail against the current sequential loop.
- The existing tests (`test_tracking_entry_persists_on_termination_failure`, `test_tracking_entry_removed_on_success`) keep passing unchanged.

## Design decisions
- Drive the coordinator with a fake terminator whose `terminate_with_timeout` records a "signalled" event, then awaits an `asyncio.Event` or a short sleep, so ordering and overlap are observable without real processes.
- Assert on ordering and overlap (all signalled before the first completes; total time near one delay, not the sum), not on exact wall-clock values.

## Alternatives considered
- Real subprocess children for the coordinator tests: rejected, because the terminator tests already cover real processes and mocks keep these tests fast and deterministic.

## Implementation
### Target file

`tests/agent/test_http_lifecycle_shutdown_coordinator.py`

### Procedure
1. Add a helper in the file that builds a mock manager for N servers (`iter_processes`, `remove_process_entry`, `cleanup_server_key`, `clear_all_health_checks`, `process_terminator`) following the existing tests' mock setup.
2. Add a test with 3 servers whose fake terminator waits 0.2 seconds each; assert `shutdown_all` finishes in well under 0.6 seconds and `cleanup_server_key` is called once per server.
3. Add a test that records events from the fake terminator and asserts all 3 "signalled" events occur before any "finished" event.
4. Add a test that cancels the `shutdown_all` task after the fake terminator calls have started and asserts all 3 servers had been signalled.
5. Add a test with 3 servers where the middle one raises `OSError`; assert the other two entries are cleaned up and only the failing one is retained (its `cleanup_server_key` not called).
### Method
- Follow the file's existing `pytest.mark.asyncio` style and `AsyncMock`/`MagicMock` usage; for the fake terminator use an `async def` that appends to a shared list at its first line, then awaits.
- Write steps 2 and 3 first and observe them fail against the current sequential loop.
### Details
- The cancellation test starts `shutdown_all` with `asyncio.create_task`, yields once with `await asyncio.sleep(0)` so the termination tasks start, then cancels and awaits the task with `pytest.raises(asyncio.CancelledError)`.

## Compatibility considerations
- N/A: test-only change.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -q` (new tests fail before the coordinator change, pass after).
- `uv run ruff format --check`, `uv run ruff check`, and `uv run mypy` on the file per `rules/toolchain.md`.

## Completion criteria
- The concurrency and signal-order tests fail on the sequential loop and pass after the change; the cancellation and failure tests pass after the change.
- The two existing tests still pass.

## Out of Scope
- Modifying any file other than the target file; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the multi-server tests and observe the concurrency and signal-order tests fail against the current loop | Completed | 20261019-222218 | 20261019-222218 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) after the coordinator change | Completed | 20261019-222218 | 20261019-222218 | Stale clean. 4 multi-server tests added; concurrency, signal-order and cancellation tests failed on the sequential loop and pass after the change. |

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
- **Requirement ID**: `REQ-005` (tests for the coordinator behavior)
- **Source issue**: issues/done/20261019-215906_mcpshut001_make-mcp-server-shutdown-bounded-and-complete.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-220318_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-220632
- **Related target files**: tests/agent/test_http_lifecycle_shutdown_coordinator.py