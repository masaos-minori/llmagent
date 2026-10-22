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
  - eventbus_06_persistence_schema_and_replay.md
  - adr_02_04_013_eventbus-authentication-authorization.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
---

# Event Bus: Configuration and Operations

## Configuration

Loaded from a TOML file (default path defined in `scripts/eventbus/config.py`).

### Environment Variables

`EVENTBUS_CONFIG_PATH` selects the TOML file and `EVENTBUS_SCHEMA_PATH` selects the event envelope JSON Schema.

### Configuration Fields

The schema and defaults are defined in `scripts/eventbus/config.py::EventBusConfig`; `__post_init__()` holds the validation rules enforced at startup. The authorization model that the token fields implement is in `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`. Operational constraints:

- `host` must be a loopback address (see Bind Address below).
- `auth_token` is required (startup fails if empty). It is a control-plane credential holding only the operator, monitoring, and admin roles. The shipped `config/eventbus.toml` stores it as an environment reference, so the credential comes from the operator environment at load time rather than from the deployed file (Explicit in code — `config/eventbus.toml`, `scripts/eventbus/config.py`). A token key written as `"${ENV:VAR_NAME}"` is resolved when the configuration is loaded: the value must be present in the environment, and an unset variable raises `ValueError` naming it, so a reference that resolves to nothing never reaches a running server. A reference that resolves to an empty string is rejected by the same non-empty rule as a literal empty value.
- `publisher_token`, `consumer_token`, `operator_token` and `monitoring_token` each grant exactly their own role when set. `admin_token` grants the operator, monitoring, and admin roles (`/admin/*`, DLQ, replay, health) and has no publisher or consumer role.
- `consumer_authorization` (`consumer_id` -> topics) and `topic_authorization` (topic -> `consumer_id`) are allowlists applied to the consumer-role token only.
- `slow_consumer_threshold` must be strictly less than `subscriber_queue_maxsize`, and `backlog_health_threshold` must be less than or equal to it. Invalid combinations fail startup with error messages naming both conflicting values.
- `sse_idle_timeout` closes a `/subscribe` connection that received no events within that period; `sse_heartbeat_interval` controls keep-alive comments.
- `publish_rate`, `subscriber_count` and `replay_batch_size` bound capacity and replay batch size.

### Token Distribution

`auth_token` and `admin_token` hold only the control-plane roles and no PUBLISHER or CONSUMER role (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`), so they cannot publish, subscribe, ACK, or NACK even if a caller receives one. Give each caller only its own token:

| Caller | Token to give it | Never give it |
|---|---|---|
| Publisher process | `publisher_token` | `auth_token`, `admin_token` |
| Consumer process | `consumer_token` (its `consumer_authorization` mapping resolves to deny-all when empty) | `auth_token`, `admin_token` |
| Monitoring probe | `monitoring_token` | `auth_token`, `admin_token` |
| Operator (DLQ, replay) | `operator_token` | — |
| Administrator | `admin_token` | — |

Before deploying a publisher or consumer process, confirm that the token it is configured with (its environment or configuration file; the variable names are operator choices) is its own per-role token and differs from the `auth_token` and `admin_token` values in the Event Bus configuration file. For the shared control-plane credential, the shipped configuration (`config/eventbus.toml`) references one environment variable, so the supported way to change it is to change that variable in the operator environment file and restart; a hand-edited copy of the deployed configuration file is replaced by the next run of `deploy/deploy.sh`. (Explicit in code — `config/eventbus.toml`, `deploy/deploy.sh`) A Consumer process needs its own `consumer_token` with explicit `consumer_authorization` (and optionally `topic_authorization`) mappings; an administrator who operates on Consumer state also needs a separate Consumer-scoped credential.

### Unsupported Keys

Startup fails if the configuration file contains any key not defined in `EventBusConfig`.

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
# Token references in the configuration are resolved when it is loaded, so the referenced
# variable must already be present in the environment before this command runs.
EVENTBUS_CONFIG_PATH=<path-to-eventbus.toml> python -m eventbus.app
```

Do not start the server with `uvicorn` directly. Starting through `python -m eventbus.app` is required because it runs the post-start loopback verification, which a direct `uvicorn` invocation bypasses (see `eventbus_06_persistence_schema_and_replay.md`).

The Event Bus process has no dependency on the remote LLM services (`embed-llm`, `agent-llm`). `deploy/setup_services.sh` withholds its launch only when `agent-llm` fails the health gate, or when either service fails under `LLM_GATE_STRICT=1`; an unreachable `embed-llm` alone does not prevent it.

The shipped `config/eventbus.toml` stores the shared control-plane credential as an environment reference. Configuration loading aborts with a `ValueError` naming the variable when it is unset, and the deployment script reports the same missing variable in its `[FATAL]` list before launching the process. (Explicit in code — `scripts/eventbus/config.py`, `config/eventbus.toml`, `deploy/setup_services.sh`)

---

## Health Endpoint Semantics

HTTP 200 = `ok`, otherwise = HTTP 503 + `status: "degraded"` + component details. An `unhealthy` state does not exist.

**A 503 status indicates a degraded state, not a process shutdown.**

**Monitoring should be based on HTTP status codes.** When degraded, check the `degraded_reasons` field (e.g., DB connection failure, DLQ task stopped, queue backlog, slow consumers, etc.). See Delivery Operations below for the specific field thresholds that drive a `degraded` slow-consumer state.

---

## Batched Replay Design

Initial replay is performed in bounded, configurable batches rather than a single unbounded `.fetchall()` call. This prevents memory exhaustion during large replays and reduces database lock contention by releasing and reacquiring `_db_lock` between batches.

### Capacity Limits

Capacity is governed by `subscriber_count` and `publish_rate` (see Configuration Fields). No replay-size limit or latency objective is defined.

### Metrics

Database-lock contention (`eventbus_db_lock_*`, `eventbus_db_query_duration_seconds`) and slow-consumer (`eventbus_slow_consumer_total`) metrics are Prometheus in-process metrics. The service does not serve a Prometheus scrape endpoint; `/health` reports lock wait and query duration averages and the contention total under its `metrics` sub-object, and reports `slow_consumers_detected` when a subscriber's queue depth exceeds `slow_consumer_threshold`.

---

## Consumer ID Stability

The Client specifies the Consumer ID via the `consumer_id` parameter; it is not automatically generated by the server. Use a stable ID that persists across restarts. Do not use volatile IDs like PIDs. A second concurrent `/subscribe` connection with the same ID is rejected with HTTP 409; see `eventbus_05_dlq_offsets_and_delivery_semantics.md` (Consumer ID Collision Risk) for what the server does and does not detect.

See `eventbus_03_dlq_operations.md` for the Subscribe/Ack protocol and `eventbus_06_persistence_schema_and_replay.md` for offset persistence details.

---

## Legacy Offset Files

`offsets_dir` (`config/eventbus.toml`) holds the file-based offsets that predate the `consumer_offsets` table. The service does not read, write, modify, or delete them; `consumer_offsets` in `eventbus.sqlite` is the only resume source. An operator may archive or delete the files.

---

## Delivery Operations

### Verifying Delivery

Verify live push using `GET /subscribe?consumer_id=test`. Events should be received within one loop tick after publishing.

### Monitoring Slow Consumers

A subscriber queue holding more than `slow_consumer_threshold` events is considered slow. This value is configurable via the `slow_consumer_threshold` field in the Event Bus TOML configuration. This can be verified via the health endpoint:

- `slow_consumers > 0` → `degraded`
- `max_queue_depth >= backlog_health_threshold` → `broker_queue_backlog_high`

If a subscriber queue becomes full (`subscriber_queue_maxsize`), the broker disconnects that subscriber. The consumer must reconnect and replay from SQLite.

Threshold validation rules are defined in Configuration Fields above.

### Recovery on Reconnection

See [Resume Behavior](eventbus_05_dlq_offsets_and_delivery_semantics.md#resume-behavior) in the DLQ, offsets and delivery semantics document.

### Subscriber Count

When the count is 0, the broker is idle. Events remain in SQLite and are available for replay upon the next connection.

---

## DLQ Operations

### DLQ File Creation

Files are created at `{deadletter_dir}/{event_id}.json` during inline processing (on `/nack`) or by the background loop (periodic). The background loop serves as a safety net.

### Requeue

`POST /dlq/{event_id}/requeue` uses the lineage model: it inserts a new event row (`redelivered_from` set to the original, `delivery_failure_count` copied, `cycle_failure_count` reset) and increments `dlq_requeue_count` on the original, whose `dlq_at` is preserved. See `eventbus_05_dlq_offsets_and_delivery_semantics.md` (Requeue (Redelivery)).

### Monitoring

Sweep results are recorded in the logs but are not exposed via the health endpoint.

## Validation

The CI workflow runs lint checks, type checks, and the test suite for `scripts/`, so the health, ACK/NACK, and DLQ tests under `tests/eventbus/` run on every change.

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
