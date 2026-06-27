"""tests/test_eventbus_requeue_edge_cases.py
Edge case tests for POST /dlq/{event_id}/requeue endpoint.

Tests requeue behavior: unknown event, non-DLQ event, repeated requeue,
and re-promotion after requeue when delivery_failure_count >= max_retry.
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


def _event(topic: str = "requeue_test") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-01-01T00:00:00Z",
    }


def _get_field(client: TestClient, event_id: str, field: str) -> Any:
    import eventbus.app as eb_app

    db = eb_app.app.state.db
    assert db is not None
    row = db.execute(
        f"SELECT {field} FROM events WHERE event_id = ?",
        (event_id,),
    ).fetchone()
    return row[0] if row else None


class TestRequeueEdgeCases:
    """Tests for POST /dlq/{event_id}/requeue edge cases."""

    def test_requeue_unknown_event(self, client: TestClient) -> None:
        """POST /dlq/{event_id}/requeue for unknown event returns 404."""
        resp = client.post("/dlq/nonexistent-event/requeue")
        assert resp.status_code == 404

    def test_requeue_non_dmq_event(self, client: TestClient) -> None:
        """POST /dlq/{event_id}/requeue for non-DLQ event returns 404."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Event is not in DLQ (dlq_at IS NULL)
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 404

    def test_requeue_valid_dmq_event(self, client: TestClient, tmp_path: Path) -> None:
        """POST /dlq/{event_id}/requeue for valid DLQ event succeeds."""
        from eventbus.db import open_db
        from eventbus.dlq import promote_to_dlq

        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Promote to DLQ
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
            (body["event_id"],),
        )
        db.commit()
        promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

        # Requeue should succeed
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        data = resp.json()
        assert data["requeued"] is True
        assert data["dlq_imminent"] is True

        # Verify dlq_at was cleared
        dlq_at = _get_field(client, body["event_id"], "dlq_at")
        assert dlq_at is None

    def test_repeated_requeue_increments_dlq_requeue_count(self, client: TestClient, tmp_path: Path) -> None:
        """Repeated requeue of same event increments dlq_requeue_count each time."""
        from eventbus.db import open_db
        from eventbus.dlq import promote_to_dlq

        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Promote to DLQ with delivery_failure_count >= max_retry so re-promotion works
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
            (body["event_id"],),
        )
        db.commit()
        promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

        # First requeue
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        assert _get_field(client, body["event_id"], "dlq_requeue_count") == 1

        # Re-promote to DLQ before second requeue (delivery_failure_count >= max_retry so it will be promoted)
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        n = promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)
        assert n == 1

        # Second requeue
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        assert _get_field(client, body["event_id"], "dlq_requeue_count") == 2

        # Re-promote to DLQ before third requeue
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        n = promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)
        assert n == 1

        # Third requeue
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        assert _get_field(client, body["event_id"], "dlq_requeue_count") == 3

    def test_requeue_event_at_max_retry_then_re_promoted(self, client: TestClient, tmp_path: Path) -> None:
        """Requeue of event at delivery_failure_count >= max_retry succeeds but re-promoted on next DLQ tick."""
        from eventbus.db import open_db
        from eventbus.dlq import promote_to_dlq

        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Promote to DLQ
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
            (body["event_id"],),
        )
        db.commit()
        promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

        dlq_file_1 = tmp_path / "deadletter" / f"{body['event_id']}.json"
        assert dlq_file_1.exists()

        # Requeue — returns dlq_imminent warning
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        data = resp.json()
        assert data["dlq_imminent"] is True

        # Verify dlq_at was cleared in DB
        dlq_at = _get_field(client, body["event_id"], "dlq_at")
        assert dlq_at is None

        # Next DLQ loop tick should re-promote (delivery_failure_count still >= max_retry)
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        n = promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)
        assert n == 1

        dlq_file_2 = tmp_path / "deadletter" / f"{body['event_id']}.json"
        assert dlq_file_2.exists()
