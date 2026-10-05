---
title: "Event Bus: Configuration and Operations"
area: eventbus
tags:
  - event-bus
  - configuration
  - environment-variables
  - config-fields
  - toml
  - bind-address
  - startup
  - security
  - public-bind
  - loopback
  - wildcard
  - health-check
  - http-status-codes
  - monitoring
  - degraded
  - consumer-id
  - offset-resume
  - reconnect
  - stability
  - delivery
  - verification
  - slow-consumer
  - reconnect-recovery
  - subscriber-count
  - dlq
  - dead-letter-queue
  - requeue
  - background-loop
  - sweep
related:
  - eventbus_00_document-guide.md
  - eventbus_01_system-overview.md
  - eventbus_03_dlq_operations.md
  - eventbus_07_persistence_schema_and_replay.md
  - eventbus_08_validation_status.md
---

# Event Bus: Configuration and Operations

## Configuration

Loaded from a TOML file (default path defined in `scripts/eventbus/config.py`).

### Environment Variables

- `EVENTBUS_CONFIG_PATH` — Path to the TOML file
- `EVENTBUS_SCHEMA_PATH` — Path to the event envelope JSON Schema

### Configuration Fields

Fields and defaults are defined in `scripts/eventbus/config.py::EventBusConfig`. This
covers connection/storage settings (`port`, `db_path`, `storage_dir`, `offsets_dir`,
`deadletter_dir`), retry/replay tuning (`max_retry`, `replay_batch_size`,
`subscriber_count`), and the fields listed individually below, each of which carries
additional constraints or operational notes not captured by the dataclass alone. See
that dataclass's `__post_init__()` for the exact validation rules enforced at startup,
and `docs/10_adr/ADR-013-eventbus-authentication-authorization.md` for the authorization
model the token fields below implement.

- `retained_event_count` — Number of events retained in SQLite for replay
- `publish_rate` — Maximum publish rate in events/sec before backpressure applies
- `host` — Listening address (must be a loopback address — see Bind Address below)
- `auth_token` — Required for all requests (startup fails if empty)
- `publisher_token` — Grants publish-role access when set (per-role alternative to the shared `auth_token`)
- `consumer_token` — Grants consume-role access when set
- `operator_token` — Grants operator-role access when set
- `monitoring_token` — Grants monitoring-role (health check) access when set
- `admin_token` — Grants admin-role access (`/admin/*`) when set
- `sse_heartbeat_interval` — SSE heartbeat interval in seconds
- `sse_idle_timeout` — Idle timeout in seconds after which a `/subscribe` connection that received no events is closed
- `consumer_authorization` — Optional `consumer_id` -> topics allowlist applied to the consumer-role token
- `topic_authorization` — Optional topic -> `consumer_id` allowlist applied to the consumer-role token
- `slow_consumer_threshold` — Queue depth at which a subscriber is considered slow
- `subscriber_queue_maxsize` — Per-subscriber queue capacity
- `backlog_health_threshold` — Max queue depth before health endpoint reports `broker_queue_backlog_high`

Validation for `port` and `max_retry` is performed in `EventBusConfig.__post_init__()`. Cross-field validation ensures `slow_consumer_threshold < subscriber_queue_maxsize` and `backlog_health_threshold <= subscriber_queue_maxsize`. Startup fails unless `auth_token` is configured; the per-role tokens above are optional additions — see `docs/10_adr/ADR-013-eventbus-authentication-authorization.md` for the authorization model these tokens implement.

### Unsupported Keys

Startup fails if the configuration file contains any key not defined in `EventBusConfig` (for example `poll_interval_ms` or `offset_checkpoint_interval`).

---

## Bind Address and Start Command

### Bind Address

Event Bus enforces loopback-only binding unconditionally — there is no
override. Binding to anything other than loopback is not permitted.

**Address Classification** (`_is_public_host()`, `scripts/eventbus/config.py`):
- Loopback (IPv4 and IPv6) — Allowed
- Everything else (private-LAN, wildcard, other public
  addresses, hostnames) — Raises `ValueError` at config-construction time

`EventBusConfig` also verifies the actual bound socket address matches
loopback immediately after startup (`_main()`'s post-start check), as a
defense-in-depth confirmation independent of the config-time validation
above.

### Start Command

```bash
EVENTBUS_CONFIG_PATH=<path-to-eventbus.toml> python -m eventbus.app
```

Or `uvicorn eventbus.app:app --host <loopback-host>`.

---

## Health Endpoint Semantics

HTTP 200 = `ok`, otherwise = HTTP 503 + `status: "degraded"` + component details. An `unhealthy` state does not exist.

**A 503 status indicates a degraded state, not a process shutdown.**

**Monitoring should be based on HTTP status codes.** When degraded, check the `degraded_reasons` field (e.g., DB connection failure, DLQ task stopped, queue backlog, slow consumers, etc.). See Delivery Operations below for the specific field thresholds that drive a `degraded` slow-consumer state.

---

## Batched Replay Design

Initial replay is performed in bounded, configurable batches rather than a single unbounded `.fetchall()` call. This prevents memory exhaustion during large replays and reduces database lock contention by releasing and reacquiring `_db_lock` between batches.

### Configuration

The following configuration fields control replay behavior (see also `retained_event_count` above):

- `replay_batch_size` — Number of rows fetched per batch
- `subscriber_count` — Maximum number of concurrent subscribers before capacity limits apply

### Capacity Limits

Capacity is governed by the configuration fields `subscriber_count`, `retained_event_count`, and `publish_rate` described above and in the Configuration section. No replay-size limit or latency objective is defined.

### Database-Lock Contention Monitoring

The following Prometheus metrics monitor database-lock contention:

- `eventbus_db_lock_wait_time_seconds` — Histogram of lock wait times
- `eventbus_db_query_duration_seconds` — Histogram of query durations
- `eventbus_db_lock_contention_total` — Counter of lock contention events

The health endpoint (`/health`) reports lock wait and query duration averages and the contention total under its `metrics` sub-object. The service does not serve a separate Prometheus scrape endpoint.

### Slow Consumer Metrics

The following Prometheus metrics track slow consumer detection:

- `eventbus_slow_consumer_total` — Counter of slow consumer events

Slow consumer events are detected when a subscriber's queue depth exceeds `slow_consumer_threshold`. The health endpoint reports `slow_consumers_detected` when this condition occurs.

---

## Consumer ID Stability

The Client specifies the Consumer ID via the `consumer_id` parameter; it is not automatically generated by the server. Use a stable ID that persists across restarts. Do not use volatile IDs like PIDs. A second concurrent `/subscribe` connection with the same ID is rejected with HTTP 409; see `eventbus_06_dlq_offsets_and_delivery_semantics.md` (Consumer ID Collision Risk) for what the server does and does not detect.

See `eventbus_03_dlq_operations.md` for the Subscribe/Ack protocol and `eventbus_07_persistence_schema_and_replay.md` for offset persistence details.

---

## Delivery Operations

### Verifying Delivery

Verify live push using `GET /subscribe?consumer_id=test`. Events should be received within one loop tick after publishing.

### Monitoring Slow Consumers

A subscriber queue holding more than `slow_consumer_threshold` events is considered slow. This value is configurable via the `slow_consumer_threshold` field in the Event Bus TOML configuration. This can be verified via the health endpoint:

- `slow_consumers > 0` → `degraded`
- `max_queue_depth >= backlog_health_threshold` → `broker_queue_backlog_high`

If a subscriber queue becomes full (`subscriber_queue_maxsize`), the broker disconnects that subscriber. The consumer must reconnect and replay from SQLite.

**Threshold validation rules:**
- `slow_consumer_threshold` must be strictly less than `subscriber_queue_maxsize`
- `backlog_health_threshold` must be less than or equal to `subscriber_queue_maxsize`

Invalid combinations fail startup with actionable error messages naming both conflicting values.

### Recovery on Reconnection

See [Resume Behavior](eventbus_06_dlq_offsets_and_delivery_semantics.md#resume-behavior) in the DLQ, offsets and delivery semantics document.

### Subscriber Count

When the count is 0, the broker is idle. Events remain in SQLite and are available for replay upon the next connection.

---

## DLQ Operations

### DLQ File Creation

Files are created at `{deadletter_dir}/{event_id}.json` during inline processing (on `/nack`) or by the background loop (periodic). The background loop serves as a safety net.

### Requeue

`POST /dlq/{event_id}/requeue` uses the lineage model: it inserts a new event row (`redelivered_from` set to the original, `delivery_failure_count` copied, `cycle_failure_count` reset) and increments `dlq_requeue_count` on the original, whose `dlq_at` is preserved. See `eventbus_06_dlq_offsets_and_delivery_semantics.md` (Requeue (Redelivery)).

### Monitoring

Sweep results are recorded in the logs but are not exposed via the health endpoint.

## Keywords

- event-bus
- configuration
- environment-variables
- config-fields
- toml
- bind-address
- startup
- security
- public-bind
- loopback
- wildcard
- health-check
- http-status-codes
- monitoring
- degraded
- consumer-id
- offset-resume
- reconnect
- stability
- delivery
- verification
- slow-consumer
- reconnect-recovery
- subscriber-count
- dlq
- dead-letter-queue
- requeue
- background-loop
- sweep
