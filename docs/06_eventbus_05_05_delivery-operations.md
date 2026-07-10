---
title: "Event Bus: Delivery Operations"
category: eventbus
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

### Verifying delivery

After enabling the in-memory broker, confirm live push is working:

```bash
# Terminal 1: subscribe (hold connection open)
curl -N "http://localhost:8010/subscribe?consumer_id=test-consumer"

# Terminal 2: publish
curl -X POST http://localhost:8010/publish \
  -H "Content-Type: application/json" \
  -d '{"event_id":"test-001","topic":"test","payload":{},"producer":"ops","published_at":"2026-06-25T12:00:00Z"}'
```

The event should appear in Terminal 1 within one event-loop tick (< 1 ms typical latency on localhost).

### Monitoring slow consumers

Slow consumers are those whose in-process queue depth reaches >= 100 events. Check via health endpoint:

```bash
curl http://localhost:8010/health | jq '.slow_consumers, .max_queue_depth, .active_subscribers'
```

**Thresholds:**
- `slow_consumers > 0` → `degraded_reasons` includes `slow_consumers_detected`
- `max_queue_depth >= 500` → `degraded_reasons` includes `broker_queue_backlog_high`

When a consumer is slow, events are dropped from the in-process queue (logged as WARNING). The consumer must reconnect to replay missed events from SQLite.

### Reconnect recovery

If a subscriber disconnects, it can resume without missing events:

```bash
# Reconnect with consumer_id — replays from last acked offset automatically
curl -N "http://localhost:8010/subscribe?consumer_id=my-consumer"
```

If the consumer has never acked any events, replay starts from seq=0 (all events). To start from a specific point:

```bash
curl -N "http://localhost:8010/subscribe?consumer_id=my-consumer&since_seq=100"
```

### Checking subscriber count

```bash
curl http://localhost:8010/health | jq '.active_subscribers'
```

Zero subscribers means the broker is idle. Events are still persisted to SQLite and available for replay on next connect.

## Related Documents

- `06_eventbus_05_03_health-endpoint-semantics.md`
- `06_eventbus_05_04_consumer-id-stability.md`
- `06_eventbus_05_06_dlq-operations.md`

## Keywords

event-bus
delivery
verification
slow-consumer
reconnect-recovery
subscriber-count
