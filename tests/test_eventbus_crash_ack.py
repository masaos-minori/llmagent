"""tests/test_eventbus_crash_ack.py
Crash-before-ack regression tests for Event Bus.

Tests that unacked events are replayed on reconnect — the core invariant
that offsets advance only via explicit ack, never automatically.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

import pytest
from eventbus_helpers import make_eventbus_client
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    with make_eventbus_client(tmp_path, monkeypatch) as c:
        yield c


def _event(topic: str = "crash") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-01-01T00:00:00Z",
    }


class TestCrashBeforeAck:
    """Verify unacked events are replayed on consumer reconnect."""

    def test_unacked_event_replayed_on_reconnect(self, client: TestClient) -> None:
        """Consumer disconnects before acking — event must be replayed."""
        import eventbus.app as eb_app
        from eventbus.offsets import read_offset

        body = _event("crash")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200
        seq = resp.json()["seq"]

        # Simulate disconnect without ack — verify offset not written
        offset = read_offset(eb_app.app.state.config.offsets_dir, "consumer-A")
        assert offset == 0, "Offset should not be written for unacked events"

        # Reconnect with same consumer_id — event should be replayed from seq=0
        resp2 = client.get("/replay?since_seq=0&format=json")
        assert resp2.status_code == 200
        data2 = resp2.json()
        items2 = data2["items"]
        assert len(items2) == 1
        assert items2[0]["event_id"] == body["event_id"]

    def test_partial_ack_replay(self, client: TestClient) -> None:
        """Consumer acks some events but not others — only unacked replayed."""
        import eventbus.app as eb_app
        from eventbus.offsets import read_offset

        body1 = _event("crash")
        body2 = _event("crash")
        resp1 = client.post("/publish", json=body1)
        resp2 = client.post("/publish", json=body2)
        assert resp1.status_code == 200
        assert resp2.status_code == 200

        # Ack only the first event
        client.post(
            "/ack",
            params={"event_id": body1["event_id"], "consumer_id": "consumer-B"},
        )

        offset = read_offset(eb_app.app.state.config.offsets_dir, "consumer-B")
        assert offset == resp1.json()["seq"]

        # Reconnect — only unacked event should be replayed
        resp2 = client.get(
            f"/replay?since_seq={offset}&format=json"
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        items2 = data2["items"]
        assert len(items2) == 1
        assert items2[0]["event_id"] == body2["event_id"]

    def test_no_offset_for_new_consumer(self, client: TestClient) -> None:
        """New consumer with no prior offset receives all events from seq=0."""
        body = _event("crash")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # New consumer — should receive all events from seq=0
        resp = client.get("/replay?since_seq=0&format=json")
        assert resp.status_code == 200
        data = resp.json()
        items = data["items"]
        assert len(items) == 1
        assert items[0]["event_id"] == body["event_id"]
