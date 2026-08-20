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
  - 06_eventbus_02_02_subscribe-ack.md
  - 06_eventbus_02_03_nack-health-dlq.md
source:
  - 06_eventbus_02_01_publish-replay.md
---

# Event Bus: Publish and Replay Endpoints

## POST /publish

Publishes an event. Idempotent: duplicate `event_id`s are silently ignored.

**Reason for idempotency**: Even if re-published with the same `event_id`, existing rows are not updated due to the SQLite UNIQUE constraint, ensuring consumers do not receive the same event twice. This is an intentional design, not a bug.

**Request Body**: Validated against the `event_envelope.json` JSON Schema. Required fields are `event_id` (UUID v4), `topic` (1–255 characters), `payload` (object), `producer` (1–255 characters), and `published_at` (ISO-8601). `schema_version` is optional and defaults to `"1.0"`. Additional properties are not allowed.

**Response**: On success, returns `{event_id, seq}`. A 422 error indicates a JSON Schema validation error.

**JSONL Append Failure**: If writing to the JSONL archive fails, the event is still committed to SQLite and a 200 status is returned. A WARNING will be recorded in the logs.

---

## GET /replay

Replays past events. Returns events where `seq > since_seq`. Supports pagination when `format=json`.

**Query Parameters:** `since_seq` (>=0), `limit` (1-1000, default 100), `offset` (>=0), `format` (sse/json, default sse).

**Response (`format=json`):** A pagination object containing `{total, limit, offset, items}`. `total` is the total count regardless of `limit`/`offset`.

**Response (`format=sse`):** Each event is output as a `data: {...}` line. The SSE format does not support paginated incremental consumption. The stream terminates after `limit` items are output.

**Error Response:** 422 — if parameter values are invalid.

## Related Documents

- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_02_03_nack-health-dlq.md`
