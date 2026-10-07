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

### Parameters

| Parameter | Required | Default | Constraints | Description |
|-----------|----------|---------|-------------|-------------|
| `limit` | No | route default | bounded (see `scripts/eventbus/dlq_route.py`) | Maximum entries to return |
| `offset` | No | `0` | `>= 0` | Offset for pagination |

### Success Response

**HTTP 200 OK**

#### Response Schema

A pagination envelope (`total`, `limit`, `offset`) plus an `items` array; see `scripts/eventbus/dlq_route.py` for the exact schema.

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total DLQ entries (ignoring pagination) |
| `limit` | integer | Requested page size |
| `offset` | integer | Requested offset |
| `items` | array[object] | Paginated DLQ entries; each carries `seq`, `event_id`, `topic`, `producer`, `published_at`, `delivery_failure_count`, `dlq_requeue_count` and `dlq_at` (the time the event was promoted to the DLQ) |

#### Empty Result

When no events are in the DLQ, the response has `total: 0` and an empty `items` array.

#### Invalid Parameters

- Missing `limit` or `offset`: the route's default values apply.
- `limit` below 1 or above the maximum bound, or `offset` below 0: HTTP 422 (FastAPI validation).

#### Ordering

Items are ordered by event `seq` ascending (oldest event first), not by the time of DLQ promotion.

### Example Request

```bash
curl -H "Authorization: Bearer ${OPERATOR_TOKEN}" \
  "http://<eventbus-host>:<port>/dlq?limit=20&offset=0"
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
| `new_seq` | integer | Integer sequence number of the newly inserted event row (looked up from the newly inserted row) |

### Example Request

```bash
curl -X POST -H "Authorization: Bearer ${OPERATOR_TOKEN}" \
  http://<eventbus-host>:<port>/dlq/evt-failed/requeue
```

### Conflict Response

**HTTP 409 Conflict**

Returned when the event exists but is not currently in the DLQ (for example, `dlq_at IS NULL`), or when it was already requeued.

#### Response Schema

```json
{
    "detail": "event is not in DLQ"
}
```

### Not Found Response

**HTTP 404 Not Found**

Returned when the event does not exist in the database.

#### Response Schema

```json
{
    "detail": "event not found"
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

## Keywords

dlq
dead-letter queue
requeue
redelivery
lineage model
concurrency
