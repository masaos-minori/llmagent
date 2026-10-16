"""tests/mcp_servers/git/test_git_health_posture.py

Security Posture publication and the HTTP bind gate for
scripts/mcp_servers/git/git_server.py (REQ-002, REQ-003, REQ-005).

The posture is built once at module import from the already loaded config, so these
tests read the module-level posture, the published `security` block, and the gate that
runs before `run_http()`.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient
from mcp_servers.git import git_server
from shared.security.posture_contract import SECURITY_CONTRACT_VERSION, SecurityPosture

_GIT_CHECK_IDS = {
    "server.repo_allowlist",
    "server.repo_allowlist_resolvable",
    "server.read_only_mode",
    "server.protected_branch_config",
}
_FINGERPRINT_RE = re.compile(r"\A[0-9a-f]{64}\Z")


@pytest.fixture
def client() -> TestClient:
    """TestClient for the real git app; git-mcp keeps the empty-token accept-all path."""
    return TestClient(git_server.app)


def _security_block(client: TestClient) -> dict[str, Any]:
    """Return the `security` block of a real /health response body."""
    body: dict[str, Any] = client.get("/health").json()
    block = body["security"]
    assert isinstance(block, dict)
    return block


def _published_check_ids(client: TestClient) -> set[str]:
    """Return the check ids the published block carries."""
    return {str(check["id"]) for check in _security_block(client)["checks"]}


def _unvalidated_posture(monkeypatch: pytest.MonkeyPatch) -> SecurityPosture:
    """Empty the repository allowlist, rebuild the posture, and restore the config."""
    cfg = git_server._cfg
    original = list(cfg.allowed_repo_paths)
    cfg.allowed_repo_paths = []
    try:
        posture = git_server._build_security_posture()
    finally:
        cfg.allowed_repo_paths = original
    monkeypatch.setattr(git_server, "_security_posture", posture)
    return posture


class TestPosturePublication:
    """AC-002: git-mcp publishes the posture on /health with no secret in it."""

    def test_health_body_carries_the_security_block(self, client: TestClient) -> None:
        block = _security_block(client)

        assert block["server_key"] == "git"
        assert block["contract_version"] == SECURITY_CONTRACT_VERSION
        assert block["validated"] is True

    def test_published_check_ids_cover_git_s_own_rules(
        self, client: TestClient
    ) -> None:
        published = _published_check_ids(client)

        assert _GIT_CHECK_IDS <= published

    def test_shipped_config_produces_a_validated_posture(self) -> None:
        posture = git_server._security_posture

        assert posture.validated is True
        assert posture.ready is True

    def test_block_carries_no_repo_path_or_token(self, client: TestClient) -> None:
        text = json.dumps(_security_block(client), ensure_ascii=False)
        cfg = git_server._cfg
        forbidden = [cfg.auth_token, cfg.audit_log_path, *cfg.allowed_repo_paths]

        assert all(value not in text for value in forbidden if value)


class TestFingerprintView:
    """The view row 43 defines is scalars and counts only (REQ-009)."""

    def test_view_carries_counts_instead_of_list_values(self) -> None:
        view = git_server._git_security_view(git_server._cfg)

        assert view["allowed_repo_paths_count"] == len(
            git_server._cfg.allowed_repo_paths
        )
        assert not any(isinstance(value, list) for value in view.values())

    def test_fingerprint_is_64_lowercase_hex(self) -> None:
        assert _FINGERPRINT_RE.match(git_server._security_posture.fingerprint)

    def test_fingerprint_changes_when_a_security_setting_changes(self) -> None:
        original = git_server._security_posture.fingerprint
        cfg = git_server._cfg
        cfg.allow_detached_head = not cfg.allow_detached_head
        try:
            rebuilt = git_server._build_security_posture()
        finally:
            cfg.allow_detached_head = not cfg.allow_detached_head

        assert rebuilt.fingerprint != original


class TestBindGate:
    """AC-003: git-mcp does not bind HTTP when validation fails."""

    def test_validated_posture_does_not_block_bind(self) -> None:
        git_server._enforce_posture_gate()

    def test_empty_allowlist_makes_the_posture_unvalidated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _unvalidated_posture(monkeypatch)

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
        _unvalidated_posture(monkeypatch)

        with pytest.raises(SystemExit) as excinfo:
            git_server._enforce_posture_gate()

        assert excinfo.value.code == 1
        message = "\n".join(record.getMessage() for record in caplog.records)
        assert "server.repo_allowlist:allowlist_empty" in message
        assert "refusing to bind" in message

    def test_health_returns_503_when_the_posture_is_not_validated(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _unvalidated_posture(monkeypatch)
        response = client.get("/health")

        assert response.status_code == 503
        body: dict[str, Any] = response.json()
        assert body["ready"] is False
        assert body["security"]["validated"] is False
