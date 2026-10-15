"""Shared helpers for Event Bus tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

# ids and topics used by the Event Bus tests; Consumer routes admit only principals
# with explicit authorizations (ADR-013 INV-02), so these are granted explicitly.
TEST_CONSUMER_IDS = (
    "consumer-A",
    "consumer-B",
    "consumer-a",
    "consumer-b",
    "consumer_a",
    "consumer_b",
    "consumer_c",
    "c1",
    "test-consumer",
    "dup-health",
    "resume-consumer",
    "reconnect-test",
    "overflow-test",
    "duplicate",
    "default-consumer",
    "svc-A",
    "shared-consumer",
    "ordered-consumer",
    "oof-route-consumer",
    "consumer-mono",
    "consumer1",
    "consumer2",
    "test-precedence",
)
TEST_TOPICS = (
    "t",
    "t1",
    "t2",
    "a",
    "test",
    "test.topic",
    "target",
    "other",
    "empty",
    "precedence",
    "resume",
    "orders",
    "users",
    "boundary",
    "overlap",
    "resume2",
)


def eventbus_test_tokens(token: str = "test-token") -> dict[str, Any]:
    """Config kwargs giving one test token the data-plane and operator roles.

    The shared ``auth_token`` holds only control-plane roles, so the token the
    tests present is registered as a publisher, consumer, operator, and
    monitoring token. The consumer role is bound to explicit consumer_id and
    topic authorizations.
    """
    return {
        "auth_token": f"{token}-control",
        "publisher_token": token,
        "consumer_token": token,
        "operator_token": token,
        "monitoring_token": token,
        "consumer_authorization": {c: list(TEST_TOPICS) for c in TEST_CONSUMER_IDS},
    }


def make_eventbus_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    max_retry: int = 3,
    sse_idle_timeout: float | None = None,
) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=max_retry,
        **eventbus_test_tokens("test-token"),
    )
    if sse_idle_timeout is not None:
        # The constructor validates the idle timeout against the heartbeat
        # interval, so a short value is assigned after construction.
        object.__setattr__(cfg, "sse_idle_timeout", sse_idle_timeout)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    # Initialize app.state before creating TestClient
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_state(cfg))
    finally:
        loop.close()

    client = TestClient(eb_app.app)
    client.headers["Authorization"] = "Bearer test-token"

    # Store cleanup callback on client for teardown
    def _cleanup():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_do_cleanup())
        finally:
            loop.close()

    client._cleanup = _cleanup  # type: ignore[attr-defined] — TestClient has no _cleanup attribute; attached here only for this test helper's own teardown call
    return client


async def _init_state(cfg: Any) -> None:
    import pathlib

    from eventbus import app as eb_app

    eb_app.app.state.config = cfg
    eb_app.app.state.db = eb_app.open_db(cfg.db_path)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    eb_app.app.state.envelope_schema = eb_app.orjson.loads(schema_path.read_bytes())
    pathlib.Path(cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    eb_app.app.state.broker = eb_app.EventBroker(cfg)


async def _do_cleanup() -> None:
    from eventbus import app as eb_app

    if eb_app.app.state.dlq_task:
        eb_app.app.state.dlq_task.cancel()
        try:
            await eb_app.app.state.dlq_task
        except asyncio.CancelledError:
            pass
    if eb_app.app.state.broker:
        eb_app.app.state.broker.shutdown()
    if eb_app.app.state.db:
        eb_app.app.state.db.close()
