---
title: "Event Bus: Reference API"
area: eventbus
tags:
  - event-bus
  - api-reference
  - core-modules
  - app-py
  - config-py
  - db-py
  - dlq-py
  - route-handlers
  - publish-route
  - ack-route
  - dlq-route
  - replay-route
  - subscribe-route
  - health-route
  - broker
  - offsets
  - eventbroker
  - subscriber
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_operations.md
---

# Event Bus: Reference API

Detailed API specifications (module responsibilities, route handlers, and internal
classes) for verification purposes. Refer to `06_eventbus_02_operations.md` for the
endpoint contracts (request/response shapes, status codes) — this document covers the
implementing modules, not the HTTP-level behavior.

## Core Modules

### scripts/eventbus/app.py

Application state and CLI entry point. See code for details.

### scripts/eventbus/config.py

`EventBusConfig` class and configuration loading functions. See code for details.

**New fields (REQ-001):** `sse_heartbeat_interval` (float, default 30.0) — interval in seconds between SSE comment heartbeats during live delivery phase. Optional TOML key; absent from TOML uses default. Validated as float type when present.

**New operational thresholds (REQ-001, REQ-002):** `slow_consumer_threshold` (int, default 100), `queue_backlog_threshold` (int, default 1000), `dlq_requeue_threshold` (int, default 500). All optional TOML keys; defaults used when absent. Relationship validation enforced: `slow_consumer_threshold < queue_backlog_threshold`.

### scripts/eventbus/db.py

DB connection and schema initialization. See code for details.

### scripts/eventbus/dlq.py

DLQ operation functions. See code for details.

### scripts/eventbus/route_helpers.py

Common route helpers. See code for details.

---

## Route Handlers

### scripts/eventbus/publish_route.py

`publish(request)`: `POST /publish`. JSON Schema validation → DB insertion → JSONL append → Broker notification. JSONL append failure does not surface as an HTTP error (Warning log + 200).

### scripts/eventbus/ack_route.py

`ack_event(request, event_id, consumer_id)`: `POST /events/{event_id}/ack`. `nack(request, event_id)`: `POST /nack`. Increments failure count; promotes to DLQ if `>= max_retry`.

### scripts/eventbus/dlq_route.py

`dlq_list(request, limit=100, offset=0)`: `GET /dlq`. `dlq_requeue(request, event_id)`: `POST /dlq/{event_id}/requeue`. If `failure_count >= max_retry`, it may be re-moved to the DLQ. See `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` for DLQ semantics.

### scripts/eventbus/replay_route.py

`replay(request, since_seq=0, fmt=sse, limit=100, offset=0)`: `GET /replay`. SSE stream or paginated JSON. See `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` for replay semantics.

**Format parameter:** Accepts only `sse` or `json`. Unsupported values return HTTP 422. Default is `sse`.

**Snapshot consistency:** When `fmt=json`, both `total` and `items` represent one internally consistent database snapshot — they are fetched under a single `run_with_db_lock()` acquisition, preventing interleaving with concurrent `/publish` calls.

**Paging behavior:** When `offset` exceeds available results, the response returns an empty `items` array with `total` reflecting the actual count of matching events.

**SSE event IDs:** Each SSE frame includes `id:<seq>` field where `seq` is the event's sequence number, enabling `EventSource`-based clients to auto-reconnect after interruption.

### scripts/eventbus/subscribe_route.py

`subscribe(request, topic=[], since_seq=0, consumer_id="")`: `GET /subscribe`. SSE streaming + replay+push. See `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` for delivery semantics, offset semantics, and backpressure behavior.

**SSE-standard features (REQ-001 through REQ-005):**
- Heartbeat: During live delivery phase, emits `: heartbeat\n\n` comments at `cfg.sse_heartbeat_interval` intervals to keep idle connections alive through proxies/LBs.
- Event IDs: Each event frame includes `id:<seq>` field where `seq` is the monotonic sequence number, enabling `EventSource`-based clients to auto-reconnect.
- Last-Event-ID: Client can send `Last-Event-ID` HTTP header with a sequence number to resume from that point. Precedence: `since_seq` query param > persisted consumer offset > `Last-Event-ID` header.
- Stale reconnect rejection: If `Last-Event-ID` exceeds current max seq in SQLite, returns HTTP 412 Precondition Failed.

For detailed delivery semantics (ordering guarantees, ACK/NACK rules, offset semantics, backpressure), see `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`.

### scripts/eventbus/health_route.py

`health_check(request)`: `GET /health`. See `06_eventbus_05_configuration-and-operations.md` for monitoring thresholds.

### HTTP Endpoints Summary

`/publish`(POST), `/replay`(GET), `/subscribe`(GET), `/health`(GET), `/dlq`(GET), `/dlq/{id}/requeue`(POST), `/events/{id}/ack`(POST), `/nack`(POST).

---

## Broker and Offsets

### scripts/eventbus/broker.py

`_Subscriber`: Internal data structure holding the queue, topic list, and disconnect signal. `EventBroker`: In-memory pub/sub broker with topic-based fanout.

Methods: `subscribe(topics→_Subscriber, consumer_id=str)`, `unsubscribe(sub→None)`, `publish(event→int)`, `shutdown()`, `subscriber_count()→int`, `max_queue_depth()→int`, `slow_consumer_count()→int`, `overflow_disconnect_count()→int`, `duplicate_rejection_count()→int`.

### scripts/eventbus/offsets.py

`read_offset(offsets_dir, consumer_id)→int`: Reads saved offset (returns 0 if not found). `write_offset(offsets_dir, consumer_id, seq)→None`: Only writes to file if `seq` is greater than the current committed offset. Skips and logs a warning if `seq <= current` (ensures monotonicity).

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_operations.md`
- `06_eventbus_03_persistence_schema_and_replay.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

## Module Class/Function Reference (auto-generated)

<!-- AUTO-GENERATED: gen_eventbus_reference.py class-function-reference -->
Generated from `scripts/eventbus/*.py` top-level public classes and functions. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type eventbus` to refresh.

| File | Class/Function | Signature | Summary |
|---|---|---|---|
| `scripts/eventbus/ack_route.py` | `ack_event` | `async def ack_event(request, event_id, consumer_id, _principal, _identity) -> dict[str, Any]` | Acknowledge an event as successfully processed by a consumer. |
|  | `nack` | `async def nack(request, event_id, consumer_id, _principal, _identity) -> dict[str, Any]` | Negatively acknowledge an event, triggering retry logic. |
| `scripts/eventbus/app.py` | `lifespan` | `async def lifespan(app) -> AsyncGenerator[None]` | FastAPI lifespan: initialize broker/db/lifecycle on startup; clean up on shutdown. |
|  | `health` | `async def health(request) -> JSONResponse` | Health check endpoint for the event bus service. |
|  | `publish` | `async def publish(request) -> dict[str, Any]` | Publish a new event to the event bus. |
|  | `replay` | `async def replay(request, since_seq, fmt, limit, offset, _principal) -> Any` | Replay events from a given sequence number via SSE or JSON. |
|  | `subscribe` | `async def subscribe(request, topic, since_seq, consumer_id, _principal, _identity) -> Any` | Subscribe to events matching the specified topics via SSE. |
|  | `dlq_list` | `async def dlq_list(request, limit, offset, _principal) -> dict[str, Any]` | List dead-letter queue entries with pagination support. |
|  | `dlq_requeue` | `async def dlq_requeue(request, event_id, _principal) -> dict[str, Any]` | Requeue a dead-letter queue entry back into the active queue. |
|  | `ack_event` | `async def ack_event(request, event_id, consumer_id, _principal, _identity) -> dict[str, Any]` | Acknowledge an event as successfully processed by a consumer. |
|  | `nack` | `async def nack(request, event_id, consumer_id, _principal, _identity) -> dict[str, Any]` | Negatively acknowledge an event, triggering retry logic. |
| `scripts/eventbus/audit.py` | `AuditRecord` | `class AuditRecord` | Structured payload for one EventBus audit record. |
|  | `log_auth_failure` | `def log_auth_failure(consumer_id, request_id, route, target, error_type, detail) -> None` | Emit one JSON-lines audit record for an authorization failure. |
|  | `log_privileged_action` | `def log_privileged_action(consumer_id, request_id, route, target, detail) -> None` | Emit one JSON-lines audit record for a privileged action. |
| `scripts/eventbus/auth.py` | `Role` | `class Role` | — |
|  | `Principal` | `class Principal` | Authenticated identity carrying roles, consumer IDs, topics, and token fingerprint. |
|  | `unauthorized_response` | `def unauthorized_response(detail) -> JSONResponse` | Return a standardized HTTP 401 Unauthorized response. |
|  | `get_auth_token` | `def get_auth_token(config) -> str` | Return the auth_token from EventBusConfig, or raise ValueError if missing. |
|  | `resolve_principal` | `async def resolve_principal(request, credentials) -> Principal` | Resolve a bearer token to a Principal, or raise 401. |
|  | `require_role` | `def require_role(role)` | FastAPI dependency factory: verify caller's principal has the required role. |
|  | `require_consumer_identity` | `async def require_consumer_identity(request, consumer_id, topics, principal) -> Principal` | FastAPI dependency: verify caller is authorized to use the given consumer_id and topics. |
|  | `attach_auth_middleware` | `def attach_auth_middleware(app) -> None` | Register X-Request-Id middleware on a FastAPI app. |
| `scripts/eventbus/broker.py` | `ConsumerAlreadyConnectedError` | `class ConsumerAlreadyConnectedError` | Raised when a second connection attempts the same non-empty consumer_id. |
|  | `EventBroker` | `class EventBroker` | In-memory pub/sub broker with per-subscriber queues and topic filtering. |
| `scripts/eventbus/config.py` | `get_config_path` | `def get_config_path() -> Path` | Return the path to the Event Bus TOML configuration file. |
|  | `get_schema_path` | `def get_schema_path() -> Path` | Return the path to the Event Envelope JSON schema file. |
|  | `EventBusConfig` | `class EventBusConfig` | Immutable configuration for the Event Bus service. |
|  | `load_config` | `def load_config(path) -> EventBusConfig` | Load and validate the EventBus TOML configuration file. Callers must always pass get_config_path()'s return value — this function does not itself restrict which path is read; see tests/eventbus/test_eventbus_config.py for the call-site regression test that locks this invariant. |
| `scripts/eventbus/db.py` | `get_db_lock` | `def get_db_lock() -> threading.Lock` | Return the lock that must be held for all DB operations. |
|  | `open_db` | `def open_db(db_path) -> sqlite3.Connection` | Return a shared SQLite connection for the Event Bus. |
|  | `ack_event` | `def ack_event(conn, event_id, now) -> tuple[bool, bool]` | Set acked_at on an event. Idempotent — will not overwrite existing ack. |
|  | `nack_event` | `def nack_event(conn, event_id, consumer_id) -> tuple[int, int]` | Increment delivery_failure_count and cycle_failure_count for an event. |
|  | `ack_event_for_consumer` | `def ack_event_for_consumer(conn, event_id, consumer_id, now) -> tuple[bool, bool, int \| None]` | Acknowledge an event for a specific consumer atomically. |
|  | `get_consumer_offset` | `def get_consumer_offset(conn, consumer_id) -> int` | Return the last-committed sequence offset for a consumer, or 0 if none exists. |
|  | `check_db` | `def check_db(conn) -> bool` | Return True if the DB connection is usable. |
|  | `insert_event` | `def insert_event(conn, event_id, topic, payload_str, producer, published_at) -> tuple[int \| None, bool, str]` | INSERT OR IGNORE. Returns (seq, inserted, status). |
|  | `get_seq` | `def get_seq(conn, event_id) -> int` | Return the seq for an existing event_id; 0 if not found. |
|  | `fetch_events_since` | `def fetch_events_since(conn, since_seq, topics, limit, offset) -> list[sqlite3.Row]` | Return events with seq > since_seq, optionally filtered by topics. |
|  | `fetch_dlq` | `def fetch_dlq(conn, limit, offset) -> list[sqlite3.Row]` | Return events currently in the DLQ (dlq_at IS NOT NULL). |
|  | `count_dlq` | `def count_dlq(conn) -> int` | Return the number of events currently in the DLQ. |
|  | `requeue_event` | `def requeue_event(conn, event_id) -> bool` | Increment dlq_requeue_count and clear dlq_at. Returns True if the event was found in DLQ. |
|  | `redeliver_event` | `def redeliver_event(conn, event_id, now) -> tuple[bool, str \| None]` | Redeliver a dead-lettered event by inserting a new row with lineage. |
|  | `migrate_legacy_offsets` | `def migrate_legacy_offsets(conn, offsets_dir) -> list[str]` | Migrate legacy file-based offsets into the consumer_offsets table. |
| `scripts/eventbus/dlq.py` | `DlqEventRecord` | `class DlqEventRecord` | A single event record written to the dead-letter queue as a JSON file on disk. |
|  | `sweep_orphans` | `def sweep_orphans(db, deadletter_dir, max_retry) -> int` | Sweep events that reached retry limit but were not promoted inline. |
|  | `promote_single` | `def promote_single(db, deadletter_dir, event_id) -> bool` | Promote one event to DLQ immediately (inline on nack threshold). |
|  | `archive_dlq_record` | `def archive_dlq_record(deadletter_dir, event_id) -> bool` | Move {deadletter_dir}/{event_id}.json to {deadletter_dir}/requeued/{event_id}_{timestamp}.json. |
| `scripts/eventbus/dlq_route.py` | `dlq_list` | `async def dlq_list(request, limit, offset) -> dict[str, Any]` | List dead-letter queue entries with pagination support. |
|  | `dlq_requeue` | `async def dlq_requeue(request, event_id) -> dict[str, Any]` | Requeue a dead-letter queue entry back into the active event queue. |
| `scripts/eventbus/health_route.py` | `health_check` | `async def health_check(request) -> JSONResponse` | Return DB/broker/DLQ task health status as a JSON response. |
| `scripts/eventbus/json_utils.py` | `dumps` | `def dumps(obj, option) -> str` | — |
|  | `now_iso` | `def now_iso() -> str` | — |
| `scripts/eventbus/offsets.py` | `CorruptOffsetError` | `class CorruptOffsetError` | Raised when offset file content is corrupted. |
|  | `read_offset` | `def read_offset(offsets_dir, consumer_id) -> int` | Read the last committed sequence offset for a consumer from disk. |
|  | `write_offset` | `def write_offset(offsets_dir, consumer_id, seq) -> None` | Write the current sequence offset for a consumer to disk. |
| `scripts/eventbus/publish_route.py` | `publish` | `async def publish(request) -> dict[str, Any]` | Publish an event after validating its envelope against the configured schema. |
| `scripts/eventbus/replay_route.py` | `replay` | `async def replay(request, since_seq, fmt, limit, offset) -> Any` | Replay events from a given sequence number via SSE or JSON response. |
| `scripts/eventbus/route_helpers.py` | `get_histogram_avg` | `def get_histogram_avg(hist) -> float` | Return the average observation for a Histogram via the public API. |
|  | `get_counter_value` | `def get_counter_value(counter) -> int` | Return the current value of a Counter via the public API. |
|  | `get_db` | `def get_db(request) -> Any` | Return the app state DB connection or raise RuntimeError. |
|  | `get_config` | `def get_config(request) -> Any` | Return the app state config or raise RuntimeError. |
|  | `get_broker` | `def get_broker(request) -> 'EventBroker'` | Return the app state broker or raise RuntimeError. |
|  | `app_get_db` | `def app_get_db(app) -> Any` | Return app.state.db or raise RuntimeError. |
|  | `app_get_config` | `def app_get_config(app) -> Any` | Return app.state.config or raise RuntimeError. |
|  | `app_get_broker` | `def app_get_broker(app) -> 'EventBroker'` | Return app.state.broker or raise RuntimeError. |
|  | `run_with_db_lock` | `async def run_with_db_lock(func) -> Any` | Execute a function inside get_db_lock() via asyncio.to_thread. |
| `scripts/eventbus/subscribe_route.py` | `subscribe` | `async def subscribe(request, topic, since_seq, consumer_id, _principal, _identity) -> Any` | Subscribe to events via SSE with optional topic filtering and offset recovery. |
<!-- END AUTO-GENERATED -->
