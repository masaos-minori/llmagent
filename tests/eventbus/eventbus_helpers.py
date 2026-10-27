"""Shared helpers for Event Bus tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from eventbus.auth import Principal

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
    """Config kwargs giving each role its own distinct test token.

    Every non-empty token field holds a distinct value and grants exactly its
    own role (REQ-003 uniqueness, REQ-004 one-role-per-token). The shared
    ``auth_token`` holds only control-plane roles; the per-role tokens grant
    PUBLISHER, CONSUMER, OPERATOR, and MONITORING respectively. The consumer
    role is bound to explicit consumer_id and topic authorizations.
    """
    return {
        "auth_token": f"{token}-control",
        "publisher_token": f"{token}-pub",
        "consumer_token": f"{token}-consumer",
        "operator_token": f"{token}-operator",
        "monitoring_token": f"{token}-monitor",
        "consumer_authorization": {c: list(TEST_TOPICS) for c in TEST_CONSUMER_IDS},
    }


def eventbus_auth_headers(role: str) -> dict[str, str]:
    """Return an Authorization header dict presenting the token for ``role``.

    ``role`` is the role name (e.g. ``"publisher"``, ``"consumer"``,
    ``"operator"``, ``"monitoring"``); the matching ``<role>_token`` from
    :func:`eventbus_test_tokens` is presented as the bearer credential. Use this
    so each request carries the token for exactly the role the endpoint requires
    instead of one global token that would grant every role.
    """
    tokens = eventbus_test_tokens()
    return {"Authorization": f"Bearer {tokens[f'{role}_token']}"}


def make_eventbus_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    max_retry: int = 3,
    sse_idle_timeout: float | None = None,
    default_role: str = "publisher",
) -> Any:
    """Build a TestClient whose default Authorization header carries ``default_role``.

    The Event Bus enforces one-role-per-token, so a single global header can only
    carry one role. Callers that exercise more than one role must pass the correct
    header per call via :func:`eventbus_auth_headers`; ``default_role`` covers the
    common case where a test starts with (and mostly stays on) one role.
    """
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
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
    client.headers["Authorization"] = eventbus_auth_headers(default_role)[
        "Authorization"
    ]

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


def principal_map() -> dict[str, Principal]:
    """Return the live Event Bus principal map.

    `eventbus.auth.publish_principals()` replaces the module-level map on every
    `_populate_token_maps()` call, so a reference imported before that call goes
    stale. Look the map up through the module each time it is read or modified.
    """
    from eventbus import auth

    return auth._TOKEN_PRINCIPAL_MAP
