# Implementation: docs/06_eventbus_06_reference_api.md — EventBroker API reference (req #44)

## Goal

Add a module-level reference section for `scripts/eventbus/broker.py`: module vars, classes, methods, and integration points.

## Scope

- New section in the Reference API doc: `scripts/eventbus/broker.py`
- Document: `_Subscriber` dataclass, `EventBroker` class, all public methods
- Document integration points: imported by `app.py`, called in publish() and subscribe()

## Assumptions

- req #35, #39, #42 define the full broker API
- The doc uses the same format as other module sections (module-level var table + function table)

## Implementation

### Target file

`docs/06_eventbus_06_reference_api.md`

### Procedure

1. Add new section after `scripts/eventbus/offsets.py` reference
2. Document module-level var, classes, and public methods

### Method

Append new section to reference doc.

### Details

**New section to add:**

---

## `scripts/eventbus/broker.py`

### Module-level

| Name | Type | Description |
|---|---|---|
| _(none)_ | — | No module-level globals; `EventBroker` is instantiated at runtime |

### Classes

#### `_Subscriber`

```python
@dataclass
class _Subscriber:
    queue: asyncio.Queue[dict[str, Any] | None]
    topics: list[str]
```

Internal dataclass. `topics=[]` means all topics. Do not construct directly; use `EventBroker.subscribe()`.

#### `EventBroker`

In-process publish/subscribe broker. One instance lives as `app._broker` for the lifetime of the server process.

**Methods:**

| Method | Signature | Description |
|---|---|---|
| `subscribe` | `(topics: list[str]) -> _Subscriber` | Register a new subscriber. Returns `_Subscriber` with a maxsize=1000 queue. |
| `unsubscribe` | `(sub: _Subscriber) -> None` | Remove subscriber. Idempotent (no-op if not found). |
| `publish` | `(event: dict[str, Any]) -> int` | Fan-out event to all matching subscribers. Returns delivered count. Drops to `QueueFull` subscribers with a WARNING log. |
| `shutdown` | `() -> None` | Push `None` sentinel to all subscriber queues to unblock `queue.get()` on lifespan teardown. |
| `subscriber_count` | `() -> int` | Number of active (registered) subscribers. |
| `max_queue_depth` | `() -> int` | Largest queue depth across all subscribers. 0 if no subscribers. |
| `slow_consumer_count` | `(threshold: int = 100) -> int` | Number of subscribers with `queue.qsize() >= threshold`. |

**Topic filter semantics:**
- `topics=[]`: receives all events (wildcard)
- `topics=["foo", "bar"]`: receives events where `event["topic"] in topics` (exact match, case-sensitive)

**Integration points:**
- `app.py`: `_broker = EventBroker()` in lifespan startup
- `app.py publish()`: calls `_broker.publish(event_dict)` after SQLite commit
- `app.py subscribe()`: calls `_broker.subscribe(topics)` before replay; `_broker.unsubscribe(sub)` in finally
- `app.py health()`: calls `subscriber_count()`, `max_queue_depth()`, `slow_consumer_count()`
- `app.py lifespan teardown`: calls `_broker.shutdown()`

---

## Validation plan

| Check | Target |
|---|---|
| Section present | `grep "EventBroker" docs/06_eventbus_06_reference_api.md` → matches |
| All public methods documented | 7 methods listed in table |
| Integration points listed | publish, subscribe, health, shutdown wiring noted |
