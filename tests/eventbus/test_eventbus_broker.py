from __future__ import annotations

import asyncio

import pytest
from eventbus.broker import EventBroker


@pytest.mark.asyncio
async def test_fan_out_all_subscribers():
    broker = EventBroker()
    sub1 = broker.subscribe([])
    sub2 = broker.subscribe([])
    broker.publish({"seq": 1, "topic": "t", "event_id": "a"})
    assert sub1.queue.qsize() == 1
    assert sub2.queue.qsize() == 1


@pytest.mark.asyncio
async def test_topic_filter_excludes_non_matching():
    broker = EventBroker()
    sub_t = broker.subscribe(["target"])
    sub_all = broker.subscribe([])
    broker.publish({"seq": 1, "topic": "other", "event_id": "a"})
    assert sub_t.queue.empty()  # filtered out
    assert sub_all.queue.qsize() == 1  # all-topics subscriber receives it


@pytest.mark.asyncio
async def test_topic_filter_delivers_matching():
    broker = EventBroker()
    sub = broker.subscribe(["target"])
    broker.publish({"seq": 1, "topic": "target", "event_id": "a"})
    assert sub.queue.qsize() == 1


@pytest.mark.asyncio
async def test_unsubscribe_stops_delivery():
    broker = EventBroker()
    sub = broker.subscribe([])
    broker.unsubscribe(sub)
    broker.publish({"seq": 1, "topic": "t", "event_id": "a"})
    assert sub.queue.empty()


@pytest.mark.asyncio
async def test_unsubscribe_idempotent():
    broker = EventBroker()
    sub = broker.subscribe([])
    broker.unsubscribe(sub)
    broker.unsubscribe(sub)  # should not raise


@pytest.mark.asyncio
async def test_shutdown_sends_sentinel():
    broker = EventBroker()
    sub = broker.subscribe([])
    broker.shutdown()
    sentinel = await asyncio.wait_for(sub.queue.get(), timeout=1.0)
    assert sentinel is None


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
