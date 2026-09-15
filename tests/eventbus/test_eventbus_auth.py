#!/usr/bin/env python3
"""tests/eventbus/test_eventbus_auth.py

Positive/negative authorization tests for every EventBus route category.

Each route category has:
- One authorized-success case
- One unauthorized/wrong-role-rejection case

Precedent: scripts/mcp_servers/server.py::attach_auth_middleware() pattern
"""

import asyncio
import time
from datetime import UTC
from pathlib import Path
from typing import Any

import pytest
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.testclient import TestClient

TEST_TOKEN = "test-auth-token"
TEST_DB_PATH = "/tmp/test-eventbus.sqlite"
TEST_STORAGE_DIR = "/tmp/test-storage"
TEST_OFFSETS_DIR = "/tmp/test-offsets"
TEST_DEADLETTER_DIR = "/tmp/test-deadletter"


def _make_test_app(
    tmp_path: Path,
    token: str | None = None,
    publisher_token: str | None = None,
    consumer_token: str | None = None,
    operator_token: str | None = None,
    admin_token: str | None = None,
) -> tuple[FastAPI, Any]:
    """Create a fresh FastAPI app with auth middleware registered."""
    from eventbus import app as eb_app
    from eventbus.auth import (
        Principal,
        Role,
        attach_auth_middleware,
        require_consumer_identity,
        require_role,
    )
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
        host="127.0.0.1",
        auth_token=token,
        publisher_token=publisher_token,
        consumer_token=consumer_token,
        operator_token=operator_token,
        admin_token=admin_token,
    )

    orig_load_config = getattr(eb_app, "load_config", None)
    del orig_load_config  # unused — needed for cleanup of original reference
    eb_app.load_config = lambda path=None: cfg

    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    eb_app._ENVELOPE_SCHEMA_PATH = schema_path
    eb_app.get_schema_path = lambda: schema_path

    local_app = FastAPI()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_local_state(local_app, cfg))
    finally:
        loop.close()

    attach_auth_middleware(local_app)

    @local_app.post("/publish")
    async def publish(
        request: Request,
        _principal: Principal = Depends(require_role(Role.PUBLISHER)),
    ) -> dict[str, Any]:
        result: dict[str, Any] = await eb_app.publish_route(
            request, _principal=_principal
        )
        return result

    @local_app.get("/subscribe")
    async def subscribe(
        request: Request,
        topic: list[str] = Query(default=[]),
        since_seq: int = Query(default=0, ge=0),
        consumer_id: str = Query(default=""),
        _principal: Principal = Depends(require_role(Role.CONSUMER)),
        _identity: dict[str, Any] = Depends(require_consumer_identity),
    ) -> Any:
        return await eb_app.subscribe_route(
            request,
            topic=topic,
            since_seq=since_seq,
            consumer_id=consumer_id,
            _principal=_principal,
            _identity=_identity,
        )

    @local_app.get("/dlq")
    async def dlq_list(
        request: Request,
        limit: int = Query(default=100, ge=1, le=1000),
        offset: int = Query(default=0, ge=0),
        _principal: Principal = Depends(require_role(Role.OPERATOR)),
    ) -> dict[str, Any]:
        result: dict[str, Any] = await eb_app.dlq_list_route(
            request, limit=limit, offset=offset, _principal=_principal
        )
        return result

    @local_app.post("/dlq/{event_id}/requeue")
    async def dlq_requeue(
        request: Request,
        event_id: str,
        _principal: Principal = Depends(require_role(Role.OPERATOR)),
    ) -> dict[str, Any]:
        result: dict[str, Any] = await eb_app.dlq_requeue_route(
            request, event_id, _principal=_principal
        )
        return result

    @local_app.get("/replay")
    async def replay(
        request: Request,
        since_seq: int = Query(default=0, ge=0),
        fmt: str = Query(default="sse", alias="format"),
        limit: int = Query(default=100, ge=1, le=1000),
        offset: int = Query(default=0, ge=0),
        _principal: Principal = Depends(require_role(Role.OPERATOR)),
    ) -> Any:
        return await eb_app.replay_route(
            request,
            since_seq=since_seq,
            fmt=fmt,
            limit=limit,
            offset=offset,
            _principal=_principal,
        )

    @local_app.post("/events/{event_id}/ack")
    async def ack_event(
        request: Request,
        event_id: str,
        consumer_id: str = Query(default=""),
        _principal: Principal = Depends(require_role(Role.CONSUMER)),
        _identity: dict[str, Any] = Depends(require_consumer_identity),
    ) -> dict[str, Any]:
        result: dict[str, Any] = await eb_app.ack_event_route(
            request,
            event_id=event_id,
            consumer_id=consumer_id,
            _principal=_principal,
            _identity=_identity,
        )
        return result

    @local_app.post("/nack")
    async def nack(
        request: Request,
        event_id: str = Query(default=""),
        _principal: Principal = Depends(require_role(Role.CONSUMER)),
        _identity: dict[str, Any] = Depends(require_consumer_identity),
    ) -> dict[str, Any]:
        result: dict[str, Any] = await eb_app.nack_route(
            request, event_id=event_id, _principal=_principal, _identity=_identity
        )
        return result

    client = TestClient(local_app, raise_server_exceptions=False)

    def _cleanup():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_do_cleanup_eb(local_app))
        finally:
            loop.close()

    client._cleanup = _cleanup  # type: ignore[attr-defined] — TestClient does not expose _cleanup as a public attribute; needed to clean up ASGI transport on teardown
    return local_app, cfg


async def _init_local_state(app: FastAPI, cfg: Any) -> None:
    """Initialize app.state for the given config."""
    import pathlib

    from eventbus import app as eb_app
    from eventbus.auth import _populate_token_maps

    app.state.config = cfg
    _populate_token_maps(cfg)
    app.state.db = eb_app.open_db(cfg.db_path)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    app.state.envelope_schema = eb_app.orjson.loads(schema_path.read_bytes())
    pathlib.Path(cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    app.state.broker = eb_app.EventBroker(cfg)


async def _do_cleanup_eb(app: FastAPI) -> None:
    """Clean up resources from this test's own local_app.state.

    Must operate on the local_app created by _make_test_app, not the
    eventbus.app module-level singleton — the singleton is a separate,
    shared app instance used by other test files' fixtures, and closing its
    db/broker here previously left it in a broken state for whichever test
    ran next.
    """
    dlq_task = getattr(app.state, "dlq_task", None)
    if dlq_task:
        dlq_task.cancel()
        try:
            await dlq_task
        except asyncio.CancelledError:
            pass
    if getattr(app.state, "broker", None):
        app.state.broker.shutdown()
    if getattr(app.state, "db", None):
        app.state.db.close()


class TestPublishAuth:
    """Tests for POST /publish authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-publish")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(
            cls.tmp_path,
            token="test-shared-token",
            publisher_token="test-publisher-token",
            consumer_token="test-consumer-token",
            operator_token=None,
            admin_token="test-admin-token",
        )
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    def test_publish_with_valid_publisher_token(self) -> None:
        """Authorized publisher can publish events."""
        import uuid
        from datetime import datetime

        body = {
            "event_id": str(uuid.uuid4()),
            "topic": "test",
            "payload": {"key": "value"},
            "producer": "test-producer",
            "published_at": datetime.now(UTC).isoformat(),
        }
        response = self.client.post(
            "/publish",
            json=body,
            headers={"Authorization": f"Bearer {self.cfg.publisher_token}"},
        )
        assert response.status_code == 200

    def test_publish_without_token(self) -> None:
        """Unauthenticated request to /publish is rejected."""
        import uuid
        from datetime import datetime

        body = {
            "event_id": str(uuid.uuid4()),
            "topic": "test",
            "payload": {"key": "value"},
            "producer": "test-producer",
            "published_at": datetime.now(UTC).isoformat(),
        }
        response = self.client.post("/publish", json=body)
        assert response.status_code == 401

    def test_publish_with_consumer_token_is_rejected(self) -> None:
        """AC-2: a consumer_token bearer is not authorized for /publish
        (Role.PUBLISHER-gated), even though the token is otherwise valid. Now
        HTTP-level (through this fixture's own `Depends(require_role(...))`
        declaration) — supersedes the earlier unit-level stopgap that called
        `_check_role` directly, which existed only because this fixture's
        routes previously declared no `Depends(...)` at all.
        """
        import uuid
        from datetime import datetime

        body = {
            "event_id": str(uuid.uuid4()),
            "topic": "test",
            "payload": {"key": "value"},
            "producer": "test-producer",
            "published_at": datetime.now(UTC).isoformat(),
        }
        response = self.client.post(
            "/publish",
            json=body,
            headers={"Authorization": f"Bearer {self.cfg.consumer_token}"},
        )
        assert response.status_code == 403


class TestSubscribeAuth:
    """Tests for GET /subscribe authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-subscribe")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(
            cls.tmp_path,
            token="test-shared-token",
            publisher_token="test-publisher-token",
            consumer_token="test-consumer-token",
            operator_token=None,
            admin_token=None,
        )
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    def test_subscribe_with_publisher_token_is_rejected(self) -> None:
        """AC-2: a publisher_token bearer is not authorized for /subscribe
        (Role.CONSUMER-gated)."""
        response = self.client.get(
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
            headers={"Authorization": f"Bearer {self.cfg.publisher_token}"},
        )
        assert response.status_code == 403

    def test_subscribe_with_valid_consumer_token(self) -> None:
        """Authorized consumer can subscribe to events."""
        with self.client.stream(
            "GET",
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
            headers={"Authorization": f"Bearer {self.cfg.consumer_token}"},
        ) as response:
            assert response.status_code == 200

    def test_subscribe_with_timeout_disconnect_detection(self) -> None:
        """Verify disconnect detection works under TestClient when no events arrive."""
        start_time = time.time()
        with self.client.stream(
            "GET",
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_b"},
            headers={"Authorization": f"Bearer {self.cfg.consumer_token}"},
        ) as response:
            assert response.status_code == 200
            data = b""
            for chunk in response.iter_bytes():
                data += chunk
                if b"\n\n" in data:
                    break

        elapsed = time.time() - start_time
        assert elapsed < 120, (
            f"Stream did not close within expected timeout: {elapsed}s"
        )

    def test_subscribe_without_token(self) -> None:
        """Unauthenticated request to /subscribe is rejected."""
        response = self.client.get(
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
        )
        assert response.status_code == 401

    def test_subscribe_as_wrong_role(self) -> None:
        """Non-consumer role cannot subscribe."""
        response = self.client.get(
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
            headers={"Authorization": "Bearer operator-token"},
        )
        assert response.status_code == 401


class TestAckAuth:
    """Tests for POST /events/{event_id}/ack authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-ack")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(
            cls.tmp_path,
            token="test-shared-token",
            publisher_token="test-publisher-token",
            consumer_token=None,
            operator_token=None,
            admin_token="test-admin-token",
        )
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    def test_ack_without_token(self) -> None:
        """Unauthenticated request to /ack is rejected."""
        response = self.client.post(
            "/events/test-event-id/ack", params={"consumer_id": "consumer_a"}
        )
        assert response.status_code == 401

    def test_ack_with_publisher_token_is_rejected(self) -> None:
        """AC-2: a publisher_token bearer is not authorized for
        /events/{event_id}/ack (Role.CONSUMER-gated)."""
        response = self.client.post(
            "/events/test-event-id/ack",
            params={"consumer_id": "consumer_a"},
            headers={"Authorization": f"Bearer {self.cfg.publisher_token}"},
        )
        assert response.status_code == 403


class TestNackAuth:
    """Tests for POST /nack authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-nack")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(
            cls.tmp_path,
            token="test-shared-token",
            publisher_token="test-publisher-token",
            consumer_token=None,
            operator_token=None,
            admin_token="test-admin-token",
        )
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    def test_nack_without_token(self) -> None:
        """Unauthenticated request to /nack is rejected."""
        response = self.client.post("/nack", params={"event_id": "test-event-id"})
        assert response.status_code == 401

    def test_nack_with_publisher_token_is_rejected(self) -> None:
        """AC-2: a publisher_token bearer is not authorized for /nack
        (Role.CONSUMER-gated)."""
        response = self.client.post(
            "/nack",
            params={"event_id": "test-event-id"},
            headers={"Authorization": f"Bearer {self.cfg.publisher_token}"},
        )
        assert response.status_code == 403


class TestDlqListAuth:
    """Tests for GET /dlq authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-dlq-list")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(
            cls.tmp_path,
            token="test-shared-token",
            publisher_token="test-publisher-token",
            consumer_token=None,
            operator_token="test-operator-token",
            admin_token=None,
        )
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    def test_dlq_list_with_publisher_token_is_rejected(self) -> None:
        """AC-2: a publisher_token bearer is not authorized for /dlq
        (Role.OPERATOR-gated)."""
        response = self.client.get(
            "/dlq",
            headers={"Authorization": f"Bearer {self.cfg.publisher_token}"},
        )
        assert response.status_code == 403

    def test_dlq_list_with_valid_operator_token(self) -> None:
        """Authorized operator can list DLQ entries."""
        response = self.client.get(
            "/dlq",
            headers={"Authorization": f"Bearer {self.cfg.operator_token}"},
        )
        assert response.status_code == 200

    def test_dlq_list_without_token(self) -> None:
        """Unauthenticated request to /dlq is rejected."""
        response = self.client.get("/dlq")
        assert response.status_code == 401


class TestDlqRequeueAuth:
    """Tests for POST /dlq/{event_id}/requeue authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-dlq-requeue")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(
            cls.tmp_path,
            token="test-shared-token",
            publisher_token="test-publisher-token",
            consumer_token=None,
            operator_token=None,
            admin_token="test-admin-token",
        )
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    def test_dlq_requeue_without_token(self) -> None:
        """Unauthenticated request to /dlq/requeue is rejected."""
        response = self.client.post("/dlq/test-event-id/requeue")
        assert response.status_code == 401

    def test_dlq_requeue_with_publisher_token_is_rejected(self) -> None:
        """AC-2: a publisher_token bearer is not authorized for
        /dlq/{event_id}/requeue (Role.OPERATOR-gated)."""
        response = self.client.post(
            "/dlq/test-event-id/requeue",
            headers={"Authorization": f"Bearer {self.cfg.publisher_token}"},
        )
        assert response.status_code == 403


class TestReplayAuth:
    """Tests for GET /replay authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-replay")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(
            cls.tmp_path,
            token="test-shared-token",
            publisher_token="test-publisher-token",
            consumer_token=None,
            operator_token="test-operator-token",
            admin_token=None,
        )
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    def test_replay_with_publisher_token_is_rejected(self) -> None:
        """AC-2: a publisher_token bearer is not authorized for /replay
        (Role.OPERATOR-gated)."""
        response = self.client.get(
            "/replay",
            params={"since_seq": 0, "limit": 100},
            headers={"Authorization": f"Bearer {self.cfg.publisher_token}"},
        )
        assert response.status_code == 403

    def test_replay_with_valid_operator_token(self) -> None:
        """Authorized operator can replay events."""
        response = self.client.get(
            "/replay",
            params={"since_seq": 0, "limit": 100},
            headers={"Authorization": f"Bearer {self.cfg.operator_token}"},
        )
        assert response.status_code == 200

    def test_replay_without_token(self) -> None:
        """Unauthenticated request to /replay is rejected."""
        response = self.client.get("/replay", params={"since_seq": 0, "limit": 100})
        assert response.status_code == 401


class TestRequireConsumerIdentityTopicSemantics:
    """Unit-level tests for require_consumer_identity's 'topics' return contract.

    See implementations/done/20260913-152721_01_scripts_eventbus_auth.py.md: a
    token with no configured topic restriction must return `"topics": None`
    (unrestricted), distinct from a genuinely non-empty allowlist.
    """

    @pytest.mark.asyncio
    async def test_no_topic_restriction_returns_none(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import (
            Principal,
            Role,
            require_consumer_identity,
        )

        principal = Principal(
            roles=frozenset([Role.CONSUMER]),
            allowed_consumer_ids=frozenset(),
            allowed_topics=None,
            token_fingerprint="test-fingerprint",
        )
        try:
            result = await require_consumer_identity(
                MagicMock(), consumer_id="", topics=["any-topic"], principal=principal
            )
            assert result["topics"] is None
        finally:
            pass

    @pytest.mark.asyncio
    async def test_non_empty_topic_restriction_is_enforced_and_returned(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import Principal, Role, require_consumer_identity

        principal_with_topics = Principal(
            roles=frozenset([Role.CONSUMER]),
            allowed_consumer_ids=frozenset(),
            allowed_topics=frozenset({"allowed-topic"}),
            token_fingerprint="test-fingerprint",
        )
        try:
            result = await require_consumer_identity(
                MagicMock(),
                consumer_id="",
                topics=["allowed-topic"],
                principal=principal_with_topics,
            )
            assert result["topics"] == frozenset({"allowed-topic"})

            with pytest.raises(HTTPException) as exc_info:
                await require_consumer_identity(
                    MagicMock(),
                    consumer_id="",
                    topics=["disallowed-topic"],
                    principal=principal_with_topics,
                )
            assert exc_info.value.status_code == 403
        finally:
            pass


class TestPrincipalFieldValidation:
    """Unit-level tests for Principal field resolution from tokens."""

    @pytest.mark.asyncio
    async def test_publisher_token_grants_only_publisher_role(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import _TOKEN_ROLE_MAP, Principal, Role, resolve_principal

        token = "publisher-token"
        _TOKEN_ROLE_MAP[token] = {Role.PUBLISHER}
        try:
            principal = await resolve_principal(
                MagicMock(),
                credentials=MagicMock(credentials=token),
            )
            assert isinstance(principal, Principal)
            assert principal.roles == frozenset([Role.PUBLISHER])
            assert principal.allowed_consumer_ids == frozenset()
            assert principal.allowed_topics is None
        finally:
            _TOKEN_ROLE_MAP.pop(token, None)

    @pytest.mark.asyncio
    async def test_admin_token_grants_all_roles(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import _TOKEN_ROLE_MAP, Principal, Role, resolve_principal

        token = "admin-token"
        _TOKEN_ROLE_MAP[token] = set(Role)
        try:
            principal = await resolve_principal(
                MagicMock(),
                credentials=MagicMock(credentials=token),
            )
            assert isinstance(principal, Principal)
            assert principal.roles == frozenset(Role)
            assert principal.allowed_consumer_ids == frozenset()
            assert principal.allowed_topics is None
        finally:
            _TOKEN_ROLE_MAP.pop(token, None)

    @pytest.mark.asyncio
    async def test_shared_token_grants_all_roles_for_backward_compat(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import _TOKEN_ROLE_MAP, Principal, Role, resolve_principal

        token = "shared-token"
        _TOKEN_ROLE_MAP[token] = set(Role)
        try:
            principal = await resolve_principal(
                MagicMock(),
                credentials=MagicMock(credentials=token),
            )
            assert isinstance(principal, Principal)
            assert principal.roles == frozenset(Role)
            # Shared token has empty allowed_consumer_ids (any consumer_id)
            assert principal.allowed_consumer_ids == frozenset()
            # Shared token has no topic restriction
            assert principal.allowed_topics is None
        finally:
            _TOKEN_ROLE_MAP.pop(token, None)

    @pytest.mark.asyncio
    async def test_per_role_token_has_no_consumer_restriction(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import (
            _TOKEN_CONSUMER_MAP,
            _TOKEN_ROLE_MAP,
            Principal,
            Role,
            resolve_principal,
        )

        token = "consumer-token"
        _TOKEN_ROLE_MAP[token] = {Role.CONSUMER}
        _TOKEN_CONSUMER_MAP[token] = set()  # Empty means any consumer_id
        try:
            principal = await resolve_principal(
                MagicMock(),
                credentials=MagicMock(credentials=token),
            )
            assert isinstance(principal, Principal)
            assert principal.roles == frozenset([Role.CONSUMER])
            assert principal.allowed_consumer_ids == frozenset()
        finally:
            _TOKEN_ROLE_MAP.pop(token, None)
            _TOKEN_CONSUMER_MAP.pop(token, None)


class TestAuditRecordValidation:
    """Tests for structured audit record emission on auth failures."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-audit")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(
            cls.tmp_path,
            token="test-shared-token",
            publisher_token="test-publisher-token",
            consumer_token="test-consumer-token",
            operator_token=None,
            admin_token="test-admin-token",
        )
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    def test_auth_failure_401_produces_structured_audit_record(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """T-1: Auth failure (401) produces structured audit record with request_id, route, target."""
        from unittest.mock import patch

        captured_records: list[str] = []

        def capture_log(record: str) -> None:
            captured_records.append(record)

        with patch("scripts.eventbus.audit.logger.warning", side_effect=capture_log):
            response = self.client.get(
                "/subscribe",
                params={"topic": "test", "consumer_id": "consumer_a"},
                headers={"Authorization": "Bearer invalid-token"},
            )
            assert response.status_code == 401

        assert len(captured_records) > 0

        import json

        audit_record = json.loads(captured_records[0])

        assert "request_id" in audit_record
        assert "route" in audit_record
        assert "target" in audit_record
        assert "outcome" in audit_record
        assert "error_type" in audit_record

        assert audit_record["error_type"] == "authentication_failed"
        assert audit_record["outcome"] == "rejected"

        assert "invalid-token" not in str(audit_record)

    def test_auth_failure_403_produces_structured_audit_record(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """T-2: Auth failure (403) produces structured audit record with role mismatch details."""
        from unittest.mock import patch

        captured_records: list[str] = []

        def capture_log(record: str) -> None:
            captured_records.append(record)

        with patch("scripts.eventbus.audit.logger.warning", side_effect=capture_log):
            response = self.client.post(
                "/events/test-event-id/ack",
                params={"consumer_id": "consumer_a"},
                headers={"Authorization": f"Bearer {self.cfg.publisher_token}"},
            )
            assert response.status_code == 403

        assert len(captured_records) > 0

        import json

        audit_record = json.loads(captured_records[0])

        assert "request_id" in audit_record
        assert "route" in audit_record
        assert "target" in audit_record
        assert "outcome" in audit_record
        assert "error_type" in audit_record

        assert audit_record["error_type"] == "authorization_failed"
        assert audit_record["outcome"] == "rejected"

        assert "publisher-token" not in str(audit_record)

    def test_consumer_identity_rejection_produces_structured_audit_record(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """T-3: Consumer identity rejection (403) produces structured audit record with consumer_id."""
        from unittest.mock import patch

        captured_records: list[str] = []

        def capture_log(record: str) -> None:
            captured_records.append(record)

        with patch("scripts.eventbus.audit.logger.warning", side_effect=capture_log):
            response = self.client.get(
                "/subscribe",
                params={"topic": "test", "consumer_id": "unauthorized-consumer"},
                headers={"Authorization": f"Bearer {self.cfg.consumer_token}"},
            )
            assert response.status_code == 403

        assert len(captured_records) > 0

        import json

        audit_record = json.loads(captured_records[0])

        assert "request_id" in audit_record
        assert "route" in audit_record
        assert "target" in audit_record
        assert "outcome" in audit_record
        assert "error_type" in audit_record

        assert audit_record["error_type"] == "consumer_identity_rejected"
        assert audit_record["outcome"] == "rejected"

        assert "consumer-token" not in str(audit_record)

    def test_topic_authorization_rejection_produces_structured_audit_record(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """T-4: Topic authorization rejection (403) produces structured audit record with topic."""
        from unittest.mock import patch

        captured_records: list[str] = []

        def capture_log(record: str) -> None:
            captured_records.append(record)

        with patch("scripts.eventbus.audit.logger.warning", side_effect=capture_log):
            response = self.client.get(
                "/subscribe",
                params={"topic": "disallowed-topic", "consumer_id": "consumer_a"},
                headers={"Authorization": f"Bearer {self.cfg.consumer_token}"},
            )
            assert response.status_code == 403

        assert len(captured_records) > 0

        import json

        audit_record = json.loads(captured_records[0])

        assert "request_id" in audit_record
        assert "route" in audit_record
        assert "target" in audit_record
        assert "outcome" in audit_record
        assert "error_type" in audit_record

        assert audit_record["error_type"] == "topic_authorization_rejected"
        assert audit_record["outcome"] == "rejected"

        assert "consumer-token" not in str(audit_record)

    def test_no_credential_leakage_in_audit_records(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """T-7: No raw tokens/credentials in any audit record."""
        from unittest.mock import patch

        captured_records: list[str] = []

        def capture_log(record: str) -> None:
            captured_records.append(record)

        scenarios = [
            ("Bearer invalid-token", 401),
            (f"Bearer {self.cfg.publisher_token}", 403),
        ]

        for header_value, expected_status in scenarios:
            captured_records.clear()

            with patch(
                "scripts.eventbus.audit.logger.warning", side_effect=capture_log
            ):
                if expected_status == 401:
                    response = self.client.get(
                        "/subscribe",
                        params={"topic": "test", "consumer_id": "consumer_a"},
                        headers={"Authorization": header_value},
                    )
                else:
                    response = self.client.post(
                        "/events/test-event-id/ack",
                        params={"consumer_id": "consumer_a"},
                        headers={"Authorization": header_value},
                    )
                assert response.status_code == expected_status

            import json

            for record in captured_records:
                audit_record = json.loads(record)

                assert "invalid-token" not in str(audit_record)
                assert "publisher-token" not in str(audit_record)
                assert "consumer-token" not in str(audit_record)
                assert "operator-token" not in str(audit_record)
                assert "admin-token" not in str(audit_record)


class TestUnified401ResponseFormat:
    """Tests for the unified HTTP 401 response format."""

    def test_missing_authorization_header_returns_unified_format(self) -> None:
        """REQ-009, REQ-010: Missing Authorization header returns standardized 401 response."""
        app, cfg = _make_test_app(
            Path("/tmp/test-unified-401"),
            token="test-shared-token",
            publisher_token=None,
            consumer_token=None,
            operator_token=None,
            admin_token=None,
        )
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/health")
        assert response.status_code == 401

        body = response.json()
        assert body["error"] == "Unauthorized"
        assert "detail" in body
        assert isinstance(body["detail"], str)
        assert len(body["detail"]) > 0

        # WWW-Authenticate header must be present
        assert "www-authenticate" in response.headers
        assert 'Bearer realm="eventbus"' in response.headers["www-authenticate"]

    def test_invalid_bearer_token_returns_unified_format(self) -> None:
        """REQ-009, REQ-010: Invalid Bearer token returns standardized 401 response."""
        app, cfg = _make_test_app(
            Path("/tmp/test-unified-401-invalid"),
            token="test-shared-token",
            publisher_token=None,
            consumer_token=None,
            operator_token=None,
            admin_token=None,
        )
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get(
            "/health",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

        body = response.json()
        assert body["error"] == "Unauthorized"
        assert "detail" in body
        assert isinstance(body["detail"], str)
        assert len(body["detail"]) > 0

        # WWW-Authenticate header must be present
        assert "www-authenticate" in response.headers
        assert 'Bearer realm="eventbus"' in response.headers["www-authenticate"]

    def test_no_double_authentication_processing(self) -> None:
        """REQ-008: Authentication failures are not processed twice."""
        app, cfg = _make_test_app(
            Path("/tmp/test-no-double-auth"),
            token="test-shared-token",
            publisher_token=None,
            consumer_token=None,
            operator_token=None,
            admin_token=None,
        )
        client = TestClient(app, raise_server_exceptions=False)

        # Make a request without authentication
        response = client.get("/health")
        assert response.status_code == 401

        # The response should come from ONE source only (middleware or handler),
        # not both. If it were processed twice, we might see duplicate error fields
        # or inconsistent behavior.
        body = response.json()
        assert body["error"] == "Unauthorized"
        # Only one "error" field — no duplication
        assert set(body.keys()) == {"error", "detail"}
