## Goal

Add the first real-body coverage of `WalCheckpointManager`: prove the bound is
enforceable when the step actually runs (REQ-001, REQ-002, REQ-008), that a
zero-frame contended checkpoint is recorded (REQ-005), and that the returned counts
are read rather than discarded (REQ-006).

## Scope

New test file `tests/agent/test_wal_checkpoint_manager.py`. No other file is
modified here. Reference reads: `scripts/agent/wal_checkpoint_manager.py` (the step
bodies under test), `scripts/db/helper.py` / `scripts/db/models.py` (`SQLiteHelper`,
`WalCheckpointCounts`). Depends on row 1 being implemented (the real step body).

## Assumptions

- A temporary SQLite database can be put into WAL mode with
  `PRAGMA journal_mode=WAL` and given committed rows so a second connection can hold
  an open read transaction over it.
- `asyncio.to_thread` gives `wait_for` an await point, so a step whose body blocks
  longer than a short bound raises `TimeoutError` at the bound (measured behavior,
  Background).
- Field names on `WalCheckpointCounts` are confirmed at `models.py:16-21` before use.

## Design decisions

- Build each test around a real temporary database (`tmp_path`), not a stub, so the
  assertion exercises the production step body (AC-1, REQ-011).
- Assert loop responsiveness during a retry backoff by scheduling a sentinel task and
  confirming it advances while the forced-retry step is mid-`time.sleep` (REQ-001,
  REQ-008) — a timing-free assertion via `asyncio.Event`, never a fixed sleep.
- Mark the end-to-end `close_resources` variant `@pytest.mark.integration` so it stays
  out of the default suite.

## Alternatives considered

- Stubbing `SQLiteHelper` (like the existing coordinator tests) — rejected: that is
  exactly the defect class REQ-011 forbids (a stub whose await behavior production
  lacks). Real database required for these assertions.

## Implementation

### Target file

`tests/agent/test_wal_checkpoint_manager.py` (new)

### Procedure

Create the file with the following cases:

1. **Success path + counts read (REQ-006).** Open a temp WAL database with committed
   rows; call the real `checkpoint_sync`; assert it returns `ok=True` and truncates
   the WAL, and assert the returned `WalCheckpointCounts` frames value is read into
   the result (not discarded) — e.g. the returned flag / recorded entry reflects the
   actual frame count.
2. **Zero-frame contention (REQ-005).** Hold a second connection open in a read
   transaction over the same database; drive a PASSIVE checkpoint that copies zero
   frames while `counts.log > 0`; assert a shutdown-error entry naming the frame
   count is recorded, and that the same over an *empty* WAL (`counts.log == 0`)
   records nothing (AC-4).
3. **Loop responsive during backoff (REQ-001, REQ-008).** Force the TRUNCATE retry
   path (e.g. make the first TRUNCATE raise once) so the step hits its
   `time.sleep(2 ** attempt)` backoff; concurrently schedule a task that sets an
   `asyncio.Event`; assert the event is set within a generous `asyncio.wait_for`
   bound, proving the loop was free during the sleep.
4. **Bound expires while step runs (REQ-001).** With a step body that blocks longer
   than a short bound (a real contended checkpoint, or a controlled block), assert
   `asyncio.wait_for` raises `TimeoutError` at the bound and the body is reported as
   not completed. Built from the production step body, not a stub.

### Details

- Use `@pytest.mark.asyncio` (auto mode per `pyproject.toml`). For cases that touch
  the real loop signal/executor, keep them plain unit tests (no real signals).
- Clean up temp databases in `finally` / `asyncio` teardown; avoid file-handle leaks
  (Risks).
- Do not import or reference any symbol that does not yet exist in row 1 without
  marking it `(new)` (e.g. a new helper the step exposes).

## Compatibility considerations

- New file; no interaction with existing tests. Runs alongside
  `tests/agent/test_resource_shutdown_coordinator.py`.

## Security considerations

- N/A: tests operate on throwaway temporary databases under `tmp_path`.

## Rollback considerations

- Delete the file. Single logical commit; reversible.

## Validation plan

- `uv run pytest tests/agent/test_wal_checkpoint_manager.py -q` (all four cases pass).
- Mutation: deleting the `time.sleep` line must fail case 3 (timing/responsiveness
  assertion); removing the zero-frame recording must fail case 2.
- `uv run pytest tests/agent -q --durations=10` to confirm no slow-test / handle-leak
  regression.

## Completion criteria

The four cases pass against a real temporary database, the mutation checks behave as
stated, and no integration-marked case runs in the default suite.

## Out of Scope

- Production step edits — row 1. Coordinator tests — row 4. `test_repl.py` — row 5.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `test_wal_checkpoint_manager.py` with the four real-body cases | Pending | — | — | REQ-001, REQ-005, REQ-006 |
| 2 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-005, REQ-006, REQ-008
- **Source issue**: `issues/20261021-093421_shutdown001-wal-checkpoint-timeout-guard-cannot-fire.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043330_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-084708
- **Related target files**: `tests/agent/test_wal_checkpoint_manager.py` (new)
