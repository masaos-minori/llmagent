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
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_operations.md
  - 06_eventbus_03_persistence_schema_and_replay.md
  - 06_eventbus_05_07_validation-status.md
---

# Event Bus: Configuration and Operations

## Configuration

Loaded from a TOML file (default: `/opt/llm/config/eventbus.toml`).

### Environment Variables

- `EVENTBUS_CONFIG_PATH` — Path to the TOML file
- `EVENTBUS_SCHEMA_PATH` — Path to the event envelope JSON Schema

### Configuration Fields

- `port` — HTTP listening port (startup fails if outside 1024–65535)
- `db_path` — SQLite DB path
- `storage_dir` — JSONL archive directory
- `offsets_dir` — Consumer offset directory
- `deadletter_dir` — DLQ directory
- `max_retry` — Retry threshold before DLQ promotion (startup fails if < 1)
- `replay_batch_size` — Replay fetch batch size for bounded memory during large replays (default: 1000)
- `subscriber_count` — Maximum number of concurrent subscribers before capacity limits apply (default: 10)
- `retained_event_count` — Number of events retained in SQLite for replay (default: 10000)
- `publish_rate` — Maximum publish rate in events/sec before backpressure applies (default: 100.0)
- `host` — Listening address (default: `127.0.0.1`; must be `127.0.0.1` or `::1` — see Bind Address below)
- `auth_token` — Required for all requests (startup fails if empty)
- `sse_heartbeat_interval` — SSE heartbeat interval in seconds (default: 30.0)
- `slow_consumer_threshold` — Queue depth at which a subscriber is considered slow (default: 100)
- `subscriber_queue_maxsize` — Per-subscriber queue capacity (default: 1000)
- `backlog_health_threshold` — Max queue depth before health endpoint reports `broker_queue_backlog_high` (default: 500)

Validation for `port` and `max_retry` is performed in `EventBusConfig.__post_init__()`. Cross-field validation ensures `slow_consumer_threshold < subscriber_queue_maxsize` and `backlog_health_threshold <= subscriber_queue_maxsize`.

### Deprecated Keys

Startup fails if `poll_interval_ms` or `offset_checkpoint_interval` remain in the configuration file.

---

## Bind Address and Start Command

### Bind Address

Event Bus enforces loopback-only binding unconditionally — there is no
override. Binding to anything other than loopback poses a security risk as
the API has no authentication.

**Address Classification** (`_is_public_host()`, `scripts/eventbus/config.py`):
- Loopback (`127.0.0.1`, `::1`) — Allowed
- Everything else (private-LAN, wildcard `0.0.0.0`/`::`, other public
  addresses, hostnames) — Raises `ValueError` at config-construction time

`EventBusConfig` also verifies the actual bound socket address matches
loopback immediately after startup (`_main()`'s post-start check), as a
defense-in-depth confirmation independent of the config-time validation
above.

### Start Command

```bash
EVENTBUS_CONFIG_PATH=/opt/llm/config/eventbus.toml python -m eventbus.app
```

Or `uvicorn eventbus.app:app --host 127.0.0.1`.

---

## Health Endpoint Semantics

HTTP 200 = `ok`, otherwise = HTTP 503 + `status: "degraded"` + component details. An `unhealthy` state does not exist.

**A 503 status indicates a degraded state, not a process shutdown.**

**Monitoring should be based on HTTP status codes.** When degraded, check the `reasons` field (e.g., DB connection failure, DLQ task stopped, queue backlog, slow consumers, etc.). See Delivery Operations below for the specific field thresholds that drive a `degraded` slow-consumer state.

---

## Batched Replay Design

Initial replay is now performed in bounded, configurable batches rather than a single unbounded `.fetchall()` call. This prevents memory exhaustion during large replays and reduces database lock contention by releasing and reacquiring `_db_lock` between batches.

### Configuration

The following configuration fields control replay behavior:

- `replay_batch_size` — Number of rows fetched per batch (default: 1000)
- `subscriber_count` — Maximum number of concurrent subscribers before capacity limits apply (default: 10)
- `retained_event_count` — Number of events retained in SQLite for replay (default: 10000)
- `publish_rate` — Maximum publish rate in events/sec before backpressure applies (default: 100.0)

### Capacity Limits

Based on representative load testing, the following capacity limits have been established:

| Metric | Limit | Measurement Methodology |
|--------|-------|-------------------------|
| Publish rate | 100 events/sec | Load test with concurrent publishers |
| Subscriber count | 10 | Load test with concurrent subscribers |
| Retained event count | 10000 | Load test with large backlog |
| Replay size | TBD MB | Load test with large replay |
| Latency objective | TBD ms p99 | Load test with concurrent operations |

### Database-Lock Contention Monitoring

The following Prometheus metrics monitor database-lock contention:

- `eventbus_db_lock_wait_time_seconds` — Histogram of lock wait times
- `eventbus_db_query_duration_seconds` — Histogram of query durations
- `eventbus_db_lock_contention_total` — Counter of lock contention events (>1ms threshold)

These metrics are exposed via the health endpoint (`/health`) under the `metrics` sub-object and via the standard Prometheus scrape target.

### Slow Consumer Metrics

The following Prometheus metrics track slow consumer detection:

- `eventbus_slow_consumer_total` — Counter of slow consumer events
- `eventbus_slow_consumer_duration_seconds` — Histogram of slow consumer durations

Slow consumer events are detected when a subscriber's queue depth exceeds `slow_consumer_threshold`. The health endpoint reports `slow_consumers_detected` when this condition occurs.

---

## Consumer ID Stability

The Client specifies the Consumer ID via the `consumer_id` parameter; it is not automatically generated by the server. Use a stable ID that persists across restarts. Do not use volatile IDs like PIDs. If multiple consumers use the same ID, the last write wins, and the server does not detect conflicts.

See `06_eventbus_02_operations.md` for the Subscribe/Ack protocol and `06_eventbus_03_persistence_schema_and_replay.md` for offset persistence details.

---

## Delivery Operations

### Verifying Delivery

Verify live push using `GET /subscribe?consumer_id=test`. Events should be received within one loop tick after publishing.

### Monitoring Slow Consumers

A process queue exceeding `slow_consumer_threshold` events is considered slow. This value is configurable via the `slow_consumer_threshold` field in the Event Bus TOML configuration (default: `100`). This can be verified via the health endpoint:

- `slow_consumers > 0` → `degraded`
- `max_queue_depth >= backlog_health_threshold` → `broker_queue_backlog_high`

If a consumer is slow, events are discarded from the queue. The consumer must reconnect and replay from SQLite.

**Threshold validation rules:**
- `slow_consumer_threshold` must be strictly less than `subscriber_queue_maxsize`
- `backlog_health_threshold` must be less than or equal to `subscriber_queue_maxsize`

Invalid combinations fail startup with actionable error messages naming both conflicting values.

### Recovery on Reconnection

Reconnecting with a `consumer_id` resumes from the last acknowledged offset. If no offsets have been acknowledged, it starts from `seq=0`. It is also possible to start from a specific position using `since_seq=N`.

### Subscriber Count

When the count is 0, the broker is idle. Events remain in SQLite and are available for replay upon the next connection.

---

## DLQ Operations

### DLQ File Creation

Files are created at `{deadletter_dir}/{event_id}.json` during inline processing (on `/nack`) or by the background loop (every 60 seconds). The background loop serves as a safety net.

### Requeue

`POST /dlq/{event_id}/requeue` clears `dlq_at` and increments `dlq_requeue_count`. It does not reset `delivery_failure_count`. If `delivery_failure_count >= max_retry`, the event will be re-promoted during the next loop.

### Monitoring

Sweep results are recorded in the logs but are not exposed via the health endpoint.

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_operations.md`
- `06_eventbus_03_persistence_schema_and_replay.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- `06_eventbus_05_07_validation-status.md`
- `06_eventbus_06_reference-api.md`
