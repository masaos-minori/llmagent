---
title: "Event Bus: Nack, Health, and DLQ Endpoints"
category: eventbus
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
  - 06_eventbus_02_publish-replay.md
  - 06_eventbus_02_subscribe-ack.md
  - 06_eventbus_02_dlq-background-loop.md
source:
  - 06_eventbus_02_http_api_and_runtime.md
---

# Event Bus: Nack, Health, and DLQ Endpoints

## POST /nack

Negative acknowledge an event. Increments `delivery_failure_count`. If `delivery_failure_count >= max_retry`, the event is promoted to the DLQ.

**Query parameters:**
- `event_id` (str, required): event ID to nack

**Response 200:** `{"event_id": "...", "delivery_failure_count": <int>}` — may include `"dlq_promoted": true` if the event was promoted to DLQ on this nack
**Response 404:** event not found.

---

## GET /health

Returns component health. HTTP 200 for `ok`, HTTP 503 for `degraded`/`unhealthy`.

```json
{"status": "ok|degraded", "db": "ok|unavailable", "dlq_task": "running|stopped", "active_subscribers": 0, "max_queue_depth": 0, "slow_consumers": 0, "degraded_reasons": []}
```

`status` is `"ok"` only when all components are healthy. Broker metrics `active_subscribers`, `max_queue_depth`, and `slow_consumers` reflect the in-process EventBroker state. `degraded_reasons` lists specific failure reasons (e.g., `db_unavailable`, `dlq_task_stopped`, `broker_queue_backlog_high`, `slow_consumers_detected`).

---

## GET /dlq

List events in the dead-letter queue (events with `dlq_at IS NOT NULL`).

**Query parameters:**
- `limit` (int, default: 100, min: 1, max: 1000): Maximum number of items to return
- `offset` (int, default: 0, min: 0): Number of items to skip for pagination

**Response:** paginated object with fields:
- `total` (int): Total number of DLQ events
- `limit` (int): The requested limit
- `offset` (int): The requested offset
- `items` ([{seq, event_id, topic, producer, published_at, delivery_failure_count, dlq_requeue_count, dlq_at}]): List of DLQ events for this page

- `delivery_failure_count`: Number of nacks since last successful ack
- `dlq_requeue_count`: Number of times this event was requeued (does not reset on requeue)

---

## POST /dlq/{event_id}/requeue

Move an event out of the DLQ back to normal delivery. Increments `dlq_requeue_count` by 1 (does NOT reset `delivery_failure_count`). If `delivery_failure_count >= max_retry` after re-promotion logic runs, the event re-enters the DLQ on the next DLQ loop tick.

**Path parameter:**
- `event_id` (str, required): event ID to requeue

**Response 200:** `{"event_id": "...", "requeued": true}` — may include `"dlq_imminent": true` if `delivery_failure_count >= max_retry` after requeue
**Response 409 Conflict:** event exists but is not in the DLQ (dlq_at IS NULL).
**Response 404:** event not found.

**Edge cases:**
- Event not in DLQ (dlq_at IS NULL): returns 409 Conflict
- Repeated requeue of same event: dlq_requeue_count increments each time
- Event at delivery_failure_count >= max_retry: requeue succeeds but next DLQ loop tick will re-promote

## Related Documents

- `06_eventbus_02_publish-replay.md`
- `06_eventbus_02_subscribe-ack.md`
- `06_eventbus_02_dlq-background-loop.md`

## Keywords

event-bus
http-api
nack
health
dlq
dead-letter-queue
requeue
error-handling
