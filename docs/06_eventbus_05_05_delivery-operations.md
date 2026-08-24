---
title: "Event Bus: Delivery Operations"
area: eventbus
tags:
  - event-bus
  - delivery
  - verification
  - slow-consumer
  - reconnect-recovery
  - subscriber-count
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_05_03_health-endpoint-semantics.md
  - 06_eventbus_05_04_consumer-id-stability.md
  - 06_eventbus_05_06_dlq-operations.md
source:
  - 06_eventbus_05_01_config-env-and-fields.md
---

# Event Bus: Delivery Operations

## Delivery Operations

### Verifying Delivery

Verify live push using `GET /subscribe?consumer_id=test`. Events should be received within one loop tick after publishing.

### Monitoring Slow Consumers

A process queue exceeding 100 events is considered slow. This can be verified via the health endpoint:

- `slow_consumers > 0` → `degraded`
- `max_queue_depth >= 500` → `broker_queue_backlog_high`

If a consumer is slow, events are discarded from the queue. The consumer must reconnect and replay from SQLite.

### Recovery on Reconnection

Reconnecting with a `consumer_id` resumes from the last acknowledged offset. If no offsets have been acknowledged, it starts from `seq=0`. It is also possible to start from a specific position using `since_seq=N`.

### Subscriber Count

When the count is 0, the broker is idle. Events remain in SQLite and are available for replay upon the next connection.

## Related Documents

- `06_eventbus_05_03_health-endpoint-semantics.md`
- `06_eventbus_05_04_consumer-id-stability.md`
- `06_eventbus_05_06_dlq-operations.md`
