---
title: "Event Bus: Health Endpoint Semantics"
category: eventbus
tags:
  - event-bus
  - health-check
  - http-status-codes
  - monitoring
  - degraded
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_05_01_config-env-and-fields.md
  - 06_eventbus_05_05_delivery-operations.md
source:
  - 06_eventbus_05_01_config-env-and-fields.md
---

# Event Bus: Health Endpoint Semantics

## Health Endpoint Semantics

| HTTP Status | Status Value | Meaning |
|---|---|---|
| 200 | `ok` | All systems nominal |
| 503 | `degraded` | Connected but degraded (DB unavailable, DLQ task stopped, broker queue backlog high, slow consumers) |

There is no `unhealthy` status value — the health endpoint returns HTTP 503 for all non-ok states. The JSON body includes `status: "degraded"` and component-level details (e.g., `"db": "unavailable"`).

**Monitoring tools MUST use HTTP status code, not JSON body, for alerting.**

## Related Documents

- `06_eventbus_05_01_config-env-and-fields.md`
- `06_eventbus_05_05_delivery-operations.md`

## Keywords

event-bus
health-check
http-status-codes
monitoring
degraded
