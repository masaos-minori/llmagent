"""tests/eventbus/test_admin_topics_authorization.py
Integration tests for the POST /admin/topics/authorization endpoint.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from eventbus.auth import _derive_token_fingerprint
from fastapi.testclient import TestClient

from tests.eventbus.eventbus_helpers import principal_map


@pytest.fixture()
def admin_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Build an Event Bus TestClient through the production lifespan with distinct
    admin_token/consumer_token (unlike `eventbus_helpers.make_eventbus_client`'s
    shared, all-roles `auth_token`), so ADMIN-gating can be tested against a
    genuinely non-admin caller.
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

    with TestClient(eb_app.app) as c:
        yield c


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
        """Empty/no-op bodies are rejected with 422."""
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
            assert call_args.kwargs["request_id"] != ""
            assert call_args.kwargs["actor"] == _derive_token_fingerprint("admin-tok")
            assert call_args.kwargs["target"] == "topics_authorization"
            assert (
                call_args.kwargs["detail"]
                == "consumer_authorization:1;persistent:false"
            )

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
        assert principal.consumer_grants == frozenset(
            {("c1", "topicA"), ("c1", "topicB")}
        )


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
        assert principal.consumer_grants == frozenset({("c1", "topicA")})


class TestPublishOrder:
    def test_failed_principal_build_keeps_previous_generation(
        self, admin_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from eventbus import app as eb_app

        config_before = eb_app.app.state.config
        map_before = principal_map()

        def _boom(config: Any) -> Any:
            raise ValueError("principal build failed")

        monkeypatch.setattr("eventbus.admin_route._build_principal_map", _boom)
        failing = TestClient(admin_client.app, raise_server_exceptions=False)
        resp = failing.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicB"]}},
        )

        assert resp.status_code == 500
        assert eb_app.app.state.config is config_before
        assert principal_map() is map_before

    def test_noop_update_publishes_nothing(self, admin_client: TestClient) -> None:
        from eventbus import app as eb_app

        config_before = eb_app.app.state.config
        map_before = principal_map()

        resp = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicA"]}},
        )

        assert resp.status_code == 200
        assert resp.json()["changed"] is False
        assert eb_app.app.state.config is config_before
        assert principal_map() is map_before

    def test_effective_update_publishes_config_and_map(
        self, admin_client: TestClient
    ) -> None:
        from eventbus import app as eb_app

        config_before = eb_app.app.state.config
        map_before = principal_map()

        resp = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicB"]}},
        )

        assert resp.status_code == 200
        assert resp.json()["changed"] is True
        assert eb_app.app.state.config is not config_before
        assert principal_map() is not map_before
        assert principal_map()["consumer-tok"].consumer_grants == frozenset(
            {("c1", "topicB")}
        )


class TestUpdateRemovesPairs:
    def test_update_removes_pairs_no_longer_configured(
        self, admin_client: TestClient
    ) -> None:
        url = "/admin/topics/authorization"
        headers = {"Authorization": "Bearer admin-tok"}
        first = admin_client.post(
            url,
            headers=headers,
            json={"consumer_authorization": {"c1": ["topicA", "topicB"]}},
        )
        assert first.status_code == 200
        second = admin_client.post(
            url, headers=headers, json={"consumer_authorization": {"c1": ["topicA"]}}
        )
        assert second.status_code == 200

        principal = principal_map()["consumer-tok"]
        assert principal.is_granted("c1", "topicA")
        assert not principal.is_granted("c1", "topicB")


class TestOneRolePerTokenAdminRebuild:
    """ADR-013 INV-02: each configured token holds exactly its documented role
    when _populate_token_maps() runs as admin_route.py rebuilds the maps."""

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
                topic_authorization={"topicA": {"c1"}},
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
    """Duplicate non-empty token values are rejected by
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
        overrides: dict[str, Any] = {field_a: "shared-value", field_b: "shared-value"}
        cfg = dataclasses.replace(base, **overrides)
        with pytest.raises(ValueError, match="duplicate token") as exc_info:
            _populate_token_maps(cfg)
        message = str(exc_info.value)
        assert "shared-value" not in message
        assert field_a in message
        assert field_b in message
