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

The response includes three distinct health-tier fields:

| Field | Meaning |
|-------|---------|
| `liveness` | Process/endpoint reachable (DLQ task running) |
| `readiness` | Dependencies healthy enough to accept work (DB connectable via `check_db`) |
| `integrity` | Schema matches expected version (deferred to H-03; currently `null`) |

`liveness` and `readiness` are boolean values. `integrity` is `null` because schema integrity is checked by H-03, not here. Readiness without integrity does not claim schema OK.

## Metric Definitions

### Lock-wait vs Query Duration

`eventbus_db_lock_wait_time_seconds` measures time spent waiting for the database lock (from thread submit to lock acquisition). `eventbus_db_query_duration_seconds` measures DB-execution time while holding the lock (excludes lock wait). These are independent measurements — `lock_wait_high` and `query_duration_high` compare against separate thresholds on separate metrics.

### Slow Consumer Metric

`eventbus_slow_consumer_current` is a gauge reporting the current number of slow consumers (not a cumulative counter). Repeated `/health` polls do not inflate this value.

## Keywords

- health endpoint
- degraded reasons
- HTTP 503
- monitoring
