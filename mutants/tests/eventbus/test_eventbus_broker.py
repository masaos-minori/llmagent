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
