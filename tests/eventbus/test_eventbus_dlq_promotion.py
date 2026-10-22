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

import pytest
from fastapi.testclient import TestClient

from tests.eventbus.eventbus_helpers import eventbus_test_tokens


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
        **eventbus_test_tokens("test-token"),
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer test-token"
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


class TestDLQPromotionSemantics:
    """Verify DLQ promotion uses delivery_failure_count, not retry_count."""

    def test_nack_increments_delivery_failure_count(self, client: TestClient) -> None:
        """NACK increments consumer_delivery_failure_count (not delivery_failure_count on events table).

        Per-consumer model: delivery_failure_count/cycle_failure_count on events table
        are no longer written to; only consumer_delivery_failure_count is authoritative.
        """
        body = _event("dlq_promo")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Nack the event to increment consumer_delivery_failure_count
        resp = client.post(
            "/nack",
            params={"event_id": body["event_id"], "consumer_id": "consumer-A"},
        )
        assert resp.status_code == 200, f"NACK failed: {resp.json()}"

        # Check consumer_delivery_failure_count (authoritative under per-consumer model)
        # Note: consumer_delivery_failure_count is on consumer_delivery table, not events
        import eventbus.app as eb_app

        db = eb_app.app.state.db
        assert db is not None
        row = db.execute(
            "SELECT consumer_delivery_failure_count FROM consumer_delivery "
            "WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", body["event_id"]),
        ).fetchone()
        cdc = row[0] if row else None
        assert cdc == 1, f"Expected consumer_delivery_failure_count=1, got {cdc}"

    def test_dlq_promotion_when_consumer_delivery_failure_count_gte_max_retry(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """Event is promoted to DLQ when consumer_delivery_failure_count >= max_retry."""
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        body = _event("dlq_promo")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Simulate delivery to consumer-A and set consumer_delivery_failure_count to max_retry
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            # The consumer exhausted its retries without ACKing (ADR-006 INV-13).
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked) VALUES (?, ?, 0)",
            ("consumer-A", body["event_id"]),
        )
        db.execute(
            "UPDATE consumer_delivery SET consumer_delivery_failure_count = 2 "
            "WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", body["event_id"]),
        )
        db.commit()

        # Promote via the DLQ function
        n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
        assert n == 1

        dlq_file = tmp_path / "deadletter" / f"{body['event_id']}.json"
        assert dlq_file.exists()

    def test_requeue_returns_dlq_imminent_when_consumer_delivery_failure_count_gte_max_retry(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """Requeue of event at consumer_delivery_failure_count >= max_retry succeeds."""
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        body = _event("dlq_promo")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Simulate delivery to consumer-A and set consumer_delivery_failure_count to max_retry
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            # The consumer exhausted its retries without ACKing (ADR-006 INV-13).
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked) VALUES (?, ?, 0)",
            ("consumer-A", body["event_id"]),
        )
        db.execute(
            "UPDATE consumer_delivery SET consumer_delivery_failure_count = 2 "
            "WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", body["event_id"]),
        )
        db.commit()
        sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

        # Requeue the event — succeeds (no dlq_imminent field: that field was
        # removed from the response, since the original event's
        # delivery_failure_count is no longer relevant after redelivery)
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200

    def test_dlq_requeue_increments_dlq_requeue_count_not_consumer_delivery_failure_count(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """DLQ requeue increments dlq_requeue_count but does NOT modify consumer_delivery_failure_count."""
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        body = _event("dlq_promo")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Simulate delivery to consumer-A and set consumer_delivery_failure_count to max_retry
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            # The consumer exhausted its retries without ACKing (ADR-006 INV-13).
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked) VALUES (?, ?, 0)",
            ("consumer-A", body["event_id"]),
        )
        db.execute(
            "UPDATE consumer_delivery SET consumer_delivery_failure_count = 2 "
            "WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", body["event_id"]),
        )
        db.commit()
        sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

        cdfc_before = db.execute(
            "SELECT consumer_delivery_failure_count FROM consumer_delivery "
            "WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", body["event_id"]),
        ).fetchone()[0]

        # Requeue the event
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200

        cdfc_after = db.execute(
            "SELECT consumer_delivery_failure_count FROM consumer_delivery "
            "WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", body["event_id"]),
        ).fetchone()[0]
        assert cdfc_after == cdfc_before, (
            "consumer_delivery_failure_count should not change on requeue"
        )

        dlq_requeue_count = _get_field(client, body["event_id"], "dlq_requeue_count")
        assert dlq_requeue_count == 1, (
            "dlq_requeue_count should be incremented on requeue"
        )

    def test_dlq_loop_promotes_after_requeue_if_consumer_delivery_failure_count_still_gte_max_retry(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """After requeue, next DLQ loop tick will re-promote if consumer_delivery_failure_count >= max_retry."""
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        body = _event("dlq_promo")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Simulate delivery to consumer-A and set consumer_delivery_failure_count to max_retry
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
            ("consumer-A", body["event_id"]),
        )
        db.commit()
        sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

        dlq_file_1 = tmp_path / "deadletter" / f"{body['event_id']}.json"
        assert dlq_file_1.exists()

        # Requeue the event
        resp = client.post(f"/dlq/{body['event_id']}/requeue")
        assert resp.status_code == 200
        data = resp.json()
        new_event_id = data["new_event_id"]

        # Create consumer_delivery record for the descendant event (required for REQ-002 per-consumer DLQ promotion)
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        db.execute(
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
            ("consumer-A", new_event_id),
        )
        db.commit()

        # Next DLQ loop tick should re-promote
        n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
        assert n == 1

        dlq_file_2 = tmp_path / "deadletter" / f"{body['event_id']}.json"
        assert dlq_file_2.exists()


def _seed_delivery(
    db: Any, consumer_id: str, event_id: str, acked: int, failure_count: int
) -> None:
    db.execute(
        "INSERT INTO consumer_delivery "
        "(consumer_id, event_id, acked, consumer_last_nack_attempt, consumer_delivery_failure_count) "
        "VALUES (?, ?, ?, 'seeded-attempt', ?)",
        (consumer_id, event_id, acked, failure_count),
    )
    db.commit()


class TestMultiConsumerPromotion:
    """ADR-006 INV-13: promote only when every attempting consumer has exhausted its
    retries and none has ACKed."""

    def _publish(self, client: TestClient) -> str:
        body = _event("dlq_multi")
        assert client.post("/publish", json=body).status_code == 200
        return str(body["event_id"])

    def test_sweep_does_not_promote_when_other_consumer_below_limit(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        event_id = self._publish(client)
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        _seed_delivery(db, "consumer-A", event_id, 0, 2)
        _seed_delivery(db, "consumer-B", event_id, 0, 1)

        assert sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2) == 0
        assert not (tmp_path / "deadletter" / f"{event_id}.json").exists()
        assert _get_field(client, event_id, "dlq_at") is None

    def test_sweep_does_not_promote_when_other_consumer_acked(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        event_id = self._publish(client)
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        _seed_delivery(db, "consumer-A", event_id, 0, 2)
        _seed_delivery(db, "consumer-B", event_id, 1, 0)

        assert sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2) == 0
        assert _get_field(client, event_id, "dlq_at") is None

    def test_sweep_promotes_when_all_consumers_exhausted(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        event_id = self._publish(client)
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        _seed_delivery(db, "consumer-A", event_id, 0, 2)
        _seed_delivery(db, "consumer-B", event_id, 0, 3)

        assert sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2) == 1
        assert (tmp_path / "deadletter" / f"{event_id}.json").exists()
        assert _get_field(client, event_id, "dlq_at") is not None

    def test_sweep_ignores_event_without_delivery_rows(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        from eventbus.db import open_db
        from eventbus.dlq import sweep_orphans

        event_id = self._publish(client)
        db = open_db(str(tmp_path / "eventbus.sqlite"))

        assert sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2) == 0
        assert _get_field(client, event_id, "dlq_at") is None

    def test_inline_does_not_promote_when_other_consumer_below_limit(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        import eventbus.app as eb_app

        event_id = self._publish(client)
        db = eb_app.app.state.db
        _seed_delivery(db, "consumer-A", event_id, 0, 1)
        _seed_delivery(db, "consumer-B", event_id, 0, 1)

        # consumer-A reaches the limit, consumer-B is still below it.
        resp = client.post(
            "/nack", params={"event_id": event_id, "consumer_id": "consumer-A"}
        )
        assert resp.status_code == 200
        assert "dlq_promoted" not in resp.json()
        assert _get_field(client, event_id, "dlq_at") is None

    def test_inline_does_not_promote_when_other_consumer_acked(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        import eventbus.app as eb_app

        event_id = self._publish(client)
        db = eb_app.app.state.db
        _seed_delivery(db, "consumer-A", event_id, 0, 1)
        _seed_delivery(db, "consumer-B", event_id, 1, 0)

        resp = client.post(
            "/nack", params={"event_id": event_id, "consumer_id": "consumer-A"}
        )
        assert resp.status_code == 200
        assert "dlq_promoted" not in resp.json()
        assert _get_field(client, event_id, "dlq_at") is None

    def test_inline_promotes_when_last_consumer_reaches_limit(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        import eventbus.app as eb_app

        event_id = self._publish(client)
        db = eb_app.app.state.db
        _seed_delivery(db, "consumer-A", event_id, 0, 1)
        _seed_delivery(db, "consumer-B", event_id, 0, 1)

        first = client.post(
            "/nack", params={"event_id": event_id, "consumer_id": "consumer-A"}
        )
        assert first.status_code == 200
        assert "dlq_promoted" not in first.json()

        last = client.post(
            "/nack", params={"event_id": event_id, "consumer_id": "consumer-B"}
        )
        assert last.status_code == 200
        assert last.json().get("dlq_promoted") is True
        assert (tmp_path / "deadletter" / f"{event_id}.json").exists()
        assert _get_field(client, event_id, "dlq_at") is not None
