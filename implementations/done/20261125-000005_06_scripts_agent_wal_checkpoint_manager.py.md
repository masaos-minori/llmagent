## Goal

Make the checkpoint and backup steps respect the remaining deadline and publish the backup atomically under a database-scoped name, so a bounded shutdown cannot be consumed by retry sleeps and a partial backup file is never visible under its final name (REQ-008: the checkpoint and backup are bounded; REQ-009: the backup name and publication are safe; AC-3).

## Scope
**Release unit**: R5-checkpoint-and-backup (Phase 5)

- In scope: `checkpoint_sync()`, `_checkpoint_step()`, `backup_sync()`, `_backup_step()`, the retry sleeps, and the backup file name and publication.
- Out of scope: the step order that calls them (row 5) and the budget object (row 1).

## Assumptions

- The retry loop sleeps `time.sleep(2**attempt)` between TRUNCATE attempts (`scripts/agent/wal_checkpoint_manager.py:121`), so three attempts can consume 3 s of a window that the budget may already have reduced to well under that; the sleep must be bounded by the remaining deadline, not by the attempt count. Verified.
- The backup name today embeds a session id (`scripts/agent/wal_checkpoint_manager.py:177-186` builds `{basename}-wal-backup-{session_tag}-{int(time.time())}`), while the artifact is a property of the database file, not of the session that happened to be closing. Verified.
- The copy today writes the final name directly with `shutil.copy2` (`scripts/agent/wal_checkpoint_manager.py:187`), so an interrupted copy leaves a truncated file at the name a later reader would trust. Verified.
- Procedure line references corrected against the current file: `checkpoint_sync()` is at `:59`, `_checkpoint_step()` at `:68`, the retry loop at `:96-127`, `backup_sync()` at `:129`, `_backup_step()` at `:136`. The procedure's `:79` and `:187` references are stale.
- Step 2 of the procedure ("record the PASSIVE no-progress case as a step outcome rather than only a log line") is already satisfied today: the loop appends `wal_checkpoint_no_progress` to the returned errors and the coordinator turns a non-empty error list into a step record. No change needed beyond keeping it.
- `SQLiteHelper.interrupt_when` takes a `threading.Event`, not a predicate (`scripts/db/helper.py:184-210`), so the interrupt channel this row consumes is an Event. `ShutdownBudget` now owns one (`interrupt_event`, set by `request_interrupt()`), which is what lets a worker thread arm a real SQLite interrupt without polling. Row 10 only has to call `request_interrupt()`.

## Design decisions

- Both public methods take a monotonic `deadline` instant and the budget's `stop` event as keyword-only arguments and pass them to the worker thread; the step keeps running off the event loop (`asyncio.to_thread`) so the bounded step does not block the loop.
- Retry sleeps are clamped to the remaining deadline and the loop stops when the deadline is reached, recording the attempts it did not get to make rather than pretending they ran.
- Publication is temporary-then-publish: write to `<final>.partial` in the same directory, flush, `os.fsync`, verify the copied size against the source, then `os.replace` to the final name. A failure at any point removes the temporary file, records the error, and returns `None` as the path.
- The final name is database-scoped: the database file basename, a unix timestamp, and a per-process token, no session id (REQ-009).
- The coordinator gives the offloaded worker a bounded grace past its own deadline so the worker can report that it stopped before the outer `wait_for` fires, and maps the reported label onto the outcome (REQ-008).
- Compatibility impact: the backup file name changes shape, which the tests that build the name string must follow (rows 28, 29).

## Alternatives considered

- keep `shutil.copy2` and rename afterwards — rejected: `copy2` does not flush or sync the destination, so the size check would run against data still in the page cache.

## Implementation
### Target file
`scripts/agent/wal_checkpoint_manager.py`

### Procedure
1. Add keyword-only `deadline` (a monotonic instant) and `stop` (a `threading.Event | None`) to `checkpoint_sync()` (`scripts/agent/wal_checkpoint_manager.py:59`) and pass both to `_checkpoint_step()` (`scripts/agent/wal_checkpoint_manager.py:68`).
2. In the PASSIVE branch (`scripts/agent/wal_checkpoint_manager.py:86-93`), keep the no-progress detection and its `wal_checkpoint_no_progress` record (already a step outcome; unchanged).
3. In the TRUNCATE retry loop (`scripts/agent/wal_checkpoint_manager.py:96-127`), check the deadline and the stop event before each attempt, clamp each backoff to the time left, and wait on the stop event instead of `time.sleep` (`:121`), returning `wal_checkpoint_deadline` or `wal_checkpoint_interrupted` when the loop stops early. Treat a SQLite error raised while the stop is set as the progress-handler abort, not a lock to retry.
4. Add the same keyword-only parameters to `backup_sync()` (`scripts/agent/wal_checkpoint_manager.py:129`) and pass them to `_backup_step()` (`scripts/agent/wal_checkpoint_manager.py:136`), checking both before the copy starts.
5. Rewrite the backup body (`scripts/agent/wal_checkpoint_manager.py:177-186`): build the database-scoped name `{db_basename}-wal-backup-{unix seconds}-{process token}`, copy to `<final>.partial` in the same directory, flush and `os.fsync`, compare the copied size with the source size, then `os.replace` to the final name; remove the temporary file on every path, and return the path only for a published backup.
6. Install `db.interrupt_when(stop)` on the checkpoint connection and clear it in a `finally`, so a statement already running aborts when the event is set.
7. In the coordinator (`scripts/agent/resource_shutdown_coordinator.py`, Plan phase-5 step 5): pass `deadline=time.monotonic()+window` and `stop=self._interrupt_stop()`, give the outer `wait_for` `_WORKER_REPORT_GRACE_S` past the worker's own deadline so the worker's "I stopped" report arrives before the bound fires, and map the returned labels with `_wal_outcome()`: `*_deadline` → `timed_out`, `*_interrupted` → `outcome_unknown`, anything else → `failed`.

### Method
- The deadline is read at each boundary (before an attempt, before a sleep, before the copy), never computed once at entry, so a step that started with time left stops when the time is gone.
- The existing best-effort contract is kept: a failed backup is recorded in the returned error list, not raised.

### Details
- The temporary file lives in the same directory as the final name so `os.replace` is atomic on the same filesystem.
- The size check compares the destination against the source size read after the copy; a mismatch is recorded as `wal_backup_size_mismatch` so the report distinguishes "no space" from "interrupted".
- The process token is a module-level `uuid4().hex[:8]` (`_PROCESS_TOKEN`): the timestamp alone collides when two processes close in the same second.

### Companion test files
- `tests/agent/test_wal_checkpoint_manager.py`
  - Procedure: bound the retry sleeps by the remaining budget, assert the registered interrupt stops the worker, and assert publication through a temporary file with size verification.
  - Validation: `uv run pytest tests/agent/test_wal_checkpoint_manager.py -q` (REQ-008, REQ-009; AC-1, AC-3).
- `tests/agent/test_wal_backup_security.py`
  - Procedure: assert the new database-scoped backup name carries no session identifier, and that an interrupted copy leaves no file at the final name.
  - Validation: `uv run pytest tests/agent/test_wal_backup_security.py -q` (REQ-009, REQ-013; AC-3).

## Compatibility considerations

- The backup file name loses the session tag, so any consumer that parsed the name must use the new shape (rows 28, 29). `rg -n "wal-backup"` matches only test strings and this Plan's documents, so no production consumer exists.
- The returned tuples keep their shape, so the coordinator's handling (row 5) is unchanged apart from the new arguments. `backup_sync()` now returns `None` for a backup that was not published, where it previously returned the name it had failed to write.
- `checkpoint_sync()` and `backup_sync()` gained keyword-only arguments with `None` defaults, so every existing call site keeps working.
- `ShutdownBudget` gained `interrupt_event` (row 1's file, amended in this batch because `interrupt_when` needs an Event); `interrupt_requested` now reads the same event, so its behavior is unchanged.

## Security considerations

- The name is derived from the database basename and a timestamp, with no session identifier in a path that is logged (REQ-009, REQ-013).
- The containment and symlink expectations that already guard the backup directory keep holding: the temporary file is created inside the same validated directory.

## Rollback considerations

- Revert this row's commit with rows 28 and 29: the name shape and the publication flow are asserted by those tests.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/wal_checkpoint_manager.py` | Unit | `uv run pytest tests/agent/test_wal_checkpoint_manager.py tests/agent/test_wal_backup_security.py -q` | bounded retries, partial-file cleanup, database-scoped name, uniqueness pass |
| `scripts/agent/wal_checkpoint_manager.py` | Integration | `uv run pytest tests/agent/test_repl.py -q` | the shutdown path produces the new name and keeps path containment |

## Completion criteria

- A checkpoint or backup step cannot exceed the deadline it was given, and an interrupted backup leaves no file at the final name.
- The published name contains no session identifier and is created by `os.replace` from a temporary file that was flushed and synced.

## Out of Scope

- Step ordering, the budget object, and the write gate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-101400 | 20261125-102600 | Step 3b corrections applied before implementing: procedure line references corrected (`checkpoint_sync` `:59`, `_checkpoint_step` `:68`, `backup_sync` `:129`), PASSIVE no-progress already a recorded outcome (no change), interrupt channel is a `threading.Event` owned by `ShutdownBudget.interrupt_event` because `interrupt_when` takes an Event, coordinator passes the deadline plus a `_WORKER_REPORT_GRACE_S` bound and maps labels through `_wal_outcome()` |
| 2 | Add or update tests per Validation plan | Completed | 20261125-102600 | 20261125-103200 | companion rows 28, 29 (no separate procedure docs): `TestBoundedRetryAndInterrupt` (5) and `TestAtomicBackupPublication` (5) in `tests/agent/test_wal_checkpoint_manager.py`, `TestBackupNameShape` (4) replacing the three session-tag name tests in `tests/agent/test_wal_backup_security.py`, `TestWALStepsShareTheBudget` (4) in `tests/agent/test_resource_shutdown_coordinator.py`. 94 passed across the four shutdown files |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-104000 | 20261125-105200 | full R4+R5 batch gate ran: 14215 passed / 5 skipped (`-n logical -m "not integration and not production_paths_allowed and not repo_scan"`), diff-cover Pass, mypy Pass, lint-imports 6 kept, bandit Pass, check_docs_quality Pass, check_module_size Pass, reference-table/manifest drift Pass. `pre-commit run --all-files` still fails only on the two pre-existing hooks (workitem-structure on rows 45-54 and `issues/20261123-120131_02_unknowns.md`), identical to the R2 baseline. `wal_step_outcome()` docstring first line drops the `REQ-008` marker: the generated reference table copies it into an active document, which the Current-Specification-Only Policy rejects |

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
- **Requirement ID**: REQ-008 (bounded checkpoint and backup), REQ-009 (safe backup name and publication)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `scripts/agent/wal_checkpoint_manager.py`, `tests/agent/test_wal_checkpoint_manager.py`, `tests/agent/test_wal_backup_security.py`
