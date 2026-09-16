---
title: DLQ Endpoint
description: DLQ list and requeue endpoint contracts for dead-letter queue management
tags: [api-reference, dlq, dead-letter]
created: 20260916
---

# DLQ Endpoint

## Overview

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

### Path Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `event_id` | Yes | The event ID to requeue |

### Success Response

**HTTP 200 OK**

#### Response Schema

```json
{
  "event_id": "evt-failed",
  "requeued": true,
  "new_event_id": "evt-requeued-abc",
  "new_seq": 1001
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | Original event ID that was requeued |
| `requeued` | boolean | Always `true` on success |
| `new_event_id` | string | New event ID created by the requeue operation |
| `new_seq` | integer | Sequence number of the new event |

### Conflict Response

**HTTP 409 Conflict**

Returned when the event is not currently in the DLQ (already redelivered or acknowledged).

#### Response Schema

```json
{
  "detail": "Event is not in the dead letter queue"
}
```

### Not Found Response

**HTTP 404 Not Found**

Returned when the event does not exist.

#### Response Schema

```json
{
  "detail": "Event not found"
}
```

### Example Request

```bash
curl -X POST -H "Authorization: Bearer ${OPERATOR_TOKEN}" \
  http://localhost:8080/dlq/evt-failed/requeue
```

### Idempotency Note

Requeue uses a lineage model: each requeue creates a new event row with `redelivered_from` pointing to the original event ID. The original row's `dlq_at` timestamp is intentionally preserved so only one successful redelivery occurs per original event. Attempting to requeue the same event twice will return HTTP 409 on the second attempt.
