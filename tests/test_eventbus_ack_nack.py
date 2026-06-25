from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def db(tmp_path: Path) -> Any:
    from eventbus.db import open_db

    return open_db(str(tmp_path / "eventbus.sqlite"))


def _event(topic: str = "t") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-22T12:00:00Z",
    }


class TestAckEvent:
    def test_ack_event_sets_acked_at(self, db: sqlite3.Connection) -> None:
        from eventbus.db import ack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (ev["event_id"], ev["topic"], json.dumps(ev["payload"]), ev["producer"], ev["published_at"]),
        )
        db.commit()

        now = "2026-06-22T13:00:00Z"
        result = ack_event(db, ev["event_id"], now)
        assert result is True

        row = db.execute(
            "SELECT acked_at FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()
        assert row["acked_at"] == now

    def test_ack_event_idempotent(self, db: sqlite3.Connection) -> None:
        from eventbus.db import ack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (ev["event_id"], ev["topic"], json.dumps(ev["payload"]), ev["producer"], ev["published_at"]),
        )
        db.commit()

        now = "2026-06-22T13:00:00Z"
        result1 = ack_event(db, ev["event_id"], now)
        assert result1 is True

        later = "2026-06-22T14:00:00Z"
        result2 = ack_event(db, ev["event_id"], later)
        assert result2 is False

        row = db.execute(
            "SELECT acked_at FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()
        assert row["acked_at"] == now

    def test_ack_event_not_found(self, db: sqlite3.Connection) -> None:
        from eventbus.db import ack_event

        result = ack_event(db, "nonexistent-event", "2026-06-22T13:00:00Z")
        assert result is False

    def test_ack_event_already_acked(self, db: sqlite3.Connection) -> None:
        from eventbus.db import ack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at, acked_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (ev["event_id"], ev["topic"], json.dumps(ev["payload"]), ev["producer"], ev["published_at"], "2026-06-22T13:00:00Z"),
        )
        db.commit()

        later = "2026-06-22T14:00:00Z"
        result = ack_event(db, ev["event_id"], later)
        assert result is False

        row = db.execute(
            "SELECT acked_at FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()
        assert row["acked_at"] == "2026-06-22T13:00:00Z"


class TestNackEvent:
    def test_nack_event_increments_failure_count(self, db: sqlite3.Connection) -> None:
        from eventbus.db import nack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (ev["event_id"], ev["topic"], json.dumps(ev["payload"]), ev["producer"], ev["published_at"]),
        )
        db.commit()

        result = nack_event(db, ev["event_id"])
        assert result == 1

        row = db.execute(
            "SELECT delivery_failure_count FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()
        assert row["delivery_failure_count"] == 1

    def test_nack_event_increments_again(self, db: sqlite3.Connection) -> None:
        from eventbus.db import nack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (ev["event_id"], ev["topic"], json.dumps(ev["payload"]), ev["producer"], ev["published_at"]),
        )
        db.commit()

        result1 = nack_event(db, ev["event_id"])
        assert result1 == 1

        result2 = nack_event(db, ev["event_id"])
        assert result2 == 2

        row = db.execute(
            "SELECT delivery_failure_count FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()
        assert row["delivery_failure_count"] == 2

    def test_nack_event_not_found(self, db: sqlite3.Connection) -> None:
        from eventbus.db import nack_event

        result = nack_event(db, "nonexistent-event")
        assert result == -1
