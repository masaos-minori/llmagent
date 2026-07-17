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
            "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
            ),
        )
        db.commit()

        now = "2026-06-22T13:00:00Z"
        found, newly_acked = ack_event(db, ev["event_id"], now)
        assert found is True
        assert newly_acked is True

        row = db.execute(
            "SELECT acked_at FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()
        assert row["acked_at"] == now

    def test_ack_event_idempotent(self, db: sqlite3.Connection) -> None:
        from eventbus.db import ack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
            ),
        )
        db.commit()

        now = "2026-06-22T13:00:00Z"
        found1, newly_acked1 = ack_event(db, ev["event_id"], now)
        assert found1 is True
        assert newly_acked1 is True

        later = "2026-06-22T14:00:00Z"
        found2, newly_acked2 = ack_event(db, ev["event_id"], later)
        assert found2 is True
        assert newly_acked2 is False

        row = db.execute(
            "SELECT acked_at FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()
        assert row["acked_at"] == now

    def test_ack_event_not_found(self, db: sqlite3.Connection) -> None:
        from eventbus.db import ack_event

        found, newly_acked = ack_event(db, "nonexistent-event", "2026-06-22T13:00:00Z")
        assert found is False
        assert newly_acked is False

    def test_ack_event_already_acked(self, db: sqlite3.Connection) -> None:
        from eventbus.db import ack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at, acked_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
                "2026-06-22T13:00:00Z",
            ),
        )
        db.commit()

        later = "2026-06-22T14:00:00Z"
        found, newly_acked = ack_event(db, ev["event_id"], later)
        assert found is True
        assert newly_acked is False

        row = db.execute(
            "SELECT acked_at FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()
        assert row["acked_at"] == "2026-06-22T13:00:00Z"


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = Path(__file__).parent.parent / "schemas" / "event_envelope.json"
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    from fastapi.testclient import TestClient

    with TestClient(eb_app.app) as c:
        yield c


class TestAckHttpBehavior:
    def test_ack_first_time_returns_200(self, client: Any) -> None:
        """POST /events/{id}/ack returns 200 with acked: true, seq: int on first ack."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        resp = client.post(
            f"/events/{body['event_id']}/ack", params={"consumer_id": "consumer-A"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["acked"] is True
        assert data["seq"] is not None

    def test_ack_repeated_returns_200_already_acked(self, client: Any) -> None:
        """Second POST /events/{id}/ack returns 200 with acked: true, already_acked: true."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        client.post(
            f"/events/{body['event_id']}/ack", params={"consumer_id": "consumer-A"}
        )
        resp = client.post(
            f"/events/{body['event_id']}/ack", params={"consumer_id": "consumer-A"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["acked"] is True
        assert data["already_acked"] is True

    def test_ack_unknown_event_returns_404(self, client: Any) -> None:
        """POST /events/{id}/ack with unknown event_id returns 404."""
        resp = client.post("/events/nonexistent-event/ack")
        assert resp.status_code == 404


class TestNackEvent:
    def test_nack_event_increments_failure_count(self, db: sqlite3.Connection) -> None:
        from eventbus.db import nack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
            ),
        )
        db.commit()

        result = nack_event(db, ev["event_id"])
        assert result == 1

        row = db.execute(
            "SELECT delivery_failure_count FROM events WHERE event_id = ?",
            (ev["event_id"],),
        ).fetchone()
        assert row["delivery_failure_count"] == 1

    def test_nack_event_increments_again(self, db: sqlite3.Connection) -> None:
        from eventbus.db import nack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
            ),
        )
        db.commit()

        result1 = nack_event(db, ev["event_id"])
        assert result1 == 1

        result2 = nack_event(db, ev["event_id"])
        assert result2 == 2

        row = db.execute(
            "SELECT delivery_failure_count FROM events WHERE event_id = ?",
            (ev["event_id"],),
        ).fetchone()
        assert row["delivery_failure_count"] == 2

    def test_nack_event_not_found(self, db: sqlite3.Connection) -> None:
        from eventbus.db import nack_event

        result = nack_event(db, "nonexistent-event")
        assert result == -1
