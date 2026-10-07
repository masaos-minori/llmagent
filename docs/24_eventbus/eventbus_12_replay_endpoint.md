---
title: Replay Endpoint
description: GET /replay endpoint contract for replaying events via SSE or JSON
tags: [api-reference, replay, sse]
area: eventbus
related:
  - eventbus_02_api-reference-index.md
  - eventbus_06_persistence_schema_and_replay.md
created: 20260916
---

# Replay Endpoint

## Overview

The `/replay` endpoint replays events from a given sequence number. Supports both Server-Sent Events (SSE) streaming and JSON response formats.

## Endpoint

```
GET /replay
```

## Authentication

**Operator role required.**

Requires `Bearer ${OPERATOR_TOKEN}` in the Authorization header.

## Parameters

| Parameter | Required | Default | Constraints | Description |
|-----------|----------|---------|-------------|-------------|
| `since_seq` | No | `0` | `>= 0` | Replay events with `seq` greater than this value (exclusive); `0` replays all events |
| `format` | No | `sse` | `sse`, `json` | Response format: SSE stream or JSON |
| `limit` | No | route default | bounded (see route definition) | Maximum number of events to return |
| `offset` | No | `0` | `>= 0` | Offset into the event set for pagination |

## Success Response

### SSE Format (default)

**HTTP 200 OK** with `Content-Type: text/event-stream`

Each event is emitted as an SSE message:

```
id:{seq}
data:{json_event}

```

The SSE stream covers only the requested page (`limit`/`offset`); it closes after the page is streamed and does not wait for new events. When no events exist after `since_seq`, the connection closes without sending any event.

#### Example SSE Response

```
id:42
data:{"event_id":"evt-abc","topic":"orders","payload":{"order_id":"123"},"seq":42}

id:43
data:{"event_id":"evt-def","topic":"users","payload":{"user_id":"456"},"seq":43}

```

### JSON Format

**HTTP 200 OK** with `Content-Type: application/json`

#### Response Schema

```json
{
  "total": 1000,
  "limit": 100,
  "offset": 0,
  "items": [
    {
      "event_id": "evt-abc",
      "topic": "orders",
      "payload": {"order_id": "123"},
      "seq": 42
    }
  ]
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total number of events available since `since_seq` |
| `limit` | integer | Requested page size |
| `offset` | integer | Requested offset |
| `items` | array[object] | Array of event objects with `seq`, `event_id`, `topic`, `payload`, `producer`, and `published_at` (examples below omit `producer` and `published_at` for brevity) |

When no events exist after `since_seq`, the JSON response has `total: 0` and an empty `items` array.

## Invalid Parameters

- Missing `since_seq`, `format`, `limit`, or `offset`: the default value (or the route's default for `limit`) applies.
- `since_seq` below 0, `limit` below 1 or above the maximum bound, `offset` below 0, or an unknown `format` value: HTTP 422 (FastAPI validation).

## Ordering and Consistency

Events are ordered by `seq` ascending (insertion order). The page and the total count are fetched under the global DB lock in a single acquisition, so the returned events and `total` form a consistent snapshot; concurrent writes do not affect the result set.

## Example Requests

### SSE Replay

```bash
curl -N -H "Authorization: Bearer ${OPERATOR_TOKEN}" \
  "http://<eventbus-host>:<port>/replay?since_seq=42&format=sse"
```

### JSON Replay

```bash
curl -H "Authorization: Bearer ${OPERATOR_TOKEN}" \
  "http://<eventbus-host>:<port>/replay?since_seq=42&format=json&limit=50&offset=0"
```

Response:

```json
{
  "total": 1000,
  "limit": 50,
  "offset": 0,
  "items": [
    {"event_id": "evt-abc", "topic": "orders", "payload": {"order_id": "123"}, "seq": 42},
    {"event_id": "evt-def", "topic": "users", "payload": {"user_id": "456"}, "seq": 43}
  ]
}
```

## Keywords

- replay endpoint
- since_seq
- SSE replay
- JSON pagination
