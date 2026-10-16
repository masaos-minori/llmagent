"""tests/mcp_servers/web_search/test_web_search_health_posture.py

Security Posture publication and the HTTP bind gate for
scripts/mcp_servers/web_search/web_search_server.py (REQ-002, REQ-003, REQ-015).

The posture is built once at module import from the already loaded config, so the gate is
startup-only and no later /health probe re-validates it (ADR-003 Static Availability).
tests/conftest.py sets MCP_WEB_SEARCH_AUTH_TOKEN to an empty string, so the shipped posture
carries common.auth_token as a warning and stays validated (Plan UNK-06).
"""

from __future__ import annotations

import dataclasses
import json
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient
from mcp_servers.web_search import web_search_server
from shared.security.posture_contract import SECURITY_CONTRACT_VERSION, SecurityPosture

_SERVER_CHECK_IDS = {
    "server.results_bounds",
    "server.search_timeout_valid",
    "server.browser_timeout_valid",
    "server.browser_response_limit",
    "server.browser_allowlist",
}
_FINGERPRINT_RE = re.compile(r"\A[0-9a-f]{64}\Z")


@pytest.fixture
def client() -> TestClient:
    """TestClient for the real web-search app, which needs no token in the test config."""
    return TestClient(web_search_server.app)


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


def _posture_with(monkeypatch: pytest.MonkeyPatch, **overrides: Any) -> SecurityPosture:
    """Rebuild the posture from a patched copy of the loaded config."""
    posture = web_search_server._build_security_posture(
        dataclasses.replace(web_search_server._cfg, **overrides)
    )
    monkeypatch.setattr(web_search_server, "_security_posture", posture)
    return posture


def _failed_checks(posture: SecurityPosture) -> dict[str, str]:
    """Return the failed check ids mapped to their reason codes."""
    return {
        check.check_id: check.reason_code
        for check in posture.checks
        if check.status.value == "failed"
    }


class TestPosturePublication:
    """AC-002: web-search-mcp publishes the posture on /health with no token or allowlist."""

    def test_health_body_carries_the_security_block(self, client: TestClient) -> None:
        block = _security_block(client)

        assert block["server_key"] == "web_search"
        assert block["contract_version"] == SECURITY_CONTRACT_VERSION
        assert block["validated"] is True

    def test_published_check_ids_cover_the_row_51_rules(
        self, client: TestClient
    ) -> None:
        assert _SERVER_CHECK_IDS <= set(_published_checks(client))

    def test_shipped_config_produces_a_validated_posture(self) -> None:
        posture = web_search_server._security_posture

        assert posture.validated is True
        assert posture.ready is True

    def test_shipped_deny_all_allowlist_is_published_as_not_applicable(
        self, client: TestClient
    ) -> None:
        assert _published_checks(client)["server.browser_allowlist"] == "not_applicable"

    def test_health_stays_200_with_no_dependency(self, client: TestClient) -> None:
        response = client.get("/health")

        assert response.status_code == 200
        body: dict[str, Any] = response.json()
        assert body["dependencies"] == {}
        assert body["ready"] is True

    def test_block_carries_no_token_or_allowlist_entry(
        self, client: TestClient
    ) -> None:
        text = json.dumps(_security_block(client), ensure_ascii=False)
        cfg = web_search_server._cfg
        forbidden = [cfg.auth_token, *cfg.browser_allowed_domains]

        assert all(value not in text for value in forbidden if value)


class TestFingerprintView:
    """The view row 51 defines carries scalars, a count, and a presence flag (REQ-009)."""

    def test_fingerprint_is_64_lowercase_hex(self) -> None:
        assert _FINGERPRINT_RE.match(web_search_server._security_posture.fingerprint)

    def test_fingerprint_changes_when_a_security_setting_changes(self) -> None:
        original = web_search_server._security_posture.fingerprint
        cfg = web_search_server._cfg
        patched = dataclasses.replace(
            cfg, browser_timeout_sec=cfg.browser_timeout_sec + 1
        )

        assert (
            web_search_server._build_security_posture(patched).fingerprint != original
        )

    def test_fingerprint_changes_when_the_allowlist_count_changes(self) -> None:
        original = web_search_server._security_posture.fingerprint
        cfg = web_search_server._cfg
        patched = dataclasses.replace(cfg, browser_allowed_domains=["example.com"])

        assert (
            web_search_server._build_security_posture(patched).fingerprint != original
        )


class TestBindGate:
    """AC-003: web-search-mcp does not bind HTTP when validation fails."""

    def test_validated_posture_does_not_block_bind(self) -> None:
        web_search_server._enforce_posture_gate()

    def test_non_positive_browser_timeout_is_a_startup_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _posture_with(monkeypatch, browser_timeout_sec=0)

        assert posture.validated is False
        assert (
            _failed_checks(posture)["server.browser_timeout_valid"] == "config_invalid"
        )

    def test_response_cap_above_the_ceiling_is_a_startup_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _posture_with(monkeypatch, browser_max_response_kb=0)

        assert (
            _failed_checks(posture)["server.browser_response_limit"] == "config_invalid"
        )

    def test_empty_allowlist_does_not_block_bind(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _posture_with(monkeypatch, browser_allowed_domains=[])

        assert posture.validated is True
        web_search_server._enforce_posture_gate()

    def test_gate_refuses_bind_and_logs_reason_codes(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        _posture_with(monkeypatch, browser_timeout_sec=0)

        with pytest.raises(SystemExit) as excinfo:
            web_search_server._enforce_posture_gate()

        assert excinfo.value.code == 1
        gate_lines = [
            record.getMessage()
            for record in caplog.records
            if "refusing to bind" in record.getMessage()
        ]
        assert gate_lines, "the gate did not log a refusal"
        assert "server.browser_timeout_valid:config_invalid" in gate_lines[0]

    def test_health_returns_503_when_the_posture_is_not_validated(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _posture_with(monkeypatch, browser_timeout_sec=0)
        response = client.get("/health")

        assert response.status_code == 503
        body: dict[str, Any] = response.json()
        assert body["status"] == "degraded"
        assert body["ready"] is False
        assert body["security"]["validated"] is False
