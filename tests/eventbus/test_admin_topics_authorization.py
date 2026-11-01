"""tests/eventbus/test_admin_topics_authorization.py
Integration tests for the POST /admin/topics/authorization endpoint.

EBAUTHGEN001: every effective update carries a mandatory `expected_generation`
optimistic-concurrency token, publishes a new AuthzGeneration, and reports the
generation transition; stale tokens are rejected with 409 before change
detection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from eventbus.auth import (
    AuthzGeneration,
    _derive_token_fingerprint,
    current_generation,
)
from fastapi.testclient import TestClient

from tests.eventbus.eventbus_helpers import post_topics_authorization, principal_map

ADMIN_HEADERS = {"Authorization": "Bearer admin-tok"}


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


def _require_generation() -> AuthzGeneration:
    """Return the in-force AuthzGeneration, failing loudly if none exists."""
    generation = current_generation()
    assert generation is not None
    return generation


class TestAdminGating:
    def test_valid_admin_token_accepted(self, admin_client: TestClient) -> None:
        resp = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA"]}},
            headers=ADMIN_HEADERS,
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
            headers=ADMIN_HEADERS,
            json={},
        )
        assert resp.status_code == 422

    def test_missing_expected_generation_rejected(
        self, admin_client: TestClient
    ) -> None:
        """A body without expected_generation is rejected with 422 (REQ-002)."""
        before = _require_generation()
        resp = admin_client.post(
            "/admin/topics/authorization",
            headers=ADMIN_HEADERS,
            json={"consumer_authorization": {"c1": ["topicA", "topicB"]}},
        )
        assert resp.status_code == 422
        assert "expected_generation" in resp.json()["detail"]
        assert current_generation() is before

    def test_non_integer_expected_generation_rejected(
        self, admin_client: TestClient
    ) -> None:
        """Non-integer (and bool) expected_generation values are rejected with
        422 and change nothing."""
        before = _require_generation()
        resp = admin_client.post(
            "/admin/topics/authorization",
            headers=ADMIN_HEADERS,
            json={
                "consumer_authorization": {"c1": ["topicA", "topicB"]},
                "expected_generation": "0",
            },
        )
        assert resp.status_code == 422
        assert "expected_generation must be int" in resp.json()["detail"]
        resp = admin_client.post(
            "/admin/topics/authorization",
            headers=ADMIN_HEADERS,
            json={
                "consumer_authorization": {"c1": ["topicA", "topicB"]},
                "expected_generation": True,
            },
        )
        assert resp.status_code == 422
        assert "expected_generation must be int" in resp.json()["detail"]
        assert current_generation() is before

    def test_response_includes_persistent_and_changed(
        self, admin_client: TestClient
    ) -> None:
        """Runtime-only default: persistent is always false; changed reflects whether config changed."""
        before = _require_generation()
        resp = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA", "topicB"]}},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["persistent"] is False
        assert data["changed"] is True
        assert data["previous_generation"] == before.generation
        assert data["new_generation"] == before.generation + 1

    def test_response_changed_false_when_noop(self, admin_client: TestClient) -> None:
        """When body has keys but no actual change, changed=false."""
        # First update to establish state
        post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA"]}},
            headers=ADMIN_HEADERS,
        )
        # Same body again — no-op
        resp = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA"]}},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["changed"] is False

    def test_audit_emitted_on_effective_change(self, admin_client: TestClient) -> None:
        """Effective change emits one redacted log_privileged_action; no-op emits none."""
        from unittest.mock import patch

        before = _require_generation()
        with patch("eventbus.admin_route.log_privileged_action") as mock_log:
            resp = post_topics_authorization(
                admin_client,
                {"consumer_authorization": {"c1": ["topicA", "topicB"]}},
                headers=ADMIN_HEADERS,
            )
            assert resp.status_code == 200
            assert mock_log.call_count == 1
            call_args = mock_log.call_args
            assert call_args.kwargs["request_id"] != ""
            assert call_args.kwargs["actor"] == _derive_token_fingerprint("admin-tok")
            assert call_args.kwargs["target"] == "topics_authorization"
            assert (
                call_args.kwargs["detail"]
                == f"consumer_authorization:1;persistent:false;gen:{before.generation}->{before.generation + 1}"
            )

    def test_audit_not_emitted_on_noop(self, admin_client: TestClient) -> None:
        """No-op does not emit audit record."""
        from unittest.mock import patch

        # Establish state first
        post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA"]}},
            headers=ADMIN_HEADERS,
        )
        with patch("eventbus.admin_route.log_privileged_action") as mock_log:
            resp = post_topics_authorization(
                admin_client,
                {"consumer_authorization": {"c1": ["topicA"]}},
                headers=ADMIN_HEADERS,
            )
            assert resp.status_code == 200
            assert mock_log.call_count == 0


class TestGenerationConflict:
    """AC-1: expected_generation optimistic concurrency."""

    def test_same_expected_generation_second_request_409(
        self, admin_client: TestClient
    ) -> None:
        """Two updates carrying the same expected_generation: one 200, one 409
        generation_conflict; the rejected request changes nothing."""
        from unittest.mock import patch

        from eventbus import app as eb_app

        expected = _require_generation().generation

        ok = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA", "topicB"]}},
            expected_generation=expected,
            headers=ADMIN_HEADERS,
        )
        assert ok.status_code == 200

        state_before = _require_generation()
        with patch("eventbus.admin_route.log_privileged_action") as mock_log:
            conflict = post_topics_authorization(
                admin_client,
                {"consumer_authorization": {"c1": ["topicA", "topicC"]}},
                expected_generation=expected,
                headers=ADMIN_HEADERS,
            )

        assert conflict.status_code == 409
        assert conflict.json() == {
            "error": "generation_conflict",
            "expected_generation": expected,
            "current_generation": expected + 1,
        }
        assert mock_log.call_count == 0
        after = current_generation()
        assert after is state_before
        assert eb_app.app.state.config is state_before.config
        assert principal_map() is state_before.principals

    def test_stale_expected_generation_on_noop_body_still_409(
        self, admin_client: TestClient
    ) -> None:
        """REQ-007: a stale expected_generation on an otherwise no-op body is
        rejected with 409 before change detection."""
        current = _require_generation()
        body = {"consumer_authorization": {"c1": ["topicA"]}}
        resp = post_topics_authorization(
            admin_client,
            body,
            expected_generation=current.generation + 1,
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 409
        assert resp.json()["error"] == "generation_conflict"
        assert current_generation() is current


class TestResponseContract:
    """REQ-003 / AC-6: additive generation fields on every success response."""

    def test_effective_response_carries_generation_fields(
        self, admin_client: TestClient
    ) -> None:
        before = _require_generation()
        resp = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA", "topicB"]}},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["persistent"] is False
        assert data["changed"] is True
        assert data["previous_generation"] == before.generation
        assert data["new_generation"] == before.generation + 1
        assert data["changed_count"] == 1
        assert data["effective_at"] >= before.effective_at
        after = _require_generation()
        assert data["baseline_hash"] == after.baseline_hash
        assert len(data["baseline_hash"]) == 64

    def test_noop_response_generation_fields(self, admin_client: TestClient) -> None:
        """A no-op reports changed_count 0 with previous_generation == new_generation."""
        current = _require_generation()
        resp = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA"]}},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["changed"] is False
        assert data["changed_count"] == 0
        assert data["previous_generation"] == current.generation
        assert data["new_generation"] == current.generation
        assert data["effective_at"] == current.effective_at
        assert data["baseline_hash"] == current.baseline_hash


class TestTTLValidation:
    """REQ-005: ttl_seconds validation and grant registration."""

    @pytest.mark.parametrize(
        "ttl",
        [0, -1, 86401, "3600", True],
    )
    def test_invalid_ttl_rejected_without_state_change(
        self, admin_client: TestClient, ttl: Any
    ) -> None:
        before = _require_generation()
        from unittest.mock import patch

        with patch("eventbus.admin_route.log_privileged_action") as mock_log:
            resp = post_topics_authorization(
                admin_client,
                {"consumer_authorization": {"c1": ["topicA", "topicB"]}},
                ttl_seconds=ttl,
                headers=ADMIN_HEADERS,
            )
        assert resp.status_code == 422
        assert "ttl_seconds" in resp.json()["detail"]
        assert mock_log.call_count == 0
        after = current_generation()
        assert after is before
        assert after.expiries == frozenset()

    def test_valid_ttl_grant_published(self, admin_client: TestClient) -> None:
        """A valid ttl_seconds registers an expiry entry for newly granted pairs."""
        before = _require_generation()
        resp = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA", "topicB"]}},
            ttl_seconds=3600,
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        effective_at = resp.json()["effective_at"]
        after = _require_generation()
        assert after.generation == before.generation + 1
        new_entries = after.expiries - before.expiries
        assert {(c, t) for c, t, _ in new_entries} == {("c1", "topicB")}
        (_, _, expires_at) = next(iter(new_entries))
        assert expires_at == pytest.approx(effective_at + 3600, abs=1)

    def test_ttl_not_applied_to_carried_over_pairs(
        self, admin_client: TestClient
    ) -> None:
        """Pairs already in force keep no new expiry entry (carry-over, REQ-005)."""
        resp = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA"]}},
            ttl_seconds=3600,
            headers=ADMIN_HEADERS,
        )
        # Body matches the baseline grant -> no-op -> no generation, no expiries.
        assert resp.status_code == 200
        assert resp.json()["changed"] is False
        assert _require_generation().expiries == frozenset()


class TestAuditGenerationFields:
    """REQ-004: audit record carries previous_generation/new_generation."""

    def test_audit_generation_kwargs_on_effective_change(
        self, admin_client: TestClient
    ) -> None:
        from unittest.mock import patch

        before = _require_generation()
        with patch("eventbus.admin_route.log_privileged_action") as mock_log:
            resp = post_topics_authorization(
                admin_client,
                {"consumer_authorization": {"c1": ["topicA", "topicB"]}},
                headers=ADMIN_HEADERS,
            )
        assert resp.status_code == 200
        call_args = mock_log.call_args
        assert call_args.kwargs["previous_generation"] == before.generation
        assert call_args.kwargs["new_generation"] == before.generation + 1

    def test_audit_generation_kwargs_absent_on_noop(
        self, admin_client: TestClient
    ) -> None:
        from unittest.mock import patch

        with patch("eventbus.admin_route.log_privileged_action") as mock_log:
            resp = post_topics_authorization(
                admin_client,
                {"consumer_authorization": {"c1": ["topicA"]}},
                headers=ADMIN_HEADERS,
            )
        assert resp.status_code == 200
        assert resp.json()["changed"] is False
        assert mock_log.call_count == 0


class TestUpdateTakesEffect:
    def test_update_reflected_in_subsequent_subscribe_authorization(
        self, admin_client: TestClient
    ) -> None:

        resp = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA", "topicB"]}},
            headers=ADMIN_HEADERS,
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
        good = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA"]}},
            headers=ADMIN_HEADERS,
        )
        assert good.status_code == 200

        # Send an invalid update (wrong type for the topics list).
        bad = admin_client.post(
            "/admin/topics/authorization",
            headers=ADMIN_HEADERS,
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
        gen_before = _require_generation()

        def _boom(config: Any) -> Any:
            raise ValueError("principal build failed")

        monkeypatch.setattr("eventbus.admin_route._build_principal_map", _boom)
        failing = TestClient(admin_client.app, raise_server_exceptions=False)
        resp = failing.post(
            "/admin/topics/authorization",
            headers=ADMIN_HEADERS,
            json={
                "consumer_authorization": {"c1": ["topicB"]},
                "expected_generation": gen_before.generation,
            },
        )

        assert resp.status_code == 500
        assert eb_app.app.state.config is config_before
        assert principal_map() is map_before
        # AC-3: the failed rebuild publishes nothing — generation number and
        # baseline hash are unchanged.
        after = _require_generation()
        assert after is gen_before
        assert after.generation == gen_before.generation
        assert after.baseline_hash == gen_before.baseline_hash

    def test_noop_update_publishes_nothing(self, admin_client: TestClient) -> None:
        from eventbus import app as eb_app

        config_before = eb_app.app.state.config
        map_before = principal_map()

        resp = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA"]}},
            headers=ADMIN_HEADERS,
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
        gen_before = _require_generation()

        resp = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicB"]}},
            headers=ADMIN_HEADERS,
        )

        assert resp.status_code == 200
        assert resp.json()["changed"] is True
        assert resp.json()["new_generation"] == gen_before.generation + 1
        assert eb_app.app.state.config is not config_before
        assert principal_map() is not map_before
        assert principal_map()["consumer-tok"].consumer_grants == frozenset(
            {("c1", "topicB")}
        )


class TestUpdateRemovesPairs:
    def test_update_removes_pairs_no_longer_configured(
        self, admin_client: TestClient
    ) -> None:
        first = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA", "topicB"]}},
            headers=ADMIN_HEADERS,
        )
        assert first.status_code == 200
        second = post_topics_authorization(
            admin_client,
            {"consumer_authorization": {"c1": ["topicA"]}},
            headers=ADMIN_HEADERS,
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
        return current_generation()

    @staticmethod
    def _restore(snapshot):
        from eventbus.auth import publish_generation

        if snapshot is not None:
            publish_generation(snapshot)

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
        return current_generation()

    @staticmethod
    def _restore(snapshot):
        from eventbus.auth import publish_generation

        if snapshot is not None:
            publish_generation(snapshot)

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
