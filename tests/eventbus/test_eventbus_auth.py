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
from unittest.mock import MagicMock

import pytest
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
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
        _TOKEN_PRINCIPAL_MAP,
        Principal,
        Role,
        attach_auth_middleware,
        require_consumer_identity,
        require_role,
        resolve_principal,
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
        # Fail-closed (ADR-013 INV-02): consumer_token requires a non-None
        # consumer_authorization. The per-fixture Principal override below
        # (lines ~94-102) governs the actual consumer_id/topic restriction; this
        # value only satisfies the startup fail-closed check and mirrors that
        # override's consumer ids.
        consumer_authorization={"consumer_a": ["test"]},
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

    # _populate_token_maps() (run inside _init_local_state) leaves every token
    # unrestricted (allowed_consumer_ids and allowed_topics are None). The
    # identity/topic rejection tests in this module (TestSubscribeAuth,
    # TestAuditRecordValidation) exercise require_consumer_identity and therefore
    # need the consumer-token to carry a concrete allowlist; mirror the
    # per-fixture overrides used by the other eventbus test modules. Restrict to
    # the consumer IDs/topics these tests legitimately use so unauthorized
    # consumers and disallowed topics still reject while valid subscribers pass.
    _ct = getattr(cfg, "consumer_token", None)
    if _ct and _ct in _TOKEN_PRINCIPAL_MAP:
        _existing = _TOKEN_PRINCIPAL_MAP[_ct]
        _TOKEN_PRINCIPAL_MAP[_ct] = Principal(
            roles=_existing.roles,
            allowed_consumer_ids=frozenset({"consumer_a", "consumer_b"}),
            allowed_topics=frozenset({"test"}),
            token_fingerprint=_existing.token_fingerprint,
        )

    attach_auth_middleware(local_app)

    async def resolve_subscribe_identity(
        request: Request,
        consumer_id: str = Query(default=""),
        topic: list[str] = Query(default=[]),
        principal: Principal = Depends(resolve_principal),
    ) -> Principal:
        # require_consumer_identity enforces the caller's allowed_consumer_ids
        # and allowed_topics; passing the real consumer_id and topic (rather than
        # empty defaults) is what makes those allowlists take effect. principal is
        # resolved here (not left as an unresolved Depends marker) so the direct
        # call below does not raise.
        return await require_consumer_identity(
            request, consumer_id=consumer_id, topics=topic, principal=principal
        )

    @local_app.get("/health")
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse(content={"status": "ok"}, status_code=200)

    @local_app.post("/publish")
    async def publish(
        request: Request,
        _principal: Principal = Depends(require_role(Role.PUBLISHER)),
    ) -> dict[str, Any]:
        result: dict[str, Any] = await eb_app.publish_route(request)
        return result

    @local_app.get("/subscribe")
    async def subscribe(
        request: Request,
        topic: list[str] = Query(default=[]),
        since_seq: int = Query(default=0, ge=0),
        consumer_id: str = Query(default=""),
        _principal: Principal = Depends(require_role(Role.CONSUMER)),
        _identity: Principal = Depends(resolve_subscribe_identity),
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
            request, limit=limit, offset=offset
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
        )

    @local_app.post("/events/{event_id}/ack")
    async def ack_event(
        request: Request,
        event_id: str,
        consumer_id: str = Query(default=""),
        _principal: Principal = Depends(require_role(Role.CONSUMER)),
        _identity: Principal = Depends(require_consumer_identity),
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
        _identity: Principal = Depends(require_consumer_identity),
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
    pathlib.Path(cfg.db_path).parent.mkdir(parents=True, exist_ok=True)
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
        # The subscribe stream under TestClient only ends when the server's idle
        # timeout fires; use the validated minimum so these tests do not wait for
        # the 60-second default. Assigned after construction because the
        # cross-field check against sse_heartbeat_interval runs only there.
        object.__setattr__(cls.cfg, "sse_idle_timeout", 1.0)
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
        assert elapsed < 10, f"Stream did not close within expected timeout: {elapsed}s"

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
            assert result.allowed_topics is None
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
        request_mock = MagicMock()
        request_mock.state.request_id = "test-request-id"
        request_mock.url.path = "/subscribe"
        try:
            result = await require_consumer_identity(
                request_mock,
                consumer_id="",
                topics=["allowed-topic"],
                principal=principal_with_topics,
            )
            assert result.allowed_topics == frozenset({"allowed-topic"})

            with pytest.raises(HTTPException) as exc_info:
                await require_consumer_identity(
                    request_mock,
                    consumer_id="",
                    topics=["disallowed-topic"],
                    principal=principal_with_topics,
                )
            assert exc_info.value.status_code == 403
        finally:
            pass


class TestPrincipalFieldValidation:
    """Unit-level tests for Principal field resolution from tokens."""

    @staticmethod
    def _make_request_mock(auth_token: str = "test-token") -> MagicMock:
        mock = MagicMock()
        mock.app.state.config.auth_token = auth_token
        return mock

    @pytest.mark.asyncio
    async def test_publisher_token_grants_only_publisher_role(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import (
            _TOKEN_PRINCIPAL_MAP,
            Principal,
            Role,
            resolve_principal,
        )

        token = "publisher-token"
        _TOKEN_PRINCIPAL_MAP[token] = Principal(
            roles=frozenset({Role.PUBLISHER}),
            allowed_consumer_ids=None,
            allowed_topics=None,
            token_fingerprint="test-fingerprint",
        )
        try:
            principal = await resolve_principal(
                self._make_request_mock(),
                credentials=MagicMock(credentials=token),
            )
            assert isinstance(principal, Principal)
            assert principal.roles == frozenset([Role.PUBLISHER])
            assert principal.allowed_consumer_ids is None
            assert principal.allowed_topics is None
        finally:
            _TOKEN_PRINCIPAL_MAP.pop(token, None)

    @pytest.mark.asyncio
    async def test_admin_token_grants_all_roles(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import (
            _TOKEN_PRINCIPAL_MAP,
            Principal,
            Role,
            resolve_principal,
        )

        token = "admin-token"
        _TOKEN_PRINCIPAL_MAP[token] = Principal(
            roles=frozenset(Role),
            allowed_consumer_ids=None,
            allowed_topics=None,
            token_fingerprint="test-fingerprint",
        )
        try:
            principal = await resolve_principal(
                self._make_request_mock(),
                credentials=MagicMock(credentials=token),
            )
            assert isinstance(principal, Principal)
            assert principal.roles == frozenset(Role)
            assert principal.allowed_consumer_ids is None
            assert principal.allowed_topics is None
        finally:
            _TOKEN_PRINCIPAL_MAP.pop(token, None)

    @pytest.mark.asyncio
    async def test_shared_token_grants_all_roles_for_backward_compat(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import (
            _TOKEN_PRINCIPAL_MAP,
            Principal,
            Role,
            resolve_principal,
        )

        token = "shared-token"
        _TOKEN_PRINCIPAL_MAP[token] = Principal(
            roles=frozenset(Role),
            allowed_consumer_ids=None,
            allowed_topics=None,
            token_fingerprint="test-fingerprint",
        )
        try:
            principal = await resolve_principal(
                self._make_request_mock(),
                credentials=MagicMock(credentials=token),
            )
            assert isinstance(principal, Principal)
            assert principal.roles == frozenset(Role)
            # Shared token has None allowed_consumer_ids (any consumer_id)
            assert principal.allowed_consumer_ids is None
            # Shared token has no topic restriction
            assert principal.allowed_topics is None
        finally:
            _TOKEN_PRINCIPAL_MAP.pop(token, None)

    @pytest.mark.asyncio
    async def test_per_role_token_has_no_consumer_restriction(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import (
            _TOKEN_PRINCIPAL_MAP,
            Principal,
            Role,
            resolve_principal,
        )

        token = "consumer-token"
        _TOKEN_PRINCIPAL_MAP[token] = Principal(
            roles=frozenset({Role.CONSUMER}),
            allowed_consumer_ids=None,
            allowed_topics=None,
            token_fingerprint="test-fingerprint",
        )
        try:
            principal = await resolve_principal(
                self._make_request_mock(),
                credentials=MagicMock(credentials=token),
            )
            assert isinstance(principal, Principal)
            assert principal.roles == frozenset([Role.CONSUMER])
            assert principal.allowed_consumer_ids is None
        finally:
            _TOKEN_PRINCIPAL_MAP.pop(token, None)


class TestFailClosedConsumerAuthorization:
    """Regression (EVENTBUS-008 / ADR-013 INV-02): a consumer_token declared
    without an explicit consumer_authorization MUST fail closed (raise
    ValueError) at startup. An empty mapping {} is accepted and leaves the consumer
    token unrestricted; only None is rejected — never weaken this guarantee."""

    @staticmethod
    def test_consumer_token_without_consumer_authorization_raises() -> None:
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP, _populate_token_maps
        from eventbus.config import EventBusConfig

        snapshot = dict(_TOKEN_PRINCIPAL_MAP)
        try:
            cfg = EventBusConfig(
                port=8091,
                db_path="/tmp/test-eventbus-failclosed.sqlite",
                storage_dir="/tmp/test-eventbus-failclosed",
                offsets_dir="/tmp/test-eventbus-failclosed",
                deadletter_dir="/tmp/test-eventbus-failclosed",
                max_retry=2,
                host="127.0.0.1",
                auth_token="shared-token",
                consumer_token="consumer-token",
                # consumer_authorization intentionally omitted (defaults to None)
            )
            with pytest.raises(ValueError, match="consumer_authorization is missing"):
                _populate_token_maps(cfg)
        finally:
            _TOKEN_PRINCIPAL_MAP.clear()
            _TOKEN_PRINCIPAL_MAP.update(snapshot)


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

        with patch("eventbus.audit.logger.warning", side_effect=capture_log):
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

        with patch("eventbus.audit.logger.warning", side_effect=capture_log):
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

        with patch("eventbus.audit.logger.warning", side_effect=capture_log):
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

        with patch("eventbus.audit.logger.warning", side_effect=capture_log):
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

            with patch("eventbus.audit.logger.warning", side_effect=capture_log):
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

        response = client.post(
            "/publish",
            json={
                "event_id": "test-event-id",
                "topic": "test.topic",
                "payload": {"x": 1},
                "producer": "test-producer",
                "published_at": "2026-06-22T12:00:00Z",
            },
        )
        assert response.status_code == 401

        body = response.json()
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

        response = client.post(
            "/publish",
            json={
                "event_id": "test-event-id",
                "topic": "test.topic",
                "payload": {"x": 1},
                "producer": "test-producer",
                "published_at": "2026-06-22T12:00:00Z",
            },
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

        body = response.json()
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
        response = client.post(
            "/publish",
            json={
                "event_id": "test-event-id",
                "topic": "test.topic",
                "payload": {"x": 1},
                "producer": "test-producer",
                "published_at": "2026-06-22T12:00:00Z",
            },
        )
        assert response.status_code == 401

        # The response should come from ONE source only (middleware or handler),
        # not both. If it were processed twice, we might see duplicate error fields
        # or inconsistent behavior.
        body = response.json()
        assert "detail" in body
        # Only one "detail" field — no duplication
        assert set(body.keys()) == {"detail"}


def _has_role_dependency(dependant: Any) -> bool:
    """Return True if any dependency in the tree is a require_role() check."""
    for sub in dependant.dependencies:
        qualname = getattr(sub.call, "__qualname__", "")
        if "require_role" in qualname or _has_role_dependency(sub):
            return True
    return False


class TestProductionRouteWiring:
    """Role enforcement through the production app object.

    The other classes in this module build their own fixture app and attach the
    role dependencies themselves, so they cannot detect a production route that
    was registered without one (EVENTBUS-016). These tests use the production
    app, so a missing dependency fails here.
    """

    @pytest.fixture
    def prod_client(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
        import dataclasses

        from eventbus import app as eb_app
        from eventbus.auth import _populate_token_maps
        from eventbus_helpers import make_eventbus_client

        with make_eventbus_client(tmp_path, monkeypatch) as client:
            cfg = dataclasses.replace(
                eb_app.app.state.config,
                publisher_token="prod-publisher-token",
                consumer_token="prod-consumer-token",
                # Fail-closed (ADR-013 INV-02): consumer_token requires a
                # non-None consumer_authorization. These tests gate on ROLE only,
                # so {} (unrestricted consumer) preserves their semantics.
                consumer_authorization={},
                monitoring_token="prod-monitoring-token",
            )
            eb_app.app.state.config = cfg
            _populate_token_maps(cfg)
            yield client

    @staticmethod
    def _event() -> dict[str, Any]:
        import uuid

        return {
            "event_id": str(uuid.uuid4()),
            "topic": "test.topic",
            "payload": {"key": "value"},
            "producer": "test-producer",
            "published_at": "2026-06-22T11:56:00Z",
        }

    def _call(self, client: Any, method: str, path: str, token: str | None) -> Any:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        client.headers.pop("Authorization", None)
        if method == "GET":
            return client.get(path, headers=headers)
        return client.post(path, json=self._event(), headers=headers)

    def test_every_production_api_route_has_a_role_dependency(self) -> None:
        from eventbus import app as eb_app
        from fastapi.routing import APIRoute

        unprotected = [
            route.path
            for route in eb_app.app.routes
            if isinstance(route, APIRoute) and not _has_role_dependency(route.dependant)
        ]
        assert unprotected == []

    @pytest.mark.parametrize(
        ("method", "path", "right_token", "wrong_token"),
        [
            ("GET", "/health", "prod-monitoring-token", "prod-consumer-token"),
            ("POST", "/publish", "prod-publisher-token", "prod-consumer-token"),
        ],
    )
    def test_route_enforces_role_through_production_app(
        self,
        prod_client: Any,
        method: str,
        path: str,
        right_token: str,
        wrong_token: str,
    ) -> None:
        assert self._call(prod_client, method, path, None).status_code == 401
        assert self._call(prod_client, method, path, "unknown").status_code == 401
        assert self._call(prod_client, method, path, wrong_token).status_code == 403
        assert self._call(prod_client, method, path, right_token).status_code == 200
        assert self._call(prod_client, method, path, "test-token").status_code == 200
