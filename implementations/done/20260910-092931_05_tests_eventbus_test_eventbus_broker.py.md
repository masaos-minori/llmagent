## Goal
Add `EventBroker`-level unit tests for `consumer_id` registry population/release and
the disconnect-signal race, independent of the HTTP layer (REQ-001, REQ-002, REQ-003,
REQ-006; AC1, AC3, AC4).

## Scope
In scope: new test functions in this file. Out of scope:
`test_fan_out_all_subscribers`, `test_topic_filter_excludes_non_matching`,
`test_topic_filter_delivers_matching`, `test_unsubscribe_stops_delivery`,
`test_unsubscribe_idempotent`, `test_shutdown_sends_sentinel` — these six existing
tests continue to pass unmodified.

## Assumptions
- This file's existing tests are plain `async def test_*` functions (no test class),
  instantiating `EventBroker()` directly — the new tests follow the same style.

## Design decisions
Add tests for:
1. Registry population: `subscribe(topics, consumer_id="c1")` records `c1` in the
   registry (verify indirectly via a second `subscribe(topics, consumer_id="c1")`
   raising).
2. Duplicate rejection: a second `subscribe()` call with the same non-empty
   `consumer_id` raises `ConsumerAlreadyConnectedError` while the first remains
   registered (AC3).
3. Registry release: `unsubscribe(sub)` clears the registry entry, confirmed by a
   subsequent `subscribe()` with the same `consumer_id` succeeding (AC4).
4. Anonymous exemption: two `subscribe(topics, consumer_id="")` calls both succeed
   (empty string is never registered).
5. Disconnect-signal firing: `publish()` on a full queue sets `sub.disconnect` and
   removes the subscriber from future deliveries (AC1) — confirmed via
   `subscriber_count()` decreasing and `sub.disconnect.is_set()` being `True`.

## Alternatives considered
Testing the disconnect-signal race (`asyncio.wait` in `subscribe_route.py`) at this
file's level was considered and rejected: that race lives in `subscribe_route.py`
(row 02), not `EventBroker` itself — this file tests only that `broker.py` sets the
signal correctly, not the SSE generator's consumption of it (covered by row 04/06's
tests instead).

## Implementation
### Target file
`tests/eventbus/test_eventbus_broker.py`

### Procedure
Add five `async def test_*` functions following this file's existing style (direct
`EventBroker()` instantiation, no fixture indirection beyond what existing tests use).

### Method
`pytest-asyncio` test functions, matching the file's existing `async def test_*`
pattern exactly.

### Details
```python
async def test_consumer_id_registry_rejects_duplicate():
    broker = EventBroker()
    broker.subscribe([], consumer_id="c1")
    with pytest.raises(ConsumerAlreadyConnectedError):
        broker.subscribe([], consumer_id="c1")


async def test_consumer_id_registry_releases_on_unsubscribe():
    broker = EventBroker()
    sub = broker.subscribe([], consumer_id="c1")
    broker.unsubscribe(sub)
    # should succeed now that c1 was released
    broker.subscribe([], consumer_id="c1")


async def test_empty_consumer_id_is_never_registered():
    broker = EventBroker()
    broker.subscribe([], consumer_id="")
    broker.subscribe([], consumer_id="")  # both succeed, no rejection


async def test_publish_disconnects_subscriber_on_queue_full():
    broker = EventBroker()
    sub = broker.subscribe([])
    for i in range(1000):
        broker.publish({"topic": "", "seq": i})
    broker.publish({"topic": "", "seq": 1000})  # triggers QueueFull
    assert sub.disconnect.is_set()
    assert broker.subscriber_count() == 0
    assert broker.overflow_disconnect_count() == 1
```
Adapt exact event-count/topic values to whatever this file's existing tests already
use for constructing a minimal event dict.

## Compatibility considerations
No existing test in this file is modified.

## Security considerations
Test-only file; no production security surface.

## Rollback considerations
Revert this file's diff; no production behavior depends on this file.

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_broker.py -v` — all tests (six existing +
five new) pass.

## Completion criteria
All five new tests pass, confirming registry population/rejection/release, the
anonymous-connection exemption, and the disconnect-signal-on-`QueueFull` behavior
(AC1, AC3, AC4).

## Out of scope
The six pre-existing tests in this file — unmodified.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_consumer_id_registry_rejects_duplicate` | Completed | — | — | |
| 2 | Add `test_consumer_id_registry_releases_on_unsubscribe` | Completed | — | — | |
| 3 | Add `test_empty_consumer_id_is_never_registered` | Completed | — | — | |
| 4 | Add `test_publish_disconnects_subscriber_on_queue_full` | Completed | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-006
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092931
- **Related target files**: tests/eventbus/test_eventbus_broker.py
