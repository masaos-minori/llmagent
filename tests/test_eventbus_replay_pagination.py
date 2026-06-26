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
        port=8016,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = Path(__file__).parent.parent / "schemas" / "event_envelope.json"
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    client = TestClient(eb_app.app)
    with client:
        yield client


def _event(topic: str = "test.topic") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"x": 1},
        "producer": "p1",
        "published_at": "2026-06-22T12:00:00Z",
    }


def test_replay_json_returns_paginated_response(client: TestClient) -> None:
    for i in range(5):
        client.post("/publish", json=_event())

    r = client.get("/replay?since_seq=0&format=json&limit=100&offset=0")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "limit" in body
    assert "offset" in body
    assert "items" in body
    assert body["total"] == 5
    assert body["limit"] == 100
    assert body["offset"] == 0
    assert len(body["items"]) == 5


def test_replay_json_pagination(client: TestClient) -> None:
    for i in range(5):
        client.post("/publish", json=_event())

    r1 = client.get("/replay?since_seq=0&format=json&limit=2&offset=0")
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["total"] == 5
    assert body1["limit"] == 2
    assert body1["offset"] == 0
    assert len(body1["items"]) == 2

    r2 = client.get("/replay?since_seq=0&format=json&limit=2&offset=2")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["total"] == 5
    assert body2["limit"] == 2
    assert body2["offset"] == 2
    assert len(body2["items"]) == 2

    ids1 = {e["event_id"] for e in body1["items"]}
    ids2 = {e["event_id"] for e in body2["items"]}
    assert ids1.isdisjoint(ids2)


def test_replay_json_limit_max(client: TestClient) -> None:
    r = client.get("/replay?since_seq=0&format=json&limit=1001")
    assert r.status_code == 422


def test_replay_json_limit_min(client: TestClient) -> None:
    r = client.get("/replay?since_seq=0&format=json&limit=0")
    assert r.status_code == 422


def test_replay_json_offset_negative(client: TestClient) -> None:
    r = client.get("/replay?since_seq=0&format=json&offset=-1")
    assert r.status_code == 422
