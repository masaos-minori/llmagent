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
  - 06_eventbus_02_03_nack-health-dlq.md
  - 06_eventbus_02_04_dlq-background-loop.md
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

## Consumer ID Collision Risk

If different clients use the same `consumer_id`, the last write wins and the offset is overwritten. This is an intentional design choice but can lead to offset inconsistencies due to collisions.

## Reliability Limits

- Total loss of all events if the DB file is lost.
- Divergence between SQLite and JSONL if appending to JSONL fails.
- Events destined for DLQ may remain visible until the next DLQ loop interval (60 seconds).

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_03_nack-health-dlq.md`
- `06_eventbus_02_04_dlq-background-loop.md`
- `06_eventbus_03_persistence_schema_and_replay.md`
