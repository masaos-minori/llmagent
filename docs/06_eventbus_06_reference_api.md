# Event Bus: Reference API

## scripts/eventbus/app.py

Module-level variables:

| Variable | Type | Description |
|---|---|---|
| `_ENVELOPE_SCHEMA_PATH` | `Path` | Path to JSON Schema; set from `get_schema_path()` at import time |
| `_cfg` | `EventBusConfig \| None` | Loaded config; set in lifespan |
| `_db` | `sqlite3.Connection \| None` | Shared SQLite connection; set in lifespan |
| `_envelope_schema` | `dict \| None` | Loaded JSON Schema; set in lifespan |
| `_dlq_task` | `asyncio.Task \| None` | DLQ background task; set in lifespan |

Internal functions:

| Function | Signature | Description |
|---|---|---|
| `_row_to_dict` | `(row: sqlite3.Row) -> dict` | Convert SQLite row to serializable dict |
| `_get_seq` | `(event_id: str) -> int` | Fetch seq for existing event_id |
| `_append_jsonl` | `(body: dict, seq: int) -> None` | Append event to JSONL archive; raises OSError on failure |

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
| `_atomic_write` | `(deadletter_dir, event_id, record) -> None` | Atomic JSON write via tempfile + os.replace |

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
