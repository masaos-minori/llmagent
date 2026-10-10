from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.auth import _populate_token_maps
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8017,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
        auth_token="principal-token",
        publisher_token="publisher-token",
        consumer_token="consumer-token",
        # Fail-closed (ADR-013 INV-02): consumer_token requires a non-None
        # consumer_authorization. {} yields an unrestricted consumer principal,
        # preserving these DLQ pagination tests' consumer_id usage.
        consumer_authorization={},
        operator_token="operator-token",
        monitoring_token="monitoring-token",
        admin_token="admin-token",
    )
    _populate_token_maps(cfg)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer consumer-token"
        yield c


def _event(topic: str = "test.topic") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"x": 1},
        "producer": "p1",
        "published_at": "2026-06-22T12:00:00Z",
    }


def _publish_event(client: Any, ev: dict[str, Any]) -> None:
    """Publish an event using the publisher token."""
    headers = {"Authorization": "Bearer publisher-token"}
    client.post("/publish", json=ev, headers=headers)


def _simulate_delivery(client: Any, event_id: str, consumer_id: str) -> None:
    """Insert a consumer_delivery record simulating one prior failed attempt.

    Seeds consumer_delivery_failure_count=1 with a mismatched last_nack_attempt
    so a subsequent NACK is not treated as a REQ-001 repeat and instead brings
    the per-consumer count to max_retry(2), enabling per-consumer DLQ promotion
    (REQ-002).
    """
    import eventbus.app as eb_app

    db = eb_app.app.state.db
    db.execute(
        "DELETE FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
        (consumer_id, event_id),
    )
    db.execute(
        "INSERT INTO consumer_delivery "
        "(consumer_id, event_id, acked_at, last_nack_attempt, consumer_delivery_failure_count) "
        "VALUES (?, ?, NULL, 'seeded-attempt', 1)",
        (consumer_id, event_id),
    )
    db.commit()


def test_dlq_list_returns_paginated_response(client: TestClient) -> None:
    pub_headers = {"Authorization": "Bearer publisher-token"}
    for i in range(5):
        client.post("/publish", json=_event(), headers=pub_headers)

    op_headers = {"Authorization": "Bearer operator-token"}
    r = client.get("/dlq?limit=100&offset=0", headers=op_headers)
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
        _publish_event(client, ev)
        events.append(ev["event_id"])

    # Simulate one prior failure per event so a single NACK reaches max_retry(2).
    for event_id in events:
        _simulate_delivery(client, event_id, "consumer-A")

    # Promote all to DLQ. Under per-consumer gating (REQ-002) a single consumer
    # reaching its own max_retry promotes; the shared delivery_failure_count is
    # intentionally not used for promotion gating.
    nack_headers = {"Authorization": "Bearer consumer-token"}
    for event_id in events:
        r = client.post(
            "/nack",
            params={"event_id": event_id, "consumer_id": "consumer-A"},
            headers=nack_headers,
        )
        assert r.status_code == 200

    dlq_headers = {"Authorization": "Bearer operator-token"}
    r = client.get("/dlq?limit=100&offset=0", headers=dlq_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 5
    assert len(body["items"]) == min(5, body["total"])

    # Page 2
    r2 = client.get("/dlq?limit=2&offset=2", headers=dlq_headers)
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["limit"] == 2
    assert body2["offset"] == 2
    assert len(body2["items"]) == min(2, max(0, body["total"] - 2))
