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

Consumer-scoped endpoints for acknowledging successful processing (`POST /events/{event_id}/ack`) and negatively acknowledging failures (`POST /nack`).

## Authentication

**Consumer role required** for both endpoints.

Requires `Bearer ${CONSUMER_TOKEN}` in the Authorization header.

Additionally, the caller must be authorized for the specific `consumer_id` being used — the `Principal.allowed_consumer_ids` field enforces this at the application layer (a principal without a `consumer_id` and topic authorization, or a `consumer_id` outside it, is rejected with HTTP 403). An empty `consumer_authorization` mapping resolves to deny-all, so a CONSUMER token with an empty mapping rejects every `consumer_id`; startup rejects a `consumer_token` with no `consumer_authorization` at all. The shared `auth_token` and `admin_token` hold no CONSUMER role and receive HTTP 403 on these endpoints; no token bypasses consumer identity validation.

On ACK, the per-consumer delivery record and the consumer offset are updated in one transaction, and offset advancement is monotonic: acknowledging an older event never moves the stored offset backwards. NACK increments the per-consumer `consumer_delivery_failure_count`; per ADR-006 INV-13 the event is promoted to the DLQ only when every consumer that attempted delivery has reached `max_retry` on its own `(consumer_id, event_id)` count and none has ACKed.

## Acknowledge Event

`POST /events/{event_id}/ack?consumer_id=<id>`. Success returns HTTP 200 with `event_id`, `acked: true` and `seq`; a repeat ACK by the same consumer is idempotent and additionally carries `already_acked: true`.

| Condition | HTTP status |
|---|---|
| Event does not exist | 404 |
| Event already in the DLQ (`events.dlq_at` set); no delivery state or offset is written | 409 |
| `consumer_id` outside the caller's authorization | 403 |
| `consumer_id` present but empty | 400 |
| `consumer_id` parameter missing | 422 (request validation) |

## Negatively Acknowledge Event

`POST /nack?event_id=<id>&consumer_id=<id>`. Success returns HTTP 200 with `event_id` and `consumer_delivery_failure_count`, which is the nacking consumer's per-consumer failure count after this NACK. `dlq_promoted: true` is added when the event was promoted.

| Condition | HTTP status |
|---|---|
| Event does not exist | 404 |
| Requesting consumer already ACKed the event (`consumer_delivery.acked` set), or the event is already in the DLQ | 409 |
| `consumer_id` outside the caller's authorization | 403 |
| `event_id` or `consumer_id` present but empty | 400 |
| `consumer_id` parameter missing | 422 (request validation) |

ACK state is per consumer; there is no event-level ACK column.

## ACK/NACK State Transition Table

| Scenario | HTTP Status | Side Effects on Persistence |
|---|---|---|
| Initial ACK | 200 | Sets `consumer_delivery.acked` and advances the consumer offset |
| Duplicate ACK | 200 (`already_acked: true`) | No new delivery state; the offset never moves backwards |
| Initial NACK | 200 | Per-consumer failure count increases; the event is promoted to the DLQ under the ADR-006 INV-13 rule |
| Duplicate NACK (same delivery attempt) | 200 | No-op: a NACK repeating the stored `consumer_last_nack_attempt` leaves counters unchanged |
| NACK followed by ACK | 200 | ACK succeeds because NACK does not set `acked`; the failure count keeps the value from the NACK |
| ACK followed by NACK (same consumer) | 409 `event already acknowledged` | NACK rejected; counters unchanged |
| Unknown event ID (ACK or NACK) | 404 | None |
| ACK or NACK on a DLQ event | 409 `event already in dead letter queue` | None: no delivery state or offset is written |
| Simultaneous ACK/NACK | 200, or 200 and 409 | Both are serialized under the DB lock; the second call observes the first call's committed state, so a NACK that runs after the ACK returns 409 and an ACK that runs after the NACK returns 200 |

## Keywords

- ack endpoint
- nack endpoint
- consumer token
- delivery acknowledgement
