---
title: "Event Bus: DLQ, Offsets, and Delivery Semantics"
area: eventbus
tags:
  - event-bus
  - dlq
  - dead-letter-queue
  - consumer-offset
  - delivery-semantics
  - at-least-once
  - idempotent
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_operations.md
  - 06_eventbus_03_persistence_schema_and_replay.md
source:
  - index.md
---

# Event Bus: DLQ, Offsets, and Delivery Semantics

## Dead Letter Queue (DLQ)

### Promotion Path

When a NACK occurs and `delivery_failure_count` reaches `>= max_retry`, the event is immediately promoted to the DLQ. The background DLQ loop (every 60 seconds) serves as a safety net to catch any events missed during inline processing.

### Promotion Process

1. Atomic write of a JSON file to `{deadletter_dir}/{event_id}.json`.
2. Setting the `dlq_at` timestamp in SQLite.

### Requeue

`POST /dlq/{event_id}/requeue` clears `dlq_at` and increments `dlq_requeue_count` (`delivery_failure_count` is not reset). If `delivery_failure_count >= max_retry`, it will be re-promoted during the next DLQ loop.

## Consumer Offset

### Offset Storage

**SQLite-backed offset store:** Offsets are now stored in the `consumer_offsets` table, keyed by `consumer_id`:

```sql
CREATE TABLE consumer_offsets (
    consumer_id TEXT PRIMARY KEY,
    offset INTEGER NOT NULL DEFAULT 0
);
```

Each row stores the last-committed sequence offset for a consumer. The primary key on `consumer_id` ensures one row per consumer. The `offset` value is monotonically non-decreasing — older-or-equal seq values cannot move a consumer's offset backward.

**Monotonic enforcement:** The offset advancement uses the SQL statement:

```sql
INSERT INTO consumer_offsets(consumer_id, offset) VALUES (?, ?) ON CONFLICT(consumer_id) DO UPDATE SET offset = excluded.offset WHERE excluded.offset > consumer_offsets.offset
```

This ensures monotonic enforcement: an older-or-equal seq value cannot move a consumer's offset backward.

**Legacy offset migration:** On startup, the `lifespan()` function calls `migrate_legacy_offsets()` to seed the `consumer_offsets` table from existing `offsets_dir` files. The migration reads each `.map` companion file to recover the original `consumer_id`, then inserts the offset using `INSERT OR IGNORE` (idempotent). Legacy files are retained until verified end-to-end.

### Explicit Ack-only Offset

Offsets advance ONLY when a consumer explicitly calls `POST /events/{event_id}/ack?consumer_id={consumer_id}`. They do not advance automatically during streaming. Idempotent duplicate ACKs do not update the offset.

**Note:** Offsets only advance based on the `seq` value provided during ACK. If ACKs are not received in `seq` order, the offset may become non-monotonic (skipped `seq` values will not be re-acquired later).

### Resuming on Reconnection

By specifying a `consumer_id`, consumers can resume from their last acknowledged offset. The Consumer ID must remain stable across restarts.

**Note:** `offset_checkpoint_interval` has been removed. Setting it will cause startup to fail.

## Delivery Guarantees

At-least-once. Duplicate publishing is suppressed by the `event_id` UNIQUE constraint. Redelivery after crashes may occur. Ordering is guaranteed per topic.

**IMPORTANT:** Consumers MUST implement idempotent processing. Since multiple deliveries of the same event can occur, duplicate ACKs or duplicate processing for the same `event_id` must be safe.

**Overflow guarantee:** When a subscriber's queue overflows, the subscription is disconnected rather than silently continuing. This prevents permanent event loss — the client can reconnect and resume from its last committed offset.

## Delivery Semantics

**Per-consumer delivery-state isolation:** Each consumer's delivery progress is tracked in the `consumer_delivery` table:

```sql
CREATE TABLE consumer_delivery (
    consumer_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    acked_at TEXT,
    PRIMARY KEY (consumer_id, event_id)
);
```

Different consumers can independently ACK the same event without interference. When a consumer acknowledges an event, a row `(consumer_id, event_id, acked_at)` is inserted atomically with the offset advancement using `INSERT OR IGNORE` semantics — if the same consumer has already ACKed the same event, the row is silently skipped.

**Atomic transaction guarantee:** The `ack_event_for_consumer()` function performs both the per-consumer delivery-state UPSERT and the offset advancement in a single SQLite transaction. If either operation fails, the entire transaction rolls back — neither the delivery nor the offset is committed. This eliminates the two-commit gap that existed before the Plan.

**SSE stream filtering:** The subscribe handler filters out events already acknowledged by the consumer by checking the `consumer_delivery` table:

```python
SELECT * FROM events WHERE seq > ? AND event_id NOT IN (
    SELECT event_id FROM consumer_delivery WHERE consumer_id = ?
)
```

This ensures the consumer only receives unacked events starting from its last-committed offset.

## Overflow Disconnection

When a subscriber's queue becomes full, the subscription is disconnected (SSE stream ends) instead of silently dropping the event. The client can reconnect using `since_seq`/`GET /replay` to resume from its last acknowledged position. This ensures that slow consumers never create undetected permanent gaps — the server terminates the affected subscription so the client can recover via reconnection.

## Consumer ID Collision Risk

With the one-connection-per-`consumer_id` policy, the collision scenario described above no longer applies. A second client attempting to connect with the same non-empty `consumer_id` receives HTTP 409 (Conflict), preventing concurrent connections and eliminating the "last write wins" offset overwrite risk. Anonymous connections (empty `consumer_id`) are exempt from this restriction.

## Reliability Limits

- Total loss of all events if the DB file is lost.
- Divergence between SQLite and JSONL if appending to JSONL fails.
- Events destined for DLQ may remain visible until the next DLQ loop interval (60 seconds).

## Migration

### Per-Consumer Delivery-State Migration

The `consumer_delivery` and `consumer_offsets` tables are created by `_migrate()` during `open_db()`, using `CREATE TABLE IF NOT EXISTS` — safe to run multiple times. The `migrate_legacy_offsets()` function seeds the `consumer_offsets` table from existing `offsets_dir` files on every startup.

### Consumer ID Recovery

When migrating offsets, the system reads each `.map` companion file under `offsets_dir` to recover the original `consumer_id`. For any offset file with no `.map` companion, the system falls back to the sanitized filename (via `_sanitize_consumer_id()`) as the `consumer_id`, logging a warning. This handles the edge case where the `.map` file was lost or corrupted.

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_operations.md`
- `06_eventbus_03_persistence_schema_and_replay.md`
