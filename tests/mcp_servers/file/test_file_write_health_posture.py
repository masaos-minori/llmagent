"""tests/mcp_servers/file/test_file_write_health_posture.py

Security Posture publication and the HTTP bind gate for
scripts/mcp_servers/file/write_server.py (REQ-002, REQ-003, REQ-012).

The posture is built once at module import from the already loaded config, so the gate is
startup-only and no later /health probe re-validates it (ADR-003 Static Availability).
FileWriteConfig is frozen, so a failing posture is produced with `dataclasses.replace()`.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient
from mcp_servers.file import write_server
from shared.security.posture_contract import SECURITY_CONTRACT_VERSION, SecurityPosture

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

_WRITE_CHECK_IDS = {
    "server.allowed_dirs_configured",
    "server.allowed_dirs_exist",
    "server.max_write_bytes",
    "server.write_dirs_writable",
    "server.supported_extensions",
}
_FINGERPRINT_RE = re.compile(r"\A[0-9a-f]{64}\Z")


@pytest.fixture
def client() -> TestClient:
    """TestClient for the real file-write app with the test-suite Bearer token."""
    return TestClient(write_server.app, headers=MCP_TEST_AUTH_HEADERS)


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
    """Rebuild the posture from a patched copy of the frozen loaded config."""
    posture = write_server._build_security_posture(
        dataclasses.replace(write_server._cfg, **overrides)
    )
    monkeypatch.setattr(write_server, "_security_posture", posture)
    return posture


def _failed_checks(posture: SecurityPosture) -> dict[str, str]:
    """Return the failed check ids mapped to their reason codes."""
    return {
        check.check_id: check.reason_code
        for check in posture.checks
        if check.status.value == "failed"
    }


def _let_the_module_log(monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-enable propagation so caplog sees the dedicated logger shared.logger disables."""
    monkeypatch.setattr(logging.getLogger(write_server.__name__), "propagate", True)


class TestPosturePublication:
    """AC-002: file-write-mcp publishes the posture on /health with no path or Secret."""

    def test_health_body_carries_the_security_block(self, client: TestClient) -> None:
        block = _security_block(client)

        assert block["server_key"] == "file_write"
        assert block["contract_version"] == SECURITY_CONTRACT_VERSION
        assert block["validated"] is True

    def test_published_check_ids_cover_file_write_s_own_rules(
        self, client: TestClient
    ) -> None:
        assert _WRITE_CHECK_IDS <= set(_published_checks(client))

    def test_unenforced_extension_setting_is_published_as_not_applicable(
        self, client: TestClient
    ) -> None:
        assert (
            _published_checks(client)["server.supported_extensions"] == "not_applicable"
        )

    def test_shipped_config_produces_a_validated_posture(self) -> None:
        posture = write_server._security_posture

        assert posture.validated is True
        assert posture.ready is True

    def test_block_carries_no_allowed_dir_or_token(self, client: TestClient) -> None:
        text = json.dumps(_security_block(client), ensure_ascii=False)
        cfg = write_server._cfg
        forbidden = [cfg.auth_token, *cfg.allowed_dirs]

        assert all(value not in text for value in forbidden if value)


class TestFingerprintView:
    """The view row 48 defines is scalars and counts only (REQ-009)."""

    def test_view_carries_counts_instead_of_list_values(self) -> None:
        view = write_server._write_security_view(write_server._cfg)

        assert view["allowed_dirs_count"] == len(write_server._cfg.allowed_dirs)
        assert view["supported_extensions_count"] == len(
            write_server._cfg.supported_extensions
        )
        assert not any(isinstance(value, list) for value in view.values())

    def test_fingerprint_is_64_lowercase_hex(self) -> None:
        assert _FINGERPRINT_RE.match(write_server._security_posture.fingerprint)

    def test_fingerprint_changes_when_a_security_setting_changes(self) -> None:
        original = write_server._security_posture.fingerprint
        cfg = write_server._cfg
        patched = dataclasses.replace(cfg, max_write_bytes=cfg.max_write_bytes + 1)

        assert write_server._build_security_posture(patched).fingerprint != original


class TestBindGate:
    """AC-003: file-write-mcp does not bind HTTP when validation fails."""

    def test_validated_posture_does_not_block_bind(self) -> None:
        write_server._enforce_posture_gate()

    def test_empty_allowed_dirs_makes_the_posture_unvalidated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _posture_with(monkeypatch, allowed_dirs=[])

        assert posture.validated is False
        assert (
            _failed_checks(posture)["server.allowed_dirs_configured"]
            == "allowlist_empty"
        )

    def test_non_positive_byte_limit_is_a_startup_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _posture_with(monkeypatch, max_write_bytes=0)

        assert _failed_checks(posture)["server.max_write_bytes"] == "config_invalid"

    def test_unwritable_allowed_dir_is_a_startup_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        target = write_server._cfg.allowed_dirs[0]
        real_access = os.access
        monkeypatch.setattr(
            os,
            "access",
            lambda path, mode: (
                False if str(path) == target else real_access(path, mode)
            ),
        )
        posture = _posture_with(monkeypatch, allowed_dirs=[target])

        assert (
            _failed_checks(posture)["server.write_dirs_writable"]
            == "dependency_unreachable"
        )

    def test_gate_refuses_bind_and_logs_reason_codes(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        _let_the_module_log(monkeypatch)
        _posture_with(monkeypatch, allowed_dirs=[])

        with pytest.raises(SystemExit) as excinfo:
            write_server._enforce_posture_gate()

        assert excinfo.value.code == 1
        gate_lines = [
            record.getMessage()
            for record in caplog.records
            if "refusing to bind" in record.getMessage()
        ]
        assert gate_lines, "the gate did not log a refusal"
        assert "server.allowed_dirs_configured:allowlist_empty" in gate_lines[0]
        assert all("/opt/llm" not in line for line in gate_lines)

    def test_health_returns_503_when_the_posture_is_not_validated(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _posture_with(monkeypatch, allowed_dirs=[])
        response = client.get("/health")

        assert response.status_code == 503
        body: dict[str, Any] = response.json()
        assert body["ready"] is False
        assert body["security"]["validated"] is False
