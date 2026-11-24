## Goal

Make the threaded write paths in the helper thread-safety tests gate-aware, so the exact entry points the gate now guards are proven to refuse from worker threads as well as from the calling thread (REQ-004: writes stop when shutdown starts; REQ-005: enforced in the db layer; AC-2).

## Scope
**Release unit**: R2-write-gate (Phase 2)

- In scope: the existing threaded `open(write_mode=True)`, `execute` and `commit` cases in this file.
- Out of scope: the gate itself (row 2), the guard placement (row 3), and the gate's own unit cases (row 21).

## Assumptions

- The cases this row touches are the threaded write helpers: `write_row()` (`tests/db/test_helper_thread_safety.py:37-39`), the worker-thread `use_conn()` bodies (`tests/db/test_helper_thread_safety.py:56-62`, `tests/db/test_helper_thread_safety.py:92`), and the `helper.open(write_mode=True)` arrangements around them.
- The gate is process-wide (row 2), so a refusal raised in a worker thread is the same exception the calling thread would get.

## Design decisions

- Add refusal cases to the existing threaded cases rather than writing a new file: these tests already drive writes from worker threads, which is the path where a gate check could plausibly be missed.
- Assert the refusal in the worker thread and the success in an authorized context separately, so a leak of authorization across threads would fail a case rather than pass silently.
- Keep the existing concurrency assertions untouched: this row adds expectations, it does not rework the threading scenarios.

## Alternatives considered

- test the gate only from the main thread — rejected: the helper's write paths are used from `asyncio.to_thread` workers, and a per-thread check would be invisible to a main-thread-only test.

## Implementation
### Target file
`tests/db/test_helper_thread_safety.py`

### Procedure
1. In the threaded write cases (`tests/db/test_helper_thread_safety.py:37-39`, `tests/db/test_helper_thread_safety.py:56-62`, `tests/db/test_helper_thread_safety.py:92`), add a case that closes the gate before the worker runs and asserts `WriteGateClosed` (new) surfaces from the worker.
2. Add a case that runs the same worker inside the authorized context (row 2) and asserts the write succeeds.
3. Keep the existing unguarded cases running with the gate open so today's behavior stays covered.

### Method

- Each new case closes the gate in the test body before starting the thread, so the state under test is explicit rather than inherited.

### Details

- The refusal is asserted by exception type, not by message text (REQ-013).

## Compatibility considerations

- Existing cases keep their current expectations; only new cases are added.

## Security considerations

- N/A: no path or credential is asserted.

## Rollback considerations

- Revert this row's commit with rows 2, 3 and 21: the guard and its expectations are one release unit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/db/test_helper_thread_safety.py` | Unit | `uv run pytest tests/db/test_helper_thread_safety.py tests/db/test_write_gate.py -q` | threaded writes refuse in `closing` and `closed`, authorized writes pass |

## Completion criteria

- A write attempted from a worker thread after the gate closes raises `WriteGateClosed` (new), and the same write inside an authorized context succeeds.

## Out of Scope

- Gate state management and the public-API expectations (row 24).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | this row is the test row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (writes stop at shutdown), REQ-005 (enforced in the db layer)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `tests/db/test_helper_thread_safety.py`, `scripts/db/helper.py`
