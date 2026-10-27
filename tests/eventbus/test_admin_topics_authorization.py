"""tests/eventbus/test_admin_topics_authorization.py
Integration tests for the POST /admin/topics/authorization endpoint.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.eventbus.eventbus_helpers import principal_map


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
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
        # A distinct, unused-by-these-tests auth_token satisfies
        # EventBusConfig's unconditional "auth_token is required" validation
        # without granting the superuser shortcut to any token these tests
        # actually present as a caller credential.
        auth_token="unused-shared-superuser-tok",
        admin_token="admin-tok",
        consumer_token="consumer-tok",
        # Fail-closed (ADR-013 INV-02): consumer_token requires a non-None
        # consumer_authorization. These tests drive the allow-list through the
        # /admin/topics/authorization endpoint (consumer id "c1"); this initial
        # value only satisfies the startup fail-closed check.
        consumer_authorization={"c1": ["topicA"]},
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

    def test_empty_body_rejected(self, admin_client: TestClient) -> None:
        """UNK-02: empty/no-op bodies are rejected with 422."""
        resp = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={},
        )
        assert resp.status_code == 422

    def test_response_includes_persistent_and_changed(
        self, admin_client: TestClient
    ) -> None:
        """Runtime-only default: persistent is always false; changed reflects whether config changed."""
        resp = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicA", "topicB"]}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["persistent"] is False
        assert data["changed"] is True

    def test_response_changed_false_when_noop(self, admin_client: TestClient) -> None:
        """When body has keys but no actual change, changed=false."""
        # First update to establish state
        admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicA"]}},
        )
        # Same body again — no-op
        resp = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicA"]}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["changed"] is False

    def test_audit_emitted_on_effective_change(self, admin_client: TestClient) -> None:
        """Effective change emits one redacted log_privileged_action; no-op emits none."""
        from unittest.mock import patch

        with patch("eventbus.admin_route.log_privileged_action") as mock_log:
            resp = admin_client.post(
                "/admin/topics/authorization",
                headers={"Authorization": "Bearer admin-tok"},
                json={"consumer_authorization": {"c1": ["topicA", "topicB"]}},
            )
            assert resp.status_code == 200
            assert mock_log.call_count == 1
            call_args = mock_log.call_args
            assert call_args.kwargs["target"] == "topics_authorization"
            assert call_args.kwargs["detail"] == "updated"

    def test_audit_not_emitted_on_noop(self, admin_client: TestClient) -> None:
        """No-op does not emit audit record."""
        from unittest.mock import patch

        # Establish state first
        admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicA"]}},
        )
        with patch("eventbus.admin_route.log_privileged_action") as mock_log:
            resp = admin_client.post(
                "/admin/topics/authorization",
                headers={"Authorization": "Bearer admin-tok"},
                json={"consumer_authorization": {"c1": ["topicA"]}},
            )
            assert resp.status_code == 200
            assert mock_log.call_count == 0


class TestUpdateTakesEffect:
    def test_update_reflected_in_subsequent_subscribe_authorization(
        self, admin_client: TestClient
    ) -> None:

        resp = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicA", "topicB"]}},
        )
        assert resp.status_code == 200

        principal = principal_map()["consumer-tok"]
        assert principal.allowed_consumer_ids == frozenset({"c1"})
        assert principal.allowed_topics == frozenset({"topicA", "topicB"})


class TestValidation:
    def test_invalid_body_rejected_without_corrupting_state(
        self, admin_client: TestClient
    ) -> None:

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
        principal = principal_map()["consumer-tok"]
        assert principal.allowed_consumer_ids == frozenset({"c1"})
        assert principal.allowed_topics == frozenset({"topicA"})


class TestOneRolePerTokenAdminRebuild:
    """REQ-004: each configured token holds exactly its documented role when
    _populate_token_maps() runs as admin_route.py rebuilds the maps."""

    @staticmethod
    def _snapshot():
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP

        return dict(_TOKEN_PRINCIPAL_MAP)

    @staticmethod
    def _restore(snapshot):
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP

        _TOKEN_PRINCIPAL_MAP.clear()
        _TOKEN_PRINCIPAL_MAP.update(snapshot)

    def test_each_token_holds_exactly_its_documented_role(self) -> None:
        """A distinct-token config gives every token exactly its documented role
        set, with no control-plane-plus-CONSUMER collision."""
        from eventbus.auth import _populate_token_maps
        from eventbus.config import EventBusConfig

        snapshot = self._snapshot()
        try:
            cfg = EventBusConfig(
                port=8016,
                db_path="/tmp/test-admin-distinct.sqlite",
                storage_dir="/tmp/test-admin-distinct",
                deadletter_dir="/tmp/test-admin-distinct",
                max_retry=3,
                auth_token="auth-token",
                publisher_token="publisher-token",
                consumer_token="consumer-token",
                operator_token="operator-token",
                monitoring_token="monitoring-token",
                admin_token="admin-token",
                consumer_authorization={"c1": ["topicA"]},
                topic_authorization={"topicA": ["c1"]},
            )
            _populate_token_maps(cfg)
            assert set(principal_map()["auth-token"].roles) == {
                "operator",
                "monitoring",
                "admin",
            }
            assert set(principal_map()["publisher-token"].roles) == {"publisher"}
            assert set(principal_map()["consumer-token"].roles) == {"consumer"}
            assert set(principal_map()["operator-token"].roles) == {"operator"}
            assert set(principal_map()["monitoring-token"].roles) == {"monitoring"}
            assert set(principal_map()["admin-token"].roles) == {
                "operator",
                "monitoring",
                "admin",
            }
        finally:
            self._restore(snapshot)


class TestDuplicateRejectionAdminRebuild:
    """REQ-003: duplicate non-empty token values are rejected by
    _populate_token_maps() as admin_route.py calls it, naming the fields."""

    @staticmethod
    def _snapshot():
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP

        return dict(_TOKEN_PRINCIPAL_MAP)

    @staticmethod
    def _restore(snapshot):
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP

        _TOKEN_PRINCIPAL_MAP.clear()
        _TOKEN_PRINCIPAL_MAP.update(snapshot)

    @pytest.mark.parametrize(
        "field_a,field_b",
        [
            ("auth_token", "consumer_token"),
            ("auth_token", "admin_token"),
            ("publisher_token", "consumer_token"),
        ],
    )
    def test_two_equal_tokens_raise_naming_fields(
        self, field_a: str, field_b: str
    ) -> None:
        """Every tested pair of distinct token fields sharing a non-empty value
        raises, naming both fields and not the shared value."""
        import dataclasses

        from eventbus.auth import _populate_token_maps
        from eventbus.config import EventBusConfig

        base = EventBusConfig(
            port=8016,
            db_path="/tmp/test-admin-dup.sqlite",
            storage_dir="/tmp/test-admin-dup",
            deadletter_dir="/tmp/test-admin-dup",
            max_retry=3,
            auth_token="auth-token",
            publisher_token="",
            consumer_token="",
            operator_token="",
            monitoring_token="",
            admin_token="",
            consumer_authorization={},
        )
        cfg = dataclasses.replace(
            base, **{field_a: "shared-value", field_b: "shared-value"}
        )
        with pytest.raises(ValueError, match="duplicate token") as exc_info:
            _populate_token_maps(cfg)
        message = str(exc_info.value)
        assert "shared-value" not in message
        assert field_a in message
        assert field_b in message
