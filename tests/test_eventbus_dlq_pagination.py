from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8017,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = Path(__file__).parent.parent / "schemas" / "event_envelope.json"
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        yield c


def _event(topic: str = "test.topic") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"x": 1},
        "producer": "p1",
        "published_at": "2026-06-22T12:00:00Z",
    }


def test_dlq_list_returns_paginated_response(client: TestClient) -> None:
    for i in range(5):
        client.post("/publish", json=_event())

    r = client.get("/dlq?limit=100&offset=0")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "limit" in body
    assert "offset" in body
    assert "items" in body
    assert body["total"] == 0
    assert len(body["items"]) == 0


def test_dlq_pagination(client: TestClient) -> None:
    events = []
    for i in range(5):
        ev = _event()
        resp = client.post("/publish", json=ev)
        events.append(ev["event_id"])

    # Promote all to DLQ
    for event_id in events:
        client.post(f"/nack?event_id={event_id}")
    # Need to nack 3 times to reach max_retry
    for event_id in events:
        client.post(f"/nack?event_id={event_id}")

    r = client.get("/dlq?limit=100&offset=0")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 5
    assert len(body["items"]) == min(5, body["total"])

    # Page 2
    r2 = client.get(f"/dlq?limit=2&offset=2")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["limit"] == 2
    assert body2["offset"] == 2
    assert len(body2["items"]) == min(2, max(0, body["total"] - 2))
