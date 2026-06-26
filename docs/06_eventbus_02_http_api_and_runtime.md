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

On disconnect, the current `seq` is written to the offset file via `write_offset()`.

---

### GET /health

Returns component health. Always HTTP 200.

```json
{"status": "ok|degraded", "db": "ok|unavailable", "dlq_task": "running|stopped", "active_subscribers": 0, "max_queue_depth": 0, "slow_consumers": 0, "degraded_reasons": []}
```

`status` is `"ok"` only when all components are healthy. Broker metrics `active_subscribers`, `max_queue_depth`, and `slow_consumers` reflect the in-process EventBroker state. `degraded_reasons` lists specific failure reasons (e.g., `db_unavailable`, `dlq_task_stopped`, `broker_queue_backlog_high`, `slow_consumers_detected`).

---

### GET /dlq

List events in the dead-letter queue (events with `dlq_at IS NOT NULL`).

**Response:** `[{seq, event_id, topic, producer, published_at, retry_count, dlq_at}, ...]`

---

### POST /dlq/{event_id}/requeue

Move an event out of the DLQ back to normal delivery. Increments `retry_count` by 1 (does NOT reset it). If `retry_count >= max_retry` after re-promotion logic runs, the event re-enters the DLQ on the next DLQ loop tick.

**Response 200:** `{"event_id": "...", "requeued": true}`  
**Response 404:** event not found.

---

## DLQ background loop

At startup, `_dlq_loop()` runs as an asyncio task, polling every 60 seconds. Events with `retry_count >= max_retry AND dlq_at IS NULL` are promoted to the DLQ (JSONL written atomically, `dlq_at` set in SQLite).

## Failure behavior summary

| Failure | Behavior |
|---|---|
| JSON Schema validation failure on publish | 422, event not stored |
| JSONL append failure after SQLite commit | 200 returned, WARNING logged, event in SQLite |
| DB unavailable on `/health` | `{"status": "degraded", "db": "unavailable", ...}` |
| DLQ task stopped on `/health` | `{"status": "degraded", ..., "dlq_task": "stopped"}` |
| Unknown `event_id` on requeue | 404 |
