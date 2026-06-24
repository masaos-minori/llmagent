from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import orjson
import pytest
from fastapi.testclient import TestClient


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
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)

    with TestClient(eb_app.app) as c:
        yield c


def _event(topic: str = "t") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-22T12:00:00Z",
    }


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
    from eventbus.db import open_db
    from eventbus.dlq import promote_to_dlq

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    db.execute(
        "UPDATE events SET retry_count = 2 WHERE event_id = ?", (ev["event_id"],)
    )
    db.commit()
    promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

    r = client.get("/dlq")
    assert r.status_code == 200
    ids = [e["event_id"] for e in r.json()]
    assert ev["event_id"] in ids


def test_dlq_requeue(client: TestClient, tmp_path: Path) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import promote_to_dlq

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    db.execute(
        "UPDATE events SET retry_count = 2 WHERE event_id = ?", (ev["event_id"],)
    )
    db.commit()
    promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

    r = client.post(f"/dlq/{ev['event_id']}/requeue")
    assert r.status_code == 200
    assert r.json()["requeued"] is True

    r2 = client.get("/dlq")
    ids = [e["event_id"] for e in r2.json()]
    assert ev["event_id"] not in ids


def test_requeue_increments_retry_count(client: TestClient, tmp_path: Path) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import promote_to_dlq

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    db.execute(
        "UPDATE events SET retry_count = 2 WHERE event_id = ?", (ev["event_id"],)
    )
    db.commit()
    promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

    client.post(f"/dlq/{ev['event_id']}/requeue")

    row = db.execute(
        "SELECT retry_count FROM events WHERE event_id = ?", (ev["event_id"],)
    ).fetchone()
    assert row is not None
    assert row[0] == 3  # incremented from 2, not reset to 0


def test_retry_exhaustion_leads_to_dlq(client: TestClient, tmp_path: Path) -> None:
    """After requeue increments retry_count past max_retry, promote_to_dlq re-promotes."""
    from eventbus.db import open_db
    from eventbus.dlq import promote_to_dlq

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    # Set retry_count at max already
    db.execute(
        "UPDATE events SET retry_count = 2 WHERE event_id = ?", (ev["event_id"],)
    )
    db.commit()
    # Promote to DLQ
    promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)
    # Requeue — this increments retry_count to 3 (> max_retry=2)
    client.post(f"/dlq/{ev['event_id']}/requeue")
    # promote_to_dlq should re-promote since retry_count (3) >= max_retry (2)
    n = promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1
