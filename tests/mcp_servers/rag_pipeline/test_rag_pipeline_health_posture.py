"""tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py

Security Posture publication and the HTTP bind gate for
scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py (REQ-002, REQ-003, REQ-010).

The posture is built once at module import from the already loaded config, so a probe-time
config failure in `_check_health_deps()` does not change it.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient
from mcp_servers.rag_pipeline import rag_pipeline_server
from shared.security.posture_contract import SECURITY_CONTRACT_VERSION, SecurityPosture

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

_RAG_CHECK_IDS = {
    "server.embed_url_configured",
    "server.llm_url_configured",
    "server.rag_db_path_configured",
    "server.sqlite_vec_available",
    "server.top_k_bounds",
    "server.min_score_valid",
    "server.refiner_limits",
}
_FINGERPRINT_RE = re.compile(r"\A[0-9a-f]{64}\Z")


@pytest.fixture
def client() -> TestClient:
    """TestClient for the real rag-pipeline app with the test-suite Bearer token."""
    return TestClient(rag_pipeline_server.app, headers=MCP_TEST_AUTH_HEADERS)


def _security_block(client: TestClient) -> dict[str, Any]:
    """Return the `security` block of a real /health response body."""
    body: dict[str, Any] = client.get("/health").json()
    block = body["security"]
    assert isinstance(block, dict)
    return block


def _published_checks(client: TestClient) -> dict[str, str]:
    """Return the published check ids mapped to their published status values."""
    return {
        str(check["id"]): str(check["status"])
        for check in _security_block(client)["checks"]
    }


def _posture_with(
    monkeypatch: pytest.MonkeyPatch, **overrides: object
) -> SecurityPosture:
    """Rebuild the posture with patched config values, then restore them."""
    cfg = rag_pipeline_server._cfg
    original = {name: getattr(cfg, name) for name in overrides}
    for name, value in overrides.items():
        setattr(cfg, name, value)
    try:
        posture = rag_pipeline_server._build_security_posture()
    finally:
        for name, value in original.items():
            setattr(cfg, name, value)
    monkeypatch.setattr(rag_pipeline_server, "_security_posture", posture)
    return posture


def _failed_checks(posture: SecurityPosture) -> dict[str, str]:
    """Return the failed check ids mapped to their reason codes."""
    return {
        check.check_id: check.reason_code
        for check in posture.checks
        if check.status.value == "failed"
    }


class TestPosturePublication:
    """AC-002: rag-pipeline-mcp publishes the posture on /health with no path or Secret."""

    def test_health_body_carries_the_security_block(self, client: TestClient) -> None:
        block = _security_block(client)

        assert block["server_key"] == "rag_pipeline"
        assert block["contract_version"] == SECURITY_CONTRACT_VERSION
        assert block["validated"] is True

    def test_published_check_ids_cover_rag_s_own_rules(
        self, client: TestClient
    ) -> None:
        assert _RAG_CHECK_IDS <= set(_published_checks(client))

    def test_disabled_refiner_limits_are_published_as_not_applicable(
        self, client: TestClient
    ) -> None:
        assert _published_checks(client)["server.refiner_limits"] == "not_applicable"

    def test_shipped_config_produces_a_validated_posture(self) -> None:
        posture = rag_pipeline_server._security_posture

        assert posture.validated is True
        assert posture.ready is True

    def test_block_carries_no_path_url_or_token(self, client: TestClient) -> None:
        text = json.dumps(_security_block(client), ensure_ascii=False)
        cfg = rag_pipeline_server._cfg
        forbidden = [
            cfg.auth_token,
            cfg.rag_db_path,
            cfg.sqlite_vec_so,
            cfg.llm_url,
            cfg.embed_url,
            cfg.mqe_prompt_template,
        ]

        assert all(value not in text for value in forbidden if value)


class TestFingerprintView:
    """The view row 46 defines hashes paths and hosts as presence booleans only (REQ-009)."""

    def test_view_carries_presence_booleans_instead_of_path_values(self) -> None:
        view = rag_pipeline_server._rag_security_view(rag_pipeline_server._cfg)

        assert view["rag_db_path_configured"] is bool(
            rag_pipeline_server._cfg.rag_db_path
        )
        assert view["sqlite_vec_so_configured"] is bool(
            rag_pipeline_server._cfg.sqlite_vec_so
        )
        strings = [value for value in view.values() if isinstance(value, str)]

        assert strings == [rag_pipeline_server.RAG_PIPELINE_OWN_CONFIG_FILE]

    def test_fingerprint_is_64_lowercase_hex(self) -> None:
        assert _FINGERPRINT_RE.match(rag_pipeline_server._security_posture.fingerprint)

    def test_fingerprint_changes_when_a_security_setting_changes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        original = rag_pipeline_server._security_posture.fingerprint
        cfg = rag_pipeline_server._cfg
        monkeypatch.setattr(cfg, "rag_top_k", cfg.rag_top_k + 1)

        assert rag_pipeline_server._build_security_posture().fingerprint != original


class TestBindGate:
    """AC-003: rag-pipeline-mcp does not bind HTTP when validation fails."""

    def test_validated_posture_does_not_block_bind(self) -> None:
        rag_pipeline_server._enforce_posture_gate()

    def test_missing_extension_makes_the_posture_unvalidated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _posture_with(monkeypatch, sqlite_vec_so="/nonexistent/vec0.so")

        assert posture.validated is False
        assert _failed_checks(posture)["server.sqlite_vec_available"] == (
            "dependency_unreachable"
        )

    def test_reversed_top_k_bounds_is_a_startup_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _posture_with(monkeypatch, rag_top_k=99)

        assert _failed_checks(posture)["server.top_k_bounds"] == "config_invalid"

    def test_gate_refuses_bind_and_logs_reason_codes(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        _posture_with(monkeypatch, sqlite_vec_so="/nonexistent/vec0.so")

        with pytest.raises(SystemExit) as excinfo:
            rag_pipeline_server._enforce_posture_gate()

        assert excinfo.value.code == 1
        message = "\n".join(record.getMessage() for record in caplog.records)
        assert "server.sqlite_vec_available:dependency_unreachable" in message
        assert "refusing to bind" in message
        assert "/nonexistent/vec0.so" not in message

    def test_health_returns_503_when_the_posture_is_not_validated(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _posture_with(monkeypatch, sqlite_vec_so="/nonexistent/vec0.so")
        response = client.get("/health")

        assert response.status_code == 503
        body: dict[str, Any] = response.json()
        assert body["dependencies"] == {}
        assert body["ready"] is False
        assert body["security"]["validated"] is False
