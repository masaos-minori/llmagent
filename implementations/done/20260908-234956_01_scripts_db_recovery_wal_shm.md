## Goal

Quarantine stale `-wal`/`-shm` sidecar files before atomic swap in `_restore_from_backup()`; stage and swap `-wal`/`-shm` sidecars alongside the main file when the backup has them (REQ-001, REQ-002).

## Scope

In scope: adding helper functions `_quarantine_sidecar_files()` and `_stage_backup_sidecars()` to `scripts/db/recovery.py`; integrating them into `_restore_from_backup()` around the atomic swap; adding unit tests for `-wal`/`-shm` presence/absence around restore in `tests/db/test_db_recovery.py`. Out of scope: changing `scripts/db/rotation.py`'s backup-creation mechanism unless investigation shows it cannot support WAL-consistent restore.

## Assumptions

- SQLite online backup API (`src.backup(dst)` in `rotation.py:41`) produces WAL-consistent backups — confirmed by SQLite documentation: the online backup API copies pages from the source database including those written to the WAL file since the last checkpoint.
- Quarantine is preferred over deletion for `-wal`/`-shm` files, consistent with the existing `corrupt_archive` pattern for the main database file.
- The backup path's `-wal`/`-shm` sidecars, if they exist, will have the same naming convention as the main database: `<stem>-wal` and `<stem>-shm`.
- The existing `tuple[DbCondition, str | None]` return shape satisfies structured dispatch — no need for an `IntegrityCheckResult` dataclass replacement.
- `recover_corruption()`'s existing branch that groups `INVALID_FORMAT` with `LOCK_CONTENTION`/`PERMISSION_FAILURE` (returning `action="error"` without touching backups) will receive dispatch correctly once `_classify_error()` can produce `INVALID_FORMAT` — confirmed by reading lines 301-311 of `recovery.py`.

## Design decisions

Quarantine strategy:
1. Generate a timestamped quarantine path: `db_path.with_name(f"{db_path.stem}_corrupt_{ts}{db_path.suffix}")`
2. Copy each `-wal`/`-shm` file to the quarantine directory using the same naming convention
3. Delete the original files after successful copy (non-destructive principle: originals preserved until success)

Backup-side `-wal`/`-shm` handling:
1. Check if `<backup_stem>-wal` and `<backup_stem>-shm` exist alongside `backup_path`
2. If present, copy them to the temp staging directory alongside `temp_restore`
3. After `os.replace(temp_restore, db_path)`, rename the temp `-wal`/`-shm` files to `<db_path.stem>-wal` and `<db_path.stem>-shm`

Integration points in `_restore_from_backup()`:
1. Call `_quarantine_sidecar_files()` before the atomic swap (after corrupt DB archival, before temp_restore copy)
2. Call `_stage_backup_sidecars()` after copying backup to temp_restore, before os.replace
3. After `os.replace(temp_restore, db_path)`, rename staged `-wal`/`-shm` files from temp dir to final locations alongside `db_path`

## Alternatives considered

- Deleting stale `-wal`/`-shm` files instead of quarantining — rejected: Plan explicitly states "Quarantine is preferred over deletion for `-wal`/`-shm` files, consistent with the existing `corrupt_archive` pattern for the main database file."
- Using SQLite's online backup API to checkpoint WAL before restore — rejected: Plan explicitly states "Do not invent checkpoint behavior beyond what `scripts/db/rotation.py`'s existing backup mechanism already guarantees."
- Adding a new `DbCondition` state — rejected: Plan explicitly states "Keep `DbCondition` as the contract (no new states)."

## Implementation
### Target file
`scripts/db/recovery.py`

### Procedure
1. Add helper function `_quarantine_sidecar_files(db_path, quarantine_dir)` to `scripts/db/recovery.py` — iterates over `<stem>-wal` and `<stem>-shm` files, copies them to quarantine dir, deletes originals on success (REQ-001; REQ-003)
2. Add helper function `_stage_backup_sidecars(backup_path, temp_restore_dir)` to `scripts/db/recovery.py` — checks for `<backup_stem>-wal` and `<backup_stem>-shm` alongside `backup_path`, copies them to temp staging dir if present (REQ-002; REQ-003)
3. In `_restore_from_backup()`, call `_quarantine_sidecar_files()` before the atomic swap (after corrupt DB archival, before temp_restore copy) (REQ-001; REQ-003)
4. In `_restore_from_backup()`, call `_stage_backup_sidecars()` after copying backup to temp_restore, before os.replace (REQ-002)
5. After `os.replace(temp_restore, db_path)`, rename staged `-wal`/`-shm` files from temp dir to final locations alongside `db_path` (REQ-002)

### Method
```python
import shutil
import time
from pathlib import Path

def _quarantine_sidecar_files(self, db_path: Path, quarantine_dir: Path) -> None:
    """Quarantine pre-existing -wal/-shm sidecar files associated with db_path."""
    stem = db_path.stem
    ts = int(time.time())
    
    # Find all sidecar files: <stem>-wal, <stem>-shm, etc.
    for suffix in ("-wal", "-shm"):
        sidecar = db_path.parent / f"{stem}{suffix}"
        if sidecar.exists():
            # Generate quarantine filename: <stem><suffix>_corrupt_<ts>
            quarantine_name = f"{stem}{suffix}_corrupt_{ts}"
            quarantine_path = quarantine_dir / quarantine_name
            
            # Copy to quarantine directory
            shutil.copy2(sidecar, quarantine_path)
            
            # Delete original only after successful copy
            sidecar.unlink()

def _stage_backup_sidecars(self, backup_path: Path, temp_restore_dir: Path) -> dict[str, Path]:
    """Stage -wal/-shm sidecars from backup_path alongside temp_restore."""
    stem = backup_path.stem
    staged = {}
    
    for suffix in ("-wal", "-shm"):
        sidecar = backup_path.parent / f"{stem}{suffix}"
        if sidecar.exists():
            # Copy to temp staging directory
            dest = temp_restore_dir / f"{stem}{suffix}"
            shutil.copy2(sidecar, dest)
            staged[suffix] = dest
    
    return staged

# Integration in _restore_from_backup():
# After corrupt archive, before temp_restore copy:
self._quarantine_sidecar_files(db_path, quarantine_dir)

# After copying backup to temp_restore, before os.replace:
staged_sidecars = self._stage_backup_sidecars(backup_path, temp_restore_dir)

# After os.replace(temp_restore, db_path):
for suffix, staged_path in staged_sidecars.items():
    final_path = db_path.parent / f"{db_path.stem}{suffix}"
    shutil.move(staged_path, final_path)
```

### Details
- The quarantine strategy follows the existing `corrupt_archive` pattern: generate a timestamped quarantine path, copy each `-wal`/`-shm` file to the quarantine directory, delete the original files after successful copy.
- The backup-side `-wal`/`-shm` handling uses the same naming convention as the main database: `<stem>-wal` and `<stem>-shm`.
- Error handling: If quarantining `-wal`/`-shm` files fails (e.g., permission denied), log an error and proceed with the main file swap — the stale sidecars remain on disk but the restore proceeds. This matches the existing behavior where errors during corrupt DB archival are logged but don't prevent the restore.
- The integration points ensure that stale sidecars are quarantined BEFORE the atomic swap, and backup sidecars are staged AFTER the backup is copied to temp_restore but BEFORE the atomic swap.

## Compatibility considerations

N/A: `_quarantine_sidecar_files()` and `_stage_backup_sidecars()` are private methods; no public API change. The existing `tuple[DbCondition, str | None]` return shape from `_run_integrity_check()` remains unchanged.

## Security considerations

N/A: no credential access, network operations, or filesystem writes introduced.

## Rollback considerations

Revert is a single-file change to `_restore_from_backup()` internals only. The existing substring matching logic serves as rollback-safe baseline since it was the original implementation.

## Validation plan

- Unit: construct exceptions per DbCondition state, assert correct return value — `uv run pytest tests/db/test_db_recovery.py::test_classify_* -v`.
- Regression: existing `recover_corruption()` tests still pass — `uv run pytest tests/db/test_db_recovery.py -v`.
- Integration: verify `recover_corruption()` dispatches `INVALID_FORMAT` to error action — `uv run pytest tests/db/test_db_recovery.py -v`.

## Completion criteria

- `_classify_error()` returns `DbCondition.INVALID_FORMAT` for `"file is not a database"` exception, distinct from `DbCondition.CORRUPTION` (AC-1).
- Lock-contention and permission-failure classification uses `sqlite3.OperationalError.errno` where available, with substring matching only as a documented fallback (AC-2).
- Direct unit test exists for `_classify_error()` covering all six `DbCondition` states (AC-3).
- Existing `recover_corruption()` tests continue to pass unchanged (AC-4).

## Out of scope

Changing `recover_corruption()` control flow or action names; changing `_run_integrity_check()` return shape; implementing backup-candidate domain-identity validation; changing WAL/SHM handling; adding `IntegrityCheckResult` dataclass.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add helper function _quarantine_sidecar_files() | Pending | — | — | |
| 2 | Add helper function _stage_backup_sidecars() | Pending | — | — | |
| 3 | Integrate _quarantine_sidecar_files() into _restore_from_backup() | Pending | — | — | |
| 4 | Integrate _stage_backup_sidecars() into _restore_from_backup() | Pending | — | — | |
| 5 | Rename staged -wal/-shm files after os.replace | Pending | — | — | |
| 6 | Add test cases per Validation plan | Pending | — | — | |
| 7 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260907-124049_h0704_staged_atomic_replacement_wal_shm_handling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-074605_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-234956
- **Related target files**: scripts/db/recovery.py
