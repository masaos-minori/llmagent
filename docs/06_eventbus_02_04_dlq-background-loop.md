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
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_03_nack-health-dlq.md
  - 06_eventbus_05_06_dlq-operations.md
source:
  - 06_eventbus_02_01_publish-replay.md
---

# Event Bus: DLQ Background Loop

At startup, the DLQ sweep background loop runs as an asyncio task, polling every 60 seconds. It queries for events with `delivery_failure_count >= max_retry AND dlq_at IS NULL` — these are events that reached the retry threshold but were not promoted inline (e.g., due to a race).

The loop uses an optimistic lock: only counts events where `dlq_at` is still NULL, preventing double-promotion. If the sweep finds orphans, it logs `"dlq_loop: swept %d orphan(s) missed by inline promotion"`. Non-zero sweep results may indicate an inline promotion issue.

Promotion actions are the same as inline: write JSONL file atomically, set `dlq_at` in SQLite.

## Related Documents

- `06_eventbus_02_03_nack-health-dlq.md`
- `06_eventbus_05_06_dlq-operations.md`

## Keywords

event-bus
dlq
dead-letter-queue
background-loop
safety-sweep
optimistic-lock
orphan-promotion
