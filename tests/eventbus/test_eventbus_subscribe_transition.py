"""tests/test_eventbus_subscribe_transition.py
Replay-to-live transition regression tests for Event Bus.

Tests that events published during the replay phase are delivered via live push
(not lost), and that no duplicate delivery occurs within the replay range.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any

import pytest
from eventbus_helpers import make_eventbus_client
from fastapi import Request
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    with make_eventbus_client(tmp_path, monkeypatch) as c:
        yield c


def _event(topic: str = "transition") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-01-01T00:00:00Z",
    }


class TestReplayToLiveTransition:
    """Verify events published during replay phase are delivered."""

    def test_event_published_during_replay_delivered_via_live_push(
        self, client: TestClient
    ) -> None:
        """Event published while subscriber is in replay phase must not be lost."""
        # Publish first event (will be included in replay)
        body1 = _event("transition")
        resp = client.post("/publish", json=body1)
        assert resp.status_code == 200

        # Then publish another event while subscriber is replaying
        body2 = _event("transition")
        resp2 = client.post("/publish", json=body2)
        assert resp2.status_code == 200

        # /replay from seq=0 should return both events
        resp = client.get("/replay?since_seq=0&format=json")
        assert resp.status_code == 200
        data = resp.json()
        items = data["items"]
        event_ids = {item["event_id"] for item in items}
        assert body1["event_id"] in event_ids, "Replay event must be delivered"
        assert body2["event_id"] in event_ids, "Live push event must be delivered"

    def test_no_duplicate_events_in_replay_range(self, client: TestClient) -> None:
        """Events within replay range should not be duplicated."""
        # Publish events
        bodies = [_event("transition") for _ in range(3)]
        for body in bodies:
            resp = client.post("/publish", json=body)
            assert resp.status_code == 200

        # /replay from seq=0 should return all events without duplication
        resp1 = client.get("/replay?since_seq=0&format=json")
        assert resp1.status_code == 200
        items1 = {item["event_id"] for item in resp1.json()["items"]}

        # Another consumer from seq=0 should get the same events
        resp2 = client.get("/replay?since_seq=0&format=json")
        assert resp2.status_code == 200
        items2 = {item["event_id"] for item in resp2.json()["items"]}

        # Both consumers should receive the same events
        assert items1 == items2, "Both consumers should receive identical events"
        assert len(items1) == len(bodies), (
            f"Expected {len(bodies)} events, got {len(items1)}"
        )

    def test_replay_ceil_deduplication(self, client: TestClient) -> None:
        """Events with seq <= replay_ceil should not be delivered twice."""
        # Publish an event
        body = _event("transition")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200
        # /replay from seq=0 — this event is in replay range
        resp = client.get("/replay?since_seq=0&format=json")
        assert resp.status_code == 200
        data = resp.json()
        items = data["items"]

        # The event should appear exactly once in the result
        event_ids = [item["event_id"] for item in items]
        assert event_ids.count(body["event_id"]) == 1, "Event must not be duplicated"


class TestSubscribeCancelledBeforeReplay:
    """Verify replay_ceil is always bound when cancelled during the replay fetch."""

    async def test_cancelled_before_replay_logs_start_seq(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Cancelling during the replay DB fetch must log seq=start_seq, not crash.

        Locks in the invariant that `replay_ceil` is unconditionally bound before
        `run_with_db_lock` is awaited: a future change that reintroduces a
        conditional initialization (e.g. moving it back inside the replay `for`
        loop) without an equivalent fallback would raise `UnboundLocalError` here
        instead of a clean `StopAsyncIteration`. Note: this does not reproduce the
        historical pyright `reportPossiblyUnboundVariable` finding itself — that
        was a static-analysis-only false positive (the previous
        `locals().get("replay_ceil")` guard already made this scenario safe at
        runtime); `uv run pyright` is what verifies that finding is resolved.
        """
        from eventbus import app as eb_app
        from eventbus import subscribe_route

        async def _raise_cancelled(_func: Any) -> Any:
            raise asyncio.CancelledError

        monkeypatch.setattr(subscribe_route, "run_with_db_lock", _raise_cancelled)

        scope = {
            "type": "http",
            "app": eb_app.app,
            "method": "GET",
            "path": "/subscribe",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        with caplog.at_level(logging.INFO, logger="eventbus.subscribe_route"):
            response = await subscribe_route.subscribe(
                request, topic=[], since_seq=0, consumer_id=""
            )
            gen = response.body_iterator
            with pytest.raises(StopAsyncIteration):
                await gen.__anext__()

        assert "seq=0" in caplog.text
