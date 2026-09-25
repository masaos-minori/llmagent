---
title: "DLQ Operations Reference"
area: eventbus
tags:
  - dlq
  - operations
  - reference
related:
---
# DLQ Operations Reference

## GET /dlq

List dead-letter queue entries with pagination support.

**Authentication**: Required — Bearer token in `Authorization` header.

### Request Parameters

| Parameter | Type | Required | Default | Bounds | Description |
|---|---|---|---|---|---|
| limit | integer | No | 100 | 1 ≤ limit ≤ 1000 | Maximum number of items to return |
| offset | integer | No | 0 | offset ≥ 0 | Number of items to skip for pagination |

### Response (HTTP 200)

Returns a pagination envelope (`total`/`limit`/`offset`) plus an `items` array of DLQ
event objects (each carrying the event's metadata plus `dlq_at`) — see
`scripts/eventbus/dlq_route.py` for the exact response schema.

**Field descriptions**:
- `total`: Total number of events in the DLQ (ignoring pagination).
- `limit`: The requested limit value.
- `offset`: The requested offset value.
- `items`: Array of event objects. Each object contains the event metadata plus `dlq_at` indicating when the event was promoted to the DLQ.

### Empty-result behavior

If no events are in the DLQ, the response body is:

```json
{
    "total": 0,
    "limit": 100,
    "offset": 0,
    "items": []
}
```

### Invalid-parameter behavior

- Missing `limit` or `offset`: Uses default values (100, 0 respectively).
- `limit` below 1: Returns HTTP 422 (FastAPI validation) with detail about minimum bound.
- `limit` above 1000: Returns HTTP 422 (FastAPI validation) with detail about maximum bound.
- `offset` below 0: Returns HTTP 422 (FastAPI validation) with detail about minimum bound.

### Ordering

Items are ordered by `seq` ascending (oldest first), which corresponds to insertion order into the DLQ.

## Related Documents

- [DLQ Requeue API Reference](/home/sugimoto/llmagent/docs/24_eventbus/eventbus_05_dlq_endpoint.md)
- [Event Bus Overview](eventbus_01_system-overview.md)
- [Event Bus DLQ/Offsets/Delivery Semantics](/home/sugimoto/llmagent/docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md)

## Keywords

dlq
dead-letter queue
operations
reference
pagination
