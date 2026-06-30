"""tests/test_eventbus_ack_endpoint.py
HTTP-level tests for POST /events/{event_id}/ack endpoint.

Tests ack endpoint behavior: path parameter vs query parameter, offset update,
404 cases, and the deprecated POST /ack alias.
"""

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
        max_retry=2,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = Path(__file__).parent.parent / "schemas" / "event_envelope.json"
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        yield c


def _event(topic: str = "ack_test") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-01-01T00:00:00Z",
    }


class TestAckEndpoint:
    """Tests for POST /events/{event_id}/ack."""

    def test_ack_event_with_consumer_id(self, client: TestClient) -> None:
        """POST /events/{event_id}/ack with consumer_id updates offset."""
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

        # Verify offset was written (check via DB state)
        import eventbus.app as eb_app

        db = eb_app.app.state.db
        row = db.execute(
            "SELECT acked_at FROM events WHERE event_id = ?",
            (body["event_id"],),
        ).fetchone()
        assert row is not None and row["acked_at"] is not None

    def test_ack_event_without_consumer_id(self, client: TestClient) -> None:
        """POST /events/{event_id}/ack without consumer_id returns seq=None."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        resp = client.post(f"/events/{body['event_id']}/ack")
        assert resp.status_code == 200
        data = resp.json()
        assert data["acked"] is True
        assert data["seq"] is None

    def test_ack_event_not_found(self, client: TestClient) -> None:
        """POST /events/{event_id}/ack for unknown event returns 404."""
        resp = client.post("/events/nonexistent-event/ack")
        assert resp.status_code == 404

    def test_ack_event_already_acked(self, client: TestClient) -> None:
        """POST /events/{event_id}/ack for already-acked event returns 200 with already_acked=True."""
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

    def test_ack_event_with_empty_consumer_id(self, client: TestClient) -> None:
        """POST /events/{event_id}/ack with empty consumer_id returns seq=None."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        resp = client.post(
            f"/events/{body['event_id']}/ack", params={"consumer_id": ""}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["acked"] is True
        assert data["seq"] is None


class TestLegacyAckEndpoint:
    """Tests for legacy POST /ack alias."""

    def test_legacy_ack_with_consumer_id(self, client: TestClient) -> None:
        """POST /ack with consumer_id updates offset (legacy alias)."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        resp = client.post(
            "/ack", params={"event_id": body["event_id"], "consumer_id": "consumer-B"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["acked"] is True
        assert data["seq"] is not None

    def test_legacy_ack_without_event_id(self, client: TestClient) -> None:
        """POST /ack without event_id returns 400."""
        resp = client.post("/ack")
        assert resp.status_code == 400


class TestAckMonotonicOffset:
    """Verify non-monotonic offset behavior: acking an older-seq event rolls offset back."""

    def test_older_seq_ack_moves_offset_backward(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        from eventbus.offsets import read_offset

        event1 = _event()
        event2 = _event()
        consumer_id = "consumer-mono"

        resp = client.post("/publish", json=event1)
        assert resp.status_code == 200
        resp = client.post("/publish", json=event2)
        assert resp.status_code == 200

        # ack event2 first (seq=2) → offset advances to 2
        resp = client.post(
            f"/events/{event2['event_id']}/ack",
            params={"consumer_id": consumer_id},
        )
        assert resp.status_code == 200
        assert resp.json()["seq"] == 2
        assert read_offset(str(tmp_path / "offsets"), consumer_id) == 2

        # ack event1 (seq=1, older) → offset rolls back to 1
        resp = client.post(
            f"/events/{event1['event_id']}/ack",
            params={"consumer_id": consumer_id},
        )
        assert resp.status_code == 200
        assert resp.json()["seq"] == 1
        assert read_offset(str(tmp_path / "offsets"), consumer_id) == 1, (
            "Non-monotonic: offset rolled back after acking older-seq event"
        )
