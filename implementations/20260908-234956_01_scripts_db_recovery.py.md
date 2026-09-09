## Goal

Replace fragile substring matching in `_classify_error()` with structured error code detection where available, and add the missing `INVALID_FORMAT` classification path for non-SQLite files misidentified as databases (REQ-001, REQ-002).

## Scope

In scope: modifying `_classify_error()` internals in `scripts/db/recovery.py` — replacing substring-only matching with structured error code detection for lock/permission conditions, and adding a deterministic path that returns `DbCondition.INVALID_FORMAT` for the "not a database" condition. Out of scope: changing `recover_corruption()` control flow or action names; changing `_run_integrity_check()` return shape; implementing backup-candidate domain-identity validation; changing WAL/SHM handling; adding `IntegrityCheckResult` dataclass.

## Assumptions

- `sqlite3.OperationalError.errno` is available on Python 3.14 (confirmed in Plan's Unknowns table) — provides POSIX errno values (EACCES for permission failures, EBUSY/EAGAIN for lock conditions).
- The `"file is not a database"` message is produced by SQLite's own C library when opening a non-database file, and is not subject to localization or version differences.
- The existing `tuple[DbCondition, str | None]` return shape satisfies structured dispatch — no need for an `IntegrityCheckResult` dataclass replacement.
- `recover_corruption()`'s existing branch that groups `INVALID_FORMAT` with `LOCK_CONTENTION`/`PERMISSION_FAILURE` (returning `action="error"` without touching backups) will receive dispatch correctly once `_classify_error()` can produce `INVALID_FORMAT` — confirmed by reading lines 301-311 of `recovery.py`.

## Design decisions

Classification priority order:
1. Check `isinstance(e, sqlite3.OperationalError)` first — if true, inspect `errno` for lock/permission conditions before falling back to substring matching.
2. For `sqlite3.OperationalError` with no matched errno, fall back to substring matching for `"database is locked"` / `"busy"` (lock) and `"permission denied"` / `"readonly"` (permission).
3. For `sqlite3.DatabaseError` or `ValueError`, check for `"file is not a database"` -> `INVALID_FORMAT`; otherwise -> `CORRUPTION`.
4. All other exceptions -> `UNKNOWN`.

## Alternatives considered

- Using `sqlite3.Error.sqlite_errorcode` / `sqlite3.Error.sqlite_errorname` — rejected: not available on Python 3.14 (confirmed in Plan's Unknowns table).
- Adding a new `DbCondition` state — rejected: Plan explicitly states "Keep `DbCondition` as the contract (no new states)".
- Relying solely on substring matching — rejected: fragile across SQLite versions/locales, conflates "file is not a valid SQLite database" with "page-level corruption".

## Implementation
### Target file
`scripts/db/recovery.py`

### Procedure
1. Confirm `sqlite3.OperationalError.errno` availability and behavior on Python 3.14 (REQ-002).
2. Document the errno-based approach for lock/permission detection in `_classify_error()` comments (REQ-002).
3. Implement INVALID_FORMAT path: detect `"file is not a database"` in `sqlite3.DatabaseError` message, return `DbCondition.INVALID_FORMAT` (REQ-001).
4. Strengthen lock detection: check `sqlite3.OperationalError.errno` for EBUSY/EAGAIN before substring matching (REQ-002).
5. Strengthen permission detection: check `sqlite3.OperationalError.errno` for EACCES/EROFS before substring matching (REQ-002).
6. Preserve existing substring matching as documented fallback for both lock and permission conditions (REQ-002).

### Method
```python
def _classify_error(self, e: Exception) -> DbCondition:
    # Use errno-based detection where available (Python 3.14+),
    # falling back to substring matching as documented fallback.
    # Priority: lock/permission via errno > INVALID_FORMAT via message > CORRUPTION > UNKNOWN
    if isinstance(e, sqlite3.OperationalError):
        # Lock/permission conditions: prefer errno over substring matching
        errno = getattr(e, 'errno', None)
        if errno is not None:
            import errno as errno_mod
            if errno == errno_mod.EBUSY or errno == errno_mod.EAGAIN:
                return DbCondition.LOCK_CONTENTION
            if errno == errno_mod.EACCES or errno == errno_mod.EROFS:
                return DbCondition.PERMISSION_FAILURE
        # Substring fallback for lock/permission conditions
        msg = str(e).lower()
        if "database is locked" in msg or "busy" in msg:
            return DbCondition.LOCK_CONTENTION
        if "permission denied" in msg or "readonly" in msg:
            return DbCondition.PERMISSION_FAILURE
    elif isinstance(e, sqlite3.DatabaseError):
        # INVALID_FORMAT: "file is not a database" signal from SQLite C library
        if "file is not a database" in str(e):
            return DbCondition.INVALID_FORMAT
        return DbCondition.CORRUPTION
    elif isinstance(e, ValueError):
        # Same INVALID_FORMAT signal applies to ValueError
        if "file is not a database" in str(e):
            return DbCondition.INVALID_FORMAT
        return DbCondition.CORRUPTION
    return DbCondition.UNKNOWN
```

### Details
- The errno-based approach uses `getattr(e, 'errno', None)` to safely access the errno attribute, which may not be set for all OperationalError instances.
- The INVALID_FORMAT detection relies on the `"file is not a database"` message string, which is produced by SQLite's C library and is stable across versions/locale.
- Existing substring matching is preserved as a documented fallback layer, providing defense-in-depth against edge cases where errno is not set.
- The classification priority order ensures lock/permission conditions are detected first (via errno), then INVALID_FORMAT, then CORRUPTION, then UNKNOWN.
- No changes to public API signatures (`_run_integrity_check` return shape, `recover_corruption` action names) unless a caller genuinely needs the new distinction surfaced.

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
| 1 | Confirm sqlite3.OperationalError.errno availability on Python 3.14 | Pending | — | — | |
| 2 | Document errno-based approach in _classify_error() comments | Pending | — | — | |
| 3 | Implement INVALID_FORMAT path | Pending | — | — | |
| 4 | Strengthen lock detection via errno | Pending | — | — | |
| 5 | Strengthen permission detection via errno | Pending | — | — | |
| 6 | Preserve substring matching as documented fallback | Pending | — | — | |
| 7 | Add or update tests per Validation plan | Pending | — | — | |
| 8 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Source issue**: issues/20260907-124049_h0702_structured_integrity_state_error_mapping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-074134_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-234956
- **Related target files**: scripts/db/recovery.py
