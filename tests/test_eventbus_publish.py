"""tests/test_eventbus_publish.py
Event Bus publish and health endpoint tests.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from eventbus_helpers import make_eventbus_client
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    with make_eventbus_client(tmp_path, monkeypatch) as c:
        yield c


def _event(topic: str = "test.topic") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-06-22T11:56:00Z",
    }


def test_health_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["dlq_task"] == "running"


def test_health_degraded_when_db_unavailable(client: TestClient) -> None:
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("DB gone")
    with patch("eventbus.app._db", mock_db):
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["db"] == "unavailable"


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


def test_publish_succeeds_if_jsonl_append_fails(client: TestClient) -> None:
    """JSONL append failure after SQLite commit must still return 200."""
    ev = _event()
    with patch("eventbus.app._append_jsonl", side_effect=OSError("disk full")):
        resp = client.post("/publish", json=ev)
    assert resp.status_code == 200
    assert resp.json()["event_id"] == ev["event_id"]

    replay = client.get("/replay", params={"since_seq": 0, "format": "json"})
    assert replay.status_code == 200
    event_ids = [e["event_id"] for e in replay.json()]
    assert ev["event_id"] in event_ids
