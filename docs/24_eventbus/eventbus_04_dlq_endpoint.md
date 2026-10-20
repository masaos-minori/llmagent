---
title: "DLQ Endpoint"
tags: [api-reference, dlq, dead-letter]
area: eventbus
related:
  - eventbus_03_dlq_operations.md
  - eventbus_01_system-overview.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
---

# DLQ Endpoint

Two endpoints manage the EventBus Dead Letter Queue: listing entries (`GET /dlq`) and requeuing individual events (`POST /dlq/{event_id}/requeue`).

## Authentication

**Operator role required** for both endpoints.

Requires `Bearer ${OPERATOR_TOKEN}` in the Authorization header.

## List DLQ Entries

### Endpoint

```
GET /dlq
```

### Behavior

- Query parameters `limit` (bounded; see `scripts/eventbus/dlq_route.py`) and `offset` (`>= 0`) paginate the result. Out-of-range values return HTTP 422.
- The response is a pagination envelope (`total`, `limit`, `offset`) plus an `items` array. Each item carries event identity, `dlq_at` (the time the event was promoted to the DLQ), `dlq_requeue_count` and `delivery_failure_count`.
- `delivery_failure_count` is the stored events-level value, a legacy value that NACK does not modify under the per-consumer model; it is not the per-consumer failure count returned by `POST /nack`.
- Items are ordered by event `seq` ascending (oldest event first), not by the time of DLQ promotion. An empty DLQ returns `total: 0` and an empty `items` array.

## Requeue DLQ Entry

### Endpoint

```
POST /dlq/{event_id}/requeue
```

This operation creates a new event row with `redelivered_from` pointing to the original `event_id`. The original row's `dlq_at` is intentionally left set so only one redelivery succeeds per original event (concurrency guard).

### Success Response

HTTP 200 with `event_id` (the original), `requeued: true`, `new_event_id` and `new_seq` of the newly inserted row.

### Error Responses

- HTTP 409 (`event is not in DLQ`): the event exists but is not currently in the DLQ (for example `dlq_at IS NULL`), or it was already requeued.
- HTTP 404 (`event not found`): the event does not exist.

### Concurrency guarantee

Concurrent requeue attempts on the same event produce exactly one successful redelivery. The `redelivered_from` existence check in `redeliver_event()` serves as a concurrency guard: if another request has already redelivered this event (a row exists with `redelivered_from = event_id`), subsequent requests return HTTP 409.

## Keywords

- dlq
- dead-letter queue
- requeue
- redelivery
- lineage model
- concurrency
