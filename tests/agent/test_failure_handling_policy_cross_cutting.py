"""tests/agent/test_failure_handling_policy_cross_cutting.py

Cross-cutting tests for ADR-004 environment failure handling policy, re-based on the MCP Security
Posture path: a required server whose published posture fails a security check aborts startup in every
environment, and no environment name or configuration knob relaxes that.
Covers ADR-004 INV-01, INV-02, INV-07 and INV-10.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from agent.services.mcp_health import check_readiness
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.security.posture_contract import (
    REQUIRED_CHECK_IDS,
    SECURITY_CONTRACT_VERSION,
)
from shared.security.result_dto import REASON_OK

FINGERPRINT = "a" * 64


def _server(server_key: str) -> McpServerConfig:
    """One required, persistent HTTP server, so its posture failure is a startup error."""
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=f"http://{server_key}-mcp:8091",
        startup_mode=StartupMode.PERSISTENT,
        required=True,
        auth_token="test-token",
        tool_names=["probe"],
    )


class _Probe:
    """Stands in for the shared httpx client, serving one canned /health answer per server."""

    def __init__(self, responses: dict[str, Any]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    async def get(self, url: str, **kwargs: Any) -> Any:
        self.calls.append(url)
        return self.responses[url]


def _response(payload: object) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = payload
    resp.text = str(payload)
    return resp


def _ctx(servers: dict[str, McpServerConfig], postures: dict[str, object]) -> MagicMock:
    """A context with no LLM or embed endpoint, so only the MCP posture path runs.

    `postures` maps a server key to the `security` block that server publishes.
    """
    http = _Probe(
        {
            f"{servers[server_key].url}/health": _response(
                {
                    "service": server_key,
                    "ready": True,
                    "dependencies": {},
                    "security": posture,
                }
            )
            for server_key, posture in postures.items()
        }
    )
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = servers
    ctx.cfg.llm.llm_url = ""
    ctx.cfg.rag.embed_url = ""
    ctx.services_required.http = http
    return ctx


def _posture(
    server_key: str,
    *,
    failed: tuple[tuple[str, str], ...] = (),
    drop: tuple[str, ...] = (),
    validated: bool | None = None,
    ready: bool | None = None,
) -> dict[str, object]:
    """A `security` block exactly as a server publishes it.

    `failed` marks required checks FAILED with a reason code, `drop` removes required checks from the
    list, and a FAILED posture is published with `validated=false` because the shared DTO forbids
    `validated=true` alongside a FAILED check.
    """
    failed_ids = {check_id for check_id, _ in failed}
    reason_by_id = {check_id: reason for check_id, reason in failed}
    checks = [
        {
            "id": check_id,
            "status": "failed" if check_id in failed_ids else "ok",
            "reason_code": reason_by_id.get(check_id, REASON_OK),
            "message": "check failed" if check_id in failed_ids else "check passed",
        }
        for check_id in REQUIRED_CHECK_IDS[server_key]
        if check_id not in drop
    ]
    if validated is None:
        validated = not failed
    if ready is None:
        ready = not failed
    return {
        "contract_version": SECURITY_CONTRACT_VERSION,
        "server_key": server_key,
        "policy_version": "1",
        "validated": validated,
        "ready": ready,
        "fingerprint": FINGERPRINT,
        "checks": checks,
    }


class TestFailureHandlingPolicy:
    async def test_shell_config_failure_production_raises(self) -> None:
        """ADR-004 INV-01/INV-02: a shell server whose allowlist check FAILED aborts startup."""
        ctx = _ctx(
            {"shell": _server("shell")},
            {
                "shell": _posture(
                    "shell",
                    failed=(("server.command_allowlist", "allowlist_empty"),),
                )
            },
        )
        with pytest.raises(RuntimeError, match="mcp:shell"):
            await check_readiness(ctx)

    async def test_git_config_failure_production_raises(self) -> None:
        """ADR-004 INV-01/INV-02: a git server whose repo allowlist check FAILED aborts startup."""
        ctx = _ctx(
            {"git": _server("git")},
            {
                "git": _posture(
                    "git", failed=(("server.repo_allowlist", "allowlist_empty"),)
                )
            },
        )
        with pytest.raises(RuntimeError, match="mcp:git"):
            await check_readiness(ctx)

    async def test_github_config_failure_production_raises(self) -> None:
        """ADR-004 INV-01/INV-02: a GitHub server whose force-push check FAILED aborts startup."""
        ctx = _ctx(
            {"github": _server("github")},
            {
                "github": _posture(
                    "github",
                    failed=(("server.force_push_policy", "force_push_enabled"),),
                )
            },
        )
        with pytest.raises(RuntimeError, match="mcp:github"):
            await check_readiness(ctx)

    async def test_shell_sandbox_backend_failure_raises(self) -> None:
        """ADR-004 INV-01/INV-02: a shell server whose sandbox backend check FAILED aborts
        startup. No configuration knob exists that could downgrade it."""
        ctx = _ctx(
            {"shell": _server("shell")},
            {
                "shell": _posture(
                    "shell",
                    failed=(("server.sandbox_backend", "sandbox_backend_unsupported"),),
                )
            },
        )
        with pytest.raises(RuntimeError, match="mcp:shell"):
            await check_readiness(ctx)

    async def test_all_configs_load_success_returns_no_warnings(self) -> None:
        """ADR-004 INV-01/INV-02: conforming postures produce no error and no warning."""
        servers = {key: _server(key) for key in ("shell", "git", "github")}
        ctx = _ctx(servers, {key: _posture(key) for key in servers})
        result = await check_readiness(ctx)
        assert result.errors == []
        assert result.warnings == []

    async def test_partial_config_failure_produces_targeted_exception(self) -> None:
        """ADR-004 INV-07/INV-10: the failure names only the server whose posture failed."""
        servers = {key: _server(key) for key in ("shell", "git", "github")}
        postures = {key: _posture(key) for key in servers}
        postures["git"] = _posture(
            "git", failed=(("server.protected_branch_config", "ref_guard_invalid"),)
        )
        ctx = _ctx(servers, postures)
        with pytest.raises(RuntimeError) as excinfo:
            await check_readiness(ctx)
        message = str(excinfo.value)
        assert "mcp:git" in message
        assert "mcp:shell" not in message
        assert "mcp:github" not in message

    async def test_missing_required_check_is_rejected(self) -> None:
        """ADR-004 INV-07/INV-10: a posture missing a required check is rejected, not accepted."""
        ctx = _ctx(
            {"shell": _server("shell")},
            {"shell": _posture("shell", drop=("server.command_allowlist",))},
        )
        with pytest.raises(RuntimeError, match="check_set_mismatch"):
            await check_readiness(ctx)

    async def test_non_production_profile_raises_on_config_failures(self) -> None:
        """ADR-004 INV-02/INV-10: a non-production profile name does not downgrade the failure."""
        ctx = _ctx(
            {"git": _server("git")},
            {
                "git": _posture(
                    "git", failed=(("server.repo_allowlist", "allowlist_empty"),)
                )
            },
        )
        ctx.cfg.env = MagicMock()
        ctx.cfg.env.name = "local"
        with pytest.raises(RuntimeError, match="safety failure"):
            await check_readiness(ctx)
