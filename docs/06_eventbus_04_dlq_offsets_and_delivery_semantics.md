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

Offset files are stored in `{offsets_dir}/{sanitized_consumer_id}`. The `consumer_id` is sanitized.

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

## Overflow Disconnection

When a subscriber's queue becomes full, the subscription is disconnected (SSE stream ends) instead of silently dropping the event. The client can reconnect using `since_seq`/`GET /replay` to resume from its last acknowledged position. This ensures that slow consumers never create undetected permanent gaps — the server terminates the affected subscription so the client can recover via reconnection.

## Consumer ID Collision Risk

With the one-connection-per-`consumer_id` policy, the collision scenario described above no longer applies. A second client attempting to connect with the same non-empty `consumer_id` receives HTTP 409 (Conflict), preventing concurrent connections and eliminating the "last write wins" offset overwrite risk. Anonymous connections (empty `consumer_id`) are exempt from this restriction.

## Reliability Limits

- Total loss of all events if the DB file is lost.
- Divergence between SQLite and JSONL if appending to JSONL fails.
- Events destined for DLQ may remain visible until the next DLQ loop interval (60 seconds).

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_operations.md`
- `06_eventbus_03_persistence_schema_and_replay.md`
