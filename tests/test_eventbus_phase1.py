from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = Path(__file__).parent.parent / "schemas" / "event_envelope.json"
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)

    with TestClient(eb_app.app) as c:
        yield c


def _event(topic: str = "test.topic") -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-06-22T11:56:00Z",
    }


def test_health_returns_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_publish_inserts_event(client: TestClient, tmp_path: Path) -> None:
    ev = _event()
    r = client.post("/publish", json=ev)
    assert r.status_code == 200
    body = r.json()
    assert body["event_id"] == ev["event_id"]
    assert body["seq"] >= 1
    jsonl = (tmp_path / "storage" / "events.jsonl").read_text()
    assert ev["event_id"] in jsonl


def test_publish_idempotent(client: TestClient) -> None:
    ev = _event()
    r1 = client.post("/publish", json=ev)
    r2 = client.post("/publish", json=ev)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["seq"] == r2.json()["seq"]


def test_publish_invalid_schema(client: TestClient) -> None:
    r = client.post("/publish", json={"invalid": "body"})
    assert r.status_code == 422
