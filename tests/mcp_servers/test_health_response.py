"""tests/mcp_servers/test_health_response.py

Tests for scripts/mcp_servers/health_response.py: the payload is unchanged when no posture is
supplied, and the Security Posture contract is published verbatim when one is. The read-only dedup
metrics block is published only when a store and its config are wired (mcpdl005 REQ-004).
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import mcp_servers.dispatch as dispatch
import pytest
from fastapi.responses import JSONResponse
from mcp_servers.health_response import (
    HEALTH_STATUS_DEGRADED,
    HEALTH_STATUS_OK,
    dedup_health_details,
    make_health_response,
)
from shared.mcp_dedup import DedupStore, DedupStoreConfig
from shared.security.posture_contract import SECURITY_CONTRACT_VERSION, SecurityPosture
from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

BASE_KEYS = {
    "status",
    "ready",
    "liveness",
    "restart_recommended",
    "operator_action_required",
    "dependencies",
    "details",
}
POSTURE_KEYS = {
    "contract_version",
    "server_key",
    "policy_version",
    "validated",
    "ready",
    "fingerprint",
    "checks",
}
# The metric fields the health `details.dedup` block publishes (mcpdl005 REQ-004).
# A per-metric status block appears only when that metric's threshold key is configured.
DEDUP_METRIC_KEYS = {
    "schema_version",
    "db_path",
    "generated_epoch",
    "row_states",
    "pending_overdue",
    "growth_rows_per_hour",
    "wal_size_bytes",
    "legal_hold_states",
    "held_past_retention",
    "lock_wait_ms",
}
# Component-keyed snapshot (execution_snapshot.COMPONENT_KEYS shape).
_SNAP = {
    "deployed_rev": "deadbeef",
    "git_sha": "abcdef1",
    "config_hash": "cafef00d",
    "schema_versions": "rag=17;skill=8",
    "dedup": "gen=1;schema=deadbeef",
}


def _body(response: JSONResponse) -> dict[str, object]:
    """The decoded /health payload."""
    return json.loads(response.body)


@pytest.fixture()
def seeded_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[DedupStoreConfig]:
    """A tmp_path store with one row per state, wired into the dispatch globals.

    Every threshold stays unset unless the test names one, so the reported status is the
    configured one, not a default.
    """
    store_config = DedupStoreConfig(db_path=str(tmp_path / "mcp_dedup.sqlite"))
    store = DedupStore(str(store_config.db_path), config=store_config)
    now = time.time()
    old = now - 15 * 86400
    for key in ("kc", "kf", "ki", "kp"):
        store.try_acquire_execution(
            key, "web_search", f"h-{key}", _SNAP, "owner-a", now_epoch=old
        )
    store.record_completed("kc", _SNAP, "done", "owner-a", now_epoch=old)
    store.record_failed("kf", "timeout", "owner-a", now_epoch=old)
    store.mark_interrupted("ki", "owner-a", now_epoch=old)
    monkeypatch.setattr(dispatch, "_dedup_store", store)
    monkeypatch.setattr(dispatch, "_dedup_config", store_config)
    yield store_config
    store.close()


def _posture(*, validated: bool) -> SecurityPosture:
    """A shell posture whose one check follows the requested verdict."""
    check = SecurityCheckResult(
        check_id="server.command_allowlist",
        status=SecurityCheckStatus.OK if validated else SecurityCheckStatus.FAILED,
        reason_code=REASON_OK if validated else REASON_ALLOWLIST_EMPTY,
        message="command allowlist checked",
    )
    return SecurityPosture(
        contract_version=SECURITY_CONTRACT_VERSION,
        server_key="shell",
        policy_version="1",
        validated=validated,
        ready=validated,
        fingerprint="0" * 64,
        checks=(check,),
    )


class TestPayloadWithoutPosture:
    """A server that passes no posture publishes exactly what it published before."""

    def test_no_posture_publishes_only_the_existing_keys(self) -> None:
        body = _body(make_health_response({}, {"service": "shell-mcp"}))

        assert set(body) == BASE_KEYS
        assert "security" not in body

    def test_no_posture_keeps_a_healthy_server_ready(self) -> None:
        response = make_health_response({}, {"service": "shell-mcp"})

        assert response.status_code == 200
        assert _body(response)["status"] == HEALTH_STATUS_OK
        assert _body(response)["ready"] is True

    def test_no_posture_still_degrades_on_a_dependency_failure(self) -> None:
        response = make_health_response({"db": "unreachable"}, None)
        body = _body(response)

        assert response.status_code == 503
        assert body["status"] == HEALTH_STATUS_DEGRADED
        assert body["ready"] is False
        assert body["operator_action_required"] is True
        assert body["details"] == {}

    def test_the_existing_two_argument_call_form_still_works(self) -> None:
        body = _body(make_health_response({}, {}))

        assert body["dependencies"] == {}
        assert body["details"] == {}


class TestPosturePublication:
    """A server that passes a posture publishes it and lets it decide readiness (REQ-002)."""

    def test_a_validated_posture_adds_the_security_block(self) -> None:
        body = _body(make_health_response({}, {}, security=_posture(validated=True)))

        assert set(body) == BASE_KEYS | {"security"}

    def test_the_security_block_carries_the_contract_field_names(self) -> None:
        body = _body(make_health_response({}, {}, security=_posture(validated=True)))

        assert set(body["security"]) == POSTURE_KEYS

    def test_the_security_block_is_the_posture_published_verbatim(self) -> None:
        posture = _posture(validated=True)
        body = _body(make_health_response({}, {}, security=posture))

        assert body["security"] == posture.to_dict()

    def test_a_failed_posture_makes_the_server_not_ready(self) -> None:
        response = make_health_response({}, {}, security=_posture(validated=False))
        body = _body(response)

        assert response.status_code == 503
        assert body["status"] == HEALTH_STATUS_DEGRADED
        assert body["ready"] is False
        assert body["restart_recommended"] is False

    def test_a_validated_posture_does_not_hide_a_dependency_failure(self) -> None:
        response = make_health_response(
            {"db": "unreachable"},
            {},
            security=_posture(validated=True),
        )

        assert response.status_code == 503
        assert _body(response)["ready"] is False

    def test_the_published_block_carries_no_config_path_or_token(self) -> None:
        body = json.dumps(
            _body(make_health_response({}, {}, security=_posture(validated=True)))
        )

        assert "/opt/llm" not in body
        assert "sk-" not in body


class TestDedupHealthDetails:
    """The metrics block appears only when a store and its config are wired (REQ-004)."""

    def test_an_unwired_dispatcher_publishes_no_block(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(dispatch, "_dedup_store", None)
        monkeypatch.setattr(dispatch, "_dedup_config", None)

        # The default is an empty mapping and nothing raises, so /health still answers.
        assert dedup_health_details() == {}
        assert _body(make_health_response({}, {}))["details"] == {}

    def test_a_wired_store_publishes_the_documented_metric_fields(
        self, seeded_store: DedupStoreConfig
    ) -> None:
        block = dedup_health_details()["dedup"]

        assert isinstance(block, dict)
        assert set(block) == DEDUP_METRIC_KEYS
        # D-6: with no threshold configured there is no status block at all.
        assert not (set(block) & {"rows", "growth", "wal"})
        assert block["row_states"] == {
            "completed": 1,
            "failed": 1,
            "interrupted": 1,
            "pending": 1,
        }
        assert block["legal_hold_states"] == []

    def test_only_a_set_and_breached_threshold_adds_its_status_block(
        self, seeded_store: DedupStoreConfig, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The seeded store holds 4 rows; only the row-count threshold is set, so only that
        # metric reports a status and the other fields stay as they are.
        configured = replace(seeded_store, max_dedup_rows=1)
        monkeypatch.setattr(dispatch, "_dedup_config", configured)
        block = dedup_health_details()["dedup"]

        assert set(block) == DEDUP_METRIC_KEYS | {"rows"}
        assert block["rows"] == {"value": 4, "threshold": 1, "status": "fail"}

    def test_the_response_builder_publishes_the_block_under_dedup(
        self, seeded_store: DedupStoreConfig
    ) -> None:
        block = dedup_health_details()
        body = _body(make_health_response({}, {"service": "web-search-mcp", **block}))

        # The payload the builder publishes is unchanged; the block sits only inside details.
        assert set(body) == BASE_KEYS
        assert body["details"]["service"] == "web-search-mcp"
        assert set(body["details"]["dedup"]) == DEDUP_METRIC_KEYS
        text = json.dumps(body)
        assert "/opt/llm" not in text
        assert "sk-" not in text
