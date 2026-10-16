"""tests/mcp_servers/shell/test_shell_health_posture.py

Security Posture publication and the HTTP bind gate for
scripts/mcp_servers/shell/shell_server.py (REQ-002, REQ-003, REQ-005).

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
from mcp_servers.shell import shell_server
from shared.security.posture_contract import SECURITY_CONTRACT_VERSION

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

_SHELL_CHECK_IDS = {
    "server.sandbox_backend",
    "server.sandbox_binary",
    "server.command_allowlist",
    "server.resource_limits",
}
_FINGERPRINT_RE = re.compile(r"\A[0-9a-f]{64}\Z")


@pytest.fixture
def client() -> TestClient:
    """TestClient for the real shell app with the test-suite Bearer token."""
    return TestClient(shell_server.app, headers=MCP_TEST_AUTH_HEADERS)


def _security_block(client: TestClient) -> dict[str, Any]:
    """Return the `security` block of a real /health response body."""
    body: dict[str, Any] = client.get("/health").json()
    block = body["security"]
    assert isinstance(block, dict)
    return block


def _published_check_ids(client: TestClient) -> set[str]:
    """Return the check ids the published block carries."""
    return {str(check["id"]) for check in _security_block(client)["checks"]}


class TestPosturePublication:
    """AC-002: shell-mcp publishes the posture on /health with no secret in it."""

    def test_health_body_carries_the_security_block(self, client: TestClient) -> None:
        block = _security_block(client)

        assert block["server_key"] == "shell"
        assert block["contract_version"] == SECURITY_CONTRACT_VERSION
        assert block["validated"] is True

    def test_published_check_ids_cover_shell_s_own_rules(
        self, client: TestClient
    ) -> None:
        published = _published_check_ids(client)

        assert _SHELL_CHECK_IDS <= published

    def test_shipped_config_produces_a_validated_posture(self) -> None:
        posture = shell_server._security_posture

        assert posture.validated is True
        assert posture.ready is True

    def test_block_carries_no_token_path_or_allowlist_entry(
        self, client: TestClient
    ) -> None:
        text = json.dumps(_security_block(client), ensure_ascii=False)
        cfg = shell_server._cfg
        forbidden = [
            cfg.auth_token,
            cfg.audit_log_path,
            cfg.default_cwd,
            *cfg.command_allowlist,
        ]

        assert all(value not in text for value in forbidden if value)


class TestFingerprintView:
    """The view row 42 defines is scalars and counts only (REQ-009)."""

    def test_view_carries_counts_instead_of_list_values(self) -> None:
        view = shell_server._shell_security_view(shell_server._cfg)

        assert view["command_allowlist_count"] == len(
            shell_server._cfg.command_allowlist
        )
        assert not any(isinstance(value, list) for value in view.values())

    def test_fingerprint_is_64_lowercase_hex(self) -> None:
        assert _FINGERPRINT_RE.match(shell_server._security_posture.fingerprint)

    def test_fingerprint_changes_when_a_security_setting_changes(self) -> None:
        original = shell_server._security_posture.fingerprint

        shell_server._cfg.shell_sandbox_backend = "none"
        try:
            rebuilt = shell_server._build_security_posture()
        finally:
            shell_server._cfg.shell_sandbox_backend = "firejail"

        assert rebuilt.fingerprint != original


class TestBindGate:
    """AC-003: shell-mcp does not bind HTTP when validation fails."""

    def test_validated_posture_does_not_block_bind(self) -> None:
        shell_server._enforce_posture_gate()

    def test_empty_allowlist_makes_the_posture_unvalidated(self) -> None:
        cfg = shell_server._cfg
        original = list(cfg.command_allowlist)
        cfg.command_allowlist = []
        try:
            posture = shell_server._build_security_posture()
        finally:
            cfg.command_allowlist = original

        assert posture.validated is False
        failed = {
            check.check_id for check in posture.checks if check.status.value == "failed"
        }
        assert "server.command_allowlist" in failed

    def test_gate_refuses_bind_and_logs_reason_codes(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        cfg = shell_server._cfg
        original = list(cfg.command_allowlist)
        cfg.command_allowlist = []
        try:
            monkeypatch.setattr(
                shell_server,
                "_security_posture",
                shell_server._build_security_posture(),
            )
        finally:
            cfg.command_allowlist = original

        with pytest.raises(SystemExit) as excinfo:
            shell_server._enforce_posture_gate()

        assert excinfo.value.code == 1
        message = "\n".join(record.getMessage() for record in caplog.records)
        assert "server.command_allowlist:allowlist_empty" in message
        assert "refusing to bind" in message

    def test_health_returns_503_when_the_posture_is_not_validated(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cfg = shell_server._cfg
        original = list(cfg.command_allowlist)
        cfg.command_allowlist = []
        try:
            monkeypatch.setattr(
                shell_server,
                "_security_posture",
                shell_server._build_security_posture(),
            )
            response = client.get("/health")
        finally:
            cfg.command_allowlist = original

        assert response.status_code == 503
        body: dict[str, Any] = response.json()
        assert body["ready"] is False
        assert body["security"]["validated"] is False
