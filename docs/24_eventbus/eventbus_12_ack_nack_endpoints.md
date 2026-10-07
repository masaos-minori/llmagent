---
title: ACK/NACK Endpoints
tags: [api-reference, ack, nack, consumer]
area: eventbus
related:
  - eventbus_02_api-reference-index.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
---

# ACK/NACK Endpoints

## Overview

Consumer-scoped endpoints for acknowledging successful processing (`POST /events/{event_id}/ack`) and negatively acknowledging failures (`POST /nack`). Both require Consumer role authentication.

## Authentication

**Consumer role required** for both endpoints.

Requires `Bearer ${CONSUMER_TOKEN}` in the Authorization header.

Additionally, the caller must be authorized for the specific `consumer_id` being used — the `Principal.allowed_consumer_ids` field enforces this at the application layer when the principal has a non-empty `consumer_id` allowlist; a principal with an empty allowlist is not restricted.

On ACK, the per-consumer delivery record and the consumer offset are updated in one transaction, and offset advancement is monotonic: acknowledging an older event never moves the stored offset backwards. NACK increases `delivery_failure_count` and moves the event to the DLQ once it reaches `max_retry`.

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
  "detail": "event not found"
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

Returned when `consumer_id` is present but empty. A completely missing `consumer_id` query parameter is rejected by request validation with HTTP 422.

#### Response Schema

```json
{
  "detail": "consumer_id is required for consumer ACK"
}
```

### Example Request

```bash
curl -X POST -H "Authorization: Bearer ${CONSUMER_TOKEN}" \
  "http://<eventbus-host>:<port>/events/evt-abc/ack?consumer_id=worker-1"
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
  "detail": "event not found"
}
```

### Conflict Responses

**HTTP 409 Conflict**

Returned when the event has `events.acked_at` set, is already in the DLQ, or the requesting consumer has already ACKed via `consumer_delivery.acked_at`.

#### Response Schemas

```json
{"detail": "event already acknowledged"}
{"detail": "event already in dead letter queue"}
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

Returned when `event_id` or `consumer_id` is present but empty. A completely missing `consumer_id` query parameter is rejected by request validation with HTTP 422.

#### Response Schema

```json
{
  "detail": "consumer_id is required for NACK"
}
```

### Example Request

```bash
curl -X POST -H "Authorization: Bearer ${CONSUMER_TOKEN}" \
  "http://<eventbus-host>:<port>/nack?event_id=evt-abc&consumer_id=worker-1"
```

## ACK/NACK State Transition Table

| Scenario | Behavior | HTTP Status | Response Body | Side Effects on Persistence |
|---|---|---|---|---|
| Initial ACK | `ack_event_for_consumer` returns `(True, True, seq)` | 200 | `{event_id, acked: true, seq}` | Sets `consumer_delivery.acked_at` and advances the consumer offset |
| Duplicate ACK | `ack_event_for_consumer` returns `(True, False, seq)` | 200 | `{event_id, acked: true, seq, already_acked: true}` | No new delivery state; the offset never moves backwards |
| Initial NACK | `nack_event` increases `delivery_failure_count` from 0 to 1 | 200 | `{event_id, delivery_failure_count}` | Counter increases; promoted to the DLQ when it reaches `max_retry` |
| Duplicate NACK | No idempotency guard in `nack_event`; the counter increases on every call (tracked as EVENTBUS-012 in `governance_03_issue-and-uncertainty-management.md`) | 200 | `{event_id, delivery_failure_count}` | Counter keeps increasing, which can trigger DLQ promotion on a later call |
| NACK followed by ACK | The consumer's `consumer_delivery.acked_at` is still unset (NACK does not set it) | 200 | `{event_id, acked: true, seq}` | ACK succeeds; `delivery_failure_count` keeps the value from the NACK |
| ACK followed by NACK (same consumer) | `nack_event` checks `consumer_delivery.acked_at` for the requesting consumer | 409 | `event already acknowledged` | NACK rejected; counters unchanged |
| Unknown event ID (ACK) | `ack_event_for_consumer` returns `found = False` | 404 | `event not found` | None |
| Unknown event ID (NACK) | `nack_event` returns `-1` | 404 | `event not found` | None |
| Simultaneous ACK/NACK | Both run under `run_with_db_lock` and are serialized | 200/200 | Depends on lock order | The second call observes the first call's committed state |

## Keywords

- ack endpoint
- nack endpoint
- consumer token
- delivery acknowledgement
