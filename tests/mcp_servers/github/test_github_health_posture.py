"""tests/mcp_servers/github/test_github_health_posture.py

Security Posture publication and the HTTP bind gate for
scripts/mcp_servers/github/github_server.py (REQ-002, REQ-003, REQ-007).

The posture is built once at module import from the already loaded config. The GitHub API
token stays a `dependencies` signal, so tests that assert a healthy payload patch
`_GITHUB_TOKEN` the same way tests/mcp_servers/github/test_github_server_endpoints.py does.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient
from mcp_servers.github import github_server
from shared.security.posture_contract import SECURITY_CONTRACT_VERSION, SecurityPosture

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

_GITHUB_CHECK_IDS = {
    "server.repo_allowlist",
    "server.force_push_policy",
    "server.pr_review_required",
    "server.protected_branches",
    "server.path_denylist",
    "server.max_file_size",
    "server.audit_log_writable",
    "server.per_page_bounds",
}
_FINGERPRINT_RE = re.compile(r"\A[0-9a-f]{64}\Z")
_TOKEN_SENTINEL = "ghp_sentinel_token_must_not_appear_in_the_posture"


@pytest.fixture
def client() -> TestClient:
    """TestClient for the real github app with the test-suite Bearer token."""
    return TestClient(github_server.app, headers=MCP_TEST_AUTH_HEADERS)


def _security_block(client: TestClient) -> dict[str, Any]:
    """Return the `security` block of a real /health response body."""
    body: dict[str, Any] = client.get("/health").json()
    block = body["security"]
    assert isinstance(block, dict)
    return block


def _published_check_ids(client: TestClient) -> set[str]:
    """Return the check ids the published block carries."""
    return {str(check["id"]) for check in _security_block(client)["checks"]}


def _posture_with(
    monkeypatch: pytest.MonkeyPatch, **overrides: object
) -> SecurityPosture:
    """Rebuild the posture with patched config values, then restore them."""
    cfg = github_server._cfg
    original = {name: getattr(cfg, name) for name in overrides}
    for name, value in overrides.items():
        setattr(cfg, name, value)
    try:
        posture = github_server._build_security_posture()
    finally:
        for name, value in original.items():
            setattr(cfg, name, value)
    monkeypatch.setattr(github_server, "_security_posture", posture)
    return posture


class TestPosturePublication:
    """AC-002: github-mcp publishes the posture on /health with no Secret in it."""

    def test_health_body_carries_the_security_block(self, client: TestClient) -> None:
        block = _security_block(client)

        assert block["server_key"] == "github"
        assert block["contract_version"] == SECURITY_CONTRACT_VERSION
        assert block["validated"] is True

    def test_published_check_ids_cover_github_s_own_rules(
        self, client: TestClient
    ) -> None:
        published = _published_check_ids(client)

        assert _GITHUB_CHECK_IDS <= published

    def test_shipped_config_produces_a_validated_posture(self) -> None:
        posture = github_server._security_posture

        assert posture.validated is True
        assert posture.ready is True

    def test_block_carries_no_repo_name_token_or_denylist_entry(
        self, client: TestClient
    ) -> None:
        text = json.dumps(_security_block(client), ensure_ascii=False)
        cfg = github_server._cfg
        forbidden = [
            cfg.auth_token,
            cfg.audit_log_path,
            cfg.llm_url,
            *cfg.allowed_repos,
            *cfg.path_denylist,
        ]

        assert all(value not in text for value in forbidden if value)

    def test_github_api_token_is_not_a_posture_input(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(github_server, "_GITHUB_TOKEN", _TOKEN_SENTINEL)
        text = json.dumps(_security_block(client), ensure_ascii=False)

        assert _TOKEN_SENTINEL not in text


class TestWarningOnlySettingsStayStartable:
    """Row 09 keeps warning-only policy settings WARNING, so the gate does not fire."""

    def test_force_push_and_pr_review_warnings_keep_validated_true(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _posture_with(
            monkeypatch, allow_force_push=True, require_pr_review=False
        )

        statuses = {check.check_id: check.status.value for check in posture.checks}
        assert statuses["server.force_push_policy"] == "warning"
        assert statuses["server.pr_review_required"] == "warning"
        assert posture.validated is True

    def test_gate_does_not_fire_for_warnings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _posture_with(monkeypatch, allow_force_push=True)

        github_server._enforce_posture_gate()


class TestFingerprintView:
    """The view row 44 defines is scalars and counts only (REQ-009)."""

    def test_view_carries_counts_instead_of_list_values(self) -> None:
        view = github_server._github_security_view(github_server._cfg)

        assert view["allowed_repos_count"] == len(github_server._cfg.allowed_repos)
        assert view["llm_url_configured"] is bool(github_server._cfg.llm_url)
        assert not any(isinstance(value, list) for value in view.values())

    def test_fingerprint_is_64_lowercase_hex(self) -> None:
        assert _FINGERPRINT_RE.match(github_server._security_posture.fingerprint)

    def test_fingerprint_changes_when_a_security_setting_changes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        original = github_server._security_posture.fingerprint
        cfg = github_server._cfg
        monkeypatch.setattr(cfg, "max_per_page", cfg.max_per_page + 1)

        assert github_server._build_security_posture().fingerprint != original


class TestBindGate:
    """AC-003: github-mcp does not bind HTTP when validation fails."""

    def test_validated_posture_does_not_block_bind(self) -> None:
        github_server._enforce_posture_gate()

    def test_empty_repo_allowlist_makes_the_posture_unvalidated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _posture_with(monkeypatch, allowed_repos=[])

        assert posture.validated is False
        failed = {
            check.check_id for check in posture.checks if check.status.value == "failed"
        }
        assert "server.repo_allowlist" in failed

    def test_gate_refuses_bind_and_logs_reason_codes(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        _posture_with(monkeypatch, allowed_repos=[])

        with pytest.raises(SystemExit) as excinfo:
            github_server._enforce_posture_gate()

        assert excinfo.value.code == 1
        message = "\n".join(record.getMessage() for record in caplog.records)
        assert "server.repo_allowlist:allowlist_empty" in message
        assert "refusing to bind" in message

    def test_health_returns_503_when_the_posture_is_not_validated(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(github_server, "_GITHUB_TOKEN", "ghp_test_token")
        _posture_with(monkeypatch, allowed_repos=[])
        response = client.get("/health")

        assert response.status_code == 503
        body: dict[str, Any] = response.json()
        assert body["dependencies"] == {}
        assert body["ready"] is False
        assert body["security"]["validated"] is False
