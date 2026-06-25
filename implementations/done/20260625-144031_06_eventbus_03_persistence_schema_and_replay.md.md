# Implementation: docs/06_eventbus_03_persistence_schema_and_replay.md — schema table update (req #32)

## Goal

Update the schema documentation to include the new `delivery_failure_count` and `dlq_requeue_count` fields, mark `retry_count` as deprecated, and remove the outdated "single async event loop thread" justification for `check_same_thread=False`.

## Scope

- Add `delivery_failure_count` and `dlq_requeue_count` to the schema CREATE TABLE block
- Update the field semantics table
- Update the "Why check_same_thread=False is safe" section (req #21 / req #16 change: now uses threading.Lock)
- Mark `acked_at` as "set by POST /events/{id}/ack" (no longer reserved)

## Assumptions

- req #28 schema is implemented
- req #16 connection model: shared connection + threading.Lock (not "single async event loop thread")
- req #25 ack endpoint is implemented (acked_at is now used)

## Implementation

### Target file

`docs/06_eventbus_03_persistence_schema_and_replay.md`

### Procedure

1. Update the schema CREATE TABLE block to include new columns
2. Update field semantics table
3. Update the "Why check_same_thread=False is safe" explanation

### Method

Edit specific sections of the existing file.

### Details

**Updated CREATE TABLE block:**
```sql
CREATE TABLE IF NOT EXISTS events (
    seq                    INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id               TEXT    NOT NULL UNIQUE,
    topic                  TEXT    NOT NULL,
    payload                TEXT    NOT NULL,   -- JSON string
    producer               TEXT    NOT NULL,
    published_at           TEXT    NOT NULL,
    acked_at               TEXT,               -- set by POST /events/{id}/ack
    retry_count            INTEGER NOT NULL DEFAULT 0, -- deprecated
    delivery_failure_count INTEGER NOT NULL DEFAULT 0,
    dlq_requeue_count      INTEGER NOT NULL DEFAULT 0,
    dlq_at                 TEXT                        -- set when promoted to DLQ
);
```

**Updated field semantics table:**

| Field | Description |
|---|---|
| `seq` | Auto-increment integer; used as cursor for replay and subscribe |
| `event_id` | Client-supplied UUID; UNIQUE prevents duplicates |
| `payload` | Serialized JSON string of the event payload |
| `acked_at` | Set by `POST /events/{id}/ack`; NULL for unacked events |
| `retry_count` | Deprecated. Previously incremented on DLQ requeue. Use `dlq_requeue_count` |
| `delivery_failure_count` | Incremented on each `POST /events/{id}/nack`; DLQ promotion trigger |
| `dlq_requeue_count` | Incremented on each `POST /dlq/{id}/requeue` |
| `dlq_at` | ISO-8601 timestamp set when promoted to DLQ; NULL for live events |

**Updated "Why check_same_thread=False is safe" section:**

Replace:
```
**Why `check_same_thread=False` is safe**: FastAPI runs on a single async event loop thread.
All DB operations execute on that thread. WAL mode serializes concurrent writers at the SQLite level.
```

With:
```
**Why `check_same_thread=False` is safe**: DB operations are offloaded to thread pool workers
via `asyncio.to_thread()`. A `threading.Lock` serializes concurrent writes at the application level.
WAL mode enables concurrent readers. The shared connection avoids per-request churn.
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| New fields in schema block | `grep "delivery_failure_count\|dlq_requeue_count" docs/06_eventbus_03_persistence_schema_and_replay.md` | 2+ results |
| acked_at description updated | `grep "acked_at" docs/06_eventbus_03_persistence_schema_and_replay.md` | references ack endpoint |
| Old thread model removed | `grep "single async event loop" docs/06_eventbus_03_persistence_schema_and_replay.md` | 0 results |
