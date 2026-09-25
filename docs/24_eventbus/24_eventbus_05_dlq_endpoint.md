---
title: "DLQ Requeue API Reference"
area: eventbus
tags:
  - dlq
  - requeue
  - reference
related:
---
# DLQ Requeue API Reference

## POST /dlq/{event_id}/requeue

Requeue a dead-letter queue entry back into the active event queue.

This operation creates a new event row with `redelivered_from` pointing to the original `event_id`. The original row's `dlq_at` is intentionally left set so only one redelivery succeeds per original event (concurrency guard).

**Authentication**: Required — Bearer token in `Authorization` header.

### Path Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| event_id | string | Yes | The original event ID to requeue |

### Request Parameters

None — `event_id` is provided as a path parameter only.

### Response (HTTP 200)

```json
{
    "event_id": "<original event ID>",
    "requeued": true,
    "new_event_id": "<UUID v4 hex>",
    "new_seq": <integer>
}
```

**Field descriptions**:
- `event_id`: The original event ID that was requeued.
- `requeued`: Always `true` on success.
- `new_event_id`: UUID v4 hex string of the newly inserted event row.
- `new_seq`: Integer sequence number of the newly inserted event row (computed atomically at insert time via `lastrowid`).

### Response (HTTP 409 Conflict)

Returned when the event exists but is not currently in the DLQ (i.e., `dlq_at IS NULL` means the event was already redelivered or acknowledged).

```json
{
    "error": "Event not in DLQ"
}
```

### Response (HTTP 404 Not Found)

Returned when the event does not exist in the database.

```json
{
    "error": "Event not found"
}
```

### Empty-result behavior

Not applicable — this endpoint operates on a single event identified by `event_id`. If the event does not exist, HTTP 404 is returned.

### Invalid-parameter behavior

- Missing `event_id` path parameter: Returns HTTP 404 (FastAPI routing) — no route matches without the path segment.
- Empty `event_id` (`/dlq//requeue`): Returns HTTP 404 (no matching route).
- Malformed `event_id` (non-string): Returns HTTP 422 (FastAPI validation) if the type converter rejects it.

### Ordering

Not applicable — this endpoint operates on a single event.

### Concurrency guarantee

Concurrent requeue attempts on the same event produce exactly one successful redelivery. The `redelivered_from` existence check in `redeliver_event()` serves as a concurrency guard: if another request has already redelivered this event (a row exists with `redelivered_from = event_id`), subsequent requests return HTTP 409.

## Related Documents

- [DLQ Operations Reference](24_eventbus_03_dlq_operations.md)
- [Event Bus Overview](24_eventbus_01_system-overview.md)
- [Event Bus DLQ/Offsets/Delivery Semantics](24_eventbus_06_dlq_offsets_and_delivery_semantics.md)

## Keywords

dlq
dead-letter queue
requeue
redelivery
lineage model
concurrency
