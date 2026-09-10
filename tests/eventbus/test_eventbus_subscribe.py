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
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        yield c


def _event(topic: str = "t") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-25T12:00:00Z",
    }


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["dlq_task"] == "running"


def test_duplicate_consumer_id_returns_409(client: TestClient) -> None:
    """A second concurrent /subscribe?consumer_id=X connection receives HTTP 409."""
    # First subscription succeeds
    resp1 = client.get("/subscribe", params={"consumer_id": "dup_test"})
    assert resp1.status_code == 200, \
        f"First subscription should succeed, got {resp1.status_code}"

    # Second subscription with the same consumer_id should fail with 409
    resp2 = client.get("/subscribe", params={"consumer_id": "dup_test"})
    assert resp2.status_code == 409, \
        f"Second subscription should receive 409, got {resp2.status_code}"

    # Verify the response body contains the expected error message
    body = resp2.json()
    assert "detail" in body, \
        "Response body should contain 'detail' field"
    assert "dup_test" in body["detail"], \
        f"Error detail should mention the consumer_id, got: {body['detail']}"
