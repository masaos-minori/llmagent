---
title: "Event Bus: Operations (Publish, Subscribe, Ack/Nack, Health, DLQ)"
area: eventbus
tags:
  - event-bus
  - http-api
  - publish
  - replay
  - subscribe
  - ack
  - nack
  - health
  - dlq
  - dead-letter-queue
  - background-loop
  - safety-sweep
  - optimistic-lock
  - orphan-promotion
  - requeue
  - error-handling
  - failure-behavior
  - sse
  - streaming
  - consumer-offset
  - idempotent
  - json-schema
  - pagination
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_04_dlq_offsets_and_delivery_semantics.md
  - 06_eventbus_05_configuration-and-operations.md
---

# Event Bus: Operations (Publish, Subscribe, Ack/Nack, Health, DLQ)

## POST /publish

Publishes an event. Idempotent: duplicate `event_id`s are silently ignored.

**Reason for idempotency**: Even if re-published with the same `event_id`, existing rows are not updated due to the SQLite UNIQUE constraint, ensuring consumers do not receive the same event twice. This is an intentional design, not a bug.

**Request Body**: Validated against the `event_envelope.json` JSON Schema. Required fields are `event_id` (UUID v4), `topic` (1–255 characters), `payload` (object), `producer` (1–255 characters), and `published_at` (ISO-8601). `schema_version` is optional and defaults to `"1.0"`. Additional properties are not allowed.

**Response**: On success, returns `{event_id, seq}`. A 422 error indicates a JSON Schema validation error.

**JSONL Append Failure**: If writing to the JSONL archive fails, the event is still committed to SQLite and a 200 status is returned. A WARNING will be recorded in the logs.

---

## GET /replay

Replays past events. Returns events where `seq > since_seq`. Supports pagination when `format=json`.

**Query Parameters:** `since_seq` (>=0), `limit` (1-1000, default 100), `offset` (>=0), `format` (sse/json, default sse).

**Response (`format=json`):** A pagination object containing `{total, limit, offset, items}`. `total` is the total count regardless of `limit`/`offset`.

**Response (`format=sse`):** Each event is output as a `data: {...}` line. The SSE format does not support paginated incremental consumption. The stream terminates after `limit` items are output.

**Error Response:** 422 — if parameter values are invalid.

---

## GET /subscribe

A hybrid model combining replay and push, streaming events to the caller.

**Phase 1 — Replay**: Upon connection, all events matching the topic filter where `seq > start_seq` are retrieved from SQLite and output as `data:` SSE lines.

**Phase 2 — Live Push**: After replay completion, the process subscribes to the internal `EventBroker` and streams new events published via `POST /publish` to the SSE stream in real-time.

**Queue Overflow**: If the consumer is slow and the queue becomes full, the event is discarded (only a WARNING is logged). Use `since_seq`/`GET /replay` for recovery.

**Reconnection**: Specifying a `consumer_id` allows resuming from the last acknowledged offset. Offsets are not saved upon disconnection, so events that were not acknowledged before disconnecting will be re-delivered upon reconnection.

**Query Parameters:** `topic` (topic filtering), `since_seq` (>=0, default 0), `consumer_id` (for offset persistence).

### `since_seq`/Offset Precedence Rules

The exact logic in the `subscribe()` function in `scripts/eventbus/subscribe_route.py` is as follows:

```
start_seq = since_seq
if consumer_id and start_seq == 0:
    start_seq = read_offset(cfg.offsets_dir, consumer_id)
```

Rule: An explicit `since_seq=0` and an omitted `since_seq` (defaults to 0 via `Query(default=0)` declaration) are indistinguishable when a `consumer_id` is provided. Both resolve to "read from the saved offset". Clients wanting to perform a full replay while providing a `consumer_id` cannot currently express this intent.

### Handling Unknown/Mismatched Consumers

There is no consumer/event ownership column in `schema.sql`. `consumer_id` is accepted as any string and only used for `write_offset`/`read_offset`. Both `/subscribe` and `/events/{event_id}/ack` accept arbitrary strings without validation against an event ownership registry. Following implementation instructions #1/#3, this is documented as "untracked/unimplemented (by design)" rather than being silently omitted.

---

## POST /events/{event_id}/ack [canonical]

Acknowledges an event. When a `consumer_id` is specified, the consumer offset is updated. Idempotent.

**Path Parameters:** `event_id` (required)
**Query Parameters:** `consumer_id` (optional)

**Response:** On success, returns `{event_id, acked: true, seq: <int>}`. If already acknowledged, returns `{event_id, acked: true, already_acked: true}`. A 404 error indicates the event was not found.

**Note on Monotonicity:** Offset advancement is not guaranteed to be monotonic. Acknowledging older events can cause the offset to regress. Consumers should acknowledge in order or handle regressions upon reconnection.

---

## POST /nack

Sends a NACK (Negative Acknowledgement) for an event. Increases `delivery_failure_count`, and moves the event to the DLQ once `delivery_failure_count >= max_retry`.

**Query Parameters:** `event_id` (required)
**Response:** On success, returns `{event_id, delivery_failure_count}`. A 404 error indicates the event was not found.

For NACK's state-transition behavior (initial/duplicate NACK, NACK after ACK, unknown event ID), see the ACK/NACK State Transition Table below — it covers both ACK and NACK together rather than repeating NACK rows separately.

---

## ACK/NACK State Transition Table

The following table summarizes the current code behavior for ACK and NACK operations.

| Scenario | Current Code Behavior | HTTP Status | Response Body | Side Effects on Persistence |
|---|---|---|---|---|
| Initial ACK | `ack_event` returns `(True, True)` | 200 | `{event_id, acked: true, seq: <int>}` | Sets `acked_at`; writes offset if `consumer_id` is provided |
| Duplicate ACK | `ack_event` returns `(True, False)` | 200 | `{event_id, acked: true, already_acked: true}` | No additional write; no offset rewrite |
| Initial NACK | `nack_event` increases `delivery_failure_count` from 0 $\to$ 1 | 200 | `{event_id, delivery_failure_count}` | `delivery_failure_count` increases; promoted to DLQ if `>= max_retry` |
| Duplicate NACK | No idempotency guard in `nack_event`; `delivery_failure_count` increases with every call | 200 | `{event_id, delivery_failure_count}` | Counter keeps increasing, potentially triggering DLQ promotion on subsequent calls — **Implementation fix required** |
| NACK followed by ACK | `ack_event`'s `WHERE acked_at IS NULL` check remains true (NACK does not set `acked_at`) | 200 | `{event_id, acked: true, seq: <int>}` | ACK succeeds, `delivery_failure_count` remains at the value from NACK — No readjustment |
| ACK followed by NACK | No `acked_at` check in `nack_event` | 200 | `{event_id, delivery_failure_count}` | Even if already ACKed, NACK succeeds and `delivery_failure_count` increases — **Implementation fix required** |
| Unknown Event ID (ACK) | `ack_event` returns `(False, False)` | 404 | `ERR_EVENT_NOT_FOUND` | None |
| Unknown Event ID (NACK) | `nack_event` returns `-1` | 404 | `ERR_EVENT_NOT_FOUND` | None |
| Simultaneous ACK/NACK | Both go through `run_with_db_lock` and are serialized at the DB layer | 200/200 | Depends on lock order | No true contention — Lock enforces total ordering, and the second call observes the first call's committed state |

---

## GET /health

Returns the health status of each component. `ok` corresponds to HTTP 200, while `degraded`/`unhealthy` corresponds to HTTP 503.

**Response Fields:** `status`, `db`, `dlq_task`, `active_subscribers`, `max_queue_depth`, `slow_consumers`, `degraded_reasons`.

The `status` is `"ok"` only when all components are healthy. `degraded_reasons` lists failure causes (`db_unavailable`, `dlq_task_stopped`, `broker_queue_backlog_high`, `slow_consumers_detected`).

---

## GET /dlq

Retrieves a list of DLQ events (events where `dlq_at IS NOT NULL`).

**Query Parameters:** `limit` (1-1000, default 100), `offset` (>=0, default 0)
**Response:** A pagination object containing `{total, limit, offset, items}`. `items` includes `{seq, event_id, topic, producer, published_at, delivery_failure_count, dlq_requeue_count, dlq_at}`.

---

## POST /dlq/{event_id}/requeue

Moves a DLQ event back to normal delivery. Increases `dlq_requeue_count` (`delivery_failure_count` is not reset). If `delivery_failure_count >= max_retry`, the event will be moved to the DLQ again during the next DLQ loop.

**Path Parameters:** `event_id` (required)
**Response:** On success, returns `{event_id, requeued: true}`. A 409 error indicates the event has not been moved to the DLQ, and a 404 error indicates it was not found.

---

## DLQ Background Loop

At startup, the DLQ sweep background loop runs as an `asyncio` task, polling every 60 seconds. It searches for events where `delivery_failure_count >= max_retry AND dlq_at IS NULL`, acting as a safety net to catch any events missed by inline processing.

Using optimistic locking, it only targets events where `dlq_at IS NULL` to prevent duplicate promotion. If orphaned events are found, they are recorded in the logs. Any non-zero count may indicate an issue with the inline promotion process.

Promotion follows the same procedure as inline processing (atomic write to JSON file + setting `dlq_at` in SQLite).

---

## Failure Behavior Summary

| Failure Cause | Action |
|---|---|
| JSON Schema validation failure during `publish` | 422, event is not saved |
| JSONL append failure after SQLite commit | 200 returned, WARNING log output, event remains in SQLite |
| DB unavailable in `/health` | `status: degraded`, `db: unavailable` |
| DLQ task stopped in `/health` | `status: degraded`, `dlq_task: stopped` |
| Unknown `event_id` during requeue | 404 |
| Event exists but is not in DLQ during requeue | 409 Conflict |
| Duplicate `event_id` during `publish` (Idempotency skip) | 200 returned (existing `seq`), broker notification skipped |
| Subscriber queue full | Event is silently discarded, WARNING log output |

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- `06_eventbus_05_configuration-and-operations.md`
