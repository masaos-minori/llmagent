"""tests/eventbus/test_admin_topics_authorization.py
Integration tests for the POST /admin/topics/authorization endpoint.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


def _make_admin_test_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Build an Event Bus TestClient with distinct admin_token/consumer_token
    (unlike `eventbus_helpers.make_eventbus_client`'s shared, all-roles
    `auth_token`), so ADMIN-gating can be tested against a genuinely
    non-admin caller.
    """
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8016,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
        # A distinct, unused-by-these-tests auth_token satisfies
        # EventBusConfig's unconditional "auth_token is required" validation
        # without granting the superuser shortcut to any token these tests
        # actually present as a caller credential.
        auth_token="unused-shared-superuser-tok",
        admin_token="admin-tok",
        consumer_token="consumer-tok",
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_state(cfg))
    finally:
        loop.close()

    client = TestClient(eb_app.app)

    def _cleanup() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_do_cleanup())
        finally:
            loop.close()

    client._cleanup = _cleanup  # type: ignore[attr-defined] — TestClient has no _cleanup attribute; attached here only for this test's own teardown call
    return client


async def _init_state(cfg: Any) -> None:
    import pathlib

    from eventbus import app as eb_app

    eb_app.app.state.config = cfg
    eb_app.app.state.db = eb_app.open_db(cfg.db_path)
    # This test builds app.state directly rather than running the real
    # lifespan handler (which sets dlq_task via asyncio.create_task), so
    # _do_cleanup's `if eb_app.app.state.dlq_task` check needs an explicit
    # None here to avoid an AttributeError/KeyError on teardown.
    eb_app.app.state.dlq_task = None
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    eb_app.app.state.envelope_schema = eb_app.orjson.loads(schema_path.read_bytes())
    pathlib.Path(cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    eb_app.app.state.broker = eb_app.EventBroker(cfg)
    from eventbus.auth import _populate_token_maps

    _populate_token_maps(cfg)


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


@pytest.fixture()
def admin_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    client = _make_admin_test_client(tmp_path, monkeypatch)
    yield client
    client._cleanup()


class TestAdminGating:
    def test_valid_admin_token_accepted(self, admin_client: TestClient) -> None:
        resp = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicA"]}},
        )
        assert resp.status_code == 200

    def test_non_admin_token_rejected(self, admin_client: TestClient) -> None:
        resp = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer consumer-tok"},
            json={"consumer_authorization": {"c1": ["topicA"]}},
        )
        assert resp.status_code == 403

    def test_missing_token_rejected(self, admin_client: TestClient) -> None:
        resp = admin_client.post(
            "/admin/topics/authorization",
            json={"consumer_authorization": {"c1": ["topicA"]}},
        )
        assert resp.status_code == 401


class TestUpdateTakesEffect:
    def test_update_reflected_in_subsequent_subscribe_authorization(
        self, admin_client: TestClient
    ) -> None:
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP

        resp = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicA", "topicB"]}},
        )
        assert resp.status_code == 200

        principal = _TOKEN_PRINCIPAL_MAP["consumer-tok"]
        assert principal.allowed_consumer_ids == frozenset({"c1"})
        assert principal.allowed_topics == frozenset({"topicA", "topicB"})


class TestValidation:
    def test_invalid_body_rejected_without_corrupting_state(
        self, admin_client: TestClient
    ) -> None:
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP

        # Establish a known-good state first.
        good = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicA"]}},
        )
        assert good.status_code == 200

        # Send an invalid update (wrong type for the topics list).
        bad = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": "not-a-list"}},
        )
        assert bad.status_code == 422

        # Confirm the earlier, valid state is unaffected by the rejected request.
        principal = _TOKEN_PRINCIPAL_MAP["consumer-tok"]
        assert principal.allowed_consumer_ids == frozenset({"c1"})
        assert principal.allowed_topics == frozenset({"topicA"})
