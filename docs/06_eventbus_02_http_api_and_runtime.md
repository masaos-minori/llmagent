# Event Bus: HTTP API and Runtime

## Endpoints

### POST /publish

Publish an event. Idempotent: duplicate `event_id` is silently ignored.

**Request body** (validated against `event_envelope.json` JSON Schema):

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "topic": "topic.name",
  "payload": {},
  "producer": "producer-name",
  "published_at": "2026-06-24T00:00:00Z"
}
```

**Request body constraints:**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `event_id` | string (UUID v4) | Yes | Must match `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` |
| `topic` | string | Yes | minLength 1, maxLength 255 |
| `payload` | object | Yes | Must be an object (not string) |
| `producer` | string | Yes | minLength 1, maxLength 255 |
| `published_at` | string (date-time) | Yes | ISO-8601 date-time format |
| `schema_version` | string | No | Default "1.0" |

**Response 200:**
```json
{"event_id": "uuid-string", "seq": 42}
```

**Response 422:** JSON Schema validation failure.

**JSONL append failure**: If writing to the JSONL archive fails (e.g. disk full), the event is still committed to SQLite and 200 is returned. A WARNING is logged.

---

### GET /replay

Replay past events. Returns events with `seq > since_seq`. Supports pagination for `format=json`.

**Query parameters:**

| Parameter | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `since_seq` | int | 0 | >= 0 | Start sequence number (exclusive) — no upper bound validation |
| `limit` | int | 100 | >= 1, <= 1000 | Maximum number of events to return per page |
| `offset` | int | 0 | >= 0 | Number of events to skip for pagination |
| `format` | str | `sse` | `sse` or `json` | Response format: SSE stream or JSON paginated object |

**Response (`format=json`):** Paginated object with `total`, `limit`, `offset`, and `items` fields:
```json
{"total": 100, "limit": 50, "offset": 0, "items": [{seq, event_id, topic, payload, producer, published_at}, ...]}
```

- `total`: Total number of matching events (ignores limit/offset) — used to compute remaining pages
- `limit`: The requested limit value
- `offset`: The requested offset value
- `items`: Array of event objects (up to `limit` items); empty array if `offset >= total`

**Response (`format=sse`):** Each event is emitted as a SSE data line:
```
data: {"seq": 42, "event_id": "...", "topic": "...", "payload": {}, "producer": "...", "published_at": "..."}
```

**SSE pagination behavior**: SSE format applies SQL-level `LIMIT/OFFSET` but does **not** support paginatable incremental consumption. The stream terminates after emitting `limit` events and closes — there is no mechanism to continue the same stream with updated offset. For paginated consumption, use `format=json`.

**Error responses:**
- **422**: Invalid parameter values (limit < 1 or limit > 1000, offset < 0)

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

### POST /events/{event_id}/ack [canonical]

Acknowledge an event. Updates the consumer offset to the event's `seq` if `consumer_id` is provided. Idempotent — repeated acks return 200 with `already_acked: true`. Returns 404 only if the event does not exist.

**Path parameter:**
- `event_id` (str, required): event ID to acknowledge

**Query parameters:**
- `consumer_id` (str, optional): consumer identifier; if present and event is newly acked, writes the event's `seq` as the consumer offset

**Response 200 (newly acked):** `{"event_id": "...", "acked": true, "seq": <int>}` — `seq` is the event's sequence number (None if consumer_id was not provided)
**Response 200 (already acked):** `{"event_id": "...", "acked": true, "already_acked": true}` — no `seq` field
**Response 404:** event not found.

**Offset behavior**: The offset is updated only when `consumer_id` is provided AND the event was newly acknowledged (not previously acked). If the event was already acked, the response returns 200 with `already_acked: true` regardless of whether a consumer_id is provided.

**Monotonic offset note**: Offset advancement is NOT monotonically enforced. Acknowledging an older event (with a smaller `seq`) will move the consumer offset backward to that `seq`. Consumers should ensure they only ack events in order, or handle offset rollback on reconnect.

---

### POST /ack [deprecated]

> **Deprecated**: This endpoint is a compatibility alias for `POST /events/{event_id}/ack`. Use the canonical path instead. This endpoint may be removed in a future version.

Same behavior as `POST /events/{event_id}/ack` but uses query parameters instead of a path parameter.

**Query parameters:**
- `event_id` (str, required): event ID to acknowledge
- `consumer_id` (str, optional): consumer identifier; if present and event is newly acked, writes the event's `seq` as the consumer offset

**Response 200 (newly acked):** `{"event_id": "...", "acked": true, "seq": <int>}` — `seq` is the event's sequence number (None if consumer_id was not provided)
**Response 200 (already acked):** `{"event_id": "...", "acked": true, "already_acked": true}` — no `seq` field
**Response 404:** event not found.

**Monotonic offset note**: Offset advancement is NOT monotonically enforced. Acknowledging an older event (with a smaller `seq`) will move the consumer offset backward to that `seq`.

---

### POST /nack

Negative acknowledge an event. Increments `delivery_failure_count`. If `delivery_failure_count >= max_retry`, the event is promoted to the DLQ.

**Query parameters:**
- `event_id` (str, required): event ID to nack

**Response 200:** `{"event_id": "...", "delivery_failure_count": <int>}` — may include `"dlq_promoted": true` if the event was promoted to DLQ on this nack
**Response 404:** event not found.

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

**Query parameters:**
- `limit` (int, default: 100, min: 1, max: 1000): Maximum number of items to return
- `offset` (int, default: 0, min: 0): Number of items to skip for pagination

**Response:** paginated object with fields:
- `total` (int): Total number of DLQ events
- `limit` (int): The requested limit
- `offset` (int): The requested offset
- `items` ([{seq, event_id, topic, producer, published_at, delivery_failure_count, dlq_requeue_count, dlq_at}]): List of DLQ events for this page

- `delivery_failure_count`: Number of nacks since last successful ack
- `dlq_requeue_count`: Number of times this event was requeued (does not reset on requeue)

---

### POST /dlq/{event_id}/requeue

Move an event out of the DLQ back to normal delivery. Increments `dlq_requeue_count` by 1 (does NOT reset `delivery_failure_count`). If `delivery_failure_count >= max_retry` after re-promotion logic runs, the event re-enters the DLQ on the next DLQ loop tick.

**Path parameter:**
- `event_id` (str, required): event ID to requeue

**Response 200:** `{"event_id": "...", "requeued": true}` — may include `"dlq_imminent": true` if `delivery_failure_count >= max_retry` after requeue
**Response 409 Conflict:** event exists but is not in the DLQ (dlq_at IS NULL).
**Response 404:** event not found.

**Edge cases:**
- Event not in DLQ (dlq_at IS NULL): returns 409 Conflict
- Repeated requeue of same event: dlq_requeue_count increments each time
- Event at delivery_failure_count >= max_retry: requeue succeeds but next DLQ loop tick will re-promote

---

## DLQ background loop (safety sweep)

At startup, `_dlq_loop()` runs as an asyncio task, polling every 60 seconds. It queries for events with `delivery_failure_count >= max_retry AND dlq_at IS NULL` — these are events that reached the retry threshold but were not promoted inline (e.g., due to a race).

The loop uses an optimistic lock: only counts events where `dlq_at` is still NULL, preventing double-promotion. If the sweep finds orphans, it logs `"dlq_loop: swept %d orphan(s) missed by inline promotion"`. Non-zero sweep results may indicate an inline promotion issue.

Promotion actions are the same as inline: write JSONL file atomically, set `dlq_at` in SQLite.

## Failure behavior summary

| Failure | Behavior |
|---|---|
| JSON Schema validation failure on publish | 422, event not stored |
| JSONL append failure after SQLite commit | 200 returned, WARNING logged, event in SQLite |
| DB unavailable on `/health` | `{"status": "degraded", "db": "unavailable", ...}` |
| DLQ task stopped on `/health` | `{"status": "degraded", ..., "dlq_task": "stopped"}` |
| Unknown `event_id` on requeue | 404 |
| Event exists but not in DLQ on requeue | 409 Conflict |
