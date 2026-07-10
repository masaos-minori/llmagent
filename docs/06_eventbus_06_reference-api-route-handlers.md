---
title: "Event Bus: Reference API — Route Handlers"
category: eventbus
tags:
  - event-bus
  - api-reference
  - route-handlers
  - publish-route
  - ack-route
  - dlq-route
  - replay-route
  - subscribe-route
  - health-route
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_06_reference-api-core-modules.md
  - 06_eventbus_06_reference-api-broker-and-offsets.md
source:
  - 06_eventbus_06_reference_api.md
---

# Event Bus: Reference API — Route Handlers

## scripts/eventbus/publish_route.py

| Function | Signature | Description |
|---|---|---|
| `publish` | `(request: Request) -> dict[str, Any]` | POST /publish handler; validates JSON Schema, inserts event to DB, appends to JSONL archive, notifies EventBroker |

### Response

| Field | Type | Description |
|---|---|---|
| `event_id` | str | The event ID |
| `seq` | int | The assigned sequence number |

### Error Responses

| Status Code | Detail | Condition |
|---|---|---|
| 422 | JSON Schema validation error message | Invalid payload |
| 500 | OSError warning logged, event still committed | JSONL append failure |

---

## scripts/eventbus/ack_route.py

| Function | Signature | Description |
|---|---|---|
| `ack` | `(request: Request, event_id: str = Query(default=""), consumer_id: str = Query(default="")) -> dict[str, Any]` | POST /ack handler (legacy alias) |
| `ack_event` | `(request: Request, event_id: str, consumer_id: str = Query(default="")) -> dict[str, Any]` | POST /events/{event_id}/ack handler (canonical path) |
| `nack` | `(request: Request, event_id: str = Query(default="")) -> dict[str, Any]` | POST /nack handler; increments failure count, promotes to DLQ if >= max_retry |

### Response (ack)

| Field | Type | Description |
|---|---|---|
| `event_id` | str | The event ID |
| `acked` | bool | Always True for successful ack |
| `seq` | int \| None | Sequence number (only if newly acked, not already acked) |
| `already_acked` | bool | Present only if event was previously acked |

### Response (nack)

| Field | Type | Description |
|---|---|---|
| `event_id` | str | The event ID |
| `delivery_failure_count` | int | Current delivery failure count |
| `dlq_promoted` | bool \| None | Present only if event was promoted to DLQ |

### Error Responses (nack)

| Status Code | Detail | Condition |
|---|---|---|
| 404 | "event not found" | Event does not exist or was already acked |
| 400 | "event_id is required" | Missing event_id query parameter |

### Internal function

| Function | Signature | Description |
|---|---|---|
| `do_ack` | `(db, cfg, event_id, consumer_id) -> dict[str, Any]` | Common ack logic shared by /ack and /events/{event_id}/ack; writes offset file on newly acked events |

---

## scripts/eventbus/dlq_route.py

| Function | Signature | Description |
|---|---|---|
| `dlq_list` | `(request: Request, limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0)) -> dict[str, Any]` | GET /dlq handler; returns paginated DLQ event list |
| `dlq_requeue` | `(request: Request, event_id: str) -> dict[str, Any]` | POST /dlq/{event_id}/requeue handler; requeues a DLQ event back to normal delivery |

### Response (dlq_list)

| Field | Type | Description |
|---|---|---|
| `total` | int | Total number of DLQ events |
| `limit` | int | Requested limit |
| `offset` | int | Requested offset |
| `items` | list[dict] | Paginated list of DLQ event dicts |

### Response (dlq_requeue)

| Field | Type | Description |
|---|---|---|
| `event_id` | str | The event ID |
| `requeued` | bool | Always True for successful requeue |
| `dlq_imminent` | bool \| None | Present only if failure_count >= max_retry (event may be immediately re-DLQ'd) |

### Error Responses (dlq_requeue)

| Status Code | Detail | Condition |
|---|---|---|
| 404 | "event not found" | Event does not exist |
| 409 | "event is not in DLQ" | Event exists but dlq_at IS NULL (already requeued or acked) |

---

## scripts/eventbus/replay_route.py

| Function | Signature | Description |
|---|---|---|
| `replay` | `(request: Request, since_seq: int = Query(default=0), fmt: str = Query(default="json"), limit: int = Query(default=100), offset: int = Query(default=0)) -> StreamingResponse \| dict[str, Any]` | GET /replay handler; streams events via SSE or returns paginated JSON |

### Internal functions

| Function | Signature | Description |
|---|---|---|
| `row_to_dict` | `(row: Any) -> dict[str, Any]` | Convert SQLite row to serializable dict |
| `count_events_since` | `(conn: Any, since_seq: int) -> int` | Count events with seq > since_seq |

---

## scripts/eventbus/subscribe_route.py

| Function | Signature | Description |
|---|---|---|
| `subscribe` | `(request: Request, topic: str = Query(default=""), since_seq: int = Query(default=0), consumer_id: str = Query(default="")) -> StreamingResponse` | GET /subscribe handler; hybrid replay+push model with SSE streaming |

### Internal functions

| Function | Signature | Description |
|---|---|---|
| `get_config` | `(request: Request) -> EventBusConfig` | Extract config from request state |
| `get_broker` | `(request: Request) -> EventBroker` | Extract EventBroker from request state |
| `row_to_dict` | `(row: Any) -> dict[str, Any]` | Convert SQLite row to serializable dict |

---

## scripts/eventbus/health_route.py

| Function | Signature | Description |
|---|---|---|
| `health_check` | `(request: Request) -> JSONResponse` | GET /health handler; returns component health status |

### Internal functions

| Function | Signature | Description |
|---|---|---|
| `get_broker` | `(request: Request) -> EventBroker` | Extract EventBroker from request state |
| `get_config` | `(request: Request) -> EventBusConfig` | Extract config from request state |

---

## scripts/eventbus/app.py — HTTP Endpoints

### Active endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/publish` | POST | Publish an event (idempotent by event_id) |
| `/replay` | GET | Replay past events (SSE stream or JSON paginated response; supports limit/offset pagination for JSON) |
| `/subscribe` | GET | Stream events via hybrid replay+push model |
| `/health` | GET | Component health check |
| `/dlq` | GET | List DLQ events |
| `/dlq/{event_id}/requeue` | POST | Requeue a DLQ event back to normal delivery |
| `/events/{event_id}/ack` | POST | Acknowledge an event (canonical ack path) |
| `/nack` | POST | Negative acknowledge an event |

### Deprecated endpoints

> **Deprecated**: The following endpoint is a compatibility alias and may be removed in a future version. Use the canonical endpoint instead.

| Endpoint | Method | Description |
|---|---|---|
| `/ack` | POST | Legacy alias for `POST /events/{event_id}/ack` (uses query params instead of path param) |

## Related Documents

- `06_eventbus_06_reference-api-core-modules.md`
- `06_eventbus_06_reference-api-broker-and-offsets.md`

## Keywords

event-bus
api-reference
route-handlers
publish-route
ack-route
dlq-route
replay-route
subscribe-route
health-route
