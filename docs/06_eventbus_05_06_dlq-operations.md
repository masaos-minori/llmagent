---
title: "Event Bus: DLQ Operations"
category: eventbus
tags:
  - event-bus
  - dlq
  - dead-letter-queue
  - requeue
  - background-loop
  - sweep
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_03_nack-health-dlq.md
  - 06_eventbus_02_04_dlq-background-loop.md
  - 06_eventbus_05_05_delivery-operations.md
source:
  - 06_eventbus_05_01_config-env-and-fields.md
---

# Event Bus: DLQ Operations

## DLQ Operations

### DLQ File Creation

Files are created at `{deadletter_dir}/{event_id}.json` during inline processing (on `/nack`) or by the background loop (every 60 seconds). The background loop serves as a safety net.

### Requeue

`POST /dlq/{event_id}/requeue` clears `dlq_at` and increments `dlq_requeue_count`. It does not reset `delivery_failure_count`. If `delivery_failure_count >= max_retry`, the event will be re-promoted during the next loop.

### Monitoring

Sweep results are recorded in the logs but are not exposed via the health endpoint.

## Related Documents

- `06_eventbus_02_03_nack-health-dlq.md`
- `06_eventbus_02_04_dlq-background-loop.md`
- `06_eventbus_05_05_delivery-operations.md`
