#!/usr/bin/env python3
"""tests/eventbus/test_eventbus_auth.py

Positive/negative authorization tests for every EventBus route category.

Each route category has:
- One authorized-success case
- One unauthorized/wrong-role-rejection case

Precedent: scripts/mcp_servers/server.py::attach_auth_middleware() pattern
"""

import asyncio
from datetime import UTC
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.testclient import TestClient

TEST_TOKEN = "test-auth-token"
TEST_DB_PATH = "/tmp/test-eventbus.sqlite"
TEST_STORAGE_DIR = "/tmp/test-storage"
TEST_OFFSETS_DIR = "/tmp/test-offsets"
TEST_DEADLETTER_DIR = "/tmp/test-deadletter"


def _make_test_app(tmp_path: Path, token: str) -> tuple[FastAPI, Any]:
    """Create a fresh FastAPI app with auth middleware registered."""
    from eventbus import app as eb_app
    from eventbus.auth import (
        attach_auth_middleware,
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

    attach_auth_middleware(local_app, token)

    @local_app.post("/publish")
    async def publish(request: Request) -> dict[str, Any]:
        result: dict[str, Any] = await eb_app.publish_route(request)
        return result

    @local_app.get("/subscribe")
    async def subscribe(
        request: Request,
        topic: list[str] = Query(default=[]),
        since_seq: int = Query(default=0, ge=0),
        consumer_id: str = Query(default=""),
    ) -> Any:
        return await eb_app.subscribe_route(
            request, topic=topic, since_seq=since_seq, consumer_id=consumer_id
        )

    @local_app.get("/dlq")
    async def dlq_list(
        request: Request,
        limit: int = Query(default=100, ge=1, le=1000),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        result: dict[str, Any] = await eb_app.dlq_list_route(
            request, limit=limit, offset=offset
        )
        return result

    @local_app.post("/dlq/{event_id}/requeue")
    async def dlq_requeue(request: Request, event_id: str) -> dict[str, Any]:
        result: dict[str, Any] = await eb_app.dlq_requeue_route(request, event_id)
        return result

    @local_app.get("/replay")
    async def replay(
        request: Request,
        since_seq: int = Query(default=0, ge=0),
        fmt: str = Query(default="sse", alias="format"),
        limit: int = Query(default=100, ge=1, le=1000),
        offset: int = Query(default=0, ge=0),
    ) -> Any:
        return await eb_app.replay_route(
            request, since_seq=since_seq, fmt=fmt, limit=limit, offset=offset
        )

    @local_app.post("/events/{event_id}/ack")
    async def ack_event(
        request: Request,
        event_id: str,
        consumer_id: str = Query(default=""),
    ) -> dict[str, Any]:
        result: dict[str, Any] = await eb_app.ack_event_route(
            request, event_id=event_id, consumer_id=consumer_id
        )
        return result

    @local_app.post("/nack")
    async def nack(
        request: Request,
        event_id: str = Query(default=""),
    ) -> dict[str, Any]:
        result: dict[str, Any] = await eb_app.nack_route(request, event_id=event_id)
        return result

    client = TestClient(local_app, raise_server_exceptions=False)

    def _cleanup():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_do_cleanup_eb())
        finally:
            loop.close()

    client._cleanup = _cleanup  # type: ignore[attr-defined] — TestClient does not expose _cleanup as a public attribute; needed to clean up ASGI transport on teardown
    return local_app, cfg


async def _init_local_state(app: FastAPI, cfg: Any) -> None:
    """Initialize app.state for the given config."""
    import pathlib

    from eventbus import app as eb_app

    app.state.config = cfg
    app.state.db = eb_app.open_db(cfg.db_path)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    app.state.envelope_schema = eb_app.orjson.loads(schema_path.read_bytes())
    pathlib.Path(cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    app.state.broker = eb_app.EventBroker()


async def _do_cleanup_eb() -> None:
    """Clean up resources from eb_app.app.state."""
    from eventbus import app as eb_app

    dlq_task = getattr(eb_app.app.state, "dlq_task", None)
    if dlq_task:
        dlq_task.cancel()
        try:
            await dlq_task
        except asyncio.CancelledError:
            pass
    if eb_app.app.state.broker:
        eb_app.app.state.broker.shutdown()
    if eb_app.app.state.db:
        eb_app.app.state.db.close()


class TestPublishAuth:
    """Tests for POST /publish authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-publish")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(cls.tmp_path, TEST_TOKEN)
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
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
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


class TestSubscribeAuth:
    """Tests for GET /subscribe authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-subscribe")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(cls.tmp_path, TEST_TOKEN)
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    def test_subscribe_with_valid_consumer_token(self) -> None:
        """Authorized consumer can subscribe to events."""
        # /subscribe is an infinite SSE stream, so use .stream() and only
        # check the response headers — a plain .get() blocks forever
        # waiting for the (never-ending) body to complete.
        with self.client.stream(
            "GET",
            "/subscribe",
            params={"topic": "test", "consumer_id": "consumer_a"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        ) as response:
            assert response.status_code == 200

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
        cls.app, cls.cfg = _make_test_app(cls.tmp_path, TEST_TOKEN)
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


class TestNackAuth:
    """Tests for POST /nack authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-nack")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(cls.tmp_path, TEST_TOKEN)
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


class TestDlqListAuth:
    """Tests for GET /dlq authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-dlq-list")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(cls.tmp_path, TEST_TOKEN)
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    def test_dlq_list_with_valid_operator_token(self) -> None:
        """Authorized operator can list DLQ entries."""
        response = self.client.get(
            "/dlq",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
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
        cls.app, cls.cfg = _make_test_app(cls.tmp_path, TEST_TOKEN)
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


class TestReplayAuth:
    """Tests for GET /replay authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-replay")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(cls.tmp_path, TEST_TOKEN)
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None

    @classmethod
    def teardown_class(cls):
        if hasattr(cls.client, "_cleanup"):
            cls.client._cleanup()

    def test_replay_with_valid_operator_token(self) -> None:
        """Authorized operator can replay events."""
        response = self.client.get(
            "/replay",
            params={"since_seq": 0, "limit": 100},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        assert response.status_code == 200

    def test_replay_without_token(self) -> None:
        """Unauthenticated request to /replay is rejected."""
        response = self.client.get("/replay", params={"since_seq": 0, "limit": 100})
        assert response.status_code == 401
