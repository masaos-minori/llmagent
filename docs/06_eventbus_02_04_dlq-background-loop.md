---
title: "Event Bus: DLQ Background Loop"
category: eventbus
tags:
  - event-bus
  - dlq
  - dead-letter-queue
  - background-loop
  - safety-sweep
  - optimistic-lock
  - orphan-promotion
  - requeue
12: related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_03_nack-health-dlq.md
  - 06_eventbus_05_06_dlq-operations.md
source:
  - 06_eventbus_02_01_publish-replay.md
---

# Event Bus: DLQ Background Loop

At startup, the DLQ sweep background loop runs as an `asyncio` task, polling every 60 seconds. It searches for events where `delivery_failure_count >= max_retry AND dlq_at IS NULL`, acting as a safety net to catch any events missed by inline processing.

Using optimistic locking, it only targets events where `dlq_at IS NULL` to prevent duplicate promotion. If orphaned events are found, they are recorded in the logs. Any non-zero count may indicate an issue with the inline promotion process.

Promotion follows the same procedure as inline processing (atomic write to JSON file + setting `dlq_at` in SQLite).

## Related Documents

- `06_eventbus_02_03_nack-health-dlq.md`
- `06_eventbus_05_06_dlq-operations.md`
