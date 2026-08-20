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
  - 06_eventbus_02_01_publish-replay.md
  - 06_eventbus_02_03_nack-health-dlq.md
source:
  - 06_eventbus_02_01_publish-replay.md
---

# Event Bus: Failure Behavior Summary

| Failure Cause | Action |
|---|---|
| JSON Schema validation failure during `publish` | 422, event is not saved |
| JSONL append failure after SQLite commit | 200 returned, WARNING log output, event remains in SQLite |
| DB unavailable in `/health` | `status: degraded`, `db: unavailable` |
| DLQ task stopped in `/health` | `status: degraded`, `dlq_task: stopped` |
| Unknown `event_id` during requeue | 404 |
| Event exists but is not in DLQ during requeue | 409 Conflict |
| Duplicate `event_id` during `publish` (Idempotency skip) | 200 returned (existing `seq`), broker notification skipped |
| Subscriber queue full | Event is silently discarded, WARNING log output |

## Related Documents

- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_02_03_nack-health-dlq.md`
