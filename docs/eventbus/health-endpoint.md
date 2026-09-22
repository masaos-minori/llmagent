---
title: Health Endpoint
description: GET /health endpoint contract for EventBus service health monitoring
tags: [api-reference, health, monitoring]
area: eventbus
related: []
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

The response body's fields are described in Field Descriptions below; see
`scripts/eventbus/health_route.py` for the exact JSON schema.

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

Returns `status: "ok"` with an empty `degraded_reasons` array when all subsystems are
healthy — see `scripts/eventbus/health_route.py` for the full response schema.

### Degraded Health Check

```bash
curl -H "Authorization: Bearer ${MONITORING_TOKEN}" \
  http://localhost:8080/health
```

Returns `status: "degraded"` with a non-empty `degraded_reasons` array listing which
conditions triggered the degraded state (see "Possible Degraded Reasons" above) — see
`scripts/eventbus/health_route.py` for the full response schema.
