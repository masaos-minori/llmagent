## Goal

Make the checkpoint and backup steps respect the remaining deadline and publish the backup atomically under a database-scoped name, so a bounded shutdown cannot be consumed by retry sleeps and a partial backup file is never visible under its final name (REQ-008: the checkpoint and backup are bounded; REQ-009: the backup name and publication are safe; AC-3).

## Scope
**Release unit**: R5-checkpoint-and-backup (Phase 5)

- In scope: `checkpoint_sync()`, `_checkpoint_step()`, `backup_sync()`, `_backup_step()`, the retry sleeps, and the backup file name and publication.
- Out of scope: the step order that calls them (row 5) and the budget object (row 1).

## Assumptions

- The retry loop sleeps `time.sleep(2**attempt)` between TRUNCATE attempts, so three attempts can consume 3 s of a window that the budget may already have reduced to well under that; the sleep must be bounded by the remaining deadline, not by the attempt count.
- The backup name today embeds a session id (`scripts/agent/wal_checkpoint_manager.py:177-186` builds `{basename}-wal-backup-{session_tag}-{int(time.time())}`), while the artifact is a property of the database file, not of the session that happened to be closing.
- The copy today writes the final name directly with `shutil.copy2`, so an interrupted copy leaves a truncated file at the name a later reader would trust.

## Design decisions

- Both public methods take the remaining deadline and pass it to the worker thread; the step keeps running off the event loop (`asyncio.to_thread`) so the bounded step does not block the loop.
- Retry sleeps are clamped to the remaining deadline and the loop stops when the deadline is reached, recording the attempts it did not get to make rather than pretending they ran.
- Publication is temporary-then-publish: write to a temporary file in the same directory, flush, `os.fsync`, verify the copied size against the source, then `os.replace` to the final name. A failure at any point removes the temporary file and records the error.
- The final name is database-scoped: the database file basename plus a timestamp, no session id (REQ-009).
- Compatibility impact: the backup file name changes shape, which the tests that build the name string must follow (rows 28, 29).

## Alternatives considered

- keep `shutil.copy2` and rename afterwards — rejected: `copy2` does not flush or sync the destination, so the size check would run against data still in the page cache.

## Implementation
### Target file
`scripts/agent/wal_checkpoint_manager.py`

### Procedure
1. Add the remaining-deadline parameter to `checkpoint_sync()` (`scripts/agent/wal_checkpoint_manager.py:66`) and pass it to `_checkpoint_step()` (`scripts/agent/wal_checkpoint_manager.py:79`).
2. In the PASSIVE branch (`scripts/agent/wal_checkpoint_manager.py:86-93`), keep the no-progress detection and record it as a step outcome rather than only a log line.
3. In the TRUNCATE retry loop (`scripts/agent/wal_checkpoint_manager.py:96-127`), clamp each attempt and each `time.sleep` (`scripts/agent/wal_checkpoint_manager.py:134`) to the remaining deadline, and stop early with a recorded reason when the deadline is spent.
4. Add the remaining-deadline parameter to `backup_sync()` (`scripts/agent/wal_checkpoint_manager.py:187`) and pass it to `_backup_step()`.
5. Rewrite the backup body (`scripts/agent/wal_checkpoint_manager.py:177-186`): build the database-scoped name, copy to a temporary file in the same directory, flush and `os.fsync`, compare the copied size with the source size, then `os.replace` to the final name; remove the temporary file on any failure.
6. Register the interrupt request so a second SIGINT can stop a sleeping retry (row 10 routes it).

### Method
- The deadline is read at each boundary (before an attempt, before a sleep, before the copy), never computed once at entry, so a step that started with time left stops when the time is gone.
- The existing best-effort contract is kept: a failed backup is recorded in the returned error list, not raised.

### Details
- The temporary file lives in the same directory as the final name so `os.replace` is atomic on the same filesystem.
- The size check compares the destination against the source size read after the copy; a mismatch is recorded as a distinct error code so the report distinguishes "no space" from "interrupted".

### Companion test files
- `tests/agent/test_wal_checkpoint_manager.py`
  - Procedure: bound the retry sleeps by the remaining budget, assert the registered interrupt stops the worker, and assert publication through a temporary file with size verification.
  - Validation: `uv run pytest tests/agent/test_wal_checkpoint_manager.py -q` (REQ-008, REQ-009; AC-1, AC-3).
- `tests/agent/test_wal_backup_security.py`
  - Procedure: assert the new database-scoped backup name carries no session identifier, and that an interrupted copy leaves no file at the final name.
  - Validation: `uv run pytest tests/agent/test_wal_backup_security.py -q` (REQ-009, REQ-013; AC-3).

## Compatibility considerations

- The backup file name loses the session tag, so any consumer that parsed the name must use the new shape (rows 28, 29).
- The returned tuples keep their shape, so the coordinator's handling (row 5) is unchanged apart from the new parameter.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion rows 28, 29 |
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
- **Requirement ID**: REQ-008 (bounded checkpoint and backup), REQ-009 (safe backup name and publication)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `scripts/agent/wal_checkpoint_manager.py`, `tests/agent/test_wal_checkpoint_manager.py`, `tests/agent/test_wal_backup_security.py`
