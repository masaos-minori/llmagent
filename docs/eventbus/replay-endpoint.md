---
title: Replay Endpoint
description: GET /replay endpoint contract for replaying events via SSE or JSON
tags: [api-reference, replay, sse]
area: eventbus
related: []
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
| `since_seq` | No | `0` | `>= 0` | Sequence number to start replaying from |
| `format` | No | `sse` | `sse`, `json` | Response format: SSE stream or JSON |
| `limit` | No | `100` | `1 <= limit <= 1000` | Maximum number of events to return |
| `offset` | No | `0` | `>= 0` | Offset into the event set for pagination |

## Success Response

### SSE Format (default)

**HTTP 200 OK** with `Content-Type: text/event-stream`

Each event is emitted as an SSE message:

```
id:{seq}
data:{json_event}

```

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
| `items` | array[object] | Array of event objects |

## Example Requests

### SSE Replay

```bash
curl -N -H "Authorization: Bearer ${OPERATOR_TOKEN}" \
  "http://localhost:8080/replay?since_seq=42&format=sse"
```

### JSON Replay

```bash
curl -H "Authorization: Bearer ${OPERATOR_TOKEN}" \
  "http://localhost:8080/replay?since_seq=42&format=json&limit=50&offset=0"
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
