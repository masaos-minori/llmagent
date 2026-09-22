---
title: ACK/NACK Endpoints
description: Consumer acknowledgment and negative acknowledgment endpoint contracts
tags: [api-reference, ack, nack, consumer]
area: eventbus
related: []
created: 20260916
---

# ACK/NACK Endpoints

## Overview

Consumer-scoped endpoints for acknowledging successful processing (`POST /events/{event_id}/ack`) and negatively acknowledging failures (`POST /nack`). Both require Consumer role authentication.

## Authentication

**Consumer role required** for both endpoints.

Requires `Bearer ${CONSUMER_TOKEN}` in the Authorization header.

Additionally, the caller must be authorized for the specific `consumer_id` being used — the `Principal.allowed_consumer_ids` field enforces this at the application layer.

## Acknowledge Event

### Endpoint

```
POST /events/{event_id}/ack
```

### Path Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `event_id` | Yes | The event ID to acknowledge |

### Query Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `consumer_id` | Yes | The consumer ID performing the acknowledgment |

### Success Response

**HTTP 200 OK**

#### Response Schema (first acknowledgement)

```json
{
  "event_id": "evt-abc",
  "acked": true,
  "seq": 42
}
```

#### Response Schema (already acknowledged)

```json
{
  "event_id": "evt-abc",
  "acked": true,
  "seq": 42,
  "already_acked": true
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | The acknowledged event ID |
| `acked` | boolean | Always `true` on success |
| `seq` | integer | Event sequence number (included for idempotent consumers) |
| `already_acked` | boolean | Present and `true` if the event was already acknowledged |

### Not Found Response

**HTTP 404 Not Found**

Returned when the event does not exist.

#### Response Schema

```json
{
  "detail": "Event not found"
}
```

### Conflict Response

**HTTP 409 Conflict**

Returned when the event was not delivered to this consumer.

#### Response Schema

```json
{
  "detail": "Event not delivered to this consumer"
}
```

### Forbidden Response

**HTTP 403 Forbidden**

Returned when the caller's principal does not include the requested `consumer_id`.

#### Response Schema

```json
{
  "detail": "Forbidden: consumer_id 'worker-1' not allowed"
}
```

### Bad Request Responses

**HTTP 400 Bad Request**

Returned when `event_id` or `consumer_id` is missing.

#### Response Schema

```json
{
  "detail": "consumer_id is required for consumer ACK"
}
```

### Example Request

```bash
curl -X POST -H "Authorization: Bearer ${CONSUMER_TOKEN}" \
  "http://localhost:8080/events/evt-abc/ack?consumer_id=worker-1"
```

## Negatively Acknowledge Event

### Endpoint

```
POST /nack
```

### Query Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `event_id` | Yes | The event ID to negatively acknowledge |
| `consumer_id` | Yes | The consumer ID performing the NACK |

### Success Response

**HTTP 200 OK**

#### Response Schema (normal NACK)

```json
{
  "event_id": "evt-abc",
  "delivery_failure_count": 2
}
```

#### Response Schema (DLQ promoted)

```json
{
  "event_id": "evt-abc",
  "delivery_failure_count": 3,
  "dlq_promoted": true
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | The NACK'd event ID |
| `delivery_failure_count` | integer | Lifetime failure count after this NACK |
| `dlq_promoted` | boolean | Present and `true` if the event was promoted to DLQ |

### Not Found Response

**HTTP 404 Not Found**

Returned when the event does not exist.

#### Response Schema

```json
{
  "detail": "Event not found"
}
```

### Conflict Responses

**HTTP 409 Conflict**

Returned when the event is already acknowledged or already in the DLQ.

#### Response Schemas

```json
{"detail": "Event is already acknowledged"}
{"detail": "Event is in the dead letter queue"}
{"detail": "invalid NACK transition"}
```

### Forbidden Response

**HTTP 403 Forbidden**

Returned when the caller's principal does not include the requested `consumer_id`.

#### Response Schema

```json
{
  "detail": "Forbidden: consumer_id 'worker-1' not allowed"
}
```

### Bad Request Responses

**HTTP 400 Bad Request**

Returned when `event_id` or `consumer_id` is missing.

#### Response Schema

```json
{
  "detail": "consumer_id is required for NACK"
}
```

### Example Request

```bash
curl -X POST -H "Authorization: Bearer ${CONSUMER_TOKEN}" \
  "http://localhost:8080/nack?event_id=evt-abc&consumer_id=worker-1"
```
