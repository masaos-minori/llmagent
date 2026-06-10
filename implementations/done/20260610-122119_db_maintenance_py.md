# Implementation: db/maintenance.py — remove fallbacks, backup API, vacuum fix, generalize recover

## Goal

1. `RetentionConfig.from_config()`: remove `except` that falls back to `cfg = {}`.
2. `checkpoint_wal()`: remove config-load fallback `cfg = {}`.
3. `_archive_db_file()`: replace `shutil.copy2()` with `sqlite3.Connection.backup()` for WAL-safe copy.
4. `_vacuum_db()`: fix VACUUM failure path to return `success=False` instead of `success=True`.
5. `recover_corruption()`: add `target: str = "rag"` parameter to allow use on session DB.

## Scope

- `scripts/db/maintenance.py` — primary target
- `tests/test_db_maintenance.py` — update tests for the changed behaviours

## Assumptions

1. `RetentionConfig.from_config()` callers (`purge_old_sessions` with `cfg=None`) should
   propagate the config error rather than running with defaults. Fail-fast is correct here.
2. `checkpoint_wal(mode=None)` path reads config; if config fails, the exception propagates.
   Callers that know the mode can pass it explicitly and bypass the config read entirely.
3. `sqlite3.Connection.backup(dest)` is the standard Python WAL-safe online backup.
   It creates a consistent snapshot even if a WAL file is present.
   The `-wal` / `-shm` copy loop in `_archive_db_file` is deleted (not needed with backup API).
4. `_vacuum_db()` currently swallows the VACUUM error and returns `success=True`.
   After fix: exception → `success=False, action="vacuum_failed"`.
5. `recover_corruption(target="rag")` currently hard-codes `SQLiteHelper("rag")`.
   After change: uses `target` param for both integrity check and VACUUM.

## Implementation

### Target file

`scripts/db/maintenance.py`

### Procedure

1. `RetentionConfig.from_config()`:
   - Remove `except Exception as e: logger.warning(...); cfg = {}`.
   - Let `ConfigLoader().load("common.toml")` raise on failure.

2. `checkpoint_wal()`:
   - Remove `except Exception as e: logger.warning(...); cfg = {}` in the `mode is None` branch.
   - Let `ConfigLoader().load()` raise on failure.

3. `_archive_db_file()`:
   - Remove `import shutil` if no longer needed elsewhere.
   - Replace the `shutil.copy2(db_path, dest)` and WAL side-file loop with:
     ```python
     src = sqlite3.connect(str(db_path))
     dst = sqlite3.connect(str(dest))
     try:
         src.backup(dst)
     finally:
         dst.close()
         src.close()
     ```
   - Keep directory creation (`dest_dir.mkdir`) and size log.

4. `_vacuum_db()`:
   - Replace `except Exception as e: logger.warning(...)` followed by `return RecoveryResult(success=True, ...)` with:
     ```python
     except Exception as e:
         logger.error(f"VACUUM failed: {e}")
         return RecoveryResult(success=False, action="vacuum_failed", detail=str(e))
     ```

5. `recover_corruption()`:
   - Add `target: str = "rag"` parameter.
   - Pass `target` to `_run_integrity_check()` and `_vacuum_db()`.
   - Update `_run_integrity_check(db_path)` to accept `target` and use `SQLiteHelper(target)`.
   - Update `_vacuum_db()` similarly.
   - Get `db_path` from the config for the given target.

### Method

Direct textual edit.

### Details

`_vacuum_db()` after fix:
```python
def _vacuum_db(target: str = "rag") -> RecoveryResult:
    logger.info("Integrity check passed; running VACUUM")
    try:
        with SQLiteHelper(target).open(write_mode=True) as db:
            db.vacuum()
    except Exception as e:
        logger.error(f"VACUUM failed: {e}")
        return RecoveryResult(success=False, action="vacuum_failed", detail=str(e))
    return RecoveryResult(success=True, action="vacuum")
```

`_archive_db_file()` after (key section):
```python
import sqlite3

src = sqlite3.connect(str(db_path))
dst = sqlite3.connect(str(dest))
try:
    src.backup(dst)
finally:
    dst.close()
    src.close()
size = dest.stat().st_size
logger.info(f"DB archived: {dest} ({size:,} bytes)")
return dest
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/db/maintenance.py` | 0 errors |
| Type | `uv run mypy scripts/db/maintenance.py` | no new errors |
| Tests | `uv run pytest tests/test_db_maintenance.py -x -v` | all pass |
| No shutil copy | `grep -n "shutil.copy2" scripts/db/maintenance.py` | 0 hits |
| No fallback cfg | `grep -n "cfg = {}" scripts/db/maintenance.py` | 0 hits |
