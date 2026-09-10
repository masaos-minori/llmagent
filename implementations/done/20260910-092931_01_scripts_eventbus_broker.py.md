## Goal
Make `EventBroker` fail safely on backpressure and enforce one-connection-per-
`consumer_id`: add a per-subscriber disconnect signal that fires on queue overflow
instead of silently dropping-and-continuing (REQ-001), add a `consumer_id`-keyed
registry rejecting a duplicate non-empty key (REQ-002), release both on
`unsubscribe()` (REQ-003), and add observable counters for both events (REQ-005).

## Scope
In scope: `_Subscriber`, `EventBroker.__init__`/`subscribe`/`unsubscribe`/`publish`,
and new counter accessors. Out of scope: `EventBroker.shutdown()`'s own
`except asyncio.QueueFull: pass` — a related but distinct pre-existing gap the Plan's
Risks explicitly defer; `max_queue_depth()`/`slow_consumer_count()` — unchanged,
capacity-limit/threshold configuration stays hardcoded per Plan Out-of-Scope.

## Assumptions
- `_SLOW_CONSUMER_THRESHOLD`/`maxsize=1000` remain hardcoded literals in this file —
  no new `EventBusConfig` field is introduced (confirmed: `EventBusConfig` has no
  queue-maxsize/threshold field today).
- A single in-process `EventBroker` instance is the sole place `consumer_id`
  connection state needs to live (confirmed via `app.py`'s single
  `app.state.broker = EventBroker()`).

## Design decisions
- **Disconnect signal, not a queue sentinel.** `_Subscriber` gains a `disconnect:
  asyncio.Event` field alongside its existing `queue`. `publish()`, on
  `asyncio.QueueFull`, sets `sub.disconnect.set()` and removes `sub` from
  `self._subscribers` immediately — it does not attempt `put_nowait()` again, since the
  queue is by definition already full. A full queue cannot carry a `None` sentinel
  without evicting buffered data, which is why `shutdown()`'s existing sentinel
  approach cannot be reused for the overflow path (this is the corrected version of the
  Issue's own suggested "reuse the shutdown sentinel pattern," per the Plan's
  Implementation intent).
- **Consumer-ID registry.** `EventBroker` gains `self._consumer_subs: dict[str,
  _Subscriber]`. `subscribe(topics, consumer_id="")` — empty string is never
  registered (anonymous connections are exempt from duplicate-rejection) — checks the
  registry before appending to `self._subscribers`; a non-empty key already present
  raises a dedicated exception (e.g. `ConsumerAlreadyConnectedError`), which the route
  layer (row 02) translates into HTTP 409, following the existing
  `HTTPException(status_code=409, ...)` pattern in `dlq_route.py`.
- **Release path stays singular.** `unsubscribe()` removes both the subscriber-list
  entry and, when present, its registry key — no second release call site is added
  (REQ-003).
- **Counters.** Add `self._overflow_disconnect_count` and
  `self._duplicate_rejection_count` integer counters, incremented at the exact points
  `publish()` disconnects on overflow and `subscribe()` rejects a duplicate,
  respectively; expose via plain getter methods matching `slow_consumer_count()`'s
  existing pattern (a plain field read, no new branching in `health_route.py`, row 03).

## Alternatives considered
Using a second `asyncio.Queue` per subscriber as the disconnect channel (instead of
`asyncio.Event`) was considered and rejected: an `Event` is simpler, has no capacity to
overflow, and the SSE generator (row 02) only needs a wait-until-set signal, not a
message payload.

## Implementation
### Target file
`scripts/eventbus/broker.py`

### Procedure
1. Add `disconnect: asyncio.Event = field(default_factory=asyncio.Event)` to
   `_Subscriber` (requires `from dataclasses import field` alongside the existing
   `dataclass` import).
2. Add a module-level exception class `ConsumerAlreadyConnectedError(Exception)` (or
   equivalent) for `subscribe()` to raise on a duplicate non-empty `consumer_id`.
3. Add `self._consumer_subs: dict[str, _Subscriber] = {}` and two counters to
   `EventBroker.__init__`.
4. Extend `subscribe(topics, consumer_id="")`: if `consumer_id` and `consumer_id in
   self._consumer_subs`, increment the duplicate-rejection counter and raise
   `ConsumerAlreadyConnectedError`; otherwise create `sub`, append to
   `self._subscribers`, and if `consumer_id`, also set
   `self._consumer_subs[consumer_id] = sub`.
5. Extend `unsubscribe(sub)`: after removing from `self._subscribers`, also remove
   `sub` from `self._consumer_subs` by value (iterate or track the reverse mapping —
   simplest: store `consumer_id` on `_Subscriber` itself so `unsubscribe()` can pop by
   key directly).
6. Extend `publish()`'s `except asyncio.QueueFull:` branch: instead of only logging,
   also call `sub.disconnect.set()`, remove `sub` from `self._subscribers` (safe since
   `publish()` already iterates a snapshot `list(self._subscribers)`), and increment
   the overflow-disconnect counter. Leave the existing `logger.warning(...)` call in
   place (still useful operationally) or upgrade it to reflect the disconnect action.
7. Add `overflow_disconnect_count()` and `duplicate_rejection_count()` getter methods,
   matching `slow_consumer_count()`'s existing style.

### Method
Extends the existing `dataclass`/plain-class style; no new abstraction beyond one
small exception class.

### Details
```python
from dataclasses import dataclass, field

@dataclass
class _Subscriber:
    queue: asyncio.Queue[dict[str, Any] | None]
    topics: list[str]
    consumer_id: str = ""
    disconnect: asyncio.Event = field(default_factory=asyncio.Event)


class ConsumerAlreadyConnectedError(Exception):
    """Raised when a second connection attempts the same non-empty consumer_id."""


class EventBroker:
    def __init__(self) -> None:
        self._subscribers: list[_Subscriber] = []
        self._consumer_subs: dict[str, _Subscriber] = {}
        self._overflow_disconnect_count = 0
        self._duplicate_rejection_count = 0

    def subscribe(self, topics: list[str], consumer_id: str = "") -> _Subscriber:
        if consumer_id and consumer_id in self._consumer_subs:
            self._duplicate_rejection_count += 1
            raise ConsumerAlreadyConnectedError(consumer_id)
        sub = _Subscriber(
            queue=asyncio.Queue(maxsize=1000), topics=list(topics), consumer_id=consumer_id
        )
        self._subscribers.append(sub)
        if consumer_id:
            self._consumer_subs[consumer_id] = sub
        return sub

    def unsubscribe(self, sub: _Subscriber) -> None:
        try:
            self._subscribers.remove(sub)
        except ValueError:
            pass
        if sub.consumer_id:
            self._consumer_subs.pop(sub.consumer_id, None)

    def publish(self, event: dict[str, Any]) -> int:
        delivered = 0
        event_topic: str = event.get("topic", "")
        for sub in list(self._subscribers):
            if sub.topics and event_topic not in sub.topics:
                continue
            try:
                sub.queue.put_nowait(event)
                delivered += 1
            except asyncio.QueueFull:
                logger.warning(
                    "broker: queue full sub=%d disconnecting seq=%s",
                    id(sub), event.get("seq"),
                )
                sub.disconnect.set()
                self.unsubscribe(sub)
                self._overflow_disconnect_count += 1
        return delivered

    def overflow_disconnect_count(self) -> int:
        return self._overflow_disconnect_count

    def duplicate_rejection_count(self) -> int:
        return self._duplicate_rejection_count
```

## Compatibility considerations
`subscribe(topics)` (no `consumer_id`) remains valid — default `""` preserves today's
anonymous-connection behavior exactly. Existing callers of `unsubscribe()`/
`subscriber_count()`/`max_queue_depth()`/`slow_consumer_count()` are unaffected.

## Security considerations
`consumer_id` is bound only as a dict key (no SQL/filesystem interpolation in this
file) — no injection surface introduced.

## Rollback considerations
Revert this file's diff. Since `subscribe_route.py` (row 02) is the only caller
passing a non-empty `consumer_id`, reverting both files together restores today's
anonymous-only, drop-and-continue behavior with no persistent state to clean up (all
state here is in-memory).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_broker.py -v` (row 05): registry
  populate/reject/release and disconnect-signal-on-`QueueFull` unit tests.
- `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py -v` (row 04): overflow
  now actually disconnects the subscriber.

## Completion criteria
A second `subscribe()` call with the same non-empty `consumer_id` raises before a
first successful connection's registration is released (AC-3); `publish()` on
`QueueFull` sets the disconnect signal and removes the subscriber instead of
continuing to attempt delivery (AC-1); `unsubscribe()` always clears both the
subscriber list and the registry entry, with no leak across repeated
subscribe/unsubscribe cycles (AC-4); both counters are observable via getters (AC-5).

## Out of scope
`shutdown()`'s own `except asyncio.QueueFull: pass` swallow — not modified by this
Plan (see Plan Risks). `max_queue_depth()`/`slow_consumer_count()`/threshold constants
— unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `disconnect`/`consumer_id` fields to `_Subscriber` | Completed | — | — | |
| 2 | Add `_consumer_subs` registry + counters to `EventBroker.__init__` | Completed | — | — | |
| 3 | Extend `subscribe()` with duplicate-rejection check | Completed | — | — | |
| 4 | Extend `unsubscribe()` to clear the registry entry | Completed | — | — | |
| 5 | Extend `publish()`'s `QueueFull` branch to disconnect instead of continue | Completed | — | — | |
| 6 | Add counter getter methods | Completed | — | — | |
| 7 | Add or update tests per Validation plan (rows 04, 05) | Completed | — | — | |
| 8 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-005
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092931
- **Related target files**: scripts/eventbus/broker.py
