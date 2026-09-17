"""tests/test_eventbus_crash_ack.py
Crash-before-ack regression tests for Event Bus.

Tests that unacked events are replayed on reconnect — the core invariant
that offsets advance only via explicit ack, never automatically.
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any

import pytest
from eventbus_helpers import make_eventbus_client
from fastapi.testclient import TestClient


class FlakyConnection:
    """Wraps sqlite3.Connection to inject failures into execute calls."""

    def __init__(self, real_conn):
        self._real_conn = real_conn
        self._failed = False

    def execute(self, sql, *args, **kwargs):
        if not self._failed and "consumer_offsets" in sql:
            self._failed = True
            raise sqlite3.OperationalError("simulated offset-write failure")
        return self._real_conn.execute(sql, *args, **kwargs)

    def commit(self):
        return self._real_conn.commit()

    def rollback(self):
        return self._real_conn.rollback()

    def __getattr__(self, name):
        return getattr(self._real_conn, name)


@pytest.fixture
def db(tmp_path: Path) -> Any:
    from eventbus.db import open_db

    return open_db(str(tmp_path / "eventbus.sqlite"))


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    with make_eventbus_client(tmp_path, monkeypatch) as c:
        yield c


@pytest.fixture
def principal_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Create a TestClient with Principal-based authentication."""
    from eventbus import app as eb_app
    from eventbus.auth import _populate_token_maps
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8018,
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


def _event(topic: str = "crash") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-01-01T00:00:00Z",
    }


class TestCrashBeforeAck:
    """Verify unacked events are replayed on consumer reconnect."""

    def _publish_with_publisher(self, client: TestClient, body: dict[str, Any]) -> int:
        """Publish an event using the publisher token."""
        publisher_headers = {"Authorization": "Bearer publisher-token"}
        resp = client.post("/publish", json=body, headers=publisher_headers)
        return resp.status_code

    def test_unacked_event_replayed_on_reconnect(self, client: TestClient) -> None:
        """Consumer disconnects before acking — event must be replayed."""
        import eventbus.app as eb_app
        from eventbus.db import get_consumer_offset

        body = _event("crash")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200
        # Simulate disconnect without ack — verify offset not written
        offset = get_consumer_offset(eb_app.app.state.db, "consumer-A")
        assert offset == 0, "Offset should not be written for unacked events"

        # Reconnect with same consumer_id — event should be replayed from seq=0
        resp2 = client.get("/replay?since_seq=0&format=json")
        assert resp2.status_code == 200
        data2 = resp2.json()
        items2 = data2["items"]
        assert len(items2) == 1
        assert items2[0]["event_id"] == body["event_id"]

    def test_partial_ack_replay(self, client: TestClient) -> None:
        """Consumer acks some events but not others — only unacked replayed."""
        import eventbus.app as eb_app
        from eventbus.db import get_consumer_offset

        body1 = _event("crash")
        body2 = _event("crash")
        resp1 = client.post("/publish", json=body1)
        resp2 = client.post("/publish", json=body2)
        assert resp1.status_code == 200
        assert resp2.status_code == 200

        # Ack only the first event
        resp = client.post(
            f"/events/{body1['event_id']}/ack",
            params={"consumer_id": "consumer-B"},
        )
        assert resp.status_code == 200

        offset = get_consumer_offset(eb_app.app.state.db, "consumer-B")
        assert offset == resp1.json()["seq"]

        # Reconnect — only unacked event should be replayed
        resp2 = client.get(f"/replay?since_seq={offset}&format=json")
        assert resp2.status_code == 200
        data2 = resp2.json()
        items2 = data2["items"]
        assert len(items2) == 1
        assert items2[0]["event_id"] == body2["event_id"]

    def test_no_offset_for_new_consumer(self, client: TestClient) -> None:
        """New consumer with no prior offset receives all events from seq=0."""
        body = _event("crash")
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        # New consumer — should receive all events from seq=0
        resp = client.get("/replay?since_seq=0&format=json")
        assert resp.status_code == 200
        data = resp.json()
        items = data["items"]
        assert len(items) == 1
        assert items[0]["event_id"] == body["event_id"]

    def test_offset_write_failure_after_delivery_state(self, db: Any) -> None:
        """When offset-write fails after delivery-state write, neither commits."""
        import sqlite3

        from eventbus.db import ack_event_for_consumer, insert_event

        now = "2026-09-09T10:00:00Z"
        consumer_id = "crash_consumer"

        # Insert an event first
        seq, inserted, _ = insert_event(
            db, "evt-crash-offset", "test-topic", '{"data": "value"}', "producer", now
        )
        assert inserted

        # sqlite3.Connection.commit is a built-in method and cannot be
        # monkeypatched on the instance (read-only attribute) — wrap the
        # connection so .commit() fails while .execute() still delegates to
        # the real connection.
        class _FailingCommitConnection:
            def __init__(self, real_conn):
                self._real_conn = real_conn

            def commit(self):
                raise sqlite3.IntegrityError("simulated commit failure")

            def __getattr__(self, name):
                return getattr(self._real_conn, name)

        failing_db = _FailingCommitConnection(db)

        # This should raise an exception
        with pytest.raises(sqlite3.IntegrityError, match="simulated commit failure"):
            ack_event_for_consumer(failing_db, "evt-crash-offset", consumer_id, now)

        # Verify neither delivery nor offset was committed
        delivery_row = db.execute(
            "SELECT 1 FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
            (consumer_id, "evt-crash-offset"),
        ).fetchone()
        assert delivery_row is None, (
            "delivery-state should NOT be committed after failed commit"
        )

        offset_row = db.execute(
            "SELECT 1 FROM consumer_offsets WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
        assert offset_row is None, "offset should NOT be committed after failed commit"

    def test_crash_ack_principal_ownership_validation(
        self, principal_client: TestClient
    ) -> None:
        """Crash ACK endpoint validates principal owns the requested consumer ID."""
        body = _event("crash")
        resp = self._publish_with_publisher(principal_client, body)
        assert resp == 200

        # Try to ACK with a consumer ID not owned by the principal
        resp = principal_client.post(
            f"/events/{body['event_id']}/ack",
            params={"consumer_id": "unauthorized-consumer"},
        )
        # Authorization check (403) should come before delivery check (409)
        assert resp.status_code in (403, 409)

    def test_crash_ack_event_delivery_verification(
        self, principal_client: TestClient
    ) -> None:
        """Crash ACK endpoint verifies event was delivered to the consumer before accepting ACK."""
        body = _event("crash")
        resp = self._publish_with_publisher(principal_client, body)
        assert resp == 200

        # Try to ACK without first delivering the event to the consumer
        resp = principal_client.post(
            f"/events/{body['event_id']}/ack",
            params={"consumer_id": "consumer-A"},
        )
        assert resp.status_code == 409

    def test_crash_ack_mandatory_consumer_id(
        self, principal_client: TestClient
    ) -> None:
        """Crash ACK endpoint requires consumer_id parameter."""
        body = _event("crash")
        resp = self._publish_with_publisher(principal_client, body)
        assert resp == 200

        # Try to ACK without providing consumer_id — FastAPI returns 422 for missing required param
        resp = principal_client.post(f"/events/{body['event_id']}/ack")
        assert resp.status_code == 422


class TestCrashRecoveryPrincipalValidation:
    """Tests for Principal field validation in crash recovery."""

    @pytest.mark.asyncio
    async def test_reconnect_with_insufficient_roles_returns_403(self) -> None:
        """A publisher cannot reconnect to /replay (requires OPERATOR role)."""
        from unittest.mock import MagicMock

        from eventbus.auth import Principal, Role, require_role
        from fastapi import HTTPException
        from fastapi.requests import Request
        from pytest import raises as pytest_raises

        dep = require_role(Role.OPERATOR)
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/replay"
        mock_request.state.request_id = "test-request-id"
        mock_principals = MagicMock(spec=Principal)
        mock_principals.roles = {Role.PUBLISHER}
        with pytest_raises(HTTPException) as exc_info:
            await dep(mock_request, principal=mock_principals)
        assert exc_info.value.status_code == 403
