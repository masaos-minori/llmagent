---
title: "Event Bus: Operations (Publish, Subscribe, DLQ Promotion)"
area: eventbus
tags:
  - event-bus
  - http-api
  - publish
  - subscribe
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
related:
  - eventbus_00_document-guide.md
  - eventbus_04_dlq_endpoint.md
  - eventbus_10_health_endpoint.md
  - eventbus_11_replay_endpoint.md
  - eventbus_12_ack_nack_endpoints.md
  - eventbus_01_system-overview.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
  - eventbus_07_configuration-and-operations.md
---

# Event Bus: Operations (Publish, Subscribe, DLQ Promotion)

This document covers publishing, subscribing, and how events reach the DLQ. The remaining HTTP endpoints are specified once, in their own reference documents:

| Endpoint | Canonical document |
|---|---|
| `GET /replay` | `eventbus_11_replay_endpoint.md` |
| `POST /events/{event_id}/ack`, `POST /nack`, ACK/NACK state transitions | `eventbus_12_ack_nack_endpoints.md` |
| `GET /health` | `eventbus_10_health_endpoint.md` |
| `GET /dlq`, `POST /dlq/{event_id}/requeue` | `eventbus_04_dlq_endpoint.md` |

Delivery semantics (offsets, resume position, state diagram) are in `eventbus_05_dlq_offsets_and_delivery_semantics.md`.

## POST /publish

Publishes an event. Idempotent: duplicate `event_id`s are silently ignored.

**Reason for idempotency**: Even if re-published with the same `event_id`, existing rows are not updated due to the SQLite UNIQUE constraint, ensuring consumers do not receive the same event twice. This is an intentional design, not a bug.

**Request Body**: Validated against the `event_envelope.json` JSON Schema. Required fields are `event_id` (UUID v4), `topic` (1–255 characters), `payload` (object), `producer` (1–255 characters), and `published_at` (ISO-8601). `schema_version` is optional and defaults to `"1.0"`. Additional properties are not allowed.

**Response**: On success, returns `{event_id, seq}`. A duplicate `event_id` with identical content returns the existing `seq`. A 422 error indicates a JSON Schema validation error, and a 409 error indicates that the `event_id` already exists with conflicting content.

**JSONL Append Failure**: If writing to the JSONL archive fails, the event is still committed to SQLite and a 200 status is returned. A WARNING will be recorded in the logs.

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

A token with no configured `consumer_id` allowlist entry (the common case for a shared per-role token) has this check skipped: an empty allowlist means "no restriction," not "deny all." This gap is tracked as EVENTBUS-008 in `governance_03_issue-and-uncertainty-management.md`.

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

Failure behavior of the other endpoints is in their reference documents above.

| Failure Cause | Action |
|---|---|
| JSON Schema validation failure during `publish` | 422, event is not saved |
| JSONL append failure after SQLite commit | 200 returned, WARNING log output, event remains in SQLite |
| Duplicate `event_id` with conflicting content during `publish` | 409 Conflict, event is not saved |
| Duplicate `event_id` during `publish` (Idempotency skip) | 200 returned (existing `seq`), broker notification skipped |
| Subscriber queue full | Subscriber disconnected; client must reconnect using its last committed offset |

## Keywords

- event-bus
- http-api
- publish
- subscribe
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
