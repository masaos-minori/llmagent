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
    poll_interval_ms: int = 500
    offset_checkpoint_interval: int = 10
```

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

---

## scripts/eventbus/dlq.py

| Function | Signature | Description |
|---|---|---|
| `promote_to_dlq` | `(db, deadletter_dir, max_retry) -> int` | Promote eligible events to DLQ; returns count promoted |
| `_atomic_write` | `(deadletter_dir, event_id, record) -> None` | Atomic JSON write via tempfile + os.replace |

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
