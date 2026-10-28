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

Additionally, the caller must be authorized for the specific `consumer_id` being used — the caller must hold a grant for the requested `consumer_id` on the topic of the event being acknowledged, enforced at the application layer (a principal without grants, or a `consumer_id` or event topic outside them, is rejected with HTTP 403). An empty `consumer_authorization` mapping resolves to deny-all, so a CONSUMER token with an empty mapping rejects every `consumer_id`; startup rejects a `consumer_token` with no `consumer_authorization` at all. The shared `auth_token` and `admin_token` hold no CONSUMER role and receive HTTP 403 on these endpoints; no token bypasses consumer identity validation.

On ACK, the per-consumer delivery record and the consumer offset are updated in one transaction, and offset advancement is monotonic: acknowledging an older event never moves the stored offset backwards. NACK increments the per-consumer `consumer_delivery_failure_count`; per ADR-006 INV-13 the event is promoted to the DLQ only when every consumer that attempted delivery has reached `max_retry` on its own `(consumer_id, event_id)` count and none has ACKed.

## Acknowledge Event

`POST /events/{event_id}/ack?consumer_id=<id>`. Success returns HTTP 200 with `event_id`, `acked: true` and `seq`; a repeat ACK by the same consumer is idempotent and additionally carries `already_acked: true`.

| Condition | HTTP status |
|---|---|
| Event does not exist | 404 |
| Event already in the DLQ (`events.dlq_at` set); no delivery state or offset is written | 409 |
| `consumer_id` or event topic outside the caller's grants | 403 |
| `consumer_id` present but empty | 400 |
| `consumer_id` parameter missing | 422 (request validation) |

## Negatively Acknowledge Event

`POST /nack?event_id=<id>&consumer_id=<id>`. Success returns HTTP 200 with `event_id` and `consumer_delivery_failure_count`, which is the nacking consumer's per-consumer failure count after this NACK. `dlq_promoted: true` is added when the event was promoted.

### Idempotency Key

`POST /nack` accepts an `idempotency_key` query parameter identifying the
delivery attempt. The client generates and holds this key (for example derived
from `(consumer_id, event_id, attempt_number)`, or a client-stored UUID) and sends
it on **every** NACK for that attempt:

- A retry of the **same** failed attempt reuses the **same** key → the NACK is a
  **no-op** (counters unchanged), so network/proxy retries do not double-count.
- Advancing to a **new** attempt uses a **new** key → counted once.

The server treats the key opaquely and passes it unchanged through to the
repository. A NACK without a key is rejected with HTTP 400.

| Condition | HTTP status |
|---|---|
| Event does not exist | 404 |
| Requesting consumer already ACKed the event (`consumer_delivery.acked` set), or the event is already in the DLQ | 409 |
| `consumer_id` or event topic outside the caller's grants | 403 |
| `event_id` or `consumer_id` present but empty | 400 |
| `consumer_id` parameter missing | 422 (request validation) |
| `idempotency_key` parameter missing | 400 |

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

**NACK idempotency key scope and retention.** Deduplication is latest-key-only:
only the most recent `consumer_last_nack_attempt` per `(consumer_id, event_id)` is
remembered. A NACK whose key is not the most recent one counts as a new attempt.
(A bounded set of recent keys would require a schema change and is not adopted.)

## Keywords

- ack endpoint
- nack endpoint
- consumer token
- delivery acknowledgement
