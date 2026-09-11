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

### Failure Count Split

The system tracks two independent failure counters:

- **`delivery_failure_count`** (lifetime): Accumulates across the event's entire lifecycle, including after redelivery. This counter represents the total number of failures since the event was first published.
- **`cycle_failure_count`** (cycle-scoped): Resets to 0 on each redelivery. This counter governs DLQ promotion decisions within a single retry cycle.

DLQ promotion thresholds use `cycle_failure_count`, not `delivery_failure_count`. This means an event that was previously promoted to the DLQ and then redelivered starts fresh — its lifetime failure history does not cause immediate re-promotion.

### Requeue (Redelivery)

`POST /dlq/{event_id}/requeue` performs actual redelivery rather than flag-only requeue:

1. Inserts a new row into the `events` table with:
   - A fresh UUID v4 `event_id`
   - `redelivered_from` set to the original `event_id`
   - `cycle_failure_count = 0` (fresh retry budget)
   - `delivery_failure_count` copied from the original row (lifetime continuity)
2. Increments `dlq_requeue_count` on the original row as audit trail.
3. Archives the original `{event_id}.json` DLQ file to `requeued/{event_id}_{timestamp}.json` subdirectory.
4. Publishes the new event via `EventBroker.publish()` so active subscribers receive it immediately.

Active subscribers receive the redelivered event via `EventBroker.publish()`. Reconnecting subscribers reach it via the existing `seq > since_seq` replay path in the subscribe endpoint.

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
