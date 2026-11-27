"""tests/mcp_servers/cicd/test_cicd_health_posture.py

Security Posture publication and the HTTP bind gate for
scripts/mcp_servers/cicd/cicd_server.py (REQ-002, REQ-003, REQ-008).

The posture is built once at module import from the already loaded config; the service is
built by the lifespan, so the pre-bind stage reports the backend availability as
not_applicable. `GITHUB_TOKEN` stays a `dependencies` signal, read through the effective
credential, so tests that assert a healthy payload set it the way
tests/mcp_servers/cicd/test_mcp_server_health_status.py does.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient
from mcp_servers.cicd import cicd_server
from mcp_servers.cicd.cicd_models import CicdConfig
from mcp_servers.cicd.cicd_service_guards import ProbeOutcome
from shared.security.posture_contract import SECURITY_CONTRACT_VERSION, SecurityPosture
from shared.security.result_dto import REASON_AUTH_TOKEN_MISSING, REASON_OK

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

_CICD_CHECK_IDS = {
    "server.repo_allowlist",
    "server.workflow_allowlist",
    "server.workflow_pattern_valid",
    "server.backend_available",
    # Added by procedure seq 04: the effective-credential posture check.
    "server.github_credential",
}
_TEST_CREDENTIAL = "ghp_test_token"
_FINGERPRINT_RE = re.compile(r"\A[0-9a-f]{64}\Z")


@pytest.fixture
def client() -> TestClient:
    """TestClient for the real cicd app, whose shipped config carries a non-empty auth token.

    `require_auth_token()` is fail-closed on an empty token, so the app cannot be constructed
    without one; the lifespan does not run here, which keeps the probe outcome unset.
    """
    return TestClient(cicd_server.app, headers=MCP_TEST_AUTH_HEADERS)


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
    cfg = cicd_server._cfg
    original = {name: getattr(cfg, name) for name in overrides}
    for name, value in overrides.items():
        setattr(cfg, name, value)
    try:
        posture = cicd_server._build_security_posture()
    finally:
        for name, value in original.items():
            setattr(cfg, name, value)
    monkeypatch.setattr(cicd_server, "_security_posture", posture)
    return posture


def _posture_with_credential(
    monkeypatch: pytest.MonkeyPatch, **overrides: object
) -> SecurityPosture:
    """Rebuild the posture with an effective credential present, then restore it.

    The credential check added by procedure seq 04 reads the effective value, so a posture
    that is expected to validate needs a credential; the shipped config's own value is empty.
    """
    monkeypatch.setenv("GITHUB_TOKEN", _TEST_CREDENTIAL)
    return _posture_with(monkeypatch, **overrides)


def _failed_check_ids(posture: SecurityPosture) -> set[str]:
    """Return the check ids the posture reports as failed."""
    return {
        check.check_id for check in posture.checks if check.status.value == "failed"
    }


class TestPosturePublication:
    """AC-002: cicd-mcp publishes the posture on /health with no Secret in it."""

    def test_health_body_carries_the_security_block(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The credential check is part of validation, so the posture is rebuilt with an
        # effective credential before the health body is read.
        _posture_with_credential(monkeypatch)
        block = _security_block(client)

        assert block["server_key"] == "cicd"
        assert block["contract_version"] == SECURITY_CONTRACT_VERSION
        assert block["validated"] is True

    def test_published_check_ids_cover_cicd_s_own_rules(
        self, client: TestClient
    ) -> None:
        assert _CICD_CHECK_IDS <= set(_published_checks(client))

    def test_backend_availability_is_published_as_not_applicable(
        self, client: TestClient
    ) -> None:
        assert _published_checks(client)["server.backend_available"] == "not_applicable"

    def test_shipped_config_validates_only_with_an_effective_credential(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The shipped config's own github_token is empty, so the credential check decides validation.

        Re-pinned by procedure seq 04: without an effective credential the posture is not
        validated, which is what keeps the bind gate closed for a tokenless start (REQ-002).
        """
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        posture = _posture_with(monkeypatch)
        assert posture.validated is False
        assert "server.github_credential" in _failed_check_ids(posture)

        monkeypatch.setenv("GITHUB_TOKEN", _TEST_CREDENTIAL)
        posture = _posture_with(monkeypatch)
        assert posture.validated is True
        assert posture.ready is True

    def test_block_carries_no_token_or_allowlist_entry(
        self, client: TestClient
    ) -> None:
        text = json.dumps(_security_block(client), ensure_ascii=False)
        cfg = cicd_server._cfg
        forbidden = [
            cfg.auth_token,
            cfg.github_token,
            *cfg.repo_allowlist,
            *cfg.workflow_allowlist,
        ]

        assert all(value not in text for value in forbidden if value)


class TestHealthDependencyValues:
    """Health reports the effective credential and a failed probe, never the token (REQ-001, REQ-003)."""

    def _cfg_with(self, monkeypatch: pytest.MonkeyPatch, github_token: str) -> None:
        """Point the module at a config whose only credential source is the fallback."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(
            cicd_server,
            "_cfg",
            CicdConfig(
                repo_allowlist=["acme/widgets"],
                workflow_allowlist=["ci.yml"],
                github_token=github_token,
            ),
        )
        monkeypatch.setattr(
            cicd_server, "_security_posture", cicd_server._build_security_posture()
        )

    def test_config_fallback_is_the_effective_credential_when_env_is_unset(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A config-only token is still the effective credential, so health is not degraded."""
        self._cfg_with(monkeypatch, "config-token")
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["dependencies"] == {}

    def test_no_effective_credential_is_a_dependency_failure(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._cfg_with(monkeypatch, "")
        response = client.get("/health")

        assert response.status_code == 503
        assert response.json()["dependencies"] == {"github_token": "not_set"}

    def test_failed_probe_adds_the_probe_dependency(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Only a failed probe becomes a dependency entry, so the ready rule is unchanged (AC-7)."""
        _posture_with_credential(monkeypatch)
        monkeypatch.setattr(
            cicd_server,
            "_probe_outcome",
            ProbeOutcome(REASON_AUTH_TOKEN_MISSING, REASON_OK, REASON_OK),
        )
        response = client.get("/health")

        assert response.status_code == 503
        assert response.json()["dependencies"] == {
            "credential_probe": REASON_AUTH_TOKEN_MISSING
        }

    def test_ok_probe_leaves_dependencies_empty(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _posture_with_credential(monkeypatch)
        monkeypatch.setattr(
            cicd_server, "_probe_outcome", ProbeOutcome(REASON_OK, REASON_OK, REASON_OK)
        )
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["dependencies"] == {}


class TestFingerprintView:
    """The view row 45 defines is scalars and counts only (REQ-009)."""

    def test_view_carries_counts_instead_of_list_values(self) -> None:
        view = cicd_server._cicd_security_view(cicd_server._cfg)

        assert view["repo_allowlist_count"] == len(cicd_server._cfg.repo_allowlist)
        assert not any(isinstance(value, list) for value in view.values())

    def test_fingerprint_is_64_lowercase_hex(self) -> None:
        assert _FINGERPRINT_RE.match(cicd_server._security_posture.fingerprint)

    def test_fingerprint_changes_when_a_security_setting_changes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        original = cicd_server._security_posture.fingerprint
        cfg = cicd_server._cfg
        monkeypatch.setattr(cfg, "max_log_size_kb", cfg.max_log_size_kb + 1)

        assert cicd_server._build_security_posture().fingerprint != original


class TestBindGate:
    """AC-003: cicd-mcp does not bind HTTP when validation fails."""

    def test_validated_posture_does_not_block_bind(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _posture_with_credential(monkeypatch)
        cicd_server._enforce_posture_gate()

    def test_empty_auth_token_is_a_warning_and_stays_validated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Documented design: the posture reports common.auth_token as a warning, while the
        # server process itself refuses to start on an empty token through require_auth_token().
        # The credential check still needs an effective credential for the posture to validate.
        posture = _posture_with_credential(monkeypatch, auth_token="")

        assert posture.validated is True
        statuses = {check.check_id: check.status.value for check in posture.checks}
        assert statuses["common.auth_token"] == "warning"

    def test_empty_repo_allowlist_makes_the_posture_unvalidated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _posture_with(monkeypatch, repo_allowlist=[])

        assert posture.validated is False
        assert "server.repo_allowlist" in _failed_check_ids(posture)

    def test_empty_workflow_allowlist_makes_the_posture_unvalidated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _posture_with(monkeypatch, workflow_allowlist=[])

        assert posture.validated is False
        assert "server.workflow_allowlist" in _failed_check_ids(posture)

    def test_invalid_workflow_pattern_is_a_startup_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        posture = _posture_with(monkeypatch, workflow_allowlist=["a/b.yml"])

        failed = {
            check.check_id: check.reason_code
            for check in posture.checks
            if check.status.value == "failed"
        }
        assert failed["server.workflow_pattern_valid"] == "config_invalid"

    def test_gate_refuses_bind_and_logs_reason_codes(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        _posture_with(monkeypatch, repo_allowlist=[])

        with pytest.raises(SystemExit) as excinfo:
            cicd_server._enforce_posture_gate()

        assert excinfo.value.code == 1
        message = "\n".join(record.getMessage() for record in caplog.records)
        assert "server.repo_allowlist:allowlist_empty" in message
        assert "refusing to bind" in message

    def test_health_returns_503_when_the_posture_is_not_validated(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        _posture_with(monkeypatch, repo_allowlist=[])
        response = client.get("/health")

        assert response.status_code == 503
        body: dict[str, Any] = response.json()
        assert body["dependencies"] == {}
        assert body["ready"] is False
        assert body["security"]["validated"] is False
