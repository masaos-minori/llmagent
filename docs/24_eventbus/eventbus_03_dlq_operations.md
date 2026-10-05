---
title: "Event Bus: Operations (Publish, Subscribe, Ack/Nack, Health, DLQ)"
area: eventbus
tags:
  - event-bus
  - http-api
  - publish
  - replay
  - subscribe
  - ack
  - nack
  - health
  - dlq
  - dead-letter-queue
  - background-loop
  - safety-sweep
  - optimistic-lock
  - orphan-promotion
  - requeue
  - error-handling
  - failure-behavior
  - sse
  - streaming
  - consumer-offset
  - idempotent
  - json-schema
  - pagination
related:
  - eventbus_00_document-guide.md
  - eventbus_01_system-overview.md
  - eventbus_06_dlq_offsets_and_delivery_semantics.md
  - eventbus_09_configuration-and-operations.md
---

# Event Bus: Operations (Publish, Subscribe, Ack/Nack, Health, DLQ)

## POST /publish

Publishes an event. Idempotent: duplicate `event_id`s are silently ignored.

**Reason for idempotency**: Even if re-published with the same `event_id`, existing rows are not updated due to the SQLite UNIQUE constraint, ensuring consumers do not receive the same event twice. This is an intentional design, not a bug.

**Request Body**: Validated against the `event_envelope.json` JSON Schema. Required fields are `event_id` (UUID v4), `topic` (1–255 characters), `payload` (object), `producer` (1–255 characters), and `published_at` (ISO-8601). `schema_version` is optional and defaults to `"1.0"`. Additional properties are not allowed.

**Response**: On success, returns `{event_id, seq}`. A duplicate `event_id` with identical content returns the existing `seq`. A 422 error indicates a JSON Schema validation error, and a 409 error indicates that the `event_id` already exists with conflicting content.

**JSONL Append Failure**: If writing to the JSONL archive fails, the event is still committed to SQLite and a 200 status is returned. A WARNING will be recorded in the logs.

---

## GET /replay

Replays past events. Returns events where `seq > since_seq`. Supports pagination when `format=json`.

**Query Parameters:** `since_seq` (>=0), `limit` (bounded; see the route definition for the default and maximum), `offset` (>=0), `format` (sse/json, default sse).

**Response (`format=json`):** A pagination object containing `{total, limit, offset, items}`. `total` is the total count regardless of `limit`/`offset`.

**Response (`format=sse`):** Each event is output as an `id:<seq>\ndata: {...}\n\n` SSE frame. The `id:` field contains the monotonic sequence number, enabling `EventSource`-based clients to auto-reconnect. The SSE format does not support paginated incremental consumption. The stream terminates after `limit` items are output.

**Error Response:** 422 — if parameter values are invalid.

---

## GET /subscribe

A hybrid model combining replay and push, streaming events to the caller.

**SSE Heartbeat:** During the live delivery phase, the server emits `: heartbeat\n\n` comments at `cfg.sse_heartbeat_interval` intervals to keep idle connections alive through proxies and load balancers. Heartbeat frames do not alter offsets or delivery state.

**SSE Event IDs:** Each event frame includes `id:<seq>` where `seq` is the monotonic sequence number. This enables `EventSource`-based clients to auto-reconnect by sending the `Last-Event-ID` header.

**Reconnection with `Last-Event-ID`:** Clients can send the `HTTP Last-Event-ID` header with a sequence number to resume from that point. Precedence for determining `start_seq`:
1. `since_seq` query parameter (highest priority)
2. Persisted consumer offset (from `consumer_id`)
3. `Last-Event-ID` header value + 1 (lowest — fallback for `EventSource` clients)

If `Last-Event-ID` exceeds the current max seq in SQLite, the server returns HTTP 412 Precondition Failed with the current max seq in the response body.

**Phase 1 — Replay**: Upon connection, events matching the topic filter where `seq > start_seq` are retrieved from SQLite in batches (`replay_batch_size`) and output as `id:<seq>\ndata: {...}\n\n` SSE frames.

**Phase 2 — Live Push**: After replay completion, the process subscribes to the internal `EventBroker` and streams new events published via `POST /publish` to the SSE stream in real-time.

**Queue Overflow**: If the consumer is slow and the queue becomes full, the server disconnects the subscriber's SSE connection. The client must reconnect using its last committed `consumer_id`/offset via `since_seq`/`GET /replay` to resume from where it left off.

**Duplicate Consumer Connection**: A second concurrent `/subscribe` connection using the same non-empty `consumer_id` as an already-active connection receives HTTP 409. The first connection remains unaffected.

**Reconnection**: Specifying a `consumer_id` allows resuming from the last acknowledged offset. Offsets are not saved upon disconnection, so events that were not acknowledged before disconnecting will be re-delivered upon reconnection.

**Query Parameters:** `topic` (topic filtering), `since_seq` (>=0, default 0), `consumer_id` (for offset persistence).

**Idle Timeout:** A connection that receives no events within `sse_idle_timeout` is closed by the server.

### `since_seq`/Offset Precedence Rules

The exact logic in the `subscribe()` function in `scripts/eventbus/subscribe_route.py` is as follows:

```
start_seq = since_seq
if consumer_id and start_seq == 0:
    start_seq = get_consumer_offset(db, consumer_id)
```

Rule: An explicit `since_seq=0` and an omitted `since_seq` (defaults to 0 via `Query(default=0)` declaration) are indistinguishable when a `consumer_id` is provided. Both resolve to "read from the saved offset". Clients wanting to perform a full replay while providing a `consumer_id` cannot currently express this intent.

### Consumer Identity Authorization

`consumer_id` is validated against the caller's token before `/subscribe`, `/events/{event_id}/ack`, and `/nack` accept it: a token that has an explicit `consumer_id` allowlist configured is rejected (HTTP 403) if it presents a `consumer_id` outside that allowlist.

**Known Issue**: a token with no configured `consumer_id` allowlist entry (the common case for a shared per-role token) has this check skipped entirely — an empty allowlist means "no restriction," not "deny all." This means `consumer_id` collisions between callers sharing such a token remain possible unless a per-caller allowlist is explicitly configured.

---

## POST /events/{event_id}/ack [canonical]

Acknowledges an event for a consumer. The per-consumer delivery record and the consumer offset are updated in one transaction. Idempotent.

**Path Parameters:** `event_id` (required)
**Query Parameters:** `consumer_id` (required)

**Response:** On success, returns `{event_id, acked: true, seq: <int>}`. If already acknowledged, returns `{event_id, acked: true, seq: <int>, already_acked: true}`. A 404 error indicates the event was not found.

**Note on Monotonicity:** Offset advancement is monotonic. Acknowledging an older event does not move the stored offset backwards.

---

## POST /nack

Sends a NACK (Negative Acknowledgement) for an event. Increases `delivery_failure_count`, and moves the event to the DLQ once `delivery_failure_count >= max_retry`.

**Query Parameters:** `event_id` (required), `consumer_id` (required)
**Response:** On success, returns `{event_id, delivery_failure_count}`, plus `dlq_promoted: true` when the NACK promoted the event to the DLQ. A 404 error indicates the event was not found. A 409 error indicates the event is already in the DLQ, or has `events.acked_at` set. A consumer's own ACK does not set `events.acked_at`; a NACK sent by a consumer after its own ACK is rejected with HTTP 409 `event already acknowledged`.

For NACK's state-transition behavior (initial/duplicate NACK, NACK after ACK, unknown event ID), see the ACK/NACK State Transition Table below — it covers both ACK and NACK together rather than repeating NACK rows separately.

---

## ACK/NACK State Transition Table

The following table summarizes the current code behavior for ACK and NACK operations.

| Scenario | Current Code Behavior | HTTP Status | Response Body | Side Effects on Persistence | Notes |
|---|---|---|---|---|---|
| Initial ACK | `ack_event_for_consumer` returns `(True, True, seq)` | 200 | `{event_id, acked: true, seq: <int>}` | Sets `consumer_delivery.acked_at` and advances the consumer offset | — |
| Duplicate ACK | `ack_event_for_consumer` returns `(True, False, seq)` | 200 | `{event_id, acked: true, seq: <int>, already_acked: true}` | No new delivery state; the offset never moves backwards | Idempotent |
| Initial NACK | `nack_event` increases `delivery_failure_count` from 0 → 1 | 200 | `{event_id, delivery_failure_count}` | `delivery_failure_count` increases; promoted to DLQ if `>= max_retry` | — |
| Duplicate NACK | No idempotency guard in `nack_event`; `delivery_failure_count` increases with every call | 200 | `{event_id, delivery_failure_count}` | Counter keeps increasing, potentially triggering DLQ promotion on subsequent calls | **Known Issue: Implementation fix required** |
| NACK followed by ACK | The consumer's `consumer_delivery.acked_at` is still unset (NACK does not set it) | 200 | `{event_id, acked: true, seq: <int>}` | ACK succeeds, `delivery_failure_count` remains at the value from NACK | No readjustment |
| ACK followed by NACK (same consumer) | `nack_event` checks `consumer_delivery.acked_at` for the requesting consumer; the per-consumer ACK sets it | 409 | `event already acknowledged` | NACK rejected; counters unchanged | **Resolved** |
| Unknown Event ID (ACK) | `ack_event_for_consumer` returns `found = False` | 404 | `ERR_EVENT_NOT_FOUND` | None | — |
| Unknown Event ID (NACK) | `nack_event` returns `-1` | 404 | `ERR_EVENT_NOT_FOUND` | None | — |
| Simultaneous ACK/NACK | Both go through `run_with_db_lock` and are serialized at the DB layer | 200/200 | Depends on lock order | No true contention — Lock enforces total ordering, and the second call observes the first call's committed state | — |

---

## GET /health

Returns the health status of each component. `ok` corresponds to HTTP 200, while `degraded`/`unhealthy` corresponds to HTTP 503.

**Response Fields:** `status`, `db`, `dlq_task`, `active_subscribers`, `max_queue_depth`, `slow_consumers`, `overflow_disconnects`, `duplicate_connection_rejections`, `degraded_reasons`, `metrics`.

The `status` is `"ok"` only when all components are healthy. `degraded_reasons` lists failure causes (`db_unavailable`, `dlq_task_stopped`, `broker_unavailable`, `broker_queue_backlog_high`, `slow_consumers_detected`, `subscribers_at_capacity`, `lock_wait_high`, `query_duration_high`).

---

## GET /dlq

Retrieves a list of DLQ events (events where `dlq_at IS NOT NULL`).

**Query Parameters:** `limit` (bounded; see the route definition for the default and maximum), `offset` (>=0, default 0)
**Response:** A pagination object containing `{total, limit, offset, items}`. `items` includes `{seq, event_id, topic, producer, published_at, delivery_failure_count, dlq_requeue_count, dlq_at}`.

---

## POST /dlq/{event_id}/requeue

Requeues a DLQ event using the lineage model: the original row stays in the DLQ (`dlq_at` is kept, `dlq_requeue_count` is increased) and a new event row is inserted with a fresh `event_id`, `redelivered_from` pointing to the original, the copied `delivery_failure_count`, and `cycle_failure_count` reset to 0. Only one requeue succeeds per original event.

**Path Parameters:** `event_id` (required)
**Response:** On success, returns `{event_id, requeued: true, new_event_id, new_seq}`. A 409 error indicates the event is not in the DLQ or has already been requeued, and a 404 error indicates it was not found.

---

## DLQ Promotion Paths

DLQ promotion occurs via two independent paths that share one underlying promotion procedure:

1. **Inline promotion**: triggered synchronously when a `POST /nack` call raises `delivery_failure_count` to `max_retry` or beyond.
2. **Background sweep**: a startup `asyncio` task polling periodically, acting as a safety net for events whose inline promotion was missed (e.g. a crash between the retry-count update and the promotion write).

Both paths call the same shared promotion routine (atomic write to JSON file + setting `dlq_at` in SQLite), so a promoted event's on-disk/DB representation does not differ by path.

## DLQ Background Sweep

The background sweep searches for events where `delivery_failure_count >= max_retry AND dlq_at IS NULL`.

Using optimistic locking, it only targets events where `dlq_at IS NULL` to prevent duplicate promotion. If orphaned events are found, they are recorded in the logs. Any non-zero count may indicate an issue with the inline promotion process (e.g. a crash before its promotion write completed) rather than a normal condition.

---

## Failure Behavior Summary

| Failure Cause | Action |
|---|---|
| JSON Schema validation failure during `publish` | 422, event is not saved |
| JSONL append failure after SQLite commit | 200 returned, WARNING log output, event remains in SQLite |
| DB unavailable in `/health` | `status: degraded`, `db: unavailable` |
| DLQ task stopped in `/health` | `status: degraded`, `dlq_task: stopped` |
| Unknown `event_id` during requeue | 404 |
| Event exists but is not in DLQ (or already requeued) during requeue | 409 Conflict |
| Duplicate `event_id` with conflicting content during `publish` | 409 Conflict, event is not saved |
| Duplicate `event_id` during `publish` (Idempotency skip) | 200 returned (existing `seq`), broker notification skipped |
| Subscriber queue full | Subscriber disconnected; client must reconnect using its last committed offset |

## Keywords

- event-bus
- http-api
- publish
- replay
- subscribe
- ack
- nack
- health
- dlq
- dead-letter-queue
- background-loop
- safety-sweep
- optimistic-lock
- orphan-promotion
- requeue
- error-handling
- failure-behavior
- sse
- streaming
- consumer-offset
- idempotent
- json-schema
- pagination
