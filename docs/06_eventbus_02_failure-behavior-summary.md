---
title: "Event Bus: Failure Behavior Summary"
category: eventbus
tags:
  - event-bus
  - error-handling
  - failure-behavior
  - http-status-codes
  - validation
  - json-schema
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_publish-replay.md
  - 06_eventbus_02_nack-health-dlq.md
source:
  - 06_eventbus_02_http_api_and_runtime.md
---

# Event Bus: Failure Behavior Summary

| Failure | Behavior |
|---|---|
| JSON Schema validation failure on publish | 422, event not stored |
| JSONL append failure after SQLite commit | 200 returned, WARNING logged, event in SQLite |
| DB unavailable on `/health` | `{"status": "degraded", "db": "unavailable", ...}` |
| DLQ task stopped on `/health` | `{"status": "degraded", ..., "dlq_task": "stopped"}` |
| Unknown `event_id` on requeue | 404 |
| Event exists but not in DLQ on requeue | 409 Conflict |

## Related Documents

- `06_eventbus_02_publish-replay.md`
- `06_eventbus_02_nack-health-dlq.md`

## Keywords

event-bus
error-handling
failure-behavior
http-status-codes
validation
json-schema
