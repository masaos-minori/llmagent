"""tests/mcp_servers/cicd/test_cicd_credential.py

Credential matrix for scripts/mcp_servers/cicd/cicd_credential.py (REQ-001, AC-1).

Environment only, config only, both, and neither, each asserting the documented
precedence: the environment variable wins, the config value is the fallback. The
startup-refusal case is added by the cicd_service_guards.py procedure, which creates
the `server.github_credential` posture check this file asserts against.
"""

from __future__ import annotations

import pytest
from mcp_servers.cicd.cicd_credential import resolve_effective_credential
from mcp_servers.cicd.cicd_models import CicdConfig
from mcp_servers.cicd.cicd_service_guards import validate_cicd_security
from shared.security.result_dto import (
    REASON_AUTH_TOKEN_MISSING,
    SecurityCheckStatus,
)

_ENV_VAR = "GITHUB_TOKEN"
_ENV_TOKEN = "env-token"
_CFG_TOKEN = "config-token"


class _NoProbeBackend:
    """A backend that exposes no availability probe, so the probe dimension stays not_applicable."""


def _cfg(github_token: str) -> CicdConfig:
    """Build a config object directly, without reading config/cicd_mcp_server.toml."""
    return CicdConfig(github_token=github_token)


def test_environment_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_ENV_VAR, raising=False)
    monkeypatch.setenv(_ENV_VAR, _ENV_TOKEN)
    assert resolve_effective_credential(_cfg("")) == _ENV_TOKEN


def test_config_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_ENV_VAR, raising=False)
    assert resolve_effective_credential(_cfg(_CFG_TOKEN)) == _CFG_TOKEN


def test_both_environment_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_ENV_VAR, _ENV_TOKEN)
    assert resolve_effective_credential(_cfg(_CFG_TOKEN)) == _ENV_TOKEN


def test_neither(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_ENV_VAR, raising=False)
    assert resolve_effective_credential(_cfg("")) == ""


def test_empty_environment_falls_back_to_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(_ENV_VAR, "")
    assert resolve_effective_credential(_cfg(_CFG_TOKEN)) == _CFG_TOKEN


def test_startup_refusal_without_an_effective_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The deferred assertion from this file's two-stage write, added by procedure seq 04.

    No effective credential produces a FAILED `server.github_credential` check, which keeps
    the posture unvalidated and the bind gate closed (REQ-002, AC-2).
    """
    monkeypatch.delenv(_ENV_VAR, raising=False)
    checks = {
        result.check_id: result
        for result in validate_cicd_security(
            _NoProbeBackend(),
            ("o/r",),
            ("ci.yml",),
            resolve_effective_credential(_cfg("")),
        )
    }
    result = checks["server.github_credential"]
    assert result.status is SecurityCheckStatus.FAILED
    assert result.reason_code == REASON_AUTH_TOKEN_MISSING
    assert _CFG_TOKEN not in result.message
