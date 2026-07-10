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
  - 06_eventbus_02_publish-replay.md
  - 06_eventbus_02_nack-health-dlq.md
source:
  - 06_eventbus_02_publish-replay.md
---

# Event Bus: Subscribe and Ack Endpoints

## GET /subscribe

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

## POST /events/{event_id}/ack [canonical]

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

**Note (2026-07-10):** `POST /ack` (the query-parameter compatibility alias) was removed. Use `POST /events/{event_id}/ack` exclusively.

## Related Documents

- `06_eventbus_02_publish-replay.md`
- `06_eventbus_02_nack-health-dlq.md`

## Keywords

event-bus
http-api
subscribe
ack
nack
sse
streaming
consumer-offset
idempotent
