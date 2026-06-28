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
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

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
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (ev["event_id"],),
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
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (ev["event_id"],),
    )
    db.commit()
    promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

    r = client.get("/dlq")
    assert r.status_code == 200
    body = r.json()
    ids = [e["event_id"] for e in body["items"]]
    assert ev["event_id"] in ids


def test_dlq_requeue(client: TestClient, tmp_path: Path) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import promote_to_dlq

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (ev["event_id"],),
    )
    db.commit()
    promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

    r = client.post(f"/dlq/{ev['event_id']}/requeue")
    assert r.status_code == 200
    assert r.json()["requeued"] is True

    r2 = client.get("/dlq")
    body2 = r2.json()
    ids = [e["event_id"] for e in body2["items"]]
    assert ev["event_id"] not in ids


def test_requeue_increments_dlq_requeue_count(
    client: TestClient, tmp_path: Path
) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import promote_to_dlq

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (ev["event_id"],),
    )
    db.commit()
    promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

    # Requeue once — dlq_requeue_count should increment to 1
    r = client.post(f"/dlq/{ev['event_id']}/requeue")
    assert r.status_code == 200
    assert r.json()["requeued"] is True

    row = db.execute(
        "SELECT dlq_requeue_count, delivery_failure_count, dlq_at FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert row["dlq_requeue_count"] == 1
    assert row["delivery_failure_count"] == 2
    assert row["dlq_at"] is None

    # Exhaust retries again — should promote to DLQ
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (ev["event_id"],),
    )
    db.commit()
    n = promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1
    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert dlq_file.exists()


def test_inline_dlq_promotion_on_nack(client: TestClient, tmp_path: Path) -> None:
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)

    # First nack — delivery_failure_count becomes 1, below threshold of 2
    r = client.post(f"/nack?event_id={ev['event_id']}")
    assert r.status_code == 200
    assert r.json()["delivery_failure_count"] == 1
    assert "dlq_promoted" not in r.json()

    # Second nack — delivery_failure_count becomes 2, hits threshold, inline promote
    r = client.post(f"/nack?event_id={ev['event_id']}")
    assert r.status_code == 200
    assert r.json()["delivery_failure_count"] == 2
    assert r.json().get("dlq_promoted") is True

    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert dlq_file.exists()
    record = orjson.loads(dlq_file.read_bytes())
    assert record["event_id"] == ev["event_id"]
    assert record["dlq_at"] is not None

    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert row["dlq_at"] is not None


def test_inline_dlq_promotion_skipped_below_threshold(
    client: TestClient, tmp_path: Path
) -> None:
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)

    # Nack once — below threshold of 2, no DLQ promotion
    r = client.post(f"/nack?event_id={ev['event_id']}")
    assert r.status_code == 200
    assert r.json()["delivery_failure_count"] == 1
    assert "dlq_promoted" not in r.json()

    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert not dlq_file.exists()

    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert row["dlq_at"] is None


def test_inline_dlq_promotion_not_found(client: TestClient) -> None:
    r = client.post("/nack?event_id=nonexistent")
    assert r.status_code == 404
    assert r.json()["detail"] == "event not found"


def test_nack_on_already_dlq_event_does_not_repromote(
    client: TestClient, tmp_path: Path
) -> None:
    from eventbus.db import open_db
    from eventbus.dlq import promote_to_dlq

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    db.execute(
        "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
        (ev["event_id"],),
    )
    db.commit()
    promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

    # Nack an already-DLQ'd event — should not promote again
    r = client.post(f"/nack?event_id={ev['event_id']}")
    assert r.status_code == 200
    assert r.json()["delivery_failure_count"] == 3
    assert "dlq_promoted" not in r.json()

    dlq_files = list((tmp_path / "deadletter").glob("*.json"))
    assert len(dlq_files) == 1


def test_requeue_non_dlq_event_fails(client: TestClient, tmp_path: Path) -> None:
    """Requeue should fail with 409 for events not currently in DLQ."""
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)

    # Requeue an event that is NOT in DLQ — should return 409 Conflict
    r = client.post(f"/dlq/{ev['event_id']}/requeue")
    assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"

    # Verify dlq_requeue_count is NOT incremented
    row = db.execute(
        "SELECT dlq_requeue_count FROM events WHERE event_id = ?",
        (ev["event_id"],),
    ).fetchone()
    assert row["dlq_requeue_count"] == 0


def test_requeue_unknown_event_returns_404(client: TestClient) -> None:
    """Requeue should return 404 for unknown events."""
    r = client.post("/dlq/nonexistent-event-id/requeue")
    assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"
