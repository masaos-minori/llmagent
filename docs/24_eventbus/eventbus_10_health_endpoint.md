---
title: Health Endpoint
tags: [api-reference, health, monitoring]
area: eventbus
related:
  - eventbus_02_api-reference-index.md
  - eventbus_07_configuration-and-operations.md
---

# Health Endpoint

## Overview

The `/health` endpoint provides real-time health status of the EventBus service, including database connectivity, broker state, and DLQ task status.

## Endpoint

```
GET /health
```

## Authentication

**Monitoring role required.**

Requires `Bearer ${MONITORING_TOKEN}` in the Authorization header.

## Success Response

**HTTP 200 OK**

Returned when all subsystems are healthy.

### Response Content

The body reports overall `status` (`"ok"` or `"degraded"`), database and DLQ sweep task state, broker counters (active subscribers, maximum queue depth, slow consumers, overflow disconnects, duplicate connection rejections), `degraded_reasons` (empty when healthy) and lock-contention metrics under `metrics`. The exact schema is in `scripts/eventbus/health_route.py`.

## Degraded Response

**HTTP 503 Service Unavailable**

Returned when one or more subsystems report degraded status.

### Response Schema

Same as success response, but with `status: "degraded"` and non-empty `degraded_reasons`.

HTTP 503 is returned for any degraded reason, including the capacity-only reasons (`subscribers_at_capacity`, `lock_wait_high`, `query_duration_high`, `slow_consumers_detected`, `broker_queue_backlog_high`). A capacity-only 503 still has `liveness` and `readiness` true, so it satisfies the deployment readiness gate; `db_unavailable` and `dlq_task_stopped` do not.

### Possible Degraded Reasons

| Reason | Description |
|--------|-------------|
| `db_unavailable` | Database connectivity check failed |
| `dlq_task_stopped` | DLQ sweep background task has stopped |
| `broker_unavailable` | The event broker is not initialized |
| `broker_queue_backlog_high` | Queue backlog exceeds `backlog_health_threshold` |
| `slow_consumers_detected` | One or more slow consumers detected |
| `subscribers_at_capacity` | Active subscribers at configured capacity limit |
| `lock_wait_high` | Average DB lock wait time exceeds its threshold |
| `query_duration_high` | Average query duration exceeds its threshold |

## Health Tiers

The response includes two boolean health-tier fields:

| Field | Meaning |
|-------|---------|
| `liveness` | The DLQ sweep task is running |
| `readiness` | The database is connectable (`check_db`) |

The deployment readiness gate is `liveness and readiness` (`is_ready()` in `scripts/eventbus/health_route.py`); `deploy/setup_services.sh` reads exactly these two fields. The broker is not part of the gate. Schema integrity is checked at startup, not reported here.

## Metric Definitions

### Lock-wait vs Query Duration

`eventbus_db_lock_wait_time_seconds` measures time spent waiting for the database lock (from thread submit to lock acquisition). `eventbus_db_query_duration_seconds` measures DB-execution time while holding the lock (excludes lock wait) and is recorded also when the callback raises. These are independent measurements — `lock_wait_high` and `query_duration_high` compare against separate thresholds on separate metrics.

### Slow Consumer Metric

`eventbus_slow_consumer_current` is a gauge reporting the current number of slow consumers (not a cumulative counter). A consumer is slow when its queue depth reaches `slow_consumer_threshold`. The gauge is refreshed on every `/health` read and whenever a subscriber is removed (an unsubscribe or an overflow disconnect), and it is set to zero at shutdown. It is not refreshed when a queue drains on its own, so after a consumer recovers the gauge keeps its previous value until the next `/health` read or subscriber removal. Repeated `/health` polls do not inflate it, and the `slow_consumers` field in the `/health` body is always computed fresh.

## Keywords

- health endpoint
- degraded reasons
- HTTP 503
- monitoring
