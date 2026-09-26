---
title: "DLQ Endpoint"
description: DLQ list and requeue endpoint contracts for dead-letter queue management
tags: [api-reference, dlq, dead-letter]
area: eventbus
related:
  - eventbus_03_dlq_operations.md
  - eventbus_01_system-overview.md
  - eventbus_06_dlq_offsets_and_delivery_semantics.md
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

### Parameters

| Parameter | Required | Default | Constraints | Description |
|-----------|----------|---------|-------------|-------------|
| `limit` | No | `100` | `1 <= limit <= 1000` | Maximum entries to return |
| `offset` | No | `0` | `>= 0` | Offset for pagination |

### Success Response

**HTTP 200 OK**

#### Response Schema

```json
{
  "total": 50,
  "limit": 100,
  "offset": 0,
  "items": [
    {
      "event_id": "evt-failed",
      "consumer_id": "worker-1",
      "failure_count": 3,
      "last_failure_reason": "timeout",
      "dlq_at": "2026-09-14T10:00:00Z"
    }
  ]
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total DLQ entries |
| `limit` | integer | Requested page size |
| `offset` | integer | Requested offset |
| `items` | array[object] | Paginated DLQ entries |

### Example Request

```bash
curl -H "Authorization: Bearer ${OPERATOR_TOKEN}" \
  "http://localhost:8080/dlq?limit=20&offset=0"
```

## Requeue DLQ Entry

### Endpoint

```
POST /dlq/{event_id}/requeue
```

This operation creates a new event row with `redelivered_from` pointing to the original `event_id`. The original row's `dlq_at` is intentionally left set so only one redelivery succeeds per original event (concurrency guard).

### Path Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `event_id` | Yes | The event ID to requeue |

### Request Parameters

None — `event_id` is provided as a path parameter only.

### Success Response

**HTTP 200 OK**

#### Response Schema

```json
{
    "event_id": "<original event ID>",
    "requeued": true,
    "new_event_id": "<UUID v4 hex>",
    "new_seq": <integer>
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | Original event ID that was requeued |
| `requeued` | boolean | Always `true` on success |
| `new_event_id` | string | UUID v4 hex string of the newly inserted event row |
| `new_seq` | integer | Integer sequence number of the newly inserted event row (computed atomically at insert time via `lastrowid`) |

### Example Request

```bash
curl -X POST -H "Authorization: Bearer ${OPERATOR_TOKEN}" \
  http://localhost:8080/dlq/evt-failed/requeue
```

### Conflict Response

**HTTP 409 Conflict**

Returned when the event exists but is not currently in the DLQ (i.e., `dlq_at IS NULL` means the event was already redelivered or acknowledged).

#### Response Schema

```json
{
    "error": "Event not in DLQ"
}
```

### Not Found Response

**HTTP 404 Not Found**

Returned when the event does not exist in the database.

#### Response Schema

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

### Idempotency Note

Requeue uses a lineage model: each requeue creates a new event row with `redelivered_from` pointing to the original event ID. The original row's `dlq_at` timestamp is intentionally preserved so only one successful redelivery occurs per original event. Attempting to requeue the same event twice will return HTTP 409 on the second attempt.

## Related Documents

- [DLQ Operations Reference](eventbus_03_dlq_operations.md)
- [Event Bus Overview](eventbus_01_system-overview.md)
- [Event Bus DLQ/Offsets/Delivery Semantics](eventbus_06_dlq_offsets_and_delivery_semantics.md)

## Keywords

dlq
dead-letter queue
requeue
redelivery
lineage model
concurrency
