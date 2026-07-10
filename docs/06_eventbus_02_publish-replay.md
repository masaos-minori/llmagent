---
title: "Event Bus: Publish and Replay Endpoints"
category: eventbus
tags:
  - event-bus
  - http-api
  - publish
  - replay
  - sse
  - streaming
  - json-schema
  - pagination
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_subscribe-ack.md
  - 06_eventbus_02_nack-health-dlq.md
source:
  - 06_eventbus_02_publish-replay.md
---

# Event Bus: Publish and Replay Endpoints

## POST /publish

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

**Additional constraint**: No additional properties allowed (`additionalProperties: false`). Extra fields cause 422 validation failure.

**Response 200:**
```json
{"event_id": "uuid-string", "seq": 42}
```

**Response 422:** JSON Schema validation failure.

**JSONL append failure**: If writing to the JSONL archive fails (e.g. disk full), the event is still committed to SQLite and 200 is returned. A WARNING is logged.

---

## GET /replay

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

## Related Documents

- `06_eventbus_02_subscribe-ack.md`
- `06_eventbus_02_nack-health-dlq.md`

## Keywords

event-bus
http-api
publish
replay
sse
streaming
json-schema
pagination
