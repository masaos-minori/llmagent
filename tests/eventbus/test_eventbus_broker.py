from __future__ import annotations

import asyncio

import pytest
from eventbus.broker import ConsumerAlreadyConnectedError, EventBroker
from eventbus.config import EventBusConfig


def _make_config() -> EventBusConfig:
    return EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
        auth_token="test-token",
    )


@pytest.mark.asyncio
async def test_fan_out_all_subscribers():
    broker = EventBroker(_make_config())
    sub1 = broker.subscribe([])
    sub2 = broker.subscribe([])
    broker.publish({"seq": 1, "topic": "t", "event_id": "a"})
    assert sub1.queue.qsize() == 1
    assert sub2.queue.qsize() == 1


@pytest.mark.asyncio
async def test_topic_filter_excludes_non_matching():
    broker = EventBroker(_make_config())
    sub_t = broker.subscribe(["target"])
    sub_all = broker.subscribe([])
    broker.publish({"seq": 1, "topic": "other", "event_id": "a"})
    assert sub_t.queue.empty()  # filtered out
    assert sub_all.queue.qsize() == 1  # all-topics subscriber receives it


@pytest.mark.asyncio
async def test_topic_filter_delivers_matching():
    broker = EventBroker(_make_config())
    sub = broker.subscribe(["target"])
    broker.publish({"seq": 1, "topic": "target", "event_id": "a"})
    assert sub.queue.qsize() == 1


@pytest.mark.asyncio
async def test_unsubscribe_stops_delivery():
    broker = EventBroker(_make_config())
    sub = broker.subscribe([])
    broker.unsubscribe(sub)
    broker.publish({"seq": 1, "topic": "t", "event_id": "a"})
    assert sub.queue.empty()


@pytest.mark.asyncio
async def test_unsubscribe_idempotent():
    broker = EventBroker(_make_config())
    sub = broker.subscribe([])
    broker.unsubscribe(sub)
    broker.unsubscribe(sub)  # should not raise


@pytest.mark.asyncio
async def test_shutdown_sends_sentinel():
    broker = EventBroker(_make_config())
    sub = broker.subscribe([])
    broker.shutdown()
    sentinel = await asyncio.wait_for(sub.queue.get(), timeout=1.0)
    assert sentinel is None


@pytest.mark.asyncio
async def test_duplicate_consumer_id_rejected():
    broker = EventBroker(_make_config())
    _ = broker.subscribe([], consumer_id="c1")
    with pytest.raises(ConsumerAlreadyConnectedError):
        broker.subscribe([], consumer_id="c1")
    assert broker.duplicate_rejection_count() == 1
    assert len(broker._subscribers) == 1  # only one subscriber registered
    assert len(broker._consumer_subs) == 1


@pytest.mark.asyncio
async def test_anonymous_connection_not_rejected():
    broker = EventBroker(_make_config())
    _ = broker.subscribe([])
    _ = broker.subscribe([])
    assert len(broker._subscribers) == 2
    assert broker.duplicate_rejection_count() == 0
    assert (
        len(broker._consumer_subs) == 0
    )  # anonymous connections not tracked in registry


@pytest.mark.asyncio
async def test_unsubscribe_clears_registry_entry():
    broker = EventBroker(_make_config())
    sub = broker.subscribe([], consumer_id="c1")
    assert len(broker._consumer_subs) == 1
    assert broker._consumer_subs["c1"] is sub
    broker.unsubscribe(sub)
    assert len(broker._consumer_subs) == 0
    assert len(broker._subscribers) == 0


@pytest.mark.asyncio
async def test_overflow_disconnect_on_queue_full():
    broker = EventBroker(_make_config())
    sub = broker.subscribe([], consumer_id="c1")
    # Fill the queue to capacity
    for i in range(1000):
        try:
            sub.queue.put_nowait({"seq": i, "topic": "t"})
        except asyncio.QueueFull:
            break
    assert sub.queue.full()
    # Publish an event that will hit QueueFull
    delivered = broker.publish({"seq": 999, "topic": "t"})
    assert delivered >= 0
    assert sub.disconnect.is_set()
    assert broker.overflow_disconnect_count() >= 1
    assert len(broker._subscribers) < 1 or broker._subscribers[0] is not sub
