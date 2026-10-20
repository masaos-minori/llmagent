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

## Keywords

- health endpoint
- degraded reasons
- HTTP 503
- monitoring
