# Implementation: Update reference API doc to reflect new db.py exports and _db description

Source plan: `plans/20260625-140631_plan.md` (req #21, reference API doc portion)

## Goal

Update `docs/06_eventbus_06_reference_api.md` to reflect the new module-level variables and functions added by req #15 (DB facade) and req #16 (threading.Lock), and correct the `_db` variable description.

## Scope

- Update the `_db` row in the `app.py` module-level variables table
- Add `_dlq_last_run` variable row (added by req #19)
- Update the `scripts/eventbus/db.py` section: add `get_db_lock`, and the six facade functions
- No changes to `config.py`, `dlq.py`, or `offsets.py` sections (those are unchanged)

## Assumptions

1. req #15 (DB facade) adds: `check_db`, `insert_event`, `get_seq`, `fetch_events_since`, `fetch_dlq`, `requeue_event`
2. req #16 (threading.Lock) adds: `_db_lock`, `get_db_lock()`
3. req #19 (/health extension) adds: `_dlq_last_run: float`
4. `_get_seq` is removed from `app.py` (absorbed into `db.py::get_seq`)

## Implementation

### Target file

`docs/06_eventbus_06_reference_api.md`

### Procedure

1. Update `_db` row description in app.py variables table
2. Add `_dlq_last_run` row to app.py variables table
3. Remove `_get_seq` row from app.py internal functions table
4. Update `scripts/eventbus/db.py` section: add `get_db_lock` function row + six facade function rows

### Method

Targeted line/row replacements plus row additions.

### Details

**app.py variables table — update `_db` row:**

| Variable | Type | Description |
| `_db` | `sqlite3.Connection \| None` | Shared SQLite connection (protected by `_db_lock` from `db.py`); set in lifespan |

**app.py variables table — add new row:**

| Variable | Type | Description |
| `_dlq_last_run` | `float` | `time.monotonic()` timestamp of the last completed DLQ loop iteration; 0.0 until first run |

**app.py internal functions table — remove `_get_seq` row** (function moved to `db.py::get_seq`).

**scripts/eventbus/db.py section — add after `open_db`:**

| Function | Signature | Description |
|---|---|---|
| `get_db_lock` | `() -> threading.Lock` | Return the module-level lock; must be held for all DB operations |
| `check_db` | `(conn) -> bool` | Return True if the connection is usable (SELECT 1) |
| `insert_event` | `(conn, event_id, topic, payload_str, producer, published_at) -> tuple[int, bool]` | INSERT OR IGNORE; return (seq, inserted) |
| `get_seq` | `(conn, event_id) -> int` | Return seq for existing event_id; 0 if not found |
| `fetch_events_since` | `(conn, since_seq, topics=None) -> list[sqlite3.Row]` | Return events with seq > since_seq, optionally filtered by topics |
| `fetch_dlq` | `(conn) -> list[sqlite3.Row]` | Return all DLQ events (dlq_at IS NOT NULL) |
| `requeue_event` | `(conn, event_id) -> bool` | Clear dlq_at, increment retry_count; return True if found |

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New functions documented | `grep "get_db_lock\|check_db\|insert_event\|fetch_events_since\|fetch_dlq\|requeue_event" docs/06_eventbus_06_reference_api.md` | 6 matches |
| `_get_seq` removed | `grep "_get_seq" docs/06_eventbus_06_reference_api.md` | 0 matches |
| `_dlq_last_run` present | `grep "_dlq_last_run" docs/06_eventbus_06_reference_api.md` | 1 match |
| Markdown lint | `markdownlint docs/06_eventbus_06_reference_api.md` | 0 errors (if installed) |
