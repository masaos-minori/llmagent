# tests/integration/test_session_sqlite.py — Agent Session <-> SQLite integration tests

**Plan:** `plans/20260625-095157_plan.md` (req #71)
**Target:** `tests/integration/test_session_sqlite.py` (new file)

## Priority: P1 (Critical)

## Test cases to implement

- **TC-B01**: WAL write succeeds in `begin_immediate()` — row committed; WAL checkpoint completes
- **TC-B02**: `SQLITE_BUSY` during `begin_immediate()` — `sqlite3.OperationalError("database is locked")`; `busy_timeout` determines retry window
- **TC-B03**: FK violation (session_id not in sessions) — `sqlite3.IntegrityError` (FK constraint enabled)
- **TC-B04**: Concurrent writes — two `asyncio.gather()` `MemoryStore.add()` calls succeed; no corruption
- **TC-B05**: Rollback on mid-transaction crash — exception after first INSERT; DB consistent
- **TC-B06**: WAL file persists after unclean shutdown — WAL auto-checkpoint on next open
- **TC-B07**: `delete()` + `import_from_jsonl()` sequence — entry reappears (documents known behavior from req #62)
- **TC-B08**: `clear_by_session()` atomicity — concurrent read sees complete state before/after clear

## Key fixtures needed

- `tmp_sqlite_db`: path to a temp SQLite DB with schema initialized
- `hold_write_lock(db_path, duration_sec)`: thread function that holds EXCLUSIVE lock

## Mocking approach

- Real SQLite via `tmp_path` fixture (no mocking of `SQLiteHelper`)
- WAL + FK + `begin_immediate()` exercised directly

## Busy lock simulation (TC-B02)

```python
import sqlite3, threading, time

def hold_write_lock(db_path, duration_sec):
    conn = sqlite3.connect(db_path, timeout=0)
    conn.execute("PRAGMA locking_mode = EXCLUSIVE")
    conn.execute("BEGIN EXCLUSIVE")
    time.sleep(duration_sec)
    conn.close()

lock_thread = threading.Thread(target=hold_write_lock, args=(db_path, 1.0))
lock_thread.start()
# Now attempt agent write — should raise OperationalError("database is locked")
```

## Validation

```
uv run pytest tests/integration/test_session_sqlite.py -v --timeout=30
```
