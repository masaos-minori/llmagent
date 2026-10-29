"""Shared helpers for Event Bus tests."""

from __future__ import annotations

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
    "probe-consumer",
    "svc-A",
    "svc-B",
    "svc-C",
    "svc-new",
    "svc-old",
    "svc-reuse",
    "svc-gap",
    "A",
    "B",
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
    "ack",
    "ack_test",
    "crash",
    "dlq",
    "dlq_edge",
    "dlq_multi",
    "dlq_promo",
)


def eventbus_test_tokens(token: str = "test-token") -> dict[str, Any]:
    """Config kwargs giving each role its own distinct test token.

    Every non-empty token field holds a distinct value and grants exactly its
    own role (ADR-013 INV-02 and INV-07). The shared
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


def eventbus_test_config(
    tmp_path: Path,
    *,
    max_retry: int = 3,
    sse_idle_timeout: float | None = None,
    token: str = "test-token",
) -> Any:
    """Build an EventBusConfig for test use.

    Returns a configured EventBusConfig instance with test tokens and paths
    derived from ``tmp_path``. This is a private test helper (not a leading
    underscore) because the restart test file imports it across modules.
    """
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=max_retry,
        **eventbus_test_tokens(token),
    )
    if sse_idle_timeout is not None:
        # The constructor validates the idle timeout against the heartbeat
        # interval, so a short value is assigned after construction.
        object.__setattr__(cfg, "sse_idle_timeout", sse_idle_timeout)
    return cfg


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

    The returned client must be entered as a context manager
    (``with make_eventbus_client(...) as c``): the production lifespan then starts
    the application and its shutdown sequence stops it. The helper builds no app
    state itself.
    """
    from eventbus import app as eb_app

    cfg = eventbus_test_config(
        tmp_path,
        max_retry=max_retry,
        sse_idle_timeout=sse_idle_timeout,
        token="test-token",
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    client = TestClient(eb_app.app)
    client.headers["Authorization"] = eventbus_auth_headers(default_role)[
        "Authorization"
    ]
    return client


def eventbus_two_lifecycle_clients(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Any:
    """Yield (open_client, snapshots).

    open_client() enters TestClient(eb_app.app) so the production lifespan builds and
    tears down app.state; each entry appends (app.state.db, app.state.broker) to
    snapshots. Callers open two sequential lifecycles on the same tmp_path database.
    """
    from contextlib import contextmanager

    from eventbus import app as eb_app

    cfg = eventbus_test_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    snapshots: list[tuple[Any, Any]] = []

    @contextmanager
    def open_client() -> Any:
        with TestClient(eb_app.app) as client:
            client.headers["Authorization"] = eventbus_auth_headers("publisher")[
                "Authorization"
            ]
            snapshots.append((eb_app.app.state.db, eb_app.app.state.broker))
            yield client

    yield open_client, snapshots


def principal_map() -> dict[str, Principal]:
    """Return the live Event Bus principal map.

    `eventbus.auth.publish_principals()` replaces the module-level map on every
    `_populate_token_maps()` call, so a reference imported before that call goes
    stale. Look the map up through the module each time it is read or modified.
    """
    from eventbus import auth

    return auth._TOKEN_PRINCIPAL_MAP
