---
title: EventBus API Reference
area: eventbus
tags: [api-reference, index, overview]
related:
  - eventbus_00_document-guide.md
  - eventbus_11_health_endpoint.md
  - eventbus_12_replay_endpoint.md
  - eventbus_04_dlq_endpoint.md
  - eventbus_13_ack_nack_endpoints.md
---

# EventBus API Reference

## Overview

This directory contains the API reference documentation for the EventBus HTTP service. Each endpoint group has its own document with request/response schemas, authentication requirements, and examples.

## Endpoint Groups

| Document | Description |
|----------|-------------|
| [Health Endpoint](eventbus_11_health_endpoint.md) | GET /health — Service health monitoring |
| [Replay Endpoint](eventbus_12_replay_endpoint.md) | GET /replay — Replay events via SSE or JSON |
| [Publish and Subscribe](eventbus_03_dlq_operations.md) | POST /publish + GET /subscribe — Publishing and SSE delivery |
| [DLQ Endpoint](eventbus_04_dlq_endpoint.md) | GET /dlq + POST /dlq/{event_id}/requeue — Dead-letter queue management |
| [ACK/NACK Endpoints](eventbus_13_ack_nack_endpoints.md) | POST /events/{event_id}/ack + POST /nack — Consumer acknowledgments |

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
| ADMIN | `${ADMIN_TOKEN}` | Admin endpoints (`/admin/*`, e.g. `POST /admin/topics/authorization`) |

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
| `limit` | route default | bounded (see route definition) |
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

## Keywords

- api-reference
- index
- overview
