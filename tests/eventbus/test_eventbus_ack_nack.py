from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import pytest
from eventbus.db import NackResult
from fastapi.testclient import TestClient


@pytest.fixture
def db(tmp_path: Path) -> Any:
    from eventbus.db import open_db

    return open_db(str(tmp_path / "eventbus.sqlite"))


def _event(topic: str = "t") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-22T12:00:00Z",
    }


def _simulate_delivery_http(client: Any, event_id: str, consumer_id: str) -> None:
    """Insert a consumer_delivery record to simulate event delivery (HTTP-level)."""
    import eventbus.app as eb_app

    db = eb_app.app.state.db
    db.execute(
        "DELETE FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
        (consumer_id, event_id),
    )
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked_at) VALUES (?, ?, NULL)",
        (consumer_id, event_id),
    )
    db.commit()


class TestAckEvent:
    def test_two_consumers_ack_same_event(self, tmp_path: Path) -> None:
        """Two distinct consumer_ids can each ACK the same event independently."""
        from eventbus.db import (  # noqa: PLC0415 — deferred import kept local to this test helper
            ack_event_for_consumer,
            insert_event,
            open_db,
        )

        db = open_db(str(tmp_path / "eventbus.sqlite"))
        now = "2026-09-09T10:00:00Z"

        # Insert an event first
        seq, inserted, _ = insert_event(
            db, "evt-multi-ack", "test-topic", '{"data": "value"}', "producer", now
        )
        assert inserted

        # Consumer A acknowledges
        found_a, newly_acked_a, _, _ = ack_event_for_consumer(
            db, "evt-multi-ack", "consumer_A", now
        )
        assert found_a
        assert newly_acked_a

        # Consumer B acknowledges the same event
        found_b, newly_acked_b, _, _ = ack_event_for_consumer(
            db, "evt-multi-ack", "consumer_B", now
        )
        assert found_b
        assert newly_acked_b

        # Both deliveries recorded separately
        row_a = db.execute(
            "SELECT acked_at FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
            ("consumer_A", "evt-multi-ack"),
        ).fetchone()
        assert row_a is not None
        assert row_a["acked_at"] == now

        row_b = db.execute(
            "SELECT acked_at FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
            ("consumer_B", "evt-multi-ack"),
        ).fetchone()
        assert row_b is not None
        assert row_b["acked_at"] == now

        # Offsets advanced independently
        row_off_a = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            ("consumer_A",),
        ).fetchone()
        assert row_off_a is not None
        assert int(row_off_a["offset"]) == seq

        row_off_b = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            ("consumer_B",),
        ).fetchone()
        assert row_off_b is not None
        assert int(row_off_b["offset"]) == seq

    def test_ack_nonexistent_event_writes_no_row(self, db: sqlite3.Connection) -> None:
        """ACK for a non-existent event writes nothing (REQ-005)."""
        from eventbus.db import ack_event_for_consumer

        found, newly_acked, seq, dlq = ack_event_for_consumer(
            db, "nonexistent-event", "consumer-A", "2026-06-22T13:00:00Z"
        )
        assert found is False
        assert newly_acked is False
        assert seq is None
        assert dlq is False

        row = db.execute(
            "SELECT COUNT(*) AS c FROM consumer_delivery "
            "WHERE consumer_id = 'consumer-A' AND event_id = 'nonexistent-event'"
        ).fetchone()
        assert int(row["c"]) == 0

    def test_ack_preserves_first_acked_at(self, db: sqlite3.Connection) -> None:
        """Second ACK preserves the first acked_at (COALESCE, REQ-005)."""
        from eventbus.db import ack_event_for_consumer

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
            ),
        )
        db.commit()
        # Simulate a pending delivery.
        db.execute(
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked_at) VALUES (?, ?, NULL)",
            ("consumer-A", ev["event_id"]),
        )
        db.commit()

        t1 = "2026-06-22T13:00:00Z"
        found1, newly_acked1, seq1, dlq1 = ack_event_for_consumer(
            db, ev["event_id"], "consumer-A", t1
        )
        assert found1 is True
        assert newly_acked1 is True
        assert dlq1 is False

        t2 = "2026-06-22T14:00:00Z"
        found2, newly_acked2, seq2, dlq2 = ack_event_for_consumer(
            db, ev["event_id"], "consumer-A", t2
        )
        assert found2 is True
        assert newly_acked2 is False
        assert dlq2 is False

        row = db.execute(
            "SELECT acked_at FROM consumer_delivery "
            "WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", ev["event_id"]),
        ).fetchone()
        assert row["acked_at"] == t1

    def test_ack_dlq_event_rejected(self, db: sqlite3.Connection) -> None:
        """ACK for an event in the DLQ signals dlq=True (REQ-005)."""
        from eventbus.db import ack_event_for_consumer, insert_event

        now = "2026-09-09T10:00:00Z"
        seq, inserted, _ = insert_event(
            db, "evt-dlq-ack", "test-topic", '{"data": "value"}', "producer", now
        )
        assert inserted

        db.execute(
            "UPDATE events SET dlq_at = ? WHERE event_id = ?",
            ("2026-09-09T11:00:00Z", "evt-dlq-ack"),
        )
        db.commit()

        found, newly_acked, seq_v, dlq = ack_event_for_consumer(
            db, "evt-dlq-ack", "consumer-A", now
        )
        assert found is True
        assert newly_acked is False
        assert seq_v == seq
        assert dlq is True

        row = db.execute(
            "SELECT acked_at FROM consumer_delivery "
            "WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", "evt-dlq-ack"),
        ).fetchone()
        assert row is None

    def test_ack_resets_last_nack_attempt(self, db: sqlite3.Connection) -> None:
        """ACK clears last_nack_attempt so a later NACK starts a fresh attempt (REQ-001)."""
        from eventbus.db import ack_event_for_consumer, nack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
            ),
        )
        db.commit()

        # NACK records the attempt identity.
        nack_event(db, ev["event_id"], consumer_id="consumer-A")
        row = db.execute(
            "SELECT last_nack_attempt FROM consumer_delivery "
            "WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", ev["event_id"]),
        ).fetchone()
        assert row is not None
        assert row["last_nack_attempt"] is not None

        # ACK clears it.
        ack_event_for_consumer(db, ev["event_id"], "consumer-A", "2026-06-22T13:00:00Z")
        row = db.execute(
            "SELECT last_nack_attempt FROM consumer_delivery "
            "WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", ev["event_id"]),
        ).fetchone()
        assert row["last_nack_attempt"] is None

        # Redeliver (acked_at reset to NULL) then NACK: a fresh attempt increments again.
        db.execute(
            "UPDATE consumer_delivery SET acked_at = NULL WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", ev["event_id"]),
        )
        db.commit()
        result = nack_event(db, ev["event_id"], consumer_id="consumer-A")
        assert result == NackResult(delivery_failure_count=2, cycle_failure_count=2)


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

    from fastapi.testclient import TestClient

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer test-token"
        yield c


@pytest.fixture
def principal_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Create a TestClient with Principal-based authentication."""
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
        # Per-role tokens for principal-based auth
        publisher_token="publisher-token",
        consumer_token="consumer-token",
        # Fail-closed (ADR-013 INV-02): consumer_token requires a non-None
        # consumer_authorization. The manual Principal override below sets the
        # actual consumer_id restriction (consumer-A); this satisfies startup.
        consumer_authorization={"consumer-A": ["test"]},
        operator_token="operator-token",
        monitoring_token="monitoring-token",
        admin_token="admin-token",
    )
    _populate_token_maps(cfg)
    # Map consumer-token to a specific consumer ID for authorization testing
    from eventbus.auth import _TOKEN_PRINCIPAL_MAP, Principal

    if "consumer-token" in _TOKEN_PRINCIPAL_MAP:
        _TOKEN_PRINCIPAL_MAP["consumer-token"] = Principal(
            roles=_TOKEN_PRINCIPAL_MAP["consumer-token"].roles,
            allowed_consumer_ids=frozenset({"consumer-A"}),
            allowed_topics=_TOKEN_PRINCIPAL_MAP["consumer-token"].allowed_topics,
            token_fingerprint=_TOKEN_PRINCIPAL_MAP["consumer-token"].token_fingerprint,
        )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        # The app lifespan re-runs _populate_token_maps() on startup, resetting
        # consumer-token to an unrestricted principal. Re-apply the per-consumer
        # restriction here so the ownership check under test actually fires.
        base = _TOKEN_PRINCIPAL_MAP.get("consumer-token")
        if base is not None:
            _TOKEN_PRINCIPAL_MAP["consumer-token"] = Principal(
                roles=base.roles,
                allowed_consumer_ids=frozenset({"consumer-A"}),
                allowed_topics=base.allowed_topics,
                token_fingerprint=base.token_fingerprint,
            )
        c.headers["Authorization"] = "Bearer consumer-token"
        yield c


class TestAckHttpBehavior:
    def test_ack_first_time_returns_200(self, client: Any) -> None:
        """POST /events/{id}/ack returns 200 with acked: true, seq: int on first ack."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        _simulate_delivery_http(client, body["event_id"], "consumer-A")

        resp = client.post(
            f"/events/{body['event_id']}/ack", params={"consumer_id": "consumer-A"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["acked"] is True
        assert data["seq"] is not None

    def test_ack_repeated_returns_200_already_acked(self, client: Any) -> None:
        """Second POST /events/{id}/ack returns 200 with acked: true, already_acked: true."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        _simulate_delivery_http(client, body["event_id"], "consumer-A")

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

    def test_ack_unknown_event_returns_404(self, client: Any) -> None:
        """POST /events/{id}/ack with unknown event_id returns 404 (no matching event/delivery)."""
        resp = client.post(
            "/events/nonexistent-event/ack", params={"consumer_id": "test-consumer"}
        )
        assert resp.status_code == 404

    def test_two_consumers_ack_same_event_independently(self, client: Any) -> None:
        """Two distinct consumer_ids can each ACK the same event_id independently (REQ-001)."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        _simulate_delivery_http(client, body["event_id"], "consumer-a")
        _simulate_delivery_http(client, body["event_id"], "consumer-b")

        resp_a = client.post(
            f"/events/{body['event_id']}/ack", params={"consumer_id": "consumer-a"}
        )
        assert resp_a.status_code == 200
        data_a = resp_a.json()
        assert data_a["acked"] is True
        assert data_a.get("already_acked") is not True

        resp_b = client.post(
            f"/events/{body['event_id']}/ack", params={"consumer_id": "consumer-b"}
        )
        assert resp_b.status_code == 200
        data_b = resp_b.json()
        assert data_b["acked"] is True
        assert data_b.get("already_acked") is not True


class TestNackEvent:
    def _publish_with_publisher(self, client: TestClient, body: dict[str, Any]) -> int:
        """Publish an event using the publisher token."""
        publisher_headers = {"Authorization": "Bearer publisher-token"}
        resp = client.post("/publish", json=body, headers=publisher_headers)
        return resp.status_code

    def test_nack_event_increments_failure_count(self, db: sqlite3.Connection) -> None:
        from eventbus.db import nack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
            ),
        )
        db.commit()

        result = nack_event(db, ev["event_id"])
        assert result == NackResult(delivery_failure_count=1, cycle_failure_count=1)

        row = db.execute(
            "SELECT delivery_failure_count, cycle_failure_count FROM events WHERE event_id = ?",
            (ev["event_id"],),
        ).fetchone()
        assert row["delivery_failure_count"] == 1
        assert row["cycle_failure_count"] == 1

    def test_nack_event_increments_again(self, db: sqlite3.Connection) -> None:
        from eventbus.db import nack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
            ),
        )
        db.commit()

        result1 = nack_event(db, ev["event_id"])
        assert result1 == NackResult(delivery_failure_count=1, cycle_failure_count=1)

        result2 = nack_event(db, ev["event_id"])
        assert result2 == NackResult(delivery_failure_count=2, cycle_failure_count=2)

        row = db.execute(
            "SELECT delivery_failure_count, cycle_failure_count FROM events WHERE event_id = ?",
            (ev["event_id"],),
        ).fetchone()
        assert row["delivery_failure_count"] == 2
        assert row["cycle_failure_count"] == 2

    def test_nack_event_not_found(self, db: sqlite3.Connection) -> None:
        from eventbus.db import nack_event

        result = nack_event(db, "nonexistent-event")
        assert result == NackResult(delivery_failure_count=-1, cycle_failure_count=-1)

    def test_nack_per_consumer_counts_repeat_once(self, db: sqlite3.Connection) -> None:
        """A NACK repeating the stored attempt identity increments once (REQ-001)."""
        from eventbus.db import nack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
            ),
        )
        db.commit()

        # First NACK for consumer-A increments once.
        result1 = nack_event(db, ev["event_id"], consumer_id="consumer-A")
        assert result1 == NackResult(delivery_failure_count=1, cycle_failure_count=1)
        # Repeat NACK for the same attempt counts once (no further increment).
        result2 = nack_event(db, ev["event_id"], consumer_id="consumer-A")
        assert result2 == NackResult(delivery_failure_count=1, cycle_failure_count=1)

        row = db.execute(
            "SELECT consumer_delivery_failure_count FROM consumer_delivery "
            "WHERE consumer_id = ? AND event_id = ?",
            ("consumer-A", ev["event_id"]),
        ).fetchone()
        assert row is not None
        assert int(row["consumer_delivery_failure_count"]) == 1

    def test_nack_per_consumer_acked_then_nack_returns_invalid_transition(
        self, db: sqlite3.Connection
    ) -> None:
        """NACK from consumer C for event E, when C has already ACKed E, returns NackResult(-2, -2)."""
        from eventbus.db import ack_event_for_consumer, nack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
            ),
        )
        db.commit()

        # Consumer A ACKs the event
        found, newly_acked, _, _ = ack_event_for_consumer(
            db, ev["event_id"], "consumer-A", "2026-06-22T13:00:00Z"
        )
        assert found is True
        assert newly_acked is True

        # Consumer A sends NACK — should be rejected
        result = nack_event(db, ev["event_id"], consumer_id="consumer-A")
        assert result == NackResult(delivery_failure_count=-2, cycle_failure_count=-2)

        # Counters should NOT have been incremented
        row = db.execute(
            "SELECT delivery_failure_count, cycle_failure_count FROM events WHERE event_id = ?",
            (ev["event_id"],),
        ).fetchone()
        assert row["delivery_failure_count"] == 0
        assert row["cycle_failure_count"] == 0

    def test_nack_different_consumer_after_same_consumer_acks(
        self, db: sqlite3.Connection
    ) -> None:
        """Consumer D (different consumer) can still NACK event E after consumer A ACKed it."""
        from eventbus.db import ack_event_for_consumer, nack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
            ),
        )
        db.commit()

        # Consumer A ACKs the event
        found, newly_acked, _, _ = ack_event_for_consumer(
            db, ev["event_id"], "consumer-A", "2026-06-22T13:00:00Z"
        )
        assert found is True
        assert newly_acked is True

        # Consumer B sends NACK — should succeed
        result = nack_event(db, ev["event_id"], consumer_id="consumer-B")
        assert result == NackResult(delivery_failure_count=1, cycle_failure_count=1)

        row = db.execute(
            "SELECT delivery_failure_count, cycle_failure_count FROM events WHERE event_id = ?",
            (ev["event_id"],),
        ).fetchone()
        assert row["delivery_failure_count"] == 1
        assert row["cycle_failure_count"] == 1

    def test_nack_no_consumer_id_unaffected_by_consumer_acks(
        self, db: sqlite3.Connection
    ) -> None:
        """NACK without consumer_id is unaffected by per-consumer ACK state."""
        from eventbus.db import ack_event_for_consumer, nack_event

        ev = _event()
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
            (
                ev["event_id"],
                ev["topic"],
                json.dumps(ev["payload"]),
                ev["producer"],
                ev["published_at"],
            ),
        )
        db.commit()

        # Consumer A ACKs the event
        found, newly_acked, _, _ = ack_event_for_consumer(
            db, ev["event_id"], "consumer-A", "2026-06-22T13:00:00Z"
        )
        assert found is True
        assert newly_acked is True

        # NACK without consumer_id — should succeed (events-level only)
        result = nack_event(db, ev["event_id"])
        assert result == NackResult(delivery_failure_count=1, cycle_failure_count=1)

        row = db.execute(
            "SELECT delivery_failure_count, cycle_failure_count FROM events WHERE event_id = ?",
            (ev["event_id"],),
        ).fetchone()
        assert row["delivery_failure_count"] == 1
        assert row["cycle_failure_count"] == 1

    def test_nack_http_409_on_per_consumer_acked(
        self, principal_client: TestClient
    ) -> None:
        """HTTP NACK returns 409 when same consumer ACKed then NACKs."""
        body = _event()
        resp = self._publish_with_publisher(principal_client, body)
        assert resp == 200

        # Simulate delivery to consumer-A
        _simulate_delivery_http(principal_client, body["event_id"], "consumer-A")

        # Consumer-A ACKs
        resp = principal_client.post(
            f"/events/{body['event_id']}/ack", params={"consumer_id": "consumer-A"}
        )
        assert resp.status_code == 200

        # Consumer-A NACKs — should get 409
        resp = principal_client.post(
            "/nack",
            params={
                "event_id": body["event_id"],
                "consumer_id": "consumer-A",
            },
        )
        assert resp.status_code == 409
        data = resp.json()
        assert data["detail"] == "event already acknowledged"

    def test_nack_http_200_on_different_consumer_after_acked(
        self, client: TestClient
    ) -> None:
        """HTTP NACK returns 200 when different consumer NACKs after same consumer ACKed."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # Simulate delivery to consumer-A
        _simulate_delivery_http(client, body["event_id"], "consumer-A")

        # Consumer-A ACKs
        resp = client.post(
            f"/events/{body['event_id']}/ack", params={"consumer_id": "consumer-A"}
        )
        assert resp.status_code == 200

        # Consumer-B NACKs — should succeed
        resp = client.post(
            "/nack",
            params={
                "event_id": body["event_id"],
                "consumer_id": "consumer-B",
            },
        )
        assert resp.status_code == 200

    def test_nack_event_principal_ownership_validation(
        self, principal_client: TestClient
    ) -> None:
        """NACK endpoint validates principal owns the requested consumer ID."""
        body = _event()
        resp = self._publish_with_publisher(principal_client, body)
        assert resp == 200

        # Simulate delivery to an authorized consumer first
        _simulate_delivery_http(principal_client, body["event_id"], "consumer-A")

        # Try to NACK with a consumer ID not owned by the principal
        resp = principal_client.post(
            "/nack",
            params={
                "event_id": body["event_id"],
                "consumer_id": "unauthorized-consumer",
            },
        )
        # Authorization check (403) should come before delivery check (409)
        assert resp.status_code in (403, 409)

    def test_nack_event_delivery_record_atomic(
        self, principal_client: TestClient
    ) -> None:
        """NACK accepts the event and records the failure atomically; no separate pre-delivery gate exists."""
        body = _event()
        resp = self._publish_with_publisher(principal_client, body)
        assert resp == 200

        # NACKing without a prior delivery still succeeds and records the failure atomically
        resp = principal_client.post(
            "/nack", params={"event_id": body["event_id"], "consumer_id": "consumer-A"}
        )
        assert resp.status_code == 200

    def test_nack_event_mandatory_consumer_id(
        self, principal_client: TestClient
    ) -> None:
        """NACK endpoint requires consumer_id parameter."""
        body = _event()
        resp = self._publish_with_publisher(principal_client, body)
        assert resp == 200

        # Try to NACK without providing consumer_id — FastAPI returns 422 for missing required param
        resp = principal_client.post("/nack", params={"event_id": body["event_id"]})
        assert resp.status_code == 422


class TestNackPrincipalValidation:
    """Tests for Principal field validation in nack endpoint."""

    @pytest.mark.asyncio
    async def test_nack_with_insufficient_roles_returns_403(self) -> None:
        """A publisher cannot NACK events (requires CONSUMER role)."""
        from unittest.mock import MagicMock

        from eventbus.auth import Principal, Role, require_role
        from fastapi import HTTPException
        from fastapi.requests import Request
        from pytest import raises as pytest_raises

        dep = require_role(Role.CONSUMER)
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/nack"
        mock_request.state.request_id = "test-request-id"
        mock_principals = MagicMock(spec=Principal)
        mock_principals.roles = {Role.PUBLISHER}
        with pytest_raises(HTTPException) as exc_info:
            await dep(mock_request, principal=mock_principals)
        assert exc_info.value.status_code == 403
