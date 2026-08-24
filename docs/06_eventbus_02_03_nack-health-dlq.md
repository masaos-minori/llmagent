---
title: "Event Bus: Nack, Health, and DLQ Endpoints"
area: eventbus
tags:
  - event-bus
  - http-api
  - nack
  - health
  - dlq
  - dead-letter-queue
  - requeue
  - error-handling
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_01_publish-replay.md
  - 06_eventbus_02_02_subscribe-ack.md
  - 06_eventbus_02_04_dlq-background-loop.md
source:
  - 06_eventbus_02_01_publish-replay.md
---

# Event Bus: Nack, Health, and DLQ Endpoints

## POST /nack

Sends a NACK (Negative Acknowledgement) for an event. Increases `delivery_failure_count`, and moves the event to the DLQ once `delivery_failure_count >= max_retry`.

**Query Parameters:** `event_id` (required)
**Response:** On success, returns `{event_id, delivery_failure_count}`. A 404 error indicates the event was not found.

### NACK State Transitions

The following describes the current code behavior for NACK operations. For transition details on the ACK side (initial ACK, duplicate ACK, NACK followed by ACK, etc.), please refer to [docs/06_eventbus_02_02_subscribe-ack.md](docs/06_eventbus_02_02_subscribe-ack.md).

| Scenario | Current Code Behavior | HTTP Status | Response Body | Side Effects on Persistence |
|---|---|---|---|---|
| Initial NACK | `nack_event` increases `delivery_failure_count` from 0 $\to$ 1 (or more) | 200 | `{event_id, delivery_failure_count}` | `delivery_failure_count` increases; promoted to DLQ if `>= max_retry` |
| Duplicate NACK | No idempotency guard in `nack_event`; `delivery_failure_count` increases with every call | 200 | `{event_id, delivery_failure_count}` | Counter keeps increasing, potentially triggering DLQ promotion on subsequent calls — **Implementation fix required** |
| NACK after ACK | No `acked_at` check in `nack_event` | 200 | `{event_id, delivery_failure_count}` | Even if already ACKed, NACK succeeds and `delivery_failure_count` increases — **Implementation fix required** |
| Unknown Event ID (NACK) | `nack_event` returns `-1` | 404 | `ERR_EVENT_NOT_FOUND` | None |

> For ACK-side transitions (Initial ACK, Duplicate ACK, NACK followed by ACK, Unknown Event ID ACK, Simultaneous ACK/NACK, Consumer Mismatch), see [docs/06_eventbus_02_02_subscribe-ack.md](docs/06_eventbus_02_02_subscribe-ack.md).

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

## Related Documents

- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_02_04_dlq-background-loop.md`
