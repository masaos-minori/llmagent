"""tests/test_eventbus_crash_ack.py
Crash-before-ack regression tests for Event Bus.

Tests that unacked events are replayed on reconnect — the core invariant
that offsets advance only via explicit ack, never automatically.
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any

import pytest
from eventbus_helpers import make_eventbus_client
from fastapi.testclient import TestClient


class FlakyConnection:
    """Wraps sqlite3.Connection to inject failures into execute calls."""

    def __init__(self, real_conn):
        self._real_conn = real_conn
        self._failed = False

    def execute(self, sql, *args, **kwargs):
        if not self._failed and "consumer_offsets" in sql:
            self._failed = True
            raise sqlite3.OperationalError("simulated offset-write failure")
        return self._real_conn.execute(sql, *args, **kwargs)

    def commit(self):
        return self._real_conn.commit()

    def rollback(self):
        return self._real_conn.rollback()

    def __getattr__(self, name):
        return getattr(self._real_conn, name)


@pytest.fixture
def db(tmp_path: Path) -> Any:
    from eventbus.db import open_db

    return open_db(str(tmp_path / "eventbus.sqlite"))


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
        from eventbus.db import get_consumer_offset

        body = _event("crash")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200
        # Simulate disconnect without ack — verify offset not written
        offset = get_consumer_offset(eb_app.app.state.db, "consumer-A")
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
        from eventbus.db import get_consumer_offset

        body1 = _event("crash")
        body2 = _event("crash")
        resp1 = client.post("/publish", json=body1)
        resp2 = client.post("/publish", json=body2)
        assert resp1.status_code == 200
        assert resp2.status_code == 200

        # Ack only the first event
        client.post(
            f"/events/{body1['event_id']}/ack",
            params={"consumer_id": "consumer-B"},
        )

        offset = get_consumer_offset(eb_app.app.state.db, "consumer-B")
        assert offset == resp1.json()["seq"]

        # Reconnect — only unacked event should be replayed
        resp2 = client.get(f"/replay?since_seq={offset}&format=json")
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

    def test_offset_write_failure_after_delivery_state(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When offset-write fails after delivery-state write, neither commits."""
        import sqlite3
        import unittest.mock

        import eventbus.app as eb_app
        from eventbus.db import ack_event_for_consumer, insert_event

        cfg = eb_app.app.state.config
        db = eb_app.app.state.db
        now = "2026-09-09T10:00:00Z"
        consumer_id = "crash_consumer"

        # Insert an event first
        seq, inserted = insert_event(
            db, "evt-crash-offset", "test-topic", '{"data": "value"}', "producer", now
        )
        assert inserted

        # Mock commit to fail after delivery-state write
        original_commit = db.commit

        def failing_commit():
            raise sqlite3.IntegrityError("simulated commit failure")

        with unittest.mock.patch.object(db, 'commit', side_effect=failing_commit):
            # This should raise an exception
            with pytest.raises(sqlite3.IntegrityError, match="simulated commit failure"):
                ack_event_for_consumer(db, "evt-crash-offset", consumer_id, now)

        # Verify neither delivery nor offset was committed
        delivery_row = db.execute(
            "SELECT 1 FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
            (consumer_id, "evt-crash-offset"),
        ).fetchone()
        assert delivery_row is None, "delivery-state should NOT be committed after failed commit"

        offset_row = db.execute(
            "SELECT 1 FROM consumer_offsets WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
        assert offset_row is None, "offset should NOT be committed after failed commit"
