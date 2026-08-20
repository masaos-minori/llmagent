---
title: "Event Bus: Subscribe and Ack Endpoints"
category: eventbus
tags:
  - event-bus
  - http-api
  - subscribe
  - ack
  - nack
  - sse
  - streaming
  - consumer-offset
  - idempotent
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_01_publish-replay.md
  - 06_eventbus_02_03_nack-health-dlq.md
source:
  - 06_eventbus_02_01_publish-replay.md
---

# Event Bus: Subscribe and Ack Endpoints

## GET /subscribe

A hybrid model combining replay and push, streaming events to the caller.

**Phase 1 — Replay**: Upon connection, all events matching the topic filter where `seq > start_seq` are retrieved from SQLite and output as `data:` SSE lines.

**Phase 2 — Live Push**: After replay completion, the process subscribes to the internal `EventBroker` and streams new events published via `POST /publish` to the SSE stream in real-time.

**Queue Overflow**: If the consumer is slow and the queue becomes full, the event is discarded (only a WARNING is logged). Use `since_seq`/`GET /replay` for recovery.

**Reconnection**: Specifying a `consumer_id` allows resuming from the last acknowledged offset. Offsets are not saved upon disconnection, so events that were not acknowledged before disconnecting will be re-delivered upon reconnection.

**Query Parameters:** `topic` (topic filtering), `since_seq` (>=0, default 0), `consumer_id` (for offset persistence).

---

## POST /events/{event_id}/ack [canonical]

Acknowledges an event. When a `consumer_id` is specified, the consumer offset is updated. Idempotent.

**Path Parameters:** `event_id` (required)
**Query Parameters:** `consumer_id` (optional)

**Response:** On success, returns `{event_id, acked: true, seq: <int>}`. If already acknowledged, returns `{event_id, acked: true, already_acked: true}`. A 404 error indicates the event was not found.

**Note on Monotonicity:** Offset advancement is not guaranteed to be monotonic. Acknowledging older events can cause the offset to regress. Consumers should acknowledge in order or handle regressions upon reconnection.

---

## ACK/NACK State Transition Table

The following table summarizes the current code behavior for ACK and NACK operations. For details on the NACK side (duplicate NACK, NACK followed by ACK, etc.), please refer to [docs/06_eventbus_02_03_nack-health-dlq.md](docs/06_eventbus_02_03_nack-health-dlq.md).

| Scenario | Current Code Behavior | HTTP Status | Response Body | Side Effects on Persistence |
|---|---|---|---|---|
| Initial ACK | `ack_event` returns `(True, True)` | 200 | `{event_id, acked: true, seq: <int>}` | Sets `acked_at`; writes offset if `consumer_id` is provided |
| Duplicate ACK | `ack_event` returns `(True, False)` | 200 | `{event_id, acked: true, already_acked: true}` | No additional write; no offset rewrite |
| Initial NACK | `nack_event` increases `delivery_failure_count` from 0 $\to$ 1 | 200 | `{event_id, delivery_failure_count}` | `delivery_failure_count` increases; promoted to DLQ if `>= max_retry` |
| Duplicate NACK | No idempotency guard in `nack_event`; `delivery_failure_count` increases with every call | 200 | `{event_id, delivery_failure_count}` | Counter keeps increasing, potentially triggering DLQ promotion on subsequent calls — **Implementation fix required** |
| NACK followed by ACK | `ack_event`'s `WHERE acked_at IS NULL` check remains true (NACK does not set `acked_at`) | 200 | `{event_id, acked: true, seq: <int>}` | ACK succeeds, `delivery_failure_count` remains at the value from NACK — No readjustment |
| ACK followed by NACK | No `acked_at` check in `nack_event` | 200 | `{event_id, delivery_failure_count}` | Even if already ACKed, NACK succeeds and `delivery_failure_count` increases — **Implementation fix required** |
| Unknown Event ID (ACK) | `ack_event` returns `(False, False)` | 404 | `ERR_EVENT_NOT_FOUND` | None |
| Unknown Event ID (NACK) | `nack_event` returns `-1` | 404 | `ERR_EVENT_NOT_FOUND` | None |
| Simultaneous ACK/NACK | Both go through `run_with_db_lock` and are serialized at the DB layer | 200/200 | Depends on lock order | No true contention — Lock enforces total ordering, and the second call observes the first call's committed state |

### `since_seq`/Offset Precedence Rules

The exact logic in `subscribe_route.py` at L32-34 is as follows:

```
start_seq = since_seq
if consumer_id and start_seq == 0:
    start_seq = read_offset(cfg.offsets_dir, consumer_id)
```

Rule: An explicit `since_seq=0` and an omitted `since_seq` (defaults to 0 via `Query(default=0)` declaration) are indistinguishable when a `consumer_id` is provided. Both resolve to "read from the saved offset". Clients wanting to perform a full replay while providing a `consumer_id` cannot currently express this intent.

### Handling Unknown/Mismatched Consumers

There is no consumer/event ownership column in `schema.sql`. `consumer_id` is accepted as any string and only used for `write_offset`/`read_offset`. Both `/subscribe` and `/events/{event_id}/ack` accept arbitrary strings without validation against an event ownership registry. Following implementation instructions #1/#3, this is documented as "untracked/unimplemented (by design)" rather than being silently omitted.

---

## Related Documents

- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_03_nack-health-dlq.md`
