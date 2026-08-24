---
title: "Event Bus: Health Endpoint Semantics"
area: eventbus
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

## Health Endpoint

HTTP 200 = `ok`, otherwise = HTTP 503 + `status: "degraded"` + component details. An `unhealthy` state does not exist.

**A 503 status indicates a degraded state, not a process shutdown.**

**Monitoring should be based on HTTP status codes.** When degraded, check the `reasons` field (e.g., DB connection failure, DLQ task stopped, queue backlog, slow consumers, etc.).

## Related Documents

- `06_eventbus_05_01_config-env-and-fields.md`
- `06_eventbus_05_05_delivery-operations.md`
