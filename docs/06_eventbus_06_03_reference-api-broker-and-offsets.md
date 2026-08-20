---
title: "Event Bus: Reference API — Broker and Offsets"
category: eventbus
tags:
  - event-bus
  - api-reference
  - broker
  - offsets
  - eventbroker
  - subscriber
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_06_01_reference-api-core-modules.md
  - 06_eventbus_06_02_reference-api-route-handlers.md
source:
  - 06_eventbus_06_01_reference-api-core-modules.md
---

# Event Bus: Reference API — Broker and Offsets

## scripts/eventbus/broker.py

`_Subscriber`: Internal data structure holding the queue and topic list. `EventBroker`: In-memory pub/sub broker with topic-based fanout.

Methods: `subscribe(topics→_Subscriber)`, `unsubscribe(sub→None)`, `publish(event→int)`, `shutdown()`, `subscriber_count()→int`, `max_queue_depth()→int`, `slow_consumer_count()→int`.

## scripts/eventbus/offsets.py

`read_offset(offsets_dir, consumer_id)→int`: Reads saved offset (returns 0 if not found). `write_offset(offsets_dir, consumer_id, seq)→None`: Only writes to file if `seq` is greater than the current committed offset. Skips and logs a warning if `seq <= current` (ensures monotonicity).

## Related Documents

- `06_eventbus_06_01_reference-api-core-modules.md`
- `06_eventbus_06_02_reference-api-route-handlers.md`
