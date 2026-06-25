# Implementation: docs/06_eventbus_06_reference_api.md — add new endpoints (req #32)

## Goal

Add `POST /events/{id}/ack` and `POST /events/{id}/nack` to the API reference, and document the new `ack_event()`, `nack_event()`, `requeue_event()`, `promote_single()`, and `sweep_orphans()` functions in their respective modules.

## Scope

- Add ack/nack endpoint descriptions in the `app.py` section
- Add new functions to `db.py` section: `ack_event()`, `nack_event()`, `requeue_event()`
- Add new functions to `dlq.py` section: `promote_single()`, `sweep_orphans()`
- Update module-level variable comments as needed

## Assumptions

- req #24–#30 are all implemented before this doc update

## Implementation

### Target file

`docs/06_eventbus_06_reference_api.md`

### Procedure

1. Add new endpoint rows to the `app.py` section (or add an Endpoints subsection)
2. Add new function rows to the `db.py` table
3. Add new function rows to the `dlq.py` table

### Method

Edit specific tables in the existing file.

### Details

**Add Endpoints subsection to app.py section:**

```markdown
### Endpoints

| Route | Method | Description |
|---|---|---|
| `/health` | GET | Service health with delivery metrics |
| `/publish` | POST | Publish event (idempotent by event_id) |
| `/subscribe` | GET | SSE stream; resumes from ack-based offset if consumer_id provided |
| `/replay` | GET | Batch replay from seq |
| `/dlq` | GET | List DLQ events |
| `/dlq/{event_id}/requeue` | POST | Return event from DLQ to live state |
| `/events/{event_id}/ack` | POST | Mark event as successfully processed; advances offset if consumer_id provided |
| `/events/{event_id}/nack` | POST | Increment delivery failure count; promotes to DLQ inline if threshold reached |
```

**Updated db.py functions table:**

| Function | Signature | Description |
|---|---|---|
| `open_db` | `(db_path: str) -> sqlite3.Connection` | Open SQLite with WAL, foreign keys, and schema init |
| `ack_event` | `(conn, event_id, now) -> bool` | Set `acked_at`; idempotent; returns True if found and acked |
| `nack_event` | `(conn, event_id) -> int` | Increment `delivery_failure_count`; returns new count or -1 if not found |
| `requeue_event` | `(conn, event_id) -> bool` | Clear `dlq_at`, increment `dlq_requeue_count`; returns True if found |

**Updated dlq.py functions table:**

| Function | Signature | Description |
|---|---|---|
| `promote_to_dlq` | `(db, deadletter_dir, max_retry) -> int` | Batch promote eligible events (legacy; use sweep_orphans in background loop) |
| `promote_single` | `(db, deadletter_dir, event_id) -> bool` | Inline promote one event immediately; returns True if promoted |
| `sweep_orphans` | `(db, deadletter_dir, max_retry) -> int` | Safety-net sweep for events missed by inline promotion |
| `_atomic_write` | `(deadletter_dir, event_id, record) -> None` | Atomic JSON write via tempfile + os.replace |

## Validation plan

| Check | Command | Target |
|---|---|---|
| ack endpoint present | `grep "/events/" docs/06_eventbus_06_reference_api.md` | /ack and /nack found |
| db.py new functions | `grep "ack_event\|nack_event\|requeue_event" docs/06_eventbus_06_reference_api.md` | 3 results |
| dlq.py new functions | `grep "promote_single\|sweep_orphans" docs/06_eventbus_06_reference_api.md` | 2 results |
