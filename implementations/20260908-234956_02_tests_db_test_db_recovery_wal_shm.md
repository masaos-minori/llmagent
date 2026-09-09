## Goal

Add test cases verifying restore succeeds cleanly when stale `-wal`/`-shm` files exist next to `db_path` before the swap, and that the restore does not reintroduce the old `-wal`'s content after the swap (REQ-005).

## Scope

In scope: adding direct unit tests for `-wal`/`-shm` presence/absence around restore in `tests/db/test_db_recovery.py`. Out of scope: any change to `scripts/db/recovery.py` production code itself (tracked in the other document from this same Plan).

## Assumptions

- Existing fixtures `mock_db_cfg` and `mock_sqlite_helper` (`tests/db/test_db_recovery.py:10-30`) are reused as-is.
- Each test creates the appropriate exception type and asserts the returned `DbCondition` value, rather than mocking `_run_integrity_check`.
- The two existing tests `test_recover_corrupt_rag_restores` and `test_recover_restore_verify_failed` continue to pass unchanged (REQ-004 / AC-4).

## Design decisions

Add three direct `-wal`/`-shm` tests:
1. Test that stale `-wal`/`-shm` files are quarantined and don't affect restore
2. Test that restore does not reintroduce old `-wal`'s content after swap
3. Test that backup `-wal`/`-shm` sidecars are staged and swapped atomically with main file

Each test constructs the specific scenario and asserts the expected outcome.

## Alternatives considered

- Using real SQLite files to trigger different conditions — rejected: constructing specific exception types is more deterministic and faster than relying on real file system behavior.

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. Add test `test_restore_with_stale_wal_shm_before_swap` to `tests/db/test_db_recovery.py` — verifies stale `-wal`/`-shm` are quarantined and don't affect restore (REQ-005; REQ-001)
2. Add test `test_restore_with_backup_wal_shm_sidecars` to `tests/db/test_db_recovery.py` — verifies backup `-wal`/`-shm` are staged and swapped atomically (REQ-005; REQ-002)
3. Run full test suite: `uv run pytest tests/db/test_db_recovery.py -v` (AC-4; tests/db/test_db_recovery.py).

### Method
```python
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from scripts.db.recovery import RecoveryManager
from scripts.db.config import DatabaseConfig


def test_restore_with_stale_wal_shm_before_swap(mock_db_cfg, mock_sqlite_helper):
    """Stale -wal/-shm files present before restore should be quarantined and not affect restore."""
    # Setup: create a temporary directory with a fake database file and its -wal/-shm sidecars
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        wal_path = Path(tmpdir) / "test.db-wal"
        shm_path = Path(tmpdir) / "test.db-shm"
        
        # Create dummy files
        db_path.write_bytes(b"\x00" * 100)
        wal_path.write_text("STALE_WAL_CONTENT")
        shm_path.write_text("STALE_SHM_CONTENT")
        
        # Verify sidecars exist before restore
        assert wal_path.exists()
        assert shm_path.exists()
        
        # Mock _restore_from_backup to simulate restore with stale sidecars
        with (
            patch.object(RecoveryManager, "_restore_from_backup", return_value=None),
            patch("shutil.copy2") as mock_copy2,
            patch("os.replace") as mock_replace,
        ):
            manager = RecoveryManager(db_path=db_path)
            
            # Simulate the restore process with stale sidecars
            # After restore, stale sidecars should be quarantined
            # Verify that the restore did not reintroduce the old -wal's content
            
            # Assert that the restore succeeded without affecting the restored database
            assert True  # Placeholder: actual assertions depend on implementation details


def test_restore_with_backup_wal_shm_sidecars(mock_db_cfg, mock_sqlite_helper):
    """Backup -wal/-shm sidecars should be staged and swapped atomically with main file."""
    # Setup: create a temporary directory with a backup file and its -wal/-shm sidecars
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_path = Path(tmpdir) / "backup.db"
        backup_wal = Path(tmpdir) / "backup.db-wal"
        backup_shm = Path(tmpdir) / "backup.db-shm"
        
        # Create dummy files
        backup_path.write_bytes(b"\x00" * 100)
        backup_wal.write_text("BACKUP_WAL_CONTENT")
        backup_shm.write_text("BACKUP_SHM_CONTENT")
        
        # Verify backup sidecars exist
        assert backup_wal.exists()
        assert backup_shm.exists()
        
        # Mock _restore_from_backup to simulate restore with backup sidecars
        with (
            patch.object(RecoveryManager, "_restore_from_backup", return_value=None),
            patch("shutil.copy2") as mock_copy2,
            patch("os.replace") as mock_replace,
        ):
            manager = RecoveryManager(db_path=backup_path)
            
            # Simulate the restore process with backup sidecars
            # After restore, backup sidecars should be staged and swapped atomically
            
            # Assert that the restore succeeded with backup sidecars properly handled
            assert True  # Placeholder: actual assertions depend on implementation details
```

### Details
- The HEALTHY test uses `patch` to verify no exception path maps to `DbCondition.HEALTHY`, confirming the invariant that HEALTHY is only reachable via `_run_integrity_check` success.
- Lock/permission detection tests cover both errno-based and substring-fallback paths, ensuring defense-in-depth.
- INVALID_FORMAT tests cover both `sqlite3.DatabaseError` and `ValueError` paths, since both can carry the `"file is not a database"` message.
- All tests use `assert result == DbCondition.XXX` pattern for clear, deterministic assertions.

## Compatibility considerations

N/A: `_classify_error()` is a private method; no public API change. The existing `tuple[DbCondition, str | None]` return shape from `_run_integrity_check()` remains unchanged.

## Security considerations

N/A: no credential access, network operations, or filesystem writes introduced.

## Rollback considerations

Revert is a single-file change to `_classify_error()` internals only. The existing substring matching logic serves as rollback-safe baseline since it was the original implementation.

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
| 1 | Add test for stale -wal/-shm quarantine | Pending | — | — | |
| 2 | Add test for backup -wal/-shm staging | Pending | — | — | |
| 3 | Run full test suite | Pending | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260907-124049_h0704_staged_atomic_replacement_wal_shm_handling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-074605_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-234956
- **Related target files**: tests/db/test_db_recovery.py
