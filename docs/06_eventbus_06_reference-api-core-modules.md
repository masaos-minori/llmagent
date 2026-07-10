---
title: "Event Bus: Reference API — Core Modules"
category: eventbus
tags:
  - event-bus
  - api-reference
  - core-modules
  - app-py
  - config-py
  - db-py
  - dlq-py
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_06_reference-api-route-handlers.md
  - 06_eventbus_06_reference-api-broker-and-offsets.md
source:
  - 06_eventbus_06_reference-api-core-modules.md
---

# Event Bus: Reference API — Core Modules

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

**Note (2026-07-10)**: `poll_interval_ms` and `offset_checkpoint_interval` were removed. `load_config()` raises `ValueError` if either key is present in the TOML file.

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

## Related Documents

- `06_eventbus_06_reference-api-route-handlers.md`
- `06_eventbus_06_reference-api-broker-and-offsets.md`

## Keywords

event-bus
api-reference
core-modules
app-py
config-py
db-py
dlq-py
