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

Each consumer's last-committed offset is stored in a per-consumer SQLite table (`consumer_offsets`), advanced atomically alongside that consumer's delivery-state record in one transaction. A one-time, idempotent startup migration seeds this table from any pre-existing legacy file-based store, which remains in place (not deleted) during the retention period.

### Explicit Ack-only Offset

Offsets advance ONLY when a consumer explicitly calls `POST /events/{event_id}/ack?consumer_id={consumer_id}`. They do not advance automatically during streaming. Idempotent duplicate ACKs do not update the offset.

**Note:** Offsets only advance based on the `seq` value provided during ACK. If ACKs are not received in `seq` order, the offset may become non-monotonic (skipped `seq` values will not be re-acquired later).

### Resuming on Reconnection

By specifying a `consumer_id`, consumers can resume from their last acknowledged offset. The Consumer ID must remain stable across restarts.

**Note:** `offset_checkpoint_interval` has been removed. Setting it will cause startup to fail.

## Delivery Guarantees

At-least-once. Duplicate publishing is suppressed by the `event_id` UNIQUE constraint. Redelivery after crashes may occur. Ordering is guaranteed per topic.

**IMPORTANT:** Consumers MUST implement idempotent processing. Since multiple deliveries of the same event can occur, duplicate ACKs or duplicate processing for the same `event_id` must be safe.

## Consumer ID Collision Risk

A second concurrent `/subscribe` connection using the same non-empty `consumer_id` as an already-active connection is rejected with HTTP 409. Only one active connection per non-empty `consumer_id` is permitted at a time. The underlying `.map`-file-based raw-string-collision detection for the legacy offset-file path remains unchanged.

## Reliability Limits

- Total loss of all events if the DB file is lost.
- Divergence between SQLite and JSONL if appending to JSONL fails.
- Events destined for DLQ may remain visible until the next DLQ loop interval (60 seconds).

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_operations.md`
- `06_eventbus_03_persistence_schema_and_replay.md`
