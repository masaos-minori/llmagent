---
title: "Replay Operations Reference"
area: eventbus
tags:
  - replay
  - sse
  - json
  - reference
related:
---
# Replay Operations Reference

## GET /replay

Replay events from a given sequence number, supporting both Server-Sent Events (SSE) and JSON response formats.

**Authentication**: Required — Bearer token in `Authorization` header.

### Request Parameters

| Parameter | Type | Required | Default | Bounds | Description |
|---|---|---|---|---|---|
| since_seq | integer | No | 0 | since_seq ≥ 0 | Start replaying from this sequence number (exclusive). Use 0 to replay all events. |
| format | string | No | sse | Values: `sse`, `json` | Response format. `sse` returns an SSE stream; `json` returns a single JSON response. |
| limit | integer | No | 100 | 1 ≤ limit ≤ 1000 | Maximum number of events to return per request. |
| offset | integer | No | 0 | offset ≥ 0 | Number of events to skip for pagination. |

### Response (HTTP 200) — SSE format (`format=sse`)

Returns a `text/event-stream` response. Each event is formatted as:

```
id:<seq>
data:<JSON payload>

```

**Field descriptions**:
- `id`: The sequence number of the event.
- `data`: A JSON-encoded object containing the event fields (same as `_row_to_dict` output).

**Connection lifecycle**: The SSE connection closes when all available events have been streamed. If no new events arrive within the configured timeout, the connection may be closed by the server.

### Response (HTTP 200) — JSON format (`format=json`)

Returns a pagination envelope (`total`/`limit`/`offset`) plus an `items` array of event
objects (each carrying the event's metadata, plus `dlq_at` if the event was promoted
to the DLQ) — see `scripts/eventbus/replay_route.py` for the exact response schema.

**Field descriptions**:
- `total`: Total number of events with `seq > since_seq` (ignoring pagination). This allows clients to determine remaining events.
- `limit`: The requested limit value.
- `offset`: The requested offset value.
- `items`: Array of event objects. Each object contains the event metadata plus `dlq_at` if the event was promoted to the DLQ.

### Empty-result behavior

If no events exist after `since_seq`, the response body is:

```json
{
    "total": 0,
    "limit": 100,
    "offset": 0,
    "items": []
}
```

For SSE format, the connection closes immediately without sending any events.

### Invalid-parameter behavior

- Missing `since_seq`: Uses default value 0 (replay all events).
- Missing `format`: Uses default value `sse`.
- Missing `limit`: Uses default value 100.
- Missing `offset`: Uses default value 0.
- `since_seq` below 0: Returns HTTP 422 (FastAPI validation) with detail about minimum bound.
- `limit` below 1: Returns HTTP 422 (FastAPI validation) with detail about minimum bound.
- `limit` above 1000: Returns HTTP 422 (FastAPI validation) with detail about maximum bound.
- `offset` below 0: Returns HTTP 422 (FastAPI validation) with detail about minimum bound.
- Unknown `format` value: Returns HTTP 422 (FastAPI validation) with detail about allowed values.

### Ordering

Events are ordered by `seq` ascending (oldest first), which corresponds to insertion order into the database.

### Concurrency guarantee

The replay endpoint acquires a shared SQLite lock during the fetch operation, ensuring that the returned events represent a consistent snapshot at the time of the query. Concurrent writes do not affect the result set.

## Related Documents

- [DLQ Operations Reference](eventbus_03_dlq_operations.md)
- [DLQ Requeue API Reference](eventbus_05_dlq_endpoint.md)
- [Event Bus Overview](eventbus_01_system-overview.md)
- [Event Bus DLQ/Offsets/Delivery Semantics](eventbus_06_dlq_offsets_and_delivery_semantics.md)

## Keywords

replay
sse
server-sent events
json
pagination
event-stream
