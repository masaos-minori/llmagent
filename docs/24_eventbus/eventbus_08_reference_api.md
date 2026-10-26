---
title: "Event Bus: Reference API"
area: eventbus
class: Reference
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
  - eventbus_00_document-guide.md
  - eventbus_01_system-overview.md
  - eventbus_03_dlq_operations.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
  - eventbus_07_configuration-and-operations.md
---

# Event Bus: Reference API

Module-level reference for `scripts/eventbus/`. HTTP-level contracts (request/response shapes, status codes, authorization) are specified once in `eventbus_03_dlq_operations.md`, `eventbus_04_dlq_endpoint.md`, `eventbus_10_health_endpoint.md`, `eventbus_11_replay_endpoint.md` and `eventbus_12_ack_nack_endpoints.md`; this document does not restate them. The signature table below is generated from the source and is the authoritative symbol inventory.

## Module Responsibilities

- Route modules (`publish_route.py`, `subscribe_route.py`, `replay_route.py`, `ack_route.py`, `dlq_route.py`, `health_route.py`, `admin_route.py`) implement the HTTP endpoints; event, delivery and DLQ state changes are implemented in the repository modules (`event_repo.py`, `delivery_repo.py`, `dlq_repo.py`) and `dlq.py`.
- `broker.py` (`EventBroker`) is the in-memory live-delivery fan-out. It holds no durable state; SQLite is the replay source.
- `config.py` (`EventBusConfig`) validates configuration at startup, including the unconditional loopback-only bind rule. Configuration semantics are in `eventbus_07_configuration-and-operations.md`.

## Module Class/Function Reference (auto-generated)

<!-- AUTO-GENERATED: generate_reference_table.py eventbus-class-function-reference -->
Generated from `scripts/eventbus/*.py` top-level public classes and functions. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type eventbus` to refresh.

| File | Class/Function | Signature | Summary |
|---|---|---|---|
| `scripts/eventbus/ack_route.py` | `ack_event` | `async def ack_event(request, event_id, consumer_id, _principal, _identity) -> dict[str, Any]` | Acknowledge an event as successfully processed by a consumer. |
|  | `nack` | `async def nack(request, event_id, consumer_id, idempotency_key, _principal, _identity) -> dict[str, Any]` | Negatively acknowledge an event, triggering retry logic. |
| `scripts/eventbus/admin_route.py` | `update_topics_authorization` | `async def update_topics_authorization(request) -> dict[str, Any]` | Update `consumer_authorization`/`topic_authorization` at runtime and |
| `scripts/eventbus/app.py` | `lifespan` | `async def lifespan(app) -> AsyncGenerator[None]` | FastAPI lifespan: initialize broker/db/lifecycle on startup; clean up on shutdown. |
|  | `resolve_subscribe_identity` | `async def resolve_subscribe_identity(request, consumer_id, topic, principal) -> Principal` | — |
|  | `health` | `async def health(request, _principal) -> JSONResponse` | Health check endpoint for the event bus service. |
|  | `publish` | `async def publish(request, _principal) -> dict[str, Any]` | Publish a new event to the event bus. |
|  | `replay` | `async def replay(request, since_seq, fmt, limit, offset, _principal) -> Any` | Replay events from a given sequence number via SSE or JSON. |
|  | `subscribe` | `async def subscribe(request, topic, since_seq, consumer_id, _principal, _identity) -> Any` | Subscribe to events matching the specified topics via SSE. |
|  | `dlq_list` | `async def dlq_list(request, limit, offset, _principal) -> dict[str, Any]` | List dead-letter queue entries with pagination support. |
|  | `dlq_requeue` | `async def dlq_requeue(request, event_id, _principal) -> dict[str, Any]` | Requeue a dead-letter queue entry back into the active queue. |
|  | `ack_event` | `async def ack_event(request, event_id, consumer_id, _principal, _identity) -> dict[str, Any]` | Acknowledge an event as successfully processed by a consumer. |
|  | `nack` | `async def nack(request, event_id, consumer_id, idempotency_key, _principal, _identity) -> dict[str, Any]` | Negatively acknowledge an event, triggering retry logic. |
|  | `admin_topics_authorization` | `async def admin_topics_authorization(request, _principal) -> dict[str, Any]` | Update consumer_authorization/topic_authorization at runtime. |
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
|  | `load_config` | `def load_config(path) -> EventBusConfig` | Load and validate the EventBus TOML configuration file. |
| `scripts/eventbus/db_conn.py` | `get_db_lock` | `def get_db_lock() -> threading.Lock` | Return the lock that must be held for all DB operations. |
|  | `set_shutdown_flag` | `def set_shutdown_flag() -> None` | Mark shutdown as begun. |
|  | `is_shutting_down` | `def is_shutting_down() -> bool` | Return True once shutdown has begun. |
|  | `clear_shutdown_flag` | `def clear_shutdown_flag() -> None` | Reset the shutdown flag at the start of a fresh app lifecycle. |
|  | `bump_active_db_user` | `def bump_active_db_user() -> None` | Increment the count of live DB users (called by run_with_db_lock()). |
|  | `release_active_db_user` | `def release_active_db_user() -> None` | Decrement the count of live DB users after the locked critical section. |
|  | `open_db` | `def open_db(db_path) -> sqlite3.Connection` | Return a shared SQLite connection for the Event Bus. |
|  | `check_db` | `def check_db(conn) -> bool` | Return True if the DB connection is usable. |
| `scripts/eventbus/delivery_repo.py` | `NackResult` | `class NackResult` | Return value for nack_event(). |
|  | `nack_event` | `def nack_event(conn, event_id, consumer_id, last_nack_attempt) -> NackResult` | Record a per-consumer NACK failure for an event. |
|  | `ack_event_for_consumer` | `def ack_event_for_consumer(conn, event_id, consumer_id, now) -> tuple[bool, bool, int \| None]` | Acknowledge an event for a specific consumer atomically. |
|  | `get_consumer_offset` | `def get_consumer_offset(conn, consumer_id) -> int` | Return the last-committed sequence offset for a consumer, or 0 if none exists. |
|  | `get_resume_position` | `def get_resume_position(conn, consumer_id) -> int` | Compute the resume position for a reconnecting consumer. |
| `scripts/eventbus/dlq.py` | `DlqEventRecord` | `class DlqEventRecord` | A single event record written to the dead-letter queue as a JSON file on disk. |
|  | `is_promotable` | `def is_promotable(db, event_id, max_retry) -> bool` | Return True if the event is not yet in the DLQ and meets the promotion rule. |
|  | `sweep_orphans` | `def sweep_orphans(db, deadletter_dir, max_retry) -> int` | Sweep events that meet the promotion rule but were not promoted inline. |
|  | `promote_single` | `def promote_single(db, deadletter_dir, event_id, consumer_failure_count) -> bool` | Promote one event to DLQ immediately (inline on nack threshold). |
|  | `archive_dlq_record` | `def archive_dlq_record(deadletter_dir, event_id) -> bool` | Move {deadletter_dir}/{event_id}.json to {deadletter_dir}/requeued/{event_id}_{timestamp}.json. |
| `scripts/eventbus/dlq_repo.py` | `RequeueResult` | `class RequeueResult` | Typed result of a redeliver_event() call (replaces the (bool, str \| None) tuple). |
|  | `redeliver_event` | `def redeliver_event(conn, event_id, now) -> RequeueResult` | Redeliver a dead-lettered event by inserting a new row with lineage. |
| `scripts/eventbus/dlq_route.py` | `dlq_list` | `async def dlq_list(request, limit, offset) -> dict[str, Any]` | List dead-letter queue entries with pagination support (one snapshot). |
|  | `dlq_requeue` | `async def dlq_requeue(request, event_id) -> dict[str, Any]` | Requeue a dead-letter queue entry back into the active event queue. |
| `scripts/eventbus/event_repo.py` | `insert_event` | `def insert_event(conn, event_id, topic, payload_str, producer, published_at) -> tuple[int \| None, bool, str]` | INSERT OR IGNORE. Returns (seq, inserted, status). |
|  | `get_seq` | `def get_seq(conn, event_id) -> int` | Return the seq for an existing event_id; 0 if not found. |
|  | `fetch_events_since` | `def fetch_events_since(conn, since_seq, topics, limit, offset) -> list[sqlite3.Row]` | Return events with seq > since_seq, optionally filtered by topics. |
|  | `fetch_dlq` | `def fetch_dlq(conn, limit, offset) -> list[sqlite3.Row]` | Return events currently in the DLQ (dlq_at IS NOT NULL). |
|  | `count_dlq` | `def count_dlq(conn) -> int` | Return the number of events currently in the DLQ. |
| `scripts/eventbus/health_route.py` | `health_check` | `async def health_check(request) -> JSONResponse` | Return DB/broker/DLQ task health status as a JSON response. |
| `scripts/eventbus/json_utils.py` | `dumps` | `def dumps(obj, option) -> str` | — |
|  | `now_iso` | `def now_iso() -> str` | — |
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

## Keywords

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
