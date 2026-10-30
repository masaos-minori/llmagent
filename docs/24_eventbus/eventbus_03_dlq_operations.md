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
  - dlq-outbox
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
  - governance_03_issue-and-uncertainty-management.md
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

Publishes an event. Idempotent: a duplicate `event_id` with identical content is not stored again and returns the existing `seq`; a duplicate `event_id` with conflicting content is rejected with HTTP 409.

**Reason for idempotency**: Even if re-published with the same `event_id`, existing rows are not updated due to the SQLite UNIQUE constraint, ensuring consumers do not receive the same event twice. This is an intentional design, not a bug.

**Request Body**: Validated against the `event_envelope.json` JSON Schema. Required fields are `event_id` (UUID v4), `topic` (1–255 characters), `payload` (object), `producer` (1–255 characters), and `published_at` (ISO-8601). `schema_version` is optional and defaults to `"1.0"`. Additional properties are not allowed.

**Response**: On success, returns `{event_id, seq}` (the existing `seq` for an identical duplicate). A 422 error indicates a JSON Schema validation error, and a 409 error indicates that the `event_id` already exists with conflicting content.

**JSONL Append Failure**: If writing to the JSONL archive fails, the event is still committed to SQLite and a 200 status is returned. A WARNING will be recorded in the logs.

---

## GET /subscribe

A hybrid model combining replay and push, streaming events to the caller.

**SSE Heartbeat:** During the live delivery phase, the server emits `: heartbeat\n\n` comments at `cfg.sse_heartbeat_interval` intervals to keep idle connections alive through proxies and load balancers. Heartbeat frames do not alter offsets or delivery state.

**SSE Event IDs:** Each event frame includes `id:<seq>` where `seq` is the monotonic sequence number. This enables `EventSource`-based clients to auto-reconnect by sending the `Last-Event-ID` header.

**Reconnection with `Last-Event-ID`:** Clients can send the `HTTP Last-Event-ID` header with a sequence number to resume from that point. Precedence for determining where replay starts:
1. `since_seq` query parameter (highest priority): replay starts with the first event whose `seq` is greater than the value
2. Resume position computed from the persisted consumer offset and the consumer's unacked events (from `consumer_id`; see the resume rules in `eventbus_05_dlq_offsets_and_delivery_semantics.md`): the first event delivered is exactly the resume position
3. `Last-Event-ID` header value + 1 (lowest — fallback for `EventSource` clients): a header value of `L` resumes with event `L+1`

If `Last-Event-ID` exceeds the current max seq in SQLite, the server returns HTTP 412 Precondition Failed with the current max seq in the response body.

**Phase 1 — Replay**: Upon connection, events matching the topic filter that follow the starting position are retrieved from SQLite in batches (`replay_batch_size`), each batch continuing after the last event sent until a batch shorter than `replay_batch_size` ends the phase, and output as `id:<seq>\ndata: {...}\n\n` SSE frames.

**Phase 2 — Live Push**: After replay completion, the process subscribes to the internal `EventBroker` and streams new events published via `POST /publish` to the SSE stream in real-time.

**Queue Overflow**: If the consumer is slow and the queue becomes full, the server disconnects the subscriber's SSE connection. The client must reconnect to `GET /subscribe` with its `consumer_id` (and optionally `since_seq`) to resume from where it left off; `GET /replay` is restricted to the operator role and is not a consumer reconnection path.

**Duplicate Consumer Connection**: A second concurrent `/subscribe` connection using the same non-empty `consumer_id` as an already-active connection receives HTTP 409. The first connection remains unaffected.

**Reconnection**: Specifying a `consumer_id` allows resuming from the last acknowledged offset. Offsets are not saved upon disconnection, so events that were not acknowledged before disconnecting will be re-delivered upon reconnection.

**Query Parameters:** `topic` (topic filtering), `since_seq` (>=0, default 0), `consumer_id` (for offset persistence).

**Idle Timeout:** A connection that receives no events within `sse_idle_timeout` is closed by the server.

### `since_seq`/Offset Precedence Rules

The exact logic in the `subscribe()` function in `scripts/eventbus/subscribe_route.py` is as follows:

```
after_seq = since_seq            # replay delivers events with seq > after_seq
if consumer_id and after_seq == 0:
    after_seq = get_resume_position(db, consumer_id) - 1   # when a resume position exists
```

Rule: An explicit `since_seq=0` and an omitted `since_seq` (defaults to 0 via `Query(default=0)` declaration) are indistinguishable when a `consumer_id` is provided. Both resolve to "read from the computed resume position" (the lowest unacked `seq` at or below the stored offset, otherwise the stored offset plus one). Clients wanting to perform a full replay while providing a `consumer_id` cannot currently express this intent.

### Consumer Identity Authorization

`consumer_id` is validated against the caller's token before `/subscribe`, `/events/{event_id}/ack`, and `/nack` accept it: a request is rejected (HTTP 403) unless the token is a CONSUMER-role token with explicit authorizations covering the presented `consumer_id` and topics.

The allowlist comes from `consumer_authorization` and `topic_authorization` in `config/eventbus.toml`, and applies to the CONSUMER-role token only. Startup rejects a `consumer_token` when `consumer_authorization` is absent (fail-closed). An empty `consumer_authorization` mapping resolves to deny-all, so a `consumer_token` with an empty mapping rejects every `consumer_id`. The shared `auth_token` and the `admin_token` hold no CONSUMER role, so they are rejected (HTTP 403) on these routes; there is no bypass.

---

## DLQ Promotion Paths

DLQ promotion occurs via two independent paths that share one underlying promotion procedure:

1. **Inline promotion**: triggered synchronously when a `POST /nack` call brings the nacking consumer's per-consumer failure count to the retry limit. The exact rule is in [Inline Promotion Path](eventbus_05_dlq_offsets_and_delivery_semantics.md#inline-promotion-path).
2. **Background sweep**: a startup `asyncio` task polling periodically, acting as a safety net for events whose inline promotion was missed (e.g. a crash between the retry-count update and the promotion write).

Both paths call the same shared promotion routine: it sets `dlq_at` in SQLite and records a durable DLQ artifact generation request in the DLQ outbox in the same committed transaction, so a promoted event's DLQ state does not differ by path. The JSON artifact itself is generated afterwards by the background outbox worker.

**Authority model**: SQLite `events.dlq_at` is the authoritative DLQ state. A committed DLQ state always implies a durable generation request committed with it in the same transaction. The JSON file in the dead-letter directory is a derived artifact: it is generated by the background outbox worker after the commit, and the commit never depends on the file write succeeding.

**Failed inline promotion**: `POST /nack` commits the NACK before attempting promotion. Promotion performs no file I/O, so there is no file-write failure to defer. A promotion interrupted between the NACK commit and the promotion transaction is repaired by the background sweep. A DLQ artifact generation failure is recorded durably on the outbox row (attempt count, last error, next scheduled attempt) and metered; the fail-closed guarantee is the persisted failure record, not file-write ordering (see [Outbox generation and retry](#outbox-generation-and-retry)).

### Outbox generation and retry

- Each DLQ artifact generation request starts `pending`. The background loop consumes due pending rows each cycle, writes the artifact atomically, and marks the row `done`. Generated artifacts are metered by `eventbus_dlq_outbox_generated_total`.
- A generation failure records the attempt on the row and schedules the next attempt with exponential backoff, bounded by `outbox_max_attempts`, `outbox_backoff_base_seconds`, and `outbox_backoff_max_seconds` in `config/eventbus.toml`. Failures are metered by `eventbus_dlq_file_write_failure_total` and `eventbus_dlq_outbox_attempt_failure_total`. After the bound the row becomes terminal `failed` and is metered by `eventbus_dlq_outbox_failed_total`; its failure history stays persisted in the row.
- One failing event never blocks the others: each event's generation is isolated within the cycle.
- A request whose artifact already exists with byte-identical canonical content completes without rewriting the file (idempotent completion), so a restart never duplicates or churns artifacts.
- The outbox never alters DLQ state: `dlq_at` is written only by the promotion paths.

## DLQ Background Sweep

The background sweep selects events by the per-consumer failure count reaching the retry limit while `dlq_at IS NULL`. The exact rule is in [Background Loop Promotion](eventbus_05_dlq_offsets_and_delivery_semantics.md#background-loop-promotion).

Optimistic locking on `dlq_at IS NULL` prevents duplicate promotion. If orphaned events are found, they are recorded in the logs. The sweep is the self-healing repair path: a non-zero count is expected after a crash between the NACK update and the promotion commit, and is not by itself an indication of a defect.

## DLQ Reconciliation

Alongside the sweep, the background loop runs a scheduled reconciliation pass that reports divergences between the SQLite DLQ state and the dead-letter directory. The sweep self-heals orphan files (`dlq_at IS NULL` with an existing `{event_id}.json`) by promoting the event — setting `dlq_at` and recording the generation request in the same transaction; an existing file with matching content completes without rewrite. A persistent generation failure for one event is metered, logged, recorded on its outbox row, and skipped; it does not block the other events in the same cycle. The following divergence cases require manual reconciliation:

### Orphan Files (file exists, `dlq_at IS NULL`)

Normally self-healed by the sweep. Reconciliation counts DLQ files that have no promoted SQLite row as `orphans` in its report. If the sweep cannot promote (e.g. the file is corrupt), list remaining orphans and promote-or-delete them per policy.

### Missing Files (row has `dlq_at IS NOT NULL`, `{event_id}.json` absent)

The background reconciliation rebuilds the lost file from the SQLite row, which is the authoritative DLQ source (see Authority model above). Rebuild reads the event row (`event_id`, `topic`, `payload`, `producer`, `published_at`) and writes the record as a derived artifact; it does not change the DLQ state, which is already committed. JSONL is best-effort and is not a rebuild source: an event whose JSONL append failed exists only in SQLite and is rebuilt from SQLite here; if the SQLite row is itself absent, quarantine the event per policy. Reconciliation runs on a schedule and retries a transient write failure on the next pass. {defer operator-command sentence until UNK-01}

### Interrupted Temp Files (leftover `.dlq_tmp_*`)

An interrupted artifact write can leave a hidden `.dlq_tmp_*` file next to the target. Reconciliation counts these as `interrupted_tmp` in its report and does not delete or trust them; the missing final artifact is rebuilt from the SQLite row, and the outbox row for the event retries generation on its next scheduled attempt.

### Content Mismatch (file exists but differs from the SQLite row)

Reconciliation compares each DLQ file's fields against its authoritative SQLite row and counts differences as `mismatch` in its report. A mismatching file is never silently overwritten; review it per policy.

### Corrupt Files (`{event_id}.json` present but unparseable JSON)

Quarantine the file (rename to `*.corrupt`) and flag for manual review. Do not silently rewrite it.

**Scope boundary**: Reconciliation preserves the committed-first durability order (SQLite DLQ state plus its durable generation request) and does not alter the requeue transaction (H-01) or the readiness/integrity definition (H-03).

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
| DLQ file missing after promotion | Rebuild from SQLite via background reconciliation, or quarantine |
| DLQ file corrupt after promotion | Quarantine (`*.corrupt`); manual review required |
| DLQ artifact generation failure | Attempt recorded on the outbox row with exponential backoff; terminal `failed` after `outbox_max_attempts`; metered, logged, never blocks other events |

## Keywords

- event-bus
- http-api
- publish
- subscribe
- dlq
- dead-letter-queue
- dlq-outbox
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
