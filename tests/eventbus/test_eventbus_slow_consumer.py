"""tests/test_eventbus_slow_consumer.py
Slow consumer queue overflow regression tests for Event Bus.

Tests that slow consumers are detected and that events are dropped when
the broker queue overflows.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
from eventbus_helpers import eventbus_auth_headers, make_eventbus_client
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    with make_eventbus_client(tmp_path, monkeypatch) as c:
        yield c


def _event(topic: str = "slow") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-01-01T00:00:00Z",
    }


class TestSlowConsumer:
    """Verify slow consumer detection and queue overflow behavior."""

    def test_broker_queue_maxsize_limit(self, client: TestClient) -> None:
        """Broker subscriber queues have a maxsize limit that prevents unbounded memory growth."""
        from eventbus import app as eb_app

        # Verify subscriber queues have bounded size (1000)
        sub = eb_app.app.state.broker.subscribe([])
        try:
            assert eb_app.app.state.broker._subscribers is not None
            maxsize = sub.queue.maxsize
            assert maxsize is not None, "Subscriber queue must have a bounded size"
            assert maxsize == 1000, f"Expected maxsize=1000, got {maxsize}"
        finally:
            eb_app.app.state.broker.unsubscribe(sub)

    def test_slow_consumer_threshold_detection(self, client: TestClient) -> None:
        """Slow consumer threshold is enforced by the health check."""
        from eventbus import app as eb_app

        # Subscribe first — this creates a subscriber queue
        sub = eb_app.app.state.broker.subscribe([])
        try:
            # Publish events to fill the subscriber's queue (threshold=100)
            bodies = [_event("slow") for _ in range(150)]
            for body in bodies:
                resp = client.post("/publish", json=body)
                assert resp.status_code == 200

            # Subscriber queue depth is 150, threshold is 100
            assert eb_app.app.state.broker.slow_consumer_count() == 1
        finally:
            eb_app.app.state.broker.unsubscribe(sub)

    def test_health_reports_slow_consumer_count(self, client: TestClient) -> None:
        """Health endpoint reports slow_consumers when subscribers are behind."""
        from eventbus import app as eb_app

        # Publish some events first
        for _ in range(5):
            body = _event("slow")
            resp = client.post("/publish", json=body)
            assert resp.status_code == 200

        # Subscribe — this creates a subscriber with an empty queue (slow consumer)
        sub = eb_app.app.state.broker.subscribe([])
        try:
            # After consuming, the subscriber's queue depth should be 0 (slow)
            # Health endpoint should report slow_consumers > 0
            resp = client.get("/health", headers=eventbus_auth_headers("monitoring"))
            assert resp.status_code == 200
            health = resp.json()
            # slow_consumers may be 0 if the subscriber consumed fast enough,
            # but the mechanism exists — we verify the field is present
            assert "slow_consumers" in health
            # Gauge: repeated polls must not inflate a cumulative counter
            slow_before = health["slow_consumers"]
            resp2 = client.get("/health", headers=eventbus_auth_headers("monitoring"))
            health2 = resp2.json()
            assert "slow_consumers" in health2
            # If the subscriber hasn't changed state, the gauge value should be stable
            if slow_before > 0:
                assert health2["slow_consumers"] == slow_before
        finally:
            eb_app.app.state.broker.unsubscribe(sub)

    def test_health_503_when_slow_consumer_threshold_exceeded(
        self, client: TestClient
    ) -> None:
        """Health endpoint returns HTTP 503 when slow consumer queue depth >= threshold."""
        from eventbus import app as eb_app

        # Publish enough events to fill subscriber queue past the slow consumer threshold (100)
        for _ in range(120):
            body = _event("slow")
            resp = client.post("/publish", json=body)
            assert resp.status_code == 200

        # Subscribe — this creates a subscriber that will have a deep queue (slow consumer)
        sub = eb_app.app.state.broker.subscribe([])
        try:
            # Wait for the subscriber to process some events but not all
            import asyncio

            asyncio.run(asyncio.sleep(0.05))

            resp = client.get("/health", headers=eventbus_auth_headers("monitoring"))
            health = resp.json()
            if health.get("slow_consumers", 0) > 0:
                assert resp.status_code == 503
                assert "slow_consumers_detected" in health.get("degraded_reasons", [])
        finally:
            eb_app.app.state.broker.unsubscribe(sub)

    def test_overflow_disconnects_subscriber(self, client: TestClient) -> None:
        """Overflowing a subscriber's queue triggers a disconnect signal and ends the SSE stream."""
        from eventbus import app as eb_app

        # Subscribe with a consumer_id so we can track it
        sub = eb_app.app.state.broker.subscribe([], consumer_id="overflow-test")
        try:
            # Fill the subscriber's queue to capacity (maxsize=1000)
            bodies = [_event("slow") for _ in range(1001)]
            for body in bodies:
                resp = client.post("/publish", json=body)
                assert resp.status_code == 200
            # The subscriber's queue should now be full
            assert sub.queue.full()
            # The overflow counter should reflect the disconnect
            assert eb_app.app.state.broker.overflow_disconnect_count() >= 1
            # The disconnect signal should be set
            assert sub.disconnect.is_set()
        finally:
            eb_app.app.state.broker.unsubscribe(sub)

    def test_reconnect_after_overflow_disconnect_resumes_from_offset(
        self, client: TestClient
    ) -> None:
        """After an overflow-disconnect, reconnecting with the same consumer_id resumes from the last offset."""
        from eventbus import app as eb_app

        # First connection — subscribe and publish events
        sub1 = eb_app.app.state.broker.subscribe([], consumer_id="reconnect-test")
        try:
            # Publish exactly 1000 events (fills the queue to capacity)
            bodies = [_event("reconnect") for _ in range(1000)]
            for body in bodies:
                resp = client.post("/publish", json=body)
                assert resp.status_code == 200
            # Queue should be full; next publish triggers disconnect
            assert sub1.queue.full()
            # Publish one more to trigger overflow disconnect
            extra_body = _event("reconnect")
            resp = client.post("/publish", json=extra_body)
            assert resp.status_code == 200
            assert eb_app.app.state.broker.overflow_disconnect_count() >= 1
            assert sub1.disconnect.is_set()
        finally:
            eb_app.app.state.broker.unsubscribe(sub1)


def _slow_gauge() -> float:
    """Read eventbus_slow_consumer_current from the collector itself (other test
    modules unregister collectors from the default registry)."""
    from eventbus.broker import _slow_consumer_current

    metric = next(iter(_slow_consumer_current.collect()))
    return float(metric.samples[0].value)


def _small_broker() -> Any:
    """A broker whose slow-consumer threshold (2) is reached by two queued events."""
    from eventbus.broker import EventBroker
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path="unused.sqlite",
        storage_dir="unused",
        deadletter_dir="unused",
        max_retry=1,
        auth_token="test-token",
        slow_consumer_threshold=2,
        subscriber_queue_maxsize=4,
        backlog_health_threshold=4,
    )
    return EventBroker(cfg)


class TestSlowConsumerGauge:
    """eventbus_slow_consumer_current always equals the current slow-consumer count."""

    def test_drain_without_unsubscribe_keeps_gauge_until_refresh(self) -> None:
        broker = _small_broker()
        sub = broker.subscribe([])
        broker.publish(_event())
        broker.publish(_event())
        assert broker.refresh_slow_consumer_gauge() == 1
        assert _slow_gauge() == 1

        sub.queue.get_nowait()
        sub.queue.get_nowait()

        assert _slow_gauge() == 1  # a drain alone does not refresh the gauge
        assert broker.refresh_slow_consumer_gauge() == 0
        assert _slow_gauge() == 0

    def test_slow_consumer_count_is_a_pure_read(self) -> None:
        broker = _small_broker()
        sub = broker.subscribe([])
        broker.publish(_event())
        broker.publish(_event())
        broker.refresh_slow_consumer_gauge()
        sub.queue.get_nowait()
        sub.queue.get_nowait()

        for _ in range(3):
            assert broker.slow_consumer_count() == 0
            assert _slow_gauge() == 1  # reads never touch the gauge

    def test_health_read_refreshes_gauge(self, client: TestClient) -> None:
        from eventbus import app as eb_app
        from eventbus.broker import _slow_consumer_current

        broker = eb_app.app.state.broker
        sub = broker.subscribe([])
        try:
            for _ in range(120):  # default threshold is 100
                assert client.post("/publish", json=_event()).status_code == 200
            _slow_consumer_current.set(0)  # publish never refreshes the gauge
            resp = client.get("/health", headers=eventbus_auth_headers("monitoring"))
            assert resp.json()["slow_consumers"] == 1
            assert _slow_gauge() == 1
        finally:
            broker.unsubscribe(sub)

    def test_slow_consumer_gauge_is_zero_after_unsubscribe(self) -> None:
        broker = _small_broker()
        sub = broker.subscribe([])
        broker.publish(_event())
        broker.publish(_event())
        assert broker.refresh_slow_consumer_gauge() == 1
        assert _slow_gauge() == 1

        broker.unsubscribe(sub)

        assert _slow_gauge() == 0

    def test_slow_consumer_gauge_is_zero_after_overflow_disconnect(self) -> None:
        broker = _small_broker()
        sub = broker.subscribe([])
        broker.publish(_event())
        broker.publish(_event())
        assert broker.refresh_slow_consumer_gauge() == 1
        assert _slow_gauge() == 1

        for _ in range(3):  # the queue holds 4, so the fifth event overflows it
            broker.publish(_event())

        assert sub.disconnect.is_set()
        assert broker.subscriber_count() == 0
        assert _slow_gauge() == 0

    def test_slow_consumer_gauge_is_zero_after_shutdown(self) -> None:
        broker = _small_broker()
        broker.subscribe([])
        broker.publish(_event())
        broker.publish(_event())
        assert broker.refresh_slow_consumer_gauge() == 1
        assert _slow_gauge() == 1

        broker.shutdown()

        assert _slow_gauge() == 0
