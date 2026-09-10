## Goal

Extend `scripts/eventbus/broker.py` with three capabilities described in REQ-001, REQ-002, and REQ-005:
1. Add a per-subscriber disconnect signal (`asyncio.Event`) alongside its existing `queue`.
2. On `publish()` `QueueFull`, set that subscriber's disconnect signal and remove it from `self._subscribers` instead of silently dropping the event and continuing.
3. Add a `consumer_id`-keyed registry (`dict[str, _Subscriber]`) to `subscribe()`/`unsubscribe()`.
4. Add overflow-disconnect/duplicate-rejection counters exposed via getter methods.

## Scope

- Add `_Subscriber.disconnect_signal: asyncio.Event` field.
- Add `EventBroker._consumer_registry: dict[str, _Subscriber]` field.
- Modify `EventBroker.publish()` to set disconnect signal and remove subscriber on `QueueFull`.
- Modify `EventBroker.subscribe()` to accept an optional `consumer_id` parameter and check the registry.
- Modify `EventBroker.unsubscribe()` to clear the registry entry when present.
- Add `EventBroker.overflow_disconnect_count` and `EventBroker.duplicate_rejection_count` counters.
- Add getter methods `overflow_disconnect_count()` and `duplicate_rejection_count()`.

## Assumptions

- The `consumer_id` parameter is always a non-empty string when passed to `subscribe()`; empty strings are exempt from duplicate-rejection (matching the Plan's "non-empty consumer ID" framing).
- The disconnect signal is only used by the SSE generator — it does not affect other code paths.
- The registry is single-process (confirmed by `app.py`'s single `EventBroker()` instantiation).

## Design decisions

- **Disconnect signal**: Use `asyncio.Event` as the disconnect signal — it's lightweight, thread-safe within the same event loop, and can be awaited independently of the queue.
- **Registry key**: Use the raw `consumer_id` string as the registry key (no sanitization needed — the caller validates it).
- **Counter placement**: Add counters as instance attributes initialized in `__init__`; expose them via getter methods following the existing pattern (`slow_consumer_count()`).
- **Idempotent unsubscribe**: `unsubscribe()` clears both the subscriber-list entry and the registry key — this is the single release path required by REQ-003.

## Alternatives considered

- **Use a separate channel for disconnect**: e.g., `asyncio.Queue` or `asyncio.Pipe`. Rejected because `asyncio.Event` is simpler and sufficient for a boolean signal.
- **Store registry in app state**: Would require passing the registry through every route handler. Rejected because the Plan's design explicitly places the registry inside `EventBroker`.
- **Add a `consumer_id` field to `_Subscriber`**: Would allow the registry to be keyed by the subscriber itself. Rejected because the registry needs to be keyed by `consumer_id` (not the subscriber object), and the two concerns are distinct.

## Implementation

### Target file

`scripts/eventbus/broker.py`

### Procedure

1. Add `_Subscriber.disconnect_signal` field.
2. Add `EventBroker._consumer_registry` field and counter attributes.
3. Modify `EventBroker.__init__()` to initialize the registry and counters.
4. Modify `EventBroker.subscribe()` to accept `consumer_id` and check the registry.
5. Modify `EventBroker.unsubscribe()` to clear the registry entry.
6. Modify `EventBroker.publish()` to set disconnect signal and remove subscriber on `QueueFull`.
7. Add getter methods for the new counters.

### Method

#### Step 1: Add `_Subscriber.disconnect_signal` field

Change line 15-20:
```python
@dataclass
class _Subscriber:
    """Internal subscriber record holding its delivery queue and topic filter."""

    queue: asyncio.Queue[dict[str, Any] | None]
    topics: list[str]  # empty = all topics
```

to:
```python
@dataclass
class _Subscriber:
    """Internal subscriber record holding its delivery queue and topic filter."""

    queue: asyncio.Queue[dict[str, Any] | None]
    topics: list[str]  # empty = all topics
    disconnect_signal: asyncio.Event = dataclasses.field(default_factory=asyncio.Event)
```

Wait — `_Subscriber` is a `@dataclass`, so we need to add the field properly. Let me revise:

```python
import dataclasses

@dataclass
class _Subscriber:
    """Internal subscriber record holding its delivery queue and topic filter."""

    queue: asyncio.Queue[dict[str, Any] | None]
    topics: list[str]  # empty = all topics
    disconnect_signal: asyncio.Event = dataclasses.field(default_factory=asyncio.Event)
```

Actually, looking at the current code more carefully, `_Subscriber` uses `@dataclass` but doesn't use `dataclasses.field` anywhere. The cleanest approach is to add the field without `default_factory` since `asyncio.Event()` creates a new event each time:

```python
@dataclass
class _Subscriber:
    """Internal subscriber record holding its delivery queue and topic filter."""

    queue: asyncio.Queue[dict[str, Any] | None]
    topics: list[str]  # empty = all topics
    disconnect_signal: asyncio.Event = dataclasses.field(default_factory=asyncio.Event)
```

Hmm, but `asyncio.Event` is not hashable and can't be compared. Since `_Subscriber` is a dataclass, comparing instances would fail if `disconnect_signal` is included. The safest approach is to exclude it from comparison:

```python
@dataclass(frozen=False)
class _Subscriber:
    """Internal subscriber record holding its delivery queue and topic filter."""

    queue: asyncio.Queue[dict[str, Any] | None]
    topics: list[str]  # empty = all topics
    disconnect_signal: asyncio.Event = dataclasses.field(
        default_factory=asyncio.Event, repr=False, compare=False
    )
```

This ensures:
- `repr=False`: The disconnect signal won't appear in `repr(_Subscriber(...))`.
- `compare=False`: The disconnect signal won't participate in equality comparisons (critical since `asyncio.Event` is not comparable).

#### Step 2: Add `EventBroker._consumer_registry` and counter attributes

Change lines 23-28:
```python
class EventBroker:
    """In-memory pub/sub broker with per-subscriber queues and topic filtering."""

    def __init__(self) -> None:
        """Initialize with empty subscriber list."""
        self._subscribers: list[_Subscriber] = []
```

to:
```python
class EventBroker:
    """In-memory pub/sub broker with per-subscriber queues and topic filtering."""

    def __init__(self) -> None:
        """Initialize with empty subscriber list."""
        self._subscribers: list[_Subscriber] = []
        self._consumer_registry: dict[str, _Subscriber] = {}
        self._overflow_disconnect_count: int = 0
        self._duplicate_rejection_count: int = 0
```

#### Step 3: Modify `EventBroker.subscribe()`

Change lines 30-34:
```python
    def subscribe(self, topics: list[str]) -> _Subscriber:
        """Register a new subscriber. topics=[] means all topics."""
        sub = _Subscriber(queue=asyncio.Queue(maxsize=1000), topics=list(topics))
        self._subscribers.append(sub)
        return sub
```

to:
```python
    def subscribe(
        self, topics: list[str], consumer_id: str = ""
    ) -> _Subscriber:
        """Register a new subscriber. topics=[] means all topics.

        Args:
            topics: Topic filter; empty list matches all topics.
            consumer_id: Non-empty consumer identifier; if present, checked against
                the consumer-connection registry. A second concurrent connection for
                the same non-empty consumer_id raises ValueError.

        Returns:
            The newly registered _Subscriber.

        Raises:
            ValueError: If consumer_id is non-empty and already present in the
                consumer-connection registry (duplicate connection attempt).
        """
        # Check consumer-connection registry before subscribing
        if consumer_id and consumer_id in self._consumer_registry:
            self._duplicate_rejection_count += 1
            logger.warning(
                "broker: duplicate consumer_id=%s rejected",
                consumer_id,
            )
            raise ValueError(
                f"duplicate consumer_id: {consumer_id}"
            )

        sub = _Subscriber(queue=asyncio.Queue(maxsize=1000), topics=list(topics))
        self._subscribers.append(sub)

        # Register in consumer-connection registry (only non-empty consumer_id)
        if consumer_id:
            self._consumer_registry[consumer_id] = sub

        return sub
```

#### Step 4: Modify `EventBroker.unsubscribe()`

Change lines 36-41:
```python
    def unsubscribe(self, sub: _Subscriber) -> None:
        """Remove subscriber from the registry. Idempotent."""
        try:
            self._subscribers.remove(sub)
        except ValueError:
            pass
```

to:
```python
    def unsubscribe(self, sub: _Subscriber) -> None:
        """Remove subscriber from the registry. Idempotent.

        Also clears the consumer-connection registry entry if present.
        """
        # Clear consumer-connection registry entry first
        keys_to_remove = [
            cid for cid, s in self._consumer_registry.items() if s is sub
        ]
        for cid in keys_to_remove:
            del self._consumer_registry[cid]

        try:
            self._subscribers.remove(sub)
        except ValueError:
            pass
```

#### Step 5: Modify `EventBroker.publish()`

Change lines 43-61:
```python
    def publish(self, event: dict[str, Any]) -> int:
        """Fan out event to matching subscribers. Returns delivery count."""
        delivered = 0
        event_topic: str = event.get("topic", "")
        for sub in list(
            self._subscribers
        ):  # snapshot to avoid mutation during iteration
            if sub.topics and event_topic not in sub.topics:
                continue
            try:
                sub.queue.put_nowait(event)
                delivered += 1
            except asyncio.QueueFull:
                logger.warning(
                    "broker: queue full sub=%d dropping seq=%s",
                    id(sub),
                    event.get("seq"),
                )
        return delivered
```

to:
```python
    def publish(self, event: dict[str, Any]) -> int:
        """Fan out event to matching subscribers. Returns delivery count.

        On QueueFull, sets the subscriber's disconnect signal and removes it
        from the active-subscriber list instead of silently dropping the event.
        """
        delivered = 0
        event_topic: str = event.get("topic", "")
        for sub in list(
            self._subscribers
        ):  # snapshot to avoid mutation during iteration
            if sub.topics and event_topic not in sub.topics:
                continue
            try:
                sub.queue.put_nowait(event)
                delivered += 1
            except asyncio.QueueFull:
                self._overflow_disconnect_count += 1
                logger.warning(
                    "broker: queue full sub=%d disconnecting seq=%s",
                    id(sub),
                    event.get("seq"),
                )
                # Set disconnect signal and remove subscriber immediately
                sub.disconnect_signal.set()
                self._subscribers.remove(sub)
        return delivered
```

#### Step 6: Add getter methods

After the existing `slow_consumer_count()` method (after line 86):
```python
    def slow_consumer_count(self) -> int:
        """Count subscribers whose queue depth exceeds the slow consumer threshold."""
        return sum(
            1
            for sub in list(self._subscribers)
            if sub.queue.qsize() >= _SLOW_CONSUMER_THRESHOLD
        )

    def overflow_disconnect_count(self) -> int:
        """Return the number of overflow-triggered disconnects."""
        return self._overflow_disconnect_count

    def duplicate_rejection_count(self) -> int:
        """Return the number of duplicate consumer-connection rejections."""
        return self._duplicate_rejection_count
```

### Details

The key changes are:

1. **Disconnect signal**: Added `disconnect_signal: asyncio.Event` field to `_Subscriber` with `repr=False, compare=False` to prevent equality comparison failures (since `asyncio.Event` is not comparable).

2. **Registry**: Added `self._consumer_registry: dict[str, _Subscriber]` keyed by non-empty `consumer_id`. The registry is populated on `subscribe()` and cleared on `unsubscribe()`.

3. **Publish modification**: On `QueueFull`, instead of logging and continuing, the method now:
   - Increments the overflow-disconnect counter.
   - Sets the subscriber's disconnect signal (`sub.disconnect_signal.set()`).
   - Removes the subscriber from `self._subscribers` immediately.

4. **Subscribe modification**: Accepts an optional `consumer_id` parameter. If non-empty and already present in the registry, raises `ValueError` with a warning log. Otherwise, registers the subscriber in both the subscriber list and the registry.

5. **Unsubscribe modification**: Clears the registry entry for the given subscriber before removing it from the subscriber list. This is the single release path required by REQ-003.

6. **Counter getters**: Added `overflow_disconnect_count()` and `duplicate_rejection_count()` following the existing pattern of `slow_consumer_count()`.

## Compatibility considerations

- The `subscribe()` signature change adds an optional `consumer_id=""` parameter — backward compatible with existing callers that don't pass `consumer_id`.
- The `ValueError` raised by `subscribe()` when a duplicate `consumer_id` is detected must be translated into HTTP 409 by the route layer (see subscribe_route.py procedure document).
- The disconnect signal is only used by the SSE generator — it does not affect other code paths.
- The counters follow the existing pattern of `slow_consumer_count()` — plain getter methods returning integer values.

## Security considerations

- No new authentication or authorization boundaries introduced.
- The `consumer_id` parameter is validated as non-empty before registry lookup — no injection risk.
- Table/column naming follows existing conventions.
- No user input flows directly into SQL — schema changes are code-only.

## Rollback considerations

- To rollback: restore the original `_Subscriber` class, `EventBroker.__init__()`, `subscribe()`, `unsubscribe()`, `publish()`, and remove the counter getters.
- The rollback restores the pre-change state where the two-commit gap exists and no consumer-connection tracking is performed.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/broker.py` | Unit test assertions | `uv run pytest tests/eventbus/test_eventbus_broker.py -v` | Registry populate/reject/release and disconnect-signal-on-QueueFull tests pass |
| Full EventBus suite | Regression | `uv run pytest tests/eventbus/ -v` | All pass |

## Completion criteria

- `_Subscriber` has a `disconnect_signal: asyncio.Event` field with `repr=False, compare=False`.
- `EventBroker` has a `_consumer_registry: dict[str, _Subscriber]` field.
- `EventBroker.publish()` sets disconnect signal and removes subscriber on `QueueFull`.
- `EventBroker.subscribe()` accepts `consumer_id` and checks the registry.
- `EventBroker.unsubscribe()` clears the registry entry when present.
- Counter getters `overflow_disconnect_count()` and `duplicate_rejection_count()` are added.
- No regressions in existing tests.

## Out of scope

- Modifying `nack_event()` behavior — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.
- Modifying the SSE generator race logic — covered by a separate procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add disconnect_signal field to _Subscriber | Completed | — | — | |
| 2 | Add _consumer_registry and counter attributes | Completed | — | — | |
| 3 | Modify subscribe() to accept consumer_id and check registry | Completed | — | — | |
| 4 | Modify unsubscribe() to clear registry entry | Completed | — | — | |
| 5 | Modify publish() to set disconnect signal on QueueFull | Completed | — | — | |
| 6 | Add counter getter methods | Completed | — | — | |
| 7 | Run validation (pytest + regression check) | Completed | — | — | Pre-existing errors in other tests (auth_token/middleware) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-005
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-161316
- **Related target files**: scripts/eventbus/broker.py
