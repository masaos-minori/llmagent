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
        """POST /dlq/{event_id}/requeue for non-DLQ event returns 409 Conflict."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Event is not in DLQ (dlq_at IS NULL)
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 409

    def test_requeue_valid_dmq_event(self, client: TestClient, tmp_path: Path) -> None:
        """POST /dlq/{event_id}/requeue for valid DLQ event succeeds."""
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Promote to DLQ
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        # Create consumer_delivery record required for REQ-002 per-consumer DLQ promotion
        db.execute(
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked_at, consumer_delivery_failure_count) VALUES (?, ?, NULL, 2)",
            ("consumer-A", body["event_id"]),
        )
        db.commit()
        db.execute(
            "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
            (body["event_id"],),
        )
        db.commit()
        sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

        # Requeue should succeed
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        data = resp.json()
        assert data["requeued"] is True
        assert "new_event_id" in data
        assert data["new_event_id"] != body["event_id"]

        # Original event remains in DLQ (lineage model: original row's dlq_at IS NOT NULL)
        orig_row = db.execute(
            "SELECT dlq_at, dlq_requeue_count FROM events WHERE event_id = ?",
            (body["event_id"],),
        ).fetchone()
        assert orig_row["dlq_at"] is not None
        assert orig_row["dlq_requeue_count"] == 1

        # New event exists with redelivered_from set
        new_row = db.execute(
            "SELECT redelivered_from, cycle_failure_count FROM events WHERE event_id = ?",
            (data["new_event_id"],),
        ).fetchone()
        assert new_row["redelivered_from"] == body["event_id"]
        assert new_row["cycle_failure_count"] == 0

    def test_second_requeue_of_same_event_rejected_after_first_redeliver(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """Second requeue of the same original event_id is rejected (409).

        The lineage model permits only one redeliver per original event_id, by
        design (see dlq_route.py's dlq_requeue docstring: "the original row's
        dlq_at is intentionally left set so only one redeliver succeeds per
        original event") — this is a permanent, per-original-event rule, not a
        guard scoped only to simultaneous concurrent requests.
        """
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Promote to DLQ with delivery_failure_count >= max_retry
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        # Create consumer_delivery record required for REQ-002 per-consumer DLQ promotion
        db.execute(
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked_at, consumer_delivery_failure_count) VALUES (?, ?, NULL, 2)",
            ("consumer-A", body["event_id"]),
        )
        db.commit()
        db.execute(
            "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
            (body["event_id"],),
        )
        db.commit()
        sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

        # First requeue — succeeds: new descendant row inserted, original
        # row's dlq_requeue_count incremented
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        data = resp.json()
        assert "new_event_id" in data
        orig_row = db.execute(
            "SELECT dlq_requeue_count FROM events WHERE event_id = ?",
            (body["event_id"],),
        ).fetchone()
        assert orig_row["dlq_requeue_count"] == 1

        # The descendant inherits delivery_failure_count >= max_retry and its
        # own dlq_at starts NULL, so it (not the original) becomes the next
        # sweep's promotion candidate — the original's dlq_at is never
        # cleared by redeliver_event, so it is never re-selected here.
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
        assert n == 1

        # Second requeue of the SAME original event_id is rejected: a
        # descendant with redelivered_from == this event_id already exists,
        # so the lineage guard treats this original event as already
        # redelivered, permanently.
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 409

        # dlq_requeue_count is not incremented further by the rejected attempt
        assert _get_field(client, body["event_id"], "dlq_requeue_count") == 1

    def test_requeue_event_at_max_retry_then_re_promoted(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """Requeue succeeds; the original event's dlq_at is never cleared (lineage
        model), so the next DLQ tick promotes the new descendant event instead of
        re-promoting the original."""
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Promote to DLQ
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        # Create a consumer_delivery record (required for REQ-002 per-consumer DLQ promotion)
        db.execute(
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked_at, consumer_delivery_failure_count) VALUES (?, ?, NULL, 2)",
            ("consumer-A", body["event_id"]),
        )
        db.commit()
        db.execute(
            "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
            (body["event_id"],),
        )
        db.commit()
        sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

        dlq_file_1 = tmp_path / "deadletter" / f"{body['event_id']}.json"
        assert dlq_file_1.exists()

        # Requeue — returns new_event_id/new_seq per the lineage model (no
        # dlq_imminent field: that field was removed from the response)
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        data = resp.json()
        assert "new_event_id" in data

        # The original row's dlq_at is intentionally left set by the lineage
        # model (see dlq_route.py's dlq_requeue docstring) — it is not cleared
        # on requeue, so only one redeliver ever succeeds per original event.
        dlq_at = _get_field(client, body["event_id"], "dlq_at")
        assert dlq_at is not None

        # Next DLQ loop tick promotes the new descendant (its inherited
        # delivery_failure_count is still >= max_retry, and its own dlq_at
        # starts NULL) — not the original, whose dlq_at was never cleared.
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
        assert n == 1

        # This path coincides with dlq_file_1 above (same original event_id),
        # which was never removed — it is not itself proof the descendant was
        # promoted; that is what `n == 1` above already confirms.
        dlq_file_2 = tmp_path / "deadletter" / f"{body['event_id']}.json"
        assert dlq_file_2.exists()
