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

| Class | Description |
|---|---|
| `_Subscriber` | Internal dataclass: `queue: asyncio.Queue[dict \| None]`, `topics: list[str]` (empty = all topics) |
| `EventBroker` | In-memory pub/sub broker with topic-aware fan-out |

### EventBroker methods

| Method | Signature | Description |
|---|---|---|
| `subscribe` | `(topics: list[str]) -> _Subscriber` | Register a new subscriber; topics=[] means all topics |
| `unsubscribe` | `(sub: _Subscriber) -> None` | Remove subscriber from the registry; idempotent |
| `publish` | `(event: dict[str, Any]) -> int` | Fan out event to matching subscribers; returns delivery count |
| `shutdown` | `() -> None` | Send None sentinel to all subscribers to unblock their queue.get() calls |
| `subscriber_count` | `() -> int` | Return number of active subscribers |
| `max_queue_depth` | `() -> int` | Return max queue depth across all subscribers |
| `slow_consumer_count` | `() -> int` | Return count of subscribers with queue depth >= 100 |

---

## scripts/eventbus/offsets.py

| Function | Signature | Description |
|---|---|---|
| `read_offset` | `(offsets_dir, consumer_id) -> int` | Read saved offset; returns 0 if not found |
| `write_offset` | `(offsets_dir, consumer_id, seq) -> None` | Write offset to file; creates directory if needed |

## Related Documents

- `06_eventbus_06_01_reference-api-core-modules.md`
- `06_eventbus_06_02_reference-api-route-handlers.md`

## Keywords

event-bus
api-reference
broker
offsets
eventbroker
subscriber
