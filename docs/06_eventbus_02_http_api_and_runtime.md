# Event Bus: HTTP API and Runtime

## Endpoints

### POST /publish

Publish an event. Idempotent: duplicate `event_id` is silently ignored.

**Request body** (validated against `event_envelope.json` JSON Schema):

```json
{
  "event_id": "uuid-string",
  "topic": "topic.name",
  "payload": {},
  "producer": "producer-name",
  "published_at": "2026-06-24T00:00:00Z"
}
```

**Response 200:**
```json
{"event_id": "uuid-string", "seq": 42}
```

**Response 422:** JSON Schema validation failure.

**JSONL append failure**: If writing to the JSONL archive fails (e.g. disk full), the event is still committed to SQLite and 200 is returned. A WARNING is logged.

---

### GET /replay

Replay past events. Returns events with `seq > since_seq`.

**Query parameters:**
- `since_seq` (int, default 0): start sequence number (exclusive)
- `format` (str, default `sse`): `sse` returns SSE stream; `json` returns a JSON array

**Response (`format=json`):** `[{seq, event_id, topic, payload, producer, published_at}, ...]`

---

### GET /subscribe

Streams events to the caller using a hybrid replay+push model:

**Phase 1 — Replay**: On connect, queries SQLite for all events with `seq > start_seq` matching the topic filter. Each event is yielded as a `data:` SSE line immediately.

**Phase 2 — Live push**: After replay completes, the connection subscribes to the in-process `EventBroker`. New events published via `POST /publish` are pushed to the SSE stream within one event loop tick — no polling delay.

**Reconnect semantics**: Provide `consumer_id` to resume from the last acknowledged offset. The handler reads the stored offset as `start_seq`, ensuring missed events during a disconnect are replayed automatically.

**Race-free transition**: The broker subscription is registered *before* the replay query. Any event published during the replay phase is queued and deduplicated against `replay_ceil` (last seq from replay) at the start of the live phase — no events are lost or duplicated.

**Query parameters:**
- `topic` (list[str], default all): filter by topic
- `since_seq` (int, default 0): starting sequence; overridden by saved offset if `consumer_id` is set and `since_seq == 0`
- `consumer_id` (str, optional): consumer identifier for offset persistence

Offsets advance only via ack (see `POST /events/{event_id}/ack`). On disconnect, no offset is written — if a consumer disconnects without acking an event, that event will be replayed on reconnect.

---

### POST /events/{event_id}/ack

Acknowledge an event. Updates the consumer offset to the event's `seq` if `consumer_id` is provided. Returns 404 if the event does not exist or is already acked.

**Path parameter:**
- `event_id` (str, required): event ID to acknowledge

**Query parameters:**
- `consumer_id` (str, optional): consumer identifier; if present and event is newly acked, writes the event's `seq` as the consumer offset

**Response 200:** `{"event_id": "...", "acked": true, "seq": <int>}` — `seq` is the event's sequence number (None if consumer_id was not provided)
**Response 404:** event not found or already acked.

**Offset behavior**: The offset is updated only when `consumer_id` is provided AND the event was newly acknowledged (not previously acked). If the event was already acked, the response returns 404 regardless of whether a consumer_id is provided.

**Deprecated alias**: `POST /ack?event_id=...&consumer_id=...` — same behavior but uses query parameters instead of path parameter. The canonical path is `POST /events/{event_id}/ack`.

---

### GET /health

Returns component health. HTTP 200 for `ok`, HTTP 503 for `degraded`/`unhealthy`.

```json
{"status": "ok|degraded", "db": "ok|unavailable", "dlq_task": "running|stopped", "active_subscribers": 0, "max_queue_depth": 0, "slow_consumers": 0, "degraded_reasons": []}
```

`status` is `"ok"` only when all components are healthy. Broker metrics `active_subscribers`, `max_queue_depth`, and `slow_consumers` reflect the in-process EventBroker state. `degraded_reasons` lists specific failure reasons (e.g., `db_unavailable`, `dlq_task_stopped`, `broker_queue_backlog_high`, `slow_consumers_detected`).

---

### GET /dlq

List events in the dead-letter queue (events with `dlq_at IS NOT NULL`).

**Response:** `[{seq, event_id, topic, producer, published_at, delivery_failure_count, dlq_at}, ...]`

---

### POST /dlq/{event_id}/requeue

Move an event out of the DLQ back to normal delivery. Increments `dlq_requeue_count` by 1 (does NOT reset `delivery_failure_count`). If `delivery_failure_count >= max_retry` after re-promotion logic runs, the event re-enters the DLQ on the next DLQ loop tick.

**Path parameter:**
- `event_id` (str, required): event ID to requeue

**Response 200:** `{"event_id": "...", "requeued": true}` — may include `"dlq_imminent": true` if `delivery_failure_count >= max_retry` after requeue
**Response 404:** event not found or not in DLQ.

**Edge cases:**
- Event not in DLQ (dlq_at IS NULL): returns 404
- Repeated requeue of same event: dlq_requeue_count increments each time
- Event at delivery_failure_count >= max_retry: requeue succeeds but next DLQ loop tick will re-promote

---

## DLQ background loop

At startup, `_dlq_loop()` runs as an asyncio task, polling every 60 seconds. Events with `delivery_failure_count >= max_retry AND dlq_at IS NULL` are promoted to the DLQ (JSONL written atomically, `dlq_at` set in SQLite).

## Failure behavior summary

| Failure | Behavior |
|---|---|
| JSON Schema validation failure on publish | 422, event not stored |
| JSONL append failure after SQLite commit | 200 returned, WARNING logged, event in SQLite |
| DB unavailable on `/health` | `{"status": "degraded", "db": "unavailable", ...}` |
| DLQ task stopped on `/health` | `{"status": "degraded", ..., "dlq_task": "stopped"}` |
| Unknown `event_id` on requeue | 404 |
