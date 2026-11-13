"""tests/eventbus/test_authz_generation_ttl.py
EBAUTHGEN001 Phase 2: generation semantics, TTL expiry sweep, and restart
baseline audit. Deterministic under the injected clock — no wall-clock sleeps.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import pytest
from eventbus.auth import AuthzGeneration, current_generation
from eventbus.authz_ttl import sweep_expired_authorizations
from eventbus.config import authorization_baseline_hash
from fastapi.testclient import TestClient

from tests.eventbus.eventbus_helpers import (
    current_principals,
    eventbus_test_config,
    eventbus_test_tokens,
    injectable_clock,
    post_topics_authorization,
    reset_generation_state,  # noqa: F401 — fixture import for this module
)

TEST_TOKENS = eventbus_test_tokens()
ADMIN_AUTH = {"Authorization": f"Bearer {TEST_TOKENS['auth_token']}"}
CONSUMER_TOKEN = TEST_TOKENS["consumer_token"]


@pytest.fixture()
def gen_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Production-lifespan TestClient through the shared eventbus helpers."""
    from tests.eventbus.eventbus_helpers import make_eventbus_client

    with make_eventbus_client(tmp_path, monkeypatch) as client:
        yield client


def _require_generation() -> AuthzGeneration:
    generation = current_generation()
    assert generation is not None
    return generation


class TestGenerationSemantics:
    def test_generation_monotonicity(self, gen_client: TestClient) -> None:
        """REQ-001/AC-1: N effective updates publish strictly increasing
        generation numbers, one generation object per update."""
        seen = [_require_generation()]
        topics = ["ttl-t1", "ttl-t2", "ttl-t3"]
        for i, topic in enumerate(topics, start=1):
            resp = post_topics_authorization(
                gen_client,
                {"consumer_authorization": {"c1": topics[:i]}},
                headers=ADMIN_AUTH,
            )
            assert resp.status_code == 200
            assert resp.json()["changed"] is True
            after = _require_generation()
            assert after is not seen[-1]
            assert after.generation == seen[-1].generation + 1
            seen.append(after)
        numbers = [gen.generation for gen in seen]
        assert numbers == sorted(numbers)
        assert len(set(numbers)) == len(numbers)

    def test_snapshot_immutability(self, gen_client: TestClient) -> None:
        """REQ-001: the published AuthzGeneration is frozen; two reads return
        the identical object between publications."""
        gen = _require_generation()
        assert current_generation() is gen
        with pytest.raises(dataclasses.FrozenInstanceError):
            gen.generation = gen.generation + 1  # type: ignore[misc]  # — the assignment to a frozen dataclass field is the behavior under test
        with pytest.raises(dataclasses.FrozenInstanceError):
            gen.baseline_hash = "0" * 64  # type: ignore[misc]  # — the assignment to a frozen dataclass field is the behavior under test
        assert current_generation() is gen

    def test_racing_updates_publish_one_generation(
        self, gen_client: TestClient
    ) -> None:
        """REQ-002 at the generation-object level: a 409-rejected update leaves
        the in-force generation object untouched."""
        before = _require_generation()
        ok = post_topics_authorization(
            gen_client,
            {"consumer_authorization": {"c1": ["race-topic"]}},
            expected_generation=before.generation,
            headers=ADMIN_AUTH,
        )
        assert ok.status_code == 200
        published = _require_generation()
        conflict = post_topics_authorization(
            gen_client,
            {"consumer_authorization": {"c1": ["other-topic"]}},
            expected_generation=before.generation,
            headers=ADMIN_AUTH,
        )
        assert conflict.status_code == 409
        assert current_generation() is published


class TestTTLExpirySweep:
    def test_expiry_publishes_one_removal_generation(
        self, gen_client: TestClient
    ) -> None:
        """REQ-005/AC-2: injected clock past expiry -> exactly one new
        generation, the pair gone from grants, one ttl_expiry audit record."""
        from unittest.mock import patch

        before = _require_generation()
        resp = post_topics_authorization(
            gen_client,
            {"consumer_authorization": {"c1": ["ttl-topic"]}},
            ttl_seconds=3600,
            headers=ADMIN_AUTH,
        )
        assert resp.status_code == 200
        effective_at = resp.json()["effective_at"]
        granted = _require_generation()
        assert ("c1", "ttl-topic") in current_principals()[
            CONSUMER_TOKEN
        ].consumer_grants

        clock, advance = injectable_clock(start=effective_at)
        # Not yet expired: the sweep publishes nothing.
        assert sweep_expired_authorizations(gen_client.app, clock) is None
        assert current_generation() is granted

        advance(3601)
        with patch("eventbus.authz_ttl.log_authorization_change") as mock_log:
            new_gen = sweep_expired_authorizations(gen_client.app, clock)

        assert new_gen is not None
        assert current_generation() is new_gen
        assert new_gen.generation == granted.generation + 1
        assert ("c1", "ttl-topic") not in current_principals()[
            CONSUMER_TOKEN
        ].consumer_grants
        assert new_gen.expiries == frozenset()
        assert mock_log.call_count == 1
        call_args = mock_log.call_args
        assert call_args.kwargs["consumer_id"] == "system"
        assert call_args.kwargs["target"] == "ttl_expiry"
        assert call_args.kwargs["route"] == "/ttl_sweep"
        assert call_args.kwargs["previous_generation"] == granted.generation
        assert call_args.kwargs["new_generation"] == new_gen.generation
        assert before.generation <= granted.generation

    def test_sweep_with_no_expired_pairs_publishes_nothing(
        self, gen_client: TestClient
    ) -> None:
        from unittest.mock import patch

        resp = post_topics_authorization(
            gen_client,
            {"consumer_authorization": {"c1": ["ttl-topic"]}},
            ttl_seconds=3600,
            headers=ADMIN_AUTH,
        )
        assert resp.status_code == 200
        granted = _require_generation()
        clock, _ = injectable_clock(start=resp.json()["effective_at"])
        with patch("eventbus.authz_ttl.log_authorization_change") as mock_log:
            assert sweep_expired_authorizations(gen_client.app, clock) is None
        assert mock_log.call_count == 0
        assert current_generation() is granted

    def test_sweep_aborts_on_concurrent_generation_bump(
        self,
        gen_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
        reset_generation_state: None,  # noqa: F811 — pytest fixture injection
    ) -> None:
        """Plan Risk: a generation bump during the sweep aborts the cycle; no
        out-of-order publish, the bumped generation stays in force."""
        from unittest.mock import patch

        import eventbus.auth as auth_module

        granted = _require_generation()

        def _bump_then_build(config: Any) -> Any:
            # Simulate a concurrent admin publish while this cycle is building.
            auth_module.publish_generation(
                dataclasses.replace(granted, generation=granted.generation + 100)
            )
            return auth_module._build_principal_map(config)

        monkeypatch.setattr("eventbus.authz_ttl._build_principal_map", _bump_then_build)
        clock, advance = injectable_clock(start=granted.effective_at)
        # Register an already-pending expiry so the sweep reaches the build.
        resp = post_topics_authorization(
            gen_client,
            {"consumer_authorization": {"c1": ["ttl-topic"]}},
            ttl_seconds=3600,
            headers=ADMIN_AUTH,
        )
        assert resp.status_code == 200
        granted = _require_generation()
        advance(3601)
        with patch("eventbus.authz_ttl.log_authorization_change") as mock_log:
            result = sweep_expired_authorizations(gen_client.app, clock)

        assert result is None
        assert mock_log.call_count == 0
        bumped = _require_generation()
        assert bumped.generation == granted.generation + 100
        # The bump did not remove the grant: the sweep aborted before publishing.
        assert ("c1", "ttl-topic") in current_principals()[
            CONSUMER_TOKEN
        ].consumer_grants

    def test_failed_rebuild_keeps_generation_unchanged(
        self,
        gen_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """REQ-001/AC-3: a failing principal build during removal aborts the
        cycle; number, config, principals, and hash are unchanged."""
        from eventbus import app as eb_app

        resp = post_topics_authorization(
            gen_client,
            {"consumer_authorization": {"c1": ["ttl-topic"]}},
            ttl_seconds=3600,
            headers=ADMIN_AUTH,
        )
        assert resp.status_code == 200
        granted = _require_generation()
        config_before = eb_app.app.state.config
        map_before = current_principals()

        def _boom(config: Any) -> Any:
            raise ValueError("principal build failed")

        monkeypatch.setattr("eventbus.authz_ttl._build_principal_map", _boom)
        clock, advance = injectable_clock(start=granted.effective_at)
        advance(3601)
        with pytest.raises(ValueError, match="principal build failed"):
            sweep_expired_authorizations(gen_client.app, clock)

        assert current_generation() is granted
        assert granted.generation == _require_generation().generation
        assert granted.baseline_hash == _require_generation().baseline_hash
        assert eb_app.app.state.config is config_before
        assert current_principals() is map_before


class TestRestartBaselineAudit:
    def test_startup_emits_one_authz_baseline_record(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """REQ-006/AC-4: each lifespan startup emits one authz_baseline audit
        record carrying the loaded baseline hash; state is baseline-only."""
        from unittest.mock import patch

        from eventbus import app as eb_app

        cfg = eventbus_test_config(tmp_path)
        monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
        schema_path = (
            Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
        )
        monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
        monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

        with patch("eventbus.app.log_privileged_action") as mock_log:
            with TestClient(eb_app.app):
                pass
            startup_records = [
                call
                for call in mock_log.call_args_list
                if call.kwargs.get("target") == "authz_baseline"
            ]
            assert len(startup_records) == 1
            record = startup_records[0].kwargs
            assert record["consumer_id"] == "system"
            assert record["route"] == "/startup"
            assert record["request_id"] == ""
            baseline_hash = authorization_baseline_hash(cfg)
            assert record["detail"] == (
                f"baseline_hash:{baseline_hash};runtime_overrides:removed"
            )

            # Second startup: baseline-only state again, one record per startup.
            with TestClient(eb_app.app):
                pass
            startup_records = [
                call
                for call in mock_log.call_args_list
                if call.kwargs.get("target") == "authz_baseline"
            ]
            assert len(startup_records) == 2
            gen = _require_generation()
            assert gen.baseline_hash == authorization_baseline_hash(cfg)
            assert gen.expiries == frozenset()


class TestBaselineHashInvariance:
    def test_permuted_pair_sets_hash_equal(self, tmp_path: Path) -> None:
        """Plan Risk: the baseline hash is invariant to pair ordering in the mapping."""
        base = eventbus_test_config(tmp_path)

        cfg_a = dataclasses.replace(
            base,
            consumer_authorization={"c1": ["t1", "t2"]},
        )
        cfg_b = dataclasses.replace(
            base,
            consumer_authorization={"c1": ["t2", "t1"]},
        )
        cfg_c = dataclasses.replace(
            base,
            consumer_authorization={"c1": ["t1", "t2"]},
        )
        assert authorization_baseline_hash(cfg_a) == authorization_baseline_hash(cfg_b)
        assert authorization_baseline_hash(cfg_a) == authorization_baseline_hash(cfg_c)
