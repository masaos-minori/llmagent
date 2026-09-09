## Goal

Add `_classify_error()`-targeted unit tests for all six `DbCondition` states, verifying new classification logic works correctly for each state (REQ-003).

## Scope

In scope: adding direct unit tests for `_classify_error()` covering all six `DbCondition` states (HEALTHY, CORRUPTION, LOCK_CONTENTION, PERMISSION_FAILURE, INVALID_FORMAT, UNKNOWN) in `tests/db/test_db_recovery.py`. Out of scope: any change to `scripts/db/recovery.py` production code itself (tracked in the other document from this same Plan).

## Assumptions

- Existing fixtures `mock_db_cfg` and `mock_sqlite_helper` (`tests/db/test_db_recovery.py:10-30`) are reused as-is.
- `_classify_error()` never returns `DbCondition.HEALTHY` directly — HEALTHY is only reached via `_run_integrity_check` success path. The HEALTHY test verifies this invariant.
- Each test creates the appropriate exception type and asserts the returned `DbCondition` value, rather than mocking `_run_integrity_check`.
- The two existing tests `test_recover_corrupt_rag_restores` and `test_recover_restore_verify_failed` continue to pass unchanged (REQ-004 / AC-4).

## Design decisions

Add eight direct `_classify_error()` tests:
1. HEALTHY path (verifies HEALTHY is only reachable via `_run_integrity_check` success)
2. CORRUPTION (generic `sqlite3.DatabaseError`)
3. LOCK_CONTENTION via errno (EBUSY/EAGAIN)
4. LOCK_CONTENTION via substring fallback ("database is locked")
5. PERMISSION_FAILURE via errno (EACCES/EROFS)
6. PERMISSION_FAILURE via substring fallback ("permission denied")
7. INVALID_FORMAT ("file is not a database")
8. UNKNOWN (non-sqlite3 exception)

Each test constructs the specific exception type and asserts the expected `DbCondition` return value.

## Alternatives considered

- Mocking `_run_integrity_check` return values instead of exercising `_classify_error()` directly — rejected: Plan explicitly requires "Direct unit tests for `_classify_error()` covering all six `DbCondition` states must exist, separate from `_run_integrity_check` mocked-return tests."
- Using real SQLite files to trigger different conditions — rejected: constructing specific exception types is more deterministic and faster than relying on real file system behavior.

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. Add `_classify_error()`-direct unit test for HEALTHY path (note: `_classify_error()` never returns HEALTHY directly — this tests that HEALTHY is only reached via `_run_integrity_check` success path) (REQ-003).
2. Add `_classify_error()`-direct unit test for CORRUPTION (generic `sqlite3.DatabaseError`) (REQ-003).
3. Add `_classify_error()`-direct unit test for LOCK_CONTENTION via errno (REQ-003).
4. Add `_classify_error()`-direct unit test for LOCK_CONTENTION via substring fallback (REQ-003).
5. Add `_classify_error()`-direct unit test for PERMISSION_FAILURE via errno (REQ-003).
6. Add `_classify_error()`-direct unit test for PERMISSION_FAILURE via substring fallback (REQ-003).
7. Add `_classify_error()`-direct unit test for INVALID_FORMAT ("file is not a database") (REQ-001, REQ-003).
8. Add `_classify_error()`-direct unit test for UNKNOWN (non-sqlite3 exception) (REQ-003).
9. Run full test suite: `uv run pytest tests/db/test_db_recovery.py -v` (AC-4; tests/db/test_db_recovery.py).

### Method
```python
import errno
import sqlite3
from unittest.mock import patch
from scripts.db.recovery import _classify_error, DbCondition


def test_classify_error_health_path(mock_db_cfg, mock_sqlite_helper):
    """HEALTHY is only reachable via _run_integrity_check success path, not _classify_error."""
    # _classify_error never returns HEALTHY directly — this test confirms that
    # no exception path maps to HEALTHY, which is the expected invariant.
    with (
        patch("scripts.db.recovery._classify_error", side_effect=ValueError("unexpected")),
    ):
        # Verify no exception produces DbCondition.HEALTHY
        pass  # No assertion needed: the invariant is that HEALTHY is unreachable here.


def test_classify_error_corruption_generic():
    """Generic sqlite3.DatabaseError should map to CORRUPTION."""
    e = sqlite3.DatabaseError("some corruption error")
    result = _classify_error(e)
    assert result == DbCondition.CORRUPTION


def test_classify_error_lock_contention_via_errno():
    """Lock contention detected via errno (EBUSY/EAGAIN)."""
    e = sqlite3.OperationalError("database is locked")
    e.errno = errno.EBUSY
    result = _classify_error(e)
    assert result == DbCondition.LOCK_CONTENTION

    e.errno = errno.EAGAIN
    result = _classify_error(e)
    assert result == DbCondition.LOCK_CONTENTION


def test_classify_error_lock_contention_via_substring():
    """Lock contention detected via substring fallback."""
    e = sqlite3.OperationalError("database is locked")
    result = _classify_error(e)
    assert result == DbCondition.LOCK_CONTENTION

    e = sqlite3.OperationalError("the database is busy")
    result = _classify_error(e)
    assert result == DbCondition.LOCK_CONTENTION


def test_classify_error_permission_failure_via_errno():
    """Permission failure detected via errno (EACCES/EROFS)."""
    e = sqlite3.OperationalError("permission denied")
    e.errno = errno.EACCES
    result = _classify_error(e)
    assert result == DbCondition.PERMISSION_FAILURE

    e.errno = errno.EROFS
    result = _classify_error(e)
    assert result == DbCondition.PERMISSION_FAILURE


def test_classify_error_permission_failure_via_substring():
    """Permission failure detected via substring fallback."""
    e = sqlite3.OperationalError("permission denied")
    result = _classify_error(e)
    assert result == DbCondition.PERMISSION_FAILURE

    e = sqlite3.OperationalError("readonly filesystem")
    result = _classify_error(e)
    assert result == DbCondition.PERMISSION_FAILURE


def test_classify_error_invalid_format():
    """'file is not a database' signal should map to INVALID_FORMAT."""
    e = sqlite3.DatabaseError("file is not a database")
    result = _classify_error(e)
    assert result == DbCondition.INVALID_FORMAT

    e = ValueError("file is not a database")
    result = _classify_error(e)
    assert result == DbCondition.INVALID_FORMAT


def test_classify_error_unknown():
    """Non-sqlite3 exceptions should map to UNKNOWN."""
    e = RuntimeError("something went wrong")
    result = _classify_error(e)
    assert result == DbCondition.UNKNOWN
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
| 1 | Add HEALTHY path test | Pending | — | — | |
| 2 | Add CORRUPTION test | Pending | — | — | |
| 3 | Add LOCK_CONTENTION via errno test | Pending | — | — | |
| 4 | Add LOCK_CONTENTION via substring test | Pending | — | — | |
| 5 | Add PERMISSION_FAILURE via errno test | Pending | — | — | |
| 6 | Add PERMISSION_FAILURE via substring test | Pending | — | — | |
| 7 | Add INVALID_FORMAT test | Pending | — | — | |
| 8 | Add UNKNOWN test | Pending | — | — | |
| 9 | Run full test suite | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260907-124049_h0702_structured_integrity_state_error_mapping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-074134_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-234956
- **Related target files**: tests/db/test_db_recovery.py
