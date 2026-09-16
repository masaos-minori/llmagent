---
title: Health Endpoint
description: GET /health endpoint contract for EventBus service health monitoring
tags: [api-reference, health, monitoring]
created: 20260916
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

### Response Schema

```json
{
  "status": "ok",
  "db": "ok",
  "dlq_task": "running",
  "active_subscribers": 0,
  "max_queue_depth": 0,
  "slow_consumers": 0,
  "overflow_disconnects": 0,
  "duplicate_connection_rejections": 0,
  "degraded_reasons": [],
  "metrics": {
    "lock_wait_avg_seconds": 0.0,
    "query_duration_avg_seconds": 0.0,
    "lock_contention_total": 0
  }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Overall health: `"ok"` or `"degraded"` |
| `db` | string | Database status: `"ok"` or `"unavailable"` |
| `dlq_task` | string | DLQ sweep task status: `"running"` or `"stopped"` |
| `active_subscribers` | integer | Current number of active SSE subscribers |
| `max_queue_depth` | integer | Maximum queue depth observed across all topics |
| `slow_consumers` | integer | Number of slow consumers detected |
| `overflow_disconnects` | integer | Count of overflow disconnects |
| `duplicate_connection_rejections` | integer | Count of duplicate connection rejections |
| `degraded_reasons` | array[string] | List of degraded reasons (empty when healthy) |
| `metrics.lock_wait_avg_seconds` | float | Average database lock wait time in seconds |
| `metrics.query_duration_avg_seconds` | float | Average query duration in seconds |
| `metrics.lock_contention_total` | integer | Total lock contention count |

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
| `broker_queue_backlog_high` | Queue backlog exceeds `backlog_health_threshold` |
| `slow_consumers_detected` | One or more slow consumers detected |
| `subscribers_at_capacity` | Active subscribers at configured capacity limit |
| `lock_wait_high` | Average DB lock wait time exceeds threshold (>0.01s) |
| `query_duration_high` | Average query duration exceeds threshold (>0.05s) |

## Example Requests

### Successful Health Check

```bash
curl -H "Authorization: Bearer ${MONITORING_TOKEN}" \
  http://localhost:8080/health
```

Response:

```json
{
  "status": "ok",
  "db": "ok",
  "dlq_task": "running",
  "active_subscribers": 5,
  "max_queue_depth": 42,
  "slow_consumers": 0,
  "overflow_disconnects": 0,
  "duplicate_connection_rejections": 0,
  "degraded_reasons": [],
  "metrics": {
    "lock_wait_avg_seconds": 0.001,
    "query_duration_avg_seconds": 0.003,
    "lock_contention_total": 12
  }
}
```

### Degraded Health Check

```bash
curl -H "Authorization: Bearer ${MONITORING_TOKEN}" \
  http://localhost:8080/health
```

Response:

```json
{
  "status": "degraded",
  "db": "ok",
  "dlq_task": "stopped",
  "active_subscribers": 10,
  "max_queue_depth": 5000,
  "slow_consumers": 3,
  "overflow_disconnects": 0,
  "duplicate_connection_rejections": 0,
  "degraded_reasons": ["dlq_task_stopped", "subscriber_count_at_capacity"],
  "metrics": {
    "lock_wait_avg_seconds": 0.015,
    "query_duration_avg_seconds": 0.06,
    "lock_contention_total": 45
  }
}
```
