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

Long-poll SSE subscription. Polls the DB every `poll_interval_ms` ms and streams new events.

**Query parameters:**
- `topic` (list[str], default all): filter by topic
- `since_seq` (int, default 0): starting sequence; overridden by saved offset if `consumer_id` is set and `since_seq == 0`
- `consumer_id` (str, optional): consumer identifier for offset persistence

On disconnect, the current `seq` is written to the offset file via `write_offset()`. A mid-stream checkpoint is also written every `offset_checkpoint_interval` delivered events.

---

### GET /health

Returns component health. Always HTTP 200.

```json
{"status": "ok|degraded", "db": "ok|unavailable", "dlq_task": "running|stopped"}
```

`status` is `"ok"` only when both `db` and `dlq_task` are healthy.

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
