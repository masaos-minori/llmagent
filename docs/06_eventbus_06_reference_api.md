# Event Bus: Reference API

## scripts/eventbus/app.py

Module-level variables are set in lifespan.

Internal functions:

| Function | Signature | Description |
|---|---|---|
| Convert SQLite row to serializable dict | `(row: sqlite3.Row) -> dict` |
| Fetch seq for existing event_id | `(event_id: str) -> int` |
| Append event to JSONL archive; raises OSError on failure | `(body: dict, seq: int) -> None` |

---

## scripts/eventbus/config.py

```python
class EventBusConfig:
    port: int
    db_path: str
    storage_dir: str
    offsets_dir: str
    deadletter_dir: str
    max_retry: int
    host: str = "127.0.0.1"  # HTTP listen address; validated at startup
    allow_public_bind: bool = False  # Override: allow binding to public/wildcard addresses
```

#### Deprecated fields (no-op, will be removed)

| Field | Type | Default | Description |
|---|---|---|---|
| `poll_interval_ms` | int | 500 | No-op; push-mode delivery via EventBroker |
| `offset_checkpoint_interval` | int | 10 | No-op; ack-only model in place |

| Function | Signature | Description |
|---|---|---|
| `get_config_path` | `() -> str` | Returns `EVENTBUS_CONFIG_PATH` env var or default |
| `get_schema_path` | `() -> str` | Returns `EVENTBUS_SCHEMA_PATH` env var or default |
| `load_config` | `(path: Path \| str \| None) -> EventBusConfig` | Load TOML config; uses `get_config_path()` if path is None |

#### Internal function

| Function | Signature | Description |
|---|---|---|
| `is_public_host` | `(host: str) -> bool` | Returns True if host is a wildcard (`0.0.0.0`, `::`) or cannot be parsed as an IP address (hostname); raises no exception |

---

## scripts/eventbus/db.py

| Function | Signature | Description |
|---|---|---|
| `open_db` | `(db_path: str) -> sqlite3.Connection` | Open SQLite with WAL, foreign keys, and schema init; logs and re-raises on error |

### DB Schema

DDL is defined in `scripts/eventbus/schema.sql`. The `events` table has the following columns:

| Column | Type | Constraints | Description |
|---|---|---|---|
| `seq` | INTEGER | PRIMARY KEY AUTOINCREMENT | Auto-increment sequence number |
| `event_id` | TEXT | NOT NULL UNIQUE | Client-supplied UUID; prevents duplicates |
| `topic` | TEXT | NOT NULL | Event topic string (1–255 characters) |
| `payload` | TEXT | NOT NULL | Serialized JSON string of the event payload |
| `producer` | TEXT | NOT NULL | Producer identifier string (1–255 characters) |
| `published_at` | TEXT | NOT NULL | ISO-8601 timestamp when event was published |
| `acked_at` | TEXT | — | Set during ack (idempotent) |
| `retry_count` | INTEGER | NOT NULL DEFAULT 0 | Deprecated; use delivery_failure_count |
| `delivery_failure_count` | INTEGER | NOT NULL DEFAULT 0 | Incremented on nack; triggers DLQ promotion at `>= max_retry` |
| `dlq_requeue_count` | INTEGER | NOT NULL DEFAULT 0 | Incremented on DLQ requeue |
| `dlq_at` | TEXT | — | Set when event is promoted to DLQ |

Indexes: `idx_events_topic` (topic), `idx_events_seq` (seq), `idx_events_dlq_at` (dlq_at), `idx_events_dlq_seq` (dlq_at, seq)

---

## scripts/eventbus/dlq.py

| Function | Signature | Description |
|---|---|---|
| `promote_to_dlq` | `(db, deadletter_dir, max_retry) -> int` | Promote eligible events to DLQ; returns count promoted |
| `atomic_write` | `(deadletter_dir, event_id, record) -> None` | Atomic JSON write via tempfile + os.replace |

---

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

---

## scripts/eventbus/broker.py

| Class | Description |
|---|---|
| `_Subscriber` | Internal dataclass: `queue: asyncio.Queue[dict \| None]`, `topics: list[str]` (empty = all topics) |
| `EventBroker` | In-memory pub/sub broker with topic-aware fan-out |

### EventBroker methods

| Method | Signature | Description |
|---|---|---|
| `subscribe` | `(topics: list[str]) -> _Subscriber` | Register a new subscriber; topics=[] means all topics |
| `unsubscribe` | `(sub: _Subscriber) -> None` | Remove subscriber from the registry; idempotent |
| `publish` | `(event: dict[str, Any]) -> int` | Fan out event to matching subscribers; returns delivery count |
| `shutdown` | `() -> None` | Send None sentinel to all subscribers to unblock their queue.get() calls |
| `subscriber_count` | `() -> int` | Return number of active subscribers |
| `max_queue_depth` | `() -> int` | Return max queue depth across all subscribers |
| `slow_consumer_count` | `() -> int` | Return count of subscribers with queue depth >= 100 |

---

## scripts/eventbus/offsets.py

| Function | Signature | Description |
|---|---|---|
| `read_offset` | `(offsets_dir, consumer_id) -> int` | Read saved offset; returns 0 if not found |
| `write_offset` | `(offsets_dir, consumer_id, seq) -> None` | Write offset to file; creates directory if needed |
