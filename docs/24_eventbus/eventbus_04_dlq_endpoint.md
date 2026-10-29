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
- The response is a pagination envelope (`total`, `limit`, `offset`) plus an `items` array. Each item carries event identity, `dlq_at` (the time the event was promoted to the DLQ) and `dlq_requeue_count`.
- Items are ordered by event `seq` ascending (oldest event first), not by the time of DLQ promotion. An empty DLQ returns `total: 0` and an empty `items` array.
- Consistency is request-local: within a single `/dlq` response the `total` count and the `items` array are read under one database lock and are internally consistent; two separate `/dlq` requests are not guaranteed to reflect the same state, because each request acquires its own lock.

## Requeue DLQ Entry

### Endpoint

```
POST /dlq/{event_id}/requeue
```

This operation creates a new event row with `redelivered_from` pointing to the original `event_id`. The original row's `dlq_at` is intentionally left set so only one redelivery succeeds per original event; the database enforces this with the partial unique index `idx_events_redelivered_from` on `events(redelivered_from)` (see [Persistence, Schema, and Replay](eventbus_06_persistence_schema_and_replay.md)).

### Success Response

HTTP 200 with `event_id` (the original), `requeued: true`, `new_event_id` and `new_seq` of the newly inserted row.

### Error Responses

- HTTP 409 (`event is not in DLQ`): the event exists but is not currently in the DLQ (for example `dlq_at IS NULL`), or it was already requeued.
- HTTP 404 (`event not found`): the event does not exist.

### Concurrency guarantee

Concurrent requeue attempts on the same event produce exactly one successful redelivery. The partial unique index `idx_events_redelivered_from` enforces at most one descendant row per `redelivered_from` source, so a racing second request fails the insert and is reported as HTTP 409; the `redelivered_from` existence check in `redeliver_event()` classifies the already-redelivered case before the insert for sequential requests.

## Keywords

- dlq
- dead-letter queue
- requeue
- redelivery
- lineage model
- concurrency
