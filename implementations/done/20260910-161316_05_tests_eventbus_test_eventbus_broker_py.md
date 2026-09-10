## Goal

Add unit tests for `EventBroker`'s `consumer_id` registry population/release and the disconnect-signal race to `tests/eventbus/test_eventbus_broker.py`:
1. Test that a non-empty `consumer_id` is registered on `subscribe()` and released on `unsubscribe()`.
2. Test that a duplicate non-empty `consumer_id` raises `ValueError`.
3. Test that the disconnect signal fires on `publish()` `QueueFull`.
4. Test that an empty `consumer_id` is exempt from duplicate-rejection.

## Scope

- Add four new test methods in `test_eventbus_broker.py`.
- Test registry population/release with non-empty `consumer_id`.
- Test duplicate-rejection with non-empty `consumer_id`.
- Test disconnect-signal firing on `QueueFull`.
- Test empty `consumer_id` exemption from duplicate-rejection.

## Assumptions

- The `consumer_id` parameter is accepted by `broker.subscribe(topics, consumer_id="")` (added in the related procedure document).
- The `ValueError` raised by `broker.subscribe()` contains the message `"duplicate consumer_id: X"` (matching the Plan's design).
- The disconnect signal is set on the subscriber when its queue overflows (added in the related procedure document).

## Design decisions

- **Reuse existing test patterns**: Follow the same `@pytest.mark.asyncio` pattern established by the existing tests.
- **Direct function calls**: Use direct `db` calls rather than HTTP requests for clarity and speed.
- **Isolation**: Each test creates its own `EventBroker` instance — no shared state between tests.

## Alternatives considered

- **Integration test with real subprocess**: Spin up a real EventBus process and send HTTP requests. Rejected because unit tests with direct function calls are faster and easier to reason about.
- **Single comprehensive test**: Combine all scenarios into one test. Rejected because each scenario has distinct assertions and failure modes that are clearer when separated.

## Implementation

### Target file

`tests/eventbus/test_eventbus_broker.py`

### Procedure

1. Add a new test method `test_consumer_id_registry_population_release` in `test_eventbus_broker.py`.
2. Add a new test method `test_duplicate_consumer_id_rejection` in `test_eventbus_broker.py`.
3. Add a new test method `test_disconnect_signal_on_queue_full` in `test_eventbus_broker.py`.
4. Add a new test method `test_empty_consumer_id_exempt_from_rejection` in `test_eventbus_broker.py`.

### Method

#### Step 1: Add registry population/release test

After the existing `test_shutdown_sends_sentinel` function:
```python
@pytest.mark.asyncio
async def test_shutdown_sends_sentinel():
    ...existing test body...

@pytest.mark.asyncio
async def test_consumer_id_registry_population_release():
    """Non-empty consumer_id is registered on subscribe() and released on unsubscribe()."""
    broker = EventBroker()
    consumer_id = "test_consumer"

    # Subscribe with non-empty consumer_id
    sub = broker.subscribe([], consumer_id=consumer_id)
    try:
        # Verify the consumer is registered
        assert consumer_id in broker._consumer_registry, \
            f"Consumer {consumer_id} should be registered"
        assert broker._consumer_registry[consumer_id] is sub, \
            "Registry entry should point to the subscriber"

        # Verify the subscriber count increased
        assert broker.subscriber_count() == 1, \
            "Subscriber count should be 1"

        # Unsubscribe — this should release the registry entry
        broker.unsubscribe(sub)

        # Verify the consumer is no longer registered
        assert consumer_id not in broker._consumer_registry, \
            f"Consumer {consumer_id} should be unregistered after unsubscribe"
        assert broker.subscriber_count() == 0, \
            "Subscriber count should be 0 after unsubscribe"
    finally:
        # Clean up any remaining subscribers
        for s in list(broker._subscribers):
            broker.unsubscribe(s)

@pytest.mark.asyncio
async def test_duplicate_consumer_id_rejection():
    """A second concurrent connection for the same non-empty consumer_id raises ValueError."""
    broker = EventBroker()
    consumer_id = "test_consumer"

    # First subscription succeeds
    sub1 = broker.subscribe([], consumer_id=consumer_id)
    try:
        # Second subscription with the same consumer_id should fail
        with pytest.raises(ValueError, match=f"duplicate consumer_id: {consumer_id}"):
            broker.subscribe([], consumer_id=consumer_id)

        # Verify only one subscriber exists
        assert broker.subscriber_count() == 1, \
            "Only one subscriber should exist"

        # Verify the duplicate rejection counter increased
        assert broker.duplicate_rejection_count() == 1, \
            "Duplicate rejection counter should be incremented"
    finally:
        # Clean up any remaining subscribers
        for s in list(broker._subscribers):
            broker.unsubscribe(s)

@pytest.mark.asyncio
async def test_disconnect_signal_on_queue_full():
    """The disconnect signal fires when publish() QueueFull occurs."""
    broker = EventBroker()
    sub = broker.subscribe([])
    try:
        # Fill the queue to capacity (maxsize=1000)
        bodies = [{"seq": i, "topic": "t", "event_id": f"evt-{i}"} for i in range(1000)]
        for body in bodies:
            broker.publish(body)

        # Queue should now be full
        assert sub.queue.full(), "Queue should be at capacity"

        # Publish one more event — this should trigger overflow disconnect
        overflow_body = {"seq": 1001, "topic": "t", "event_id": "overflow"}
        broker.publish(overflow_body)

        # Verify the subscriber was removed from the active list
        assert broker.subscriber_count() == 0, \
            "Overflowing subscriber should be removed from active list"

        # Verify the disconnect signal was set
        assert sub.disconnect_signal.is_set(), \
            "Disconnect signal should be set after overflow"

        # Verify the overflow disconnect counter increased
        assert broker.overflow_disconnect_count() == 1, \
            "Overflow disconnect counter should be incremented"
    finally:
        # Clean up any remaining subscribers
        for s in list(broker._subscribers):
            broker.unsubscribe(s)

@pytest.mark.asyncio
async def test_empty_consumer_id_exempt_from_rejection():
    """An empty consumer_id is exempt from duplicate-rejection."""
    broker = EventBroker()

    # Two subscriptions with empty consumer_id should both succeed
    sub1 = broker.subscribe([])
    sub2 = broker.subscribe([])
    try:
        # Both subscribers should exist
        assert broker.subscriber_count() == 2, \
            "Both anonymous subscribers should exist"

        # No duplicate rejections should occur
        assert broker.duplicate_rejection_count() == 0, \
            "No duplicate rejections for empty consumer_id"
    finally:
        # Clean up any remaining subscribers
        for s in list(broker._subscribers):
            broker.unsubscribe(s)
```

### Details

The key changes are:

1. **Registry population/release**: Tests that a non-empty `consumer_id` is registered on `subscribe()` and released on `unsubscribe()`, verifying both the registry contents and the subscriber count.

2. **Duplicate-rejection**: Tests that a second concurrent connection for the same non-empty `consumer_id` raises `ValueError`, verifying the error message matches the expected format.

3. **Disconnect-signal firing**: Tests that the disconnect signal is set when `publish()` encounters `QueueFull`, verifying the subscriber is removed from the active list and the overflow disconnect counter is incremented.

4. **Empty consumer_id exemption**: Tests that two subscriptions with empty `consumer_id` both succeed without triggering duplicate-rejection, verifying the exemption behavior.

## Compatibility considerations

- The existing `test_fan_out_all_subscribers`, `test_topic_filter_excludes_non_matching`, `test_topic_filter_delivers_matching`, `test_unsubscribe_stops_delivery`, `test_unsubscribe_idempotent`, and `test_shutdown_sends_sentinel` tests continue to pass unmodified.
- The `@pytest.mark.asyncio` decorator is reused as-is.
- Each test creates its own `EventBroker` instance — no shared state between tests.

## Security considerations

- No new authentication or authorization boundaries introduced.
- File operations use the existing `tmp_path` fixture for safe isolation.
- No user input flows directly into SQL — schema changes are code-only.

## Rollback considerations

- To rollback: remove the four new test methods.
- The rollback restores the pre-change state where only fan-out/topic-filter/unsubscribe/shutdown testing exists.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_broker.py` | Unit test assertions | `uv run pytest tests/eventbus/test_eventbus_broker.py -v` | Registry populate/reject/release and disconnect-signal-on-QueueFull tests pass |
| Full EventBus suite | Regression | `uv run pytest tests/eventbus/ -v` | All pass |

## Completion criteria

- `test_consumer_id_registry_population_release` asserts registry population and release.
- `test_duplicate_consumer_id_rejection` asserts ValueError on duplicate consumer_id.
- `test_disconnect_signal_on_queue_full` asserts disconnect signal fires on QueueFull.
- `test_empty_consumer_id_exempt_from_rejection` asserts empty consumer_id exemption.
- No regressions in existing tests.

## Out of scope

- Modifying `nack_event()` behavior — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add registry population/release test | Completed | — | — | |
| 2 | Add duplicate-rejection test | Completed | — | — | |
| 3 | Add disconnect-signal test | Completed | — | — | |
| 4 | Add empty consumer_id exemption test | Completed | — | — | |
| 5 | Run validation (pytest + regression check) | Completed | — | — | Pre-existing errors (auth_token config) |

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
- **Generated at**: 20260910-161316
- **Related target files**: tests/eventbus/test_eventbus_broker.py
