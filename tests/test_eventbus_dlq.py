"""tests/test_eventbus_dlq.py
Event Bus dead-letter queue tests.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import orjson
import pytest
from eventbus_helpers import make_eventbus_client
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    with make_eventbus_client(tmp_path, monkeypatch, max_retry=2) as c:
        yield c


def _event(topic: str = "t") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-22T12:00:00Z",
    }


def _promote(client: TestClient, ev: dict[str, Any], tmp_path: Path) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import promote_to_dlq

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    db.execute(
        "UPDATE events SET retry_count = 2 WHERE event_id = ?", (ev["event_id"],)
    )
    db.commit()
    promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)


def test_dlq_promotion_when_retry_exhausted(client: TestClient, tmp_path: Path) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import promote_to_dlq

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    db.execute(
        "UPDATE events SET retry_count = 2 WHERE event_id = ?", (ev["event_id"],)
    )
    db.commit()

    n = promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1
    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert dlq_file.exists()
    record = orjson.loads(dlq_file.read_bytes())
    assert record["event_id"] == ev["event_id"]
    assert record["dlq_at"] is not None


def test_dlq_list(client: TestClient, tmp_path: Path) -> None:
    ev = _event()
    client.post("/publish", json=ev)
    _promote(client, ev, tmp_path)

    r = client.get("/dlq")
    assert r.status_code == 200
    ids = [e["event_id"] for e in r.json()]
    assert ev["event_id"] in ids


def test_dlq_requeue(client: TestClient, tmp_path: Path) -> None:
    ev = _event()
    client.post("/publish", json=ev)
    _promote(client, ev, tmp_path)

    r = client.post(f"/dlq/{ev['event_id']}/requeue")
    assert r.status_code == 200
    assert r.json()["requeued"] is True

    r2 = client.get("/dlq")
    ids = [e["event_id"] for e in r2.json()]
    assert ev["event_id"] not in ids


def test_requeue_increments_retry_count(client: TestClient, tmp_path: Path) -> None:
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    _promote(client, ev, tmp_path)

    client.post(f"/dlq/{ev['event_id']}/requeue")

    row = db.execute(
        "SELECT retry_count FROM events WHERE event_id = ?", (ev["event_id"],)
    ).fetchone()
    assert row is not None
    assert row[0] == 3


def test_retry_exhaustion_leads_to_dlq(client: TestClient, tmp_path: Path) -> None:
    """After requeue increments retry_count past max_retry, promote_to_dlq re-promotes."""
    from eventbus.db import open_db
    from eventbus.dlq import promote_to_dlq

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    _promote(client, ev, tmp_path)
    client.post(f"/dlq/{ev['event_id']}/requeue")

    n = promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1
