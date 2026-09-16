---
title: EventBus API Reference
description: Index and overview of the EventBus HTTP API reference documents
tags: [api-reference, index, overview]
created: 20260916
---

# EventBus API Reference

## Overview

This directory contains the API reference documentation for the EventBus HTTP service. Each endpoint group has its own document with request/response schemas, authentication requirements, and examples.

## Endpoint Groups

| Document | Description |
|----------|-------------|
| [Health Endpoint](health-endpoint.md) | GET /health — Service health monitoring |
| [Replay Endpoint](replay-endpoint.md) | GET /replay — Replay events via SSE or JSON |
| [DLQ Endpoint](dlq-endpoint.md) | GET /dlq + POST /dlq/{event_id}/requeue — Dead-letter queue management |
| [ACK/NACK Endpoints](ack-nack-endpoints.md) | POST /events/{event_id}/ack + POST /nack — Consumer acknowledgments |

## Authentication Model

All endpoints require role-based authentication via the `Authorization` header:

```
Authorization: Bearer ${ROLE_TOKEN}
```

The available roles are:

| Role | Token Variable | Access |
|------|---------------|--------|
| PUBLISHER | `${PUBLISHER_TOKEN}` | Publish events |
| CONSUMER | `${CONSUMER_TOKEN}` | Subscribe, ACK, NACK |
| OPERATOR | `${OPERATOR_TOKEN}` | Replay, DLQ management |
| MONITORING | `${MONITORING_TOKEN}` | Health checks |

When per-role tokens are configured, each token grants only its own role. When the shared `auth_token` is set, it grants all roles for backward compatibility.

## Common Patterns

### Error Response Format

All error responses use the FastAPI standard format:

```json
{
  "detail": "Error description"
}
```

### Pagination

List endpoints support pagination via `limit` and `offset` query parameters:

```
GET /dlq?limit=50&offset=0
```

| Parameter | Default | Constraints |
|-----------|---------|-------------|
| `limit` | 100 | 1 <= limit <= 1000 |
| `offset` | 0 | >= 0 |

### Response Schema

Paginated list responses follow this pattern:

```json
{
  "total": 1000,
  "limit": 50,
  "offset": 0,
  "items": [...]
}
```

### Security Notes

- All examples use placeholder values (e.g., `"Bearer ${TOKEN}"`) — no real credentials or secrets.
- Consumer authorization requires the caller's principal to include the requested `consumer_id` in `allowed_consumer_ids`.
- Requeue operations use a lineage model where each requeue creates a new event; the original event's `dlq_at` timestamp is preserved to prevent duplicate redeliveries.
