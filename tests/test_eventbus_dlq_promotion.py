"""tests/test_eventbus_dlq_promotion.py
DLQ promotion semantics regression tests for Event Bus.

Tests that DLQ promotion uses delivery_failure_count (not retry_count),
that dlq_requeue_count increments on requeue, and that the dlq_imminent
warning is returned when delivery_failure_count >= max_retry.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import orjson
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


def _event(topic: str = "dlq_promo") -> dict[str, Any]:
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


class TestDLQPROMotionSemantics:
    """Verify DLQ promotion uses delivery_failure_count, not retry_count."""

    def test_nack_increments_delivery_failure_count(self, client: TestClient) -> None:
        """nack increments delivery_failure_count (not retry_count)."""
        import eventbus.app as eb_app

        body = _event("dlq_promo")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Nack the event to increment delivery_failure_count
        client.post(
            "/nack",
            params={"event_id": body["event_id"], "consumer_id": "consumer-A"},
        )

        dfc = _get_field(client, body["event_id"], "delivery_failure_count")
        assert dfc == 1, f"Expected delivery_failure_count=1, got {dfc}"

    def test_dlq_promotion_when_delivery_failure_count_gte_max_retry(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """Event is promoted to DLQ when delivery_failure_count >= max_retry."""
        import eventbus.app as eb_app
        from eventbus.db import open_db
        from eventbus.dlq import promote_to_dlq

        body = _event("dlq_promo")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Set delivery_failure_count to max_retry to trigger inline promotion
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
            (body["event_id"],),
        )
        db.commit()

        # Promote via the DLQ function
        n = promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)
        assert n == 1

        dlq_file = tmp_path / "deadletter" / f"{body['event_id']}.json"
        assert dlq_file.exists()

    def test_requeue_returns_dlq_imminent_when_delivery_failure_count_gte_max_retry(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """Requeue of event at delivery_failure_count >= max_retry returns dlq_imminent warning."""
        import eventbus.app as eb_app
        from eventbus.db import open_db
        from eventbus.dlq import promote_to_dlq

        body = _event("dlq_promo")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Set delivery_failure_count to max_retry and promote to DLQ
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
            (body["event_id"],),
        )
        db.commit()
        promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

        # Requeue the event — should return dlq_imminent warning
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        data = resp.json()
        assert data["dlq_imminent"] is True, "dlq_imminent should be true when delivery_failure_count >= max_retry"

    def test_dlq_requeue_increments_dlq_requeue_count_not_delivery_failure_count(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """DLQ requeue increments dlq_requeue_count but does NOT modify delivery_failure_count."""
        import eventbus.app as eb_app
        from eventbus.db import open_db
        from eventbus.dlq import promote_to_dlq

        body = _event("dlq_promo")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Set delivery_failure_count to max_retry and promote to DLQ
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
            (body["event_id"],),
        )
        db.commit()
        promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

        dfc_before = _get_field(client, body["event_id"], "delivery_failure_count")

        # Requeue the event
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200

        dfc_after = _get_field(client, body["event_id"], "delivery_failure_count")
        assert dfc_after == dfc_before, "delivery_failure_count should not change on requeue"

        dlq_requeue_count = _get_field(client, body["event_id"], "dlq_requeue_count")
        assert dlq_requeue_count == 1, "dlq_requeue_count should be incremented on requeue"

    def test_dlq_loop_promotes_after_requeue_if_delivery_failure_count_still_gte_max_retry(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """After requeue, next DLQ loop tick will re-promote if delivery_failure_count >= max_retry."""
        import eventbus.app as eb_app
        from eventbus.db import open_db
        from eventbus.dlq import promote_to_dlq

        body = _event("dlq_promo")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Set delivery_failure_count to max_retry and promote to DLQ
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            "UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?",
            (body["event_id"],),
        )
        db.commit()
        promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

        dlq_file_1 = tmp_path / "deadletter" / f"{body['event_id']}.json"
        assert dlq_file_1.exists()

        # Requeue the event
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200

        # Next DLQ loop tick should re-promote
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        n = promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)
        assert n == 1

        dlq_file_2 = tmp_path / "deadletter" / f"{body['event_id']}.json"
        assert dlq_file_2.exists()
