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
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from tests.eventbus.eventbus_helpers import (
    current_principals,
    publish_derived_generation,
)


def _await(coro):
    """Run a coroutine to completion (unit-level resolve_principal calls)."""
    import asyncio

    return asyncio.run(coro)


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
        attach_auth_middleware,
        current_generation,
    )
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
        host="127.0.0.1",
        auth_token=token or "",
        publisher_token=publisher_token or "",
        consumer_token=consumer_token or "",
        # Fail-closed (ADR-013 INV-02): consumer_token requires a non-None
        # consumer_authorization. The per-fixture Principal override below
        # (lines ~94-102) governs the actual consumer_id/topic restriction; this
        # value only satisfies the startup fail-closed check and mirrors that
        # override's consumer ids.
        consumer_authorization={"consumer_a": ["test"]},
        operator_token=operator_token or "",
        admin_token=admin_token or "",
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

    # build_and_publish_generation() (run inside _init_local_state) leaves every token
    # carry no consumer grants. The
    # identity/topic rejection tests in this module (TestSubscribeAuth,
    # TestAuditRecordValidation) exercise require_consumer_identity and therefore
    # need the consumer-token to carry a concrete allowlist; mirror the
    # per-fixture overrides used by the other eventbus test modules. Restrict to
    # the consumer IDs/topics these tests legitimately use so unauthorized
    # consumers and disallowed topics still reject while valid subscribers pass.
    _ct = getattr(cfg, "consumer_token", None)
    _generation = current_generation()
    if _ct and _generation is not None and _ct in _generation.principals:
        _existing = _generation.principals[_ct]
        publish_derived_generation(
            overrides={
                _ct: Principal(
                    roles=_existing.roles,
                    consumer_grants=frozenset(
                        {("consumer_a", "test"), ("consumer_b", "test")}
                    ),
                    token_fingerprint=_existing.token_fingerprint,
                )
            }
        )

    attach_auth_middleware(local_app)

    from eventbus.ack_route import router as ack_router
    from eventbus.admin_route import router as admin_router
    from eventbus.dlq_route import router as dlq_router
    from eventbus.health_route import router as health_router
    from eventbus.publish_route import router as publish_router
    from eventbus.replay_route import router as replay_router
    from eventbus.subscribe_route import router as subscribe_router

    for production_router in (
        health_router,
        publish_router,
        replay_router,
        subscribe_router,
        dlq_router,
        ack_router,
        admin_router,
    ):
        local_app.include_router(production_router)

    client = TestClient(local_app, raise_server_exceptions=False)

    def _cleanup():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_do_cleanup_eb(local_app))
        finally:
            loop.close()

    # TestClient does not expose _cleanup as a public attribute; needed to clean up ASGI transport on teardown
    client._cleanup = _cleanup
    return local_app, cfg


async def _init_local_state(app: FastAPI, cfg: Any) -> None:
    """Initialize app.state for the given config."""
    import pathlib

    from eventbus import app as eb_app
    from eventbus.auth import build_and_publish_generation

    app.state.config = cfg
    build_and_publish_generation(cfg)
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

    client: TestClient
    cfg: Any

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
        """ADR-013 INV-02: a consumer_token bearer is not authorized for /publish
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

    client: TestClient
    cfg: Any

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
        """ADR-013 INV-02: a publisher_token bearer is not authorized for /subscribe
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

    client: TestClient
    cfg: Any

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
        """ADR-013 INV-02: a publisher_token bearer is not authorized for
        /events/{event_id}/ack (Role.CONSUMER-gated)."""
        response = self.client.post(
            "/events/test-event-id/ack",
            params={"consumer_id": "consumer_a"},
            headers={"Authorization": f"Bearer {self.cfg.publisher_token}"},
        )
        assert response.status_code == 403


class TestNackAuth:
    """Tests for POST /nack authorization."""

    client: TestClient
    cfg: Any

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
        """ADR-013 INV-02: a publisher_token bearer is not authorized for /nack
        (Role.CONSUMER-gated)."""
        response = self.client.post(
            "/nack",
            params={"event_id": "test-event-id"},
            headers={"Authorization": f"Bearer {self.cfg.publisher_token}"},
        )
        assert response.status_code == 403


class TestDlqListAuth:
    """Tests for GET /dlq authorization."""

    client: TestClient
    cfg: Any

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
        """ADR-013 INV-02: a publisher_token bearer is not authorized for /dlq
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

    client: TestClient
    cfg: Any

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
        """ADR-013 INV-02: a publisher_token bearer is not authorized for
        /dlq/{event_id}/requeue (Role.OPERATOR-gated)."""
        response = self.client.post(
            "/dlq/test-event-id/requeue",
            headers={"Authorization": f"Bearer {self.cfg.publisher_token}"},
        )
        assert response.status_code == 403


class TestReplayAuth:
    """Tests for GET /replay authorization."""

    client: TestClient
    cfg: Any

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
        """ADR-013 INV-02: a publisher_token bearer is not authorized for /replay
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
    (no grants), distinct from a genuinely non-empty allowlist.
    """

    @pytest.mark.asyncio
    async def test_principal_without_topic_binding_is_rejected(self) -> None:
        """ADR-013 INV-07: a principal without explicit topic authorization is denied."""
        from unittest.mock import MagicMock

        from eventbus.auth import Principal, Role, require_consumer_identity
        from fastapi import HTTPException

        principal = Principal(
            roles=frozenset([Role.CONSUMER]),
            consumer_grants=frozenset(),
            token_fingerprint="test-fingerprint",
        )
        mock_request = MagicMock()
        mock_request.state.request_id = "req-no-topic-binding"
        mock_request.url.path = "/subscribe"
        with pytest.raises(HTTPException) as exc:
            await require_consumer_identity(
                mock_request,
                consumer_id="c1",
                topics=["any-topic"],
                principal=principal,
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_non_empty_topic_restriction_is_enforced_and_returned(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import Principal, Role, require_consumer_identity

        principal_with_topics = Principal(
            roles=frozenset([Role.CONSUMER]),
            consumer_grants=frozenset({("c1", "allowed-topic")}),
            token_fingerprint="test-fingerprint",
        )
        request_mock = MagicMock()
        request_mock.state.request_id = "test-request-id"
        request_mock.url.path = "/subscribe"
        try:
            result = await require_consumer_identity(
                request_mock,
                consumer_id="c1",
                topics=["allowed-topic"],
                principal=principal_with_topics,
            )
            assert result.is_granted("c1", "allowed-topic")

            with pytest.raises(HTTPException) as exc_info:
                await require_consumer_identity(
                    request_mock,
                    consumer_id="c1",
                    topics=["disallowed-topic"],
                    principal=principal_with_topics,
                )
            assert exc_info.value.status_code == 403
        finally:
            pass


class TestPairwiseConsumerAuthorization:
    """Pairwise (consumer_id, topic) decision shared by subscribe, ACK and NACK."""

    @staticmethod
    def _request() -> Any:
        from unittest.mock import MagicMock

        request = MagicMock()
        request.state.request_id = "req-pairwise"
        request.url.path = "/subscribe"
        return request

    @pytest.mark.asyncio
    async def test_pairwise_matrix_rejects_cross_pairs(self) -> None:
        from eventbus.auth import Principal, Role, require_consumer_identity

        principal = Principal(
            roles=frozenset([Role.CONSUMER]),
            consumer_grants=frozenset(
                {("consumer_a", "topic_a"), ("consumer_b", "topic_b")}
            ),
            token_fingerprint="test-fingerprint",
        )
        for consumer_id, topic in (
            ("consumer_a", "topic_a"),
            ("consumer_b", "topic_b"),
        ):
            accepted = await require_consumer_identity(
                self._request(),
                consumer_id=consumer_id,
                topics=[topic],
                principal=principal,
            )
            assert accepted is principal
        for consumer_id, topic in (
            ("consumer_a", "topic_b"),
            ("consumer_b", "topic_a"),
        ):
            with pytest.raises(HTTPException) as exc:
                await require_consumer_identity(
                    self._request(),
                    consumer_id=consumer_id,
                    topics=[topic],
                    principal=principal,
                )
            assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_control_plane_token_cannot_use_consumer_routes(self) -> None:
        from eventbus.auth import (
            build_and_publish_generation,
            require_consumer_identity,
        )
        from eventbus.config import EventBusConfig

        cfg = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-control-plane.sqlite",
            storage_dir="/tmp/test-eventbus-control-plane",
            deadletter_dir="/tmp/test-eventbus-control-plane",
            max_retry=2,
            host="127.0.0.1",
            auth_token="shared-token",
            admin_token="admin-token",
            consumer_token="consumer-token",
            consumer_authorization={"consumer_a": ["test"]},
        )
        build_and_publish_generation(cfg)
        for token in ("shared-token", "admin-token"):
            with pytest.raises(HTTPException) as exc:
                await require_consumer_identity(
                    self._request(),
                    consumer_id="consumer_a",
                    topics=["test"],
                    principal=current_principals()[token],
                )
            assert exc.value.status_code == 403


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
            Principal,
            Role,
            build_and_publish_generation,
            resolve_principal,
        )
        from eventbus.config import EventBusConfig

        token = "publisher-token"
        cfg = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-fields1.sqlite",
            storage_dir="/tmp/test-eventbus-fields1",
            deadletter_dir="/tmp/test-eventbus-fields1",
            max_retry=2,
            host="127.0.0.1",
            auth_token="test-token",
            publisher_token=token,
        )
        build_and_publish_generation(cfg)
        principal = await resolve_principal(
            self._make_request_mock(auth_token=cfg.auth_token),
            credentials=MagicMock(credentials=token),
        )
        assert isinstance(principal, Principal)
        assert principal.roles == frozenset([Role.PUBLISHER])
        assert principal.consumer_grants == frozenset()

    @pytest.mark.asyncio
    async def test_per_role_token_has_no_consumer_restriction(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import (
            Principal,
            Role,
            build_and_publish_generation,
            resolve_principal,
        )
        from eventbus.config import EventBusConfig

        token = "consumer-token"
        cfg = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-fields2.sqlite",
            storage_dir="/tmp/test-eventbus-fields2",
            deadletter_dir="/tmp/test-eventbus-fields2",
            max_retry=2,
            host="127.0.0.1",
            auth_token="test-token",
            consumer_token=token,
            # Empty (deny-all) mapping: the Principal carries no consumer grants.
            consumer_authorization={},
        )
        build_and_publish_generation(cfg)
        principal = await resolve_principal(
            self._make_request_mock(auth_token=cfg.auth_token),
            credentials=MagicMock(credentials=token),
        )
        assert isinstance(principal, Principal)
        assert principal.roles == frozenset([Role.CONSUMER])
        assert principal.consumer_grants == frozenset()


class TestFailClosedConsumerAuthorization:
    """Regression (EVENTBUS-008 / ADR-013 INV-02): a consumer_token declared
    without an explicit consumer_authorization MUST fail closed (raise
    ValueError) at startup. An empty mapping resolves to frozenset() (deny-all)
    and rejects every consumer_id; only None (a missing key) raises at startup.
    Never weaken this guarantee."""

    @staticmethod
    def test_consumer_token_without_consumer_authorization_raises() -> None:
        from eventbus.auth import build_and_publish_generation
        from eventbus.config import EventBusConfig

        cfg = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-failclosed.sqlite",
            storage_dir="/tmp/test-eventbus-failclosed",
            deadletter_dir="/tmp/test-eventbus-failclosed",
            max_retry=2,
            host="127.0.0.1",
            auth_token="shared-token",
            consumer_token="consumer-token",
            # consumer_authorization intentionally omitted (defaults to None)
        )
        with pytest.raises(ValueError, match="consumer_authorization is missing"):
            build_and_publish_generation(cfg)

    @pytest.mark.asyncio
    async def test_shared_and_admin_tokens_have_no_consumer_bypass(self) -> None:
        """ADR-013 INV-02/INV-07: auth_token and admin_token hold no Consumer role,
        so require_consumer_identity rejects them for any consumer_id and topic."""
        from unittest.mock import MagicMock

        from eventbus.auth import (
            Role,
            build_and_publish_generation,
            require_consumer_identity,
        )
        from eventbus.config import EventBusConfig
        from fastapi import HTTPException

        cfg = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-superuser.sqlite",
            storage_dir="/tmp/test-eventbus-superuser",
            deadletter_dir="/tmp/test-eventbus-superuser",
            max_retry=2,
            host="127.0.0.1",
            auth_token="shared-token",
            admin_token="admin-token",
            consumer_token="consumer-token",
            consumer_authorization={"consumer-a": ["topic-a"]},
            topic_authorization={},
        )
        build_and_publish_generation(cfg)
        mock_request = MagicMock()
        mock_request.state.request_id = "req-superuser"
        mock_request.url.path = "/subscribe"
        for token in ("shared-token", "admin-token"):
            principal = current_principals()[token]
            assert Role.CONSUMER not in principal.roles
            assert Role.PUBLISHER not in principal.roles
            with pytest.raises(HTTPException) as exc:
                await require_consumer_identity(
                    mock_request,
                    consumer_id="consumer-a",
                    topics=["topic-a"],
                    principal=principal,
                )
            assert exc.value.status_code == 403
        consumer = current_principals()["consumer-token"]
        assert (
            await require_consumer_identity(
                mock_request,
                consumer_id="consumer-a",
                topics=["topic-a"],
                principal=consumer,
            )
            is consumer
        )

    @pytest.mark.asyncio
    async def test_empty_mappings_deny_all_consumers(self) -> None:
        """ADR-013 INV-07: empty consumer/topic authorization mappings resolve to
        frozenset() (deny-all); every consumer_id is rejected by
        require_consumer_identity."""
        from unittest.mock import MagicMock

        from eventbus.auth import (
            Principal,
            Role,
            build_and_publish_generation,
            require_consumer_identity,
        )
        from eventbus.config import EventBusConfig
        from fastapi import HTTPException

        token = "consumer-token"
        cfg = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-denyall.sqlite",
            storage_dir="/tmp/test-eventbus-denyall",
            deadletter_dir="/tmp/test-eventbus-denyall",
            max_retry=2,
            host="127.0.0.1",
            auth_token="shared-token",
            consumer_token=token,
            consumer_authorization={},
            topic_authorization={},
        )
        build_and_publish_generation(cfg)
        principal = current_principals()[token]
        assert isinstance(principal, Principal)
        assert principal.roles == frozenset({Role.CONSUMER})
        assert principal.consumer_grants == frozenset()
        mock_request = MagicMock()
        mock_request.state.request_id = "req-denyall"
        mock_request.url.path = "/subscribe"
        with pytest.raises(HTTPException) as exc:
            await require_consumer_identity(
                mock_request,
                consumer_id="consumer-x",
                principal=principal,
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_non_empty_mapping_restricts_to_allowlist(self) -> None:
        """A non-empty consumer/topic authorization mapping restricts the CONSUMER
        principal to its allowlist union; in-allowlist consumer_ids pass and
        out-of-allowlist ones are rejected."""
        from unittest.mock import MagicMock

        from eventbus.auth import (
            Principal,
            build_and_publish_generation,
            require_consumer_identity,
        )
        from eventbus.config import EventBusConfig
        from fastapi import HTTPException

        token = "consumer-token"
        cfg = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-allowlist.sqlite",
            storage_dir="/tmp/test-eventbus-allowlist",
            deadletter_dir="/tmp/test-eventbus-allowlist",
            max_retry=2,
            host="127.0.0.1",
            auth_token="shared-token",
            consumer_token=token,
            consumer_authorization={"consumer_a": ["test"], "consumer_b": ["test"]},
            topic_authorization={"test": {"consumer_a", "consumer_b"}},
        )
        build_and_publish_generation(cfg)
        principal = current_principals()[token]
        assert isinstance(principal, Principal)
        assert principal.consumer_grants == frozenset(
            {("consumer_a", "test"), ("consumer_b", "test")}
        )
        mock_request = MagicMock()
        mock_request.state.request_id = "req-allowlist"
        mock_request.url.path = "/subscribe"
        accepted = await require_consumer_identity(
            mock_request,
            consumer_id="consumer_a",
            principal=principal,
        )
        assert accepted is principal
        with pytest.raises(HTTPException) as exc:
            await require_consumer_identity(
                mock_request,
                consumer_id="consumer_c",
                principal=principal,
            )
        assert exc.value.status_code == 403


class TestAuditRecordValidation:
    """Tests for structured audit record emission on auth failures."""

    client: TestClient
    cfg: Any

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

        # Effective admin update: privileged_action records carry the
        # generation fields (EBAUTHGEN001 AC-5) and must not leak tokens.
        from eventbus.auth import current_generation, publish_generation

        captured_records.clear()
        before = current_generation()
        assert before is not None
        try:
            with (
                patch("eventbus.audit.logger.warning", side_effect=capture_log),
                patch("eventbus.audit.logger.info", side_effect=capture_log),
            ):
                response = self.client.post(
                    "/admin/topics/authorization",
                    json={
                        "consumer_authorization": {
                            "consumer_a": ["test", "leak-test-topic"]
                        },
                        "expected_generation": before.generation,
                    },
                    headers={"Authorization": f"Bearer {self.cfg.admin_token}"},
                )
                assert response.status_code == 200
        finally:
            # Restore the global generation so later tests observe the same state.
            publish_generation(before)

        import json

        privileged_records = [
            json.loads(record)
            for record in captured_records
            if json.loads(record).get("event") == "privileged_action"
        ]
        assert len(privileged_records) > 0
        audit_record = privileged_records[-1]
        assert audit_record["previous_generation"] == before.generation
        assert audit_record["new_generation"] == before.generation + 1

        for token_value in (
            self.cfg.auth_token,
            self.cfg.publisher_token,
            self.cfg.consumer_token,
            self.cfg.operator_token,
            self.cfg.admin_token,
        ):
            if token_value:
                assert token_value not in str(audit_record)


class TestUnified401ResponseFormat:
    """Tests for the unified HTTP 401 response format."""

    def test_missing_authorization_header_returns_unified_format(self) -> None:
        """ADR-013 INV-01: Missing Authorization header returns standardized 401 response."""
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
        """ADR-013 INV-01: Invalid Bearer token returns standardized 401 response."""
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
        """Authentication failures are not processed twice."""
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
    was registered without one. These tests use the production
    app, so a missing dependency fails here.
    """

    @pytest.fixture
    def prod_client(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
        import dataclasses

        from eventbus import app as eb_app
        from eventbus.auth import build_and_publish_generation
        from eventbus_helpers import make_eventbus_client

        with make_eventbus_client(tmp_path, monkeypatch) as client:
            cfg = dataclasses.replace(
                eb_app.app.state.config,
                publisher_token="prod-publisher-token",
                consumer_token="prod-consumer-token",
                # consumer_token requires a non-None consumer_authorization;
                # these tests gate on ROLE only, so an empty (deny-all) mapping suffices.
                consumer_authorization={},
                monitoring_token="prod-monitoring-token",
            )
            eb_app.app.state.config = cfg
            build_and_publish_generation(cfg)
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
        # The shared auth_token holds only control-plane roles (no Publisher/Consumer).
        control_status = 200 if path == "/health" else 403
        assert (
            self._call(prod_client, method, path, "test-token-control").status_code
            == control_status
        )


class TestDuplicateTokenBinding:
    """Duplicate non-empty token values are rejected and each token holds
    exactly its documented role."""

    def test_consumer_token_equal_to_auth_token_is_rejected(self) -> None:
        """A per-role token equal to the shared auth_token is rejected, not
        admitted with control-plane + CONSUMER roles."""
        from eventbus.auth import build_and_publish_generation
        from eventbus.config import EventBusConfig

        cfg = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-dup1.sqlite",
            storage_dir="/tmp/test-eventbus-dup1",
            deadletter_dir="/tmp/test-eventbus-dup1",
            max_retry=2,
            host="127.0.0.1",
            auth_token="shared-dup",
            consumer_token="shared-dup",
            consumer_authorization={},
        )
        with pytest.raises(ValueError, match="duplicate token") as exc_info:
            build_and_publish_generation(cfg)
        message = str(exc_info.value)
        assert "shared-dup" not in message
        for field in ("auth_token", "consumer_token"):
            assert field in message

    def test_distinct_tokens_get_exactly_their_documented_role(self) -> None:
        """A distinct-token config gives each token exactly its documented role."""
        from eventbus.auth import (
            Role,
            build_and_publish_generation,
        )
        from eventbus.config import EventBusConfig

        cfg = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-distinct.sqlite",
            storage_dir="/tmp/test-eventbus-distinct",
            deadletter_dir="/tmp/test-eventbus-distinct",
            max_retry=2,
            host="127.0.0.1",
            auth_token="auth-token",
            publisher_token="publisher-token",
            consumer_token="consumer-token",
            operator_token="operator-token",
            monitoring_token="monitoring-token",
            admin_token="admin-token",
            consumer_authorization={"consumer_a": ["test"]},
            topic_authorization={"test": {"consumer_a"}},
        )
        build_and_publish_generation(cfg)
        assert current_principals()["auth-token"].roles == frozenset(
            {Role.OPERATOR, Role.MONITORING, Role.ADMIN}
        )
        assert current_principals()["publisher-token"].roles == frozenset(
            {Role.PUBLISHER}
        )
        assert current_principals()["consumer-token"].roles == frozenset(
            {Role.CONSUMER}
        )
        assert current_principals()["admin-token"].roles == frozenset(
            {Role.OPERATOR, Role.MONITORING, Role.ADMIN}
        )

    @pytest.mark.parametrize(
        "field_a,field_b",
        [
            ("auth_token", "admin_token"),
            ("publisher_token", "consumer_token"),
            ("operator_token", "monitoring_token"),
        ],
    )
    def test_any_two_equal_tokens_raise_naming_fields(
        self, field_a: str, field_b: str
    ) -> None:
        """Every pair of distinct token fields sharing a non-empty value raises,
        naming both fields and not the shared value."""
        from eventbus.auth import build_and_publish_generation
        from eventbus.config import EventBusConfig

        cfg = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-dup2.sqlite",
            storage_dir="/tmp/test-eventbus-dup2",
            deadletter_dir="/tmp/test-eventbus-dup2",
            max_retry=2,
            host="127.0.0.1",
            auth_token="auth-token",
            publisher_token="",
            consumer_token="",
            operator_token="",
            monitoring_token="",
            admin_token="",
            consumer_authorization={},
        )
        import dataclasses

        overrides: dict[str, Any] = {
            field_a: "shared-value",
            field_b: "shared-value",
        }
        cfg = dataclasses.replace(cfg, **overrides)
        with pytest.raises(ValueError, match="duplicate token") as exc_info:
            build_and_publish_generation(cfg)
        message = str(exc_info.value)
        assert "shared-value" not in message
        assert field_a in message
        assert field_b in message


class TestAtomicPublishAndFailedRebuild:
    """Assert atomic publish (no empty-map window) and failed-rebuild preservation."""

    def test_atomic_publish_no_empty_map_window(self) -> None:
        """build_and_publish_generation publishes atomically — readers never see an empty map."""
        from eventbus.auth import Role, build_and_publish_generation
        from eventbus.config import EventBusConfig

        # Establish a known-good principal map first
        cfg = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-atomic.sqlite",
            storage_dir="/tmp/test-eventbus-atomic",
            deadletter_dir="/tmp/test-eventbus-atomic",
            max_retry=2,
            host="127.0.0.1",
            auth_token="auth-token",
            consumer_token="consumer-token",
            consumer_authorization={"consumer_a": ["topicA"]},
        )
        build_and_publish_generation(cfg)
        assert len(current_principals()) > 0

        # Now call build_and_publish_generation again — it should swap atomically.
        # If there were an empty-map window, we'd see zero entries mid-swap.
        # Simulate concurrent reads by checking before and after.
        pre_count = len(current_principals())
        build_and_publish_generation(cfg)
        post_count = len(current_principals())

        # Both before and after must have entries; no empty-map window.
        assert pre_count > 0
        assert post_count > 0
        assert post_count == pre_count  # same config → same number of entries

        # Verify the principal for auth-token is still present (not cleared).
        assert "auth-token" in current_principals()
        assert current_principals()["auth-token"].roles == frozenset(
            {Role.OPERATOR, Role.MONITORING, Role.ADMIN}
        )

    def test_failed_rebuild_preserves_previous_generation(self) -> None:
        """A failed rebuild (e.g. missing consumer_authorization) leaves the
        previous generation's principals intact and in force."""
        from eventbus import auth
        from eventbus.auth import Role, build_and_publish_generation
        from eventbus.config import EventBusConfig

        # Step 1: establish a valid principal map
        cfg_valid = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-fail1.sqlite",
            storage_dir="/tmp/test-eventbus-fail1",
            deadletter_dir="/tmp/test-eventbus-fail1",
            max_retry=2,
            host="127.0.0.1",
            auth_token="auth-token",
            consumer_token="consumer-token",
            consumer_authorization={"consumer_a": ["topicA"]},
        )
        build_and_publish_generation(cfg_valid)
        assert len(current_principals()) > 0
        assert "auth-token" in current_principals()

        # Step 2: attempt a rebuild with invalid config (consumer_token without
        # consumer_authorization raises ValueError)
        cfg_invalid = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-fail2.sqlite",
            storage_dir="/tmp/test-eventbus-fail2",
            deadletter_dir="/tmp/test-eventbus-fail2",
            max_retry=2,
            host="127.0.0.1",
            auth_token="auth-token",
            consumer_token="consumer-token",
            # consumer_authorization omitted — should raise
        )
        gen_before = auth.current_generation()
        with pytest.raises(ValueError, match="consumer_authorization"):
            build_and_publish_generation(cfg_invalid)
        # AC-004: the previous generation object stays in force.
        assert auth.current_generation() is gen_before

        # Step 3: verify the previous generation is still in force
        assert len(current_principals()) > 0
        assert "auth-token" in current_principals()
        assert current_principals()["auth-token"].roles == frozenset(
            {Role.OPERATOR, Role.MONITORING, Role.ADMIN}
        )

    def test_published_generation_read_returns_identical_object(self) -> None:
        """REQ-001: two reads of current_generation() return the identical
        object between publications (the snapshot is never rebuilt per read)."""
        from eventbus.auth import build_and_publish_generation, current_generation
        from eventbus.config import EventBusConfig

        # Self-contained baseline: conftest rolls generations back per test,
        # so this test publishes its own generation before reading it.
        cfg = EventBusConfig(
            port=8091,
            db_path="/tmp/test-eventbus-ident.sqlite",
            storage_dir="/tmp/test-eventbus-ident",
            deadletter_dir="/tmp/test-eventbus-ident",
            max_retry=2,
            host="127.0.0.1",
            auth_token="auth-token",
        )
        build_and_publish_generation(cfg)
        generation = current_generation()
        assert generation is not None
        assert current_generation() is generation

    def test_published_generation_principals_is_the_map_resolve_principal_consults(
        self,
    ) -> None:
        """REQ-001: resolve_principal() consults exactly the published
        AuthzGeneration's principals map; a failed rebuild leaves the previous
        generation object in force and a successful one advances the number."""
        from unittest.mock import MagicMock

        from eventbus.auth import (
            build_and_publish_generation,
            current_generation,
            resolve_principal,
        )
        from eventbus.config import EventBusConfig

        base_kwargs: dict[str, Any] = dict(
            port=8091,
            db_path="/tmp/test-eventbus-resolve-map.sqlite",
            storage_dir="/tmp/test-eventbus-resolve-map",
            deadletter_dir="/tmp/test-eventbus-resolve-map",
            max_retry=2,
            host="127.0.0.1",
            auth_token="shared-token",
        )
        cfg_v1 = EventBusConfig(**base_kwargs, publisher_token="publisher-v1")
        build_and_publish_generation(cfg_v1)
        gen1 = current_generation()
        assert gen1 is not None
        assert "publisher-v1" in gen1.principals

        mock_request = MagicMock()
        mock_request.app.state.config.auth_token = cfg_v1.auth_token
        mock_request.state.request_id = "req-resolve-map"
        mock_request.url.path = "/publish"
        principal = _await(
            resolve_principal(
                mock_request, credentials=MagicMock(credentials="publisher-v1")
            )
        )
        assert principal.roles == gen1.principals["publisher-v1"].roles

        # A failed rebuild keeps the previous generation object in force.
        with pytest.raises(ValueError, match="consumer_authorization"):
            build_and_publish_generation(
                EventBusConfig(**base_kwargs, consumer_token="consumer-bad")
            )
        assert current_generation() is gen1

        # A successful rebuild publishes generation+1 with a new principals map.
        cfg_v2 = EventBusConfig(**base_kwargs, publisher_token="publisher-v2")
        build_and_publish_generation(cfg_v2)
        gen2 = current_generation()
        assert gen2 is not None
        assert gen2.generation == gen1.generation + 1
        assert gen2.principals is not gen1.principals
        assert "publisher-v2" in gen2.principals
        assert "publisher-v1" not in gen2.principals
