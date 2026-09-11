"""tests/test_eventbus_ack_endpoint.py
HTTP-level tests for POST /events/{event_id}/ack endpoint.

Tests ack endpoint behavior: offset update, 404 cases, already-acked handling.
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
        auth_token="test-token",
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer test-token"
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

        # Verify the per-consumer delivery state was written (check via DB
        # state). ack_event_for_consumer() records acked_at on
        # consumer_delivery, not on events — a single event can be acked
        # independently by multiple consumers, so events.acked_at is no
        # longer the source of truth once a consumer_id is supplied.
        import eventbus.app as eb_app

        db = eb_app.app.state.db
        row = db.execute(
            "SELECT acked_at FROM consumer_delivery WHERE event_id = ? AND consumer_id = ?",
            (body["event_id"], "consumer-A"),
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


class TestAckMonotonicOffset:
    """Verify monotonic offset behavior: acking an older-seq event does not move the
    consumer's offset backward.

    This deliberately supersedes an older test (test_older_seq_ack_moves_offset_backward,
    removed here) that asserted the opposite — a rollback on an older-seq ack — and
    checked the legacy file-based read_offset(), which ack_event_for_consumer()'s
    SQLite-backed consumer_offsets table has replaced. The monotonic (non-regressing)
    behavior is the current, intentional design: see
    ack_event_for_consumer()'s `WHERE excluded.offset > consumer_offsets.offset` clause
    in scripts/eventbus/db.py, and the equivalent lower-level coverage in
    tests/eventbus/test_eventbus_offsets.py::TestConsumerOffsetsTable::test_offset_does_not_regress_on_older_seq.
    """

    def test_older_seq_ack_does_not_move_offset_backward(
        self, client: TestClient
    ) -> None:
        import eventbus.app as eb_app
        from eventbus.db import get_consumer_offset

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
        db = eb_app.app.state.db
        assert get_consumer_offset(db, consumer_id) == 2

        # ack event1 (seq=1, older) → offset stays at 2, does not regress
        resp = client.post(
            f"/events/{event1['event_id']}/ack",
            params={"consumer_id": consumer_id},
        )
        assert resp.status_code == 200
        assert resp.json()["seq"] == 1
        assert get_consumer_offset(db, consumer_id) == 2, (
            "Monotonic: offset must not regress after acking an older-seq event"
        )
