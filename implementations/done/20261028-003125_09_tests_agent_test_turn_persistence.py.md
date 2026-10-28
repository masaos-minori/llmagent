## Goal

Extend `tests/agent/test_turn_persistence.py` with the REQ-001 off-loop-thread proof
and the REQ-006 contention acceptance: a locked boundary write must not stall the
event loop (heartbeat keeps ticking) and must complete within `busy_timeout`.

## Scope

- Only `tests/agent/test_turn_persistence.py` (exists, created by turn001):
  - New test class (e.g. `TestOffloadedWrites` (new)) with file-backed DB tests that
    use the real `SQLiteHelper` instead of the existing in-memory
    `_FakeSQLiteHelper`, because cross-connection `busy_timeout` waiting requires a
    real DB file.
  - Off-thread proof: record `threading.get_ident()` around a patched repository write
    and assert the boundary write ran on a thread different from the event loop's.
  - Contention test per the frozen row: a second connection holds the write lock
    (`BEGIN IMMEDIATE`), a 50 ms heartbeat task keeps ticking while the boundary write
    waits, then the write completes within `busy_timeout`.
- Existing tests in the file stay untouched (they lock turn001 behavior).

## Assumptions

- Depends on `..._02_...` being implemented (offload wired) before these tests can
  pass; land order: `..._02_...` then this file (Plan phase P3 → P5).
- File-backed fixture: `SQLiteHelper(db_path=str(tmp_path / "turn.db"), sqlite_busy_timeout_ms=2000)`
  (explicit-path branch bypasses `build_db_config()`); schema created with the file's
  existing `_SCHEMA_SQL` constant.
- The locker connection is a plain `sqlite3.connect` created and used on a dedicated
  locker `threading.Thread` (owner thread), released via `commit`/`rollback` on command
  — deterministic, no sleep-based race assumptions; heartbeat tick counts are asserted
  with a lower bound (e.g. >= 2 ticks during a >= 300 ms lock hold), not exact timing.
- 50 ms heartbeat + 2000 ms busy_timeout keeps the test well under the suite timeout
  while producing several ticks.
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this file.

## Design decisions

- New class rather than editing existing tests: the fake-helper fixture cannot express
  two-connection contention; the class isolates file-DB fixtures to the new tests.
- Off-thread proof via thread identity (not timing): timing assertions are flaky;
  identity comparison is deterministic under `asyncio.to_thread`.

## Alternatives considered

- Contention via `fcntl`/OS-level file lock: rejected — sqlite's own
  `BEGIN IMMEDIATE` write-lock is exactly the mechanism the acceptance names.
- pytest-asyncio-only heartbeat via `time.monotonic` diffs: rejected as primary signal;
  tick counts prove the loop kept running, timestamps only prove wall time passed.

## Implementation

### Target file

`tests/agent/test_turn_persistence.py`

### Procedure

Add a file-backed test class with two acceptance tests.

### Method

1. Fixture `file_wired` (new): create the DB file with `_SCHEMA_SQL` + one session
   row; patch `agent.session_message_repo.SQLiteHelper` to a factory returning a real
   `SQLiteHelper(db_path=..., sqlite_busy_timeout_ms=2000)`; wire `AgentSession` +
   `ConversationState` + `TurnPersistence` as the existing `wired` fixture does.
2. `test_phase_write_runs_off_loop_thread` (new): capture
   `loop_thread = threading.get_ident()` inside `asyncio.run`; wrap the repository's
   `save_phase_grouped` with a spy recording `threading.get_ident()`; await
   `boundary.save_phase_grouped([...])`; assert recorded ident != loop_thread ident and
   the row exists.
3. `test_locked_write_does_not_stall_event_loop` (new):
   - Locker thread opens its own `sqlite3.connect(db_path)`, executes
     `BEGIN IMMEDIATE; INSERT` (holding the write lock), then waits on a
     `threading.Event` release signal before `commit()`.
   - Main: start a heartbeat task (`while True: ticks += 1; await asyncio.sleep(0.05)`);
     start `task = asyncio.ensure_future(boundary.save_phase_grouped([...]))`;
     sleep ~0.15 s asserting the task is not done and `ticks` keeps increasing (loop
     responsive while the write waits on `busy_timeout`);
     signal the locker to commit and join it; `await task` completes well within the
     2000 ms `busy_timeout`; assert the boundary row landed and `ticks >= 2`.
   - Heartbeat task is cancelled in `finally`.
4. Update the module docstring test inventory to list the two new acceptance areas
   (REQ-001 offload proof, REQ-006 contention).

### Details

- The spy must call through to the real repository method (wrap, not replace) so the
  per-call connection pattern under `to_thread` is what actually gets proven.
- Use `asyncio.run` per test (same async style as the file's existing async tests).
- WAL is applied by `SQLiteHelper` pragmas on its own connection; the locker uses a raw
  connection with the same file — `BEGIN IMMEDIATE` is the reserved write lock
  regardless of locker WAL participation.

## Compatibility considerations

- Existing `_FakeSQLiteHelper`-based tests must stay green (behavior lock for
  turn001); only additive changes to this file.

## Security considerations

- Tests touch only `tmp_path` files.

## Rollback considerations

- Additive class: removal reverts cleanly; keep as a separate commit from `..._02_...`
  so a failure can be attributed to either the offload or the tests.

## Validation plan

- `uv run pytest tests/agent/test_turn_persistence.py` (whole file) green — including
  the pre-existing turn001 tests.
- Full validation sequence (`rules/toolchain.md`).

## Completion criteria

- REQ-001: off-loop thread identity proven.
- REQ-006: heartbeat ticks during a held write lock, write completes within
  `busy_timeout` (acceptance criterion met).

## Out of Scope

- `tests/db/test_helper_thread_safety.py` probes (`..._08_...`).
- Tuning `busy_timeout` config values (Plan out-of-scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-085037 | 20261028-085037 | file_wired fixture (real SQLiteHelper, db_path branch, busy_timeout 2000ms, WAL pre-enabled in seed) + TestOffloadedWrites: off-loop thread identity proof + held-write-lock heartbeat contention test |
| 2 | Add or update tests per Validation plan | Completed | 20261028-085037 | 20261028-085037 | 2 new tests green; 6 pre-existing turn001 tests unchanged and green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-085037 | 20261028-085037 | whole file 8 passed (3 random-seed reruns stable); full suite 10261 passed shared with ..._02_; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-085037 | 20261028-085037 | out of scope |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| 20261028-003125-09 | 1 | test | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-003, REQ-006
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `tests/agent/test_turn_persistence.py`
