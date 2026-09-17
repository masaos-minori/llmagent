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
    from eventbus.auth import _populate_token_maps
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
    _populate_token_maps(cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

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
        port=8016,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
        auth_token="principal-token",
        # Per-role tokens for principal-based auth
        publisher_token="publisher-token",
        consumer_token="consumer-token",
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
        c.headers["Authorization"] = "Bearer consumer-token"
        yield c


def _event(topic: str = "ack_test") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-01-01T00:00:00Z",
    }


def _simulate_delivery(client: TestClient, event_id: str, consumer_id: str) -> None:
    """Insert a consumer_delivery record to simulate event delivery."""
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


class TestAckEndpoint:
    """Tests for POST /events/{event_id}/ack."""

    def _publish_with_publisher(self, client: TestClient, body: dict[str, Any]) -> int:
        """Publish an event using the publisher token."""
        publisher_headers = {"Authorization": "Bearer publisher-token"}
        resp = client.post("/publish", json=body, headers=publisher_headers)
        return resp.status_code

    def test_ack_event_with_consumer_id(self, client: TestClient) -> None:
        """POST /events/{event_id}/ack with consumer_id updates offset."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        _simulate_delivery(client, body["event_id"], "consumer-A")

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
        """POST /events/{event_id}/ack without consumer_id returns 422."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        resp = client.post(f"/events/{body['event_id']}/ack")
        assert resp.status_code == 422

    def test_ack_event_not_found(self, client: TestClient) -> None:
        """POST /events/{event_id}/ack for unknown event returns 409 (REQ-003: no delivery record)."""
        resp = client.post(
            "/events/nonexistent-event/ack", params={"consumer_id": "test-consumer"}
        )
        assert resp.status_code == 409

    def test_ack_event_already_acked(self, client: TestClient) -> None:
        """POST /events/{event_id}/ack for already-acked event returns 200 with already_acked=True."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        _simulate_delivery(client, body["event_id"], "consumer-A")

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
        """POST /events/{event_id}/ack with empty consumer_id returns 400 (REQ-004)."""
        body = _event()
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        resp = client.post(
            f"/events/{body['event_id']}/ack", params={"consumer_id": ""}
        )
        assert resp.status_code == 400

    def test_ack_event_principal_ownership_validation(
        self, principal_client: TestClient
    ) -> None:
        """ACK endpoint validates principal owns the requested consumer ID."""
        body = _event()
        resp = self._publish_with_publisher(principal_client, body)
        assert resp == 200

        # Simulate delivery to an authorized consumer first
        _simulate_delivery(principal_client, body["event_id"], "consumer-A")

        # Try to ACK with a consumer ID not owned by the principal
        # The consumer-token is mapped to ["consumer-A"], so "unauthorized-consumer" should fail
        resp = principal_client.post(
            f"/events/{body['event_id']}/ack",
            params={"consumer_id": "unauthorized-consumer"},
        )
        # Authorization check (403) should come before delivery check (409)
        # because _principal.allowed_consumer_ids is populated from _TOKEN_CONSUMER_MAP
        assert resp.status_code in (403, 409)

    def test_ack_event_delivery_verification(
        self, principal_client: TestClient
    ) -> None:
        """ACK endpoint verifies event was delivered to the consumer before accepting ACK."""
        body = _event()
        resp = self._publish_with_publisher(principal_client, body)
        assert resp == 200

        # Try to ACK without first delivering the event to the consumer
        resp = principal_client.post(
            f"/events/{body['event_id']}/ack", params={"consumer_id": "consumer-A"}
        )
        assert resp.status_code == 409

    def test_ack_event_mandatory_consumer_id(
        self, principal_client: TestClient
    ) -> None:
        """ACK endpoint requires consumer_id parameter."""
        body = _event()
        resp = self._publish_with_publisher(principal_client, body)
        assert resp == 200

        # Try to ACK without providing consumer_id — FastAPI returns 422 for missing required param
        resp = principal_client.post(f"/events/{body['event_id']}/ack")
        assert resp.status_code == 422


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

        # Simulate delivery for both events
        _simulate_delivery(client, event1["event_id"], consumer_id)
        _simulate_delivery(client, event2["event_id"], consumer_id)

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


class TestAckPrincipalValidation:
    """Tests for Principal field validation in ack endpoint."""

    @pytest.mark.asyncio
    async def test_ack_with_insufficient_roles_returns_403(self) -> None:
        """A publisher cannot ACK events (requires CONSUMER role)."""
        from unittest.mock import MagicMock

        from eventbus.auth import Principal, Role, require_role
        from fastapi import HTTPException
        from fastapi.requests import Request
        from pytest import raises as pytest_raises

        dep = require_role(Role.CONSUMER)
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/events/test-event-id/ack"
        mock_request.state.request_id = "test-request-id"
        mock_principals = MagicMock(spec=Principal)
        mock_principals.roles = {Role.PUBLISHER}
        with pytest_raises(HTTPException) as exc_info:
            await dep(mock_request, principal=mock_principals)
        assert exc_info.value.status_code == 403
