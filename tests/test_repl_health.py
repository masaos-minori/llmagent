"""
tests/test_repl_health.py
Unit tests for repl_health module-level functions.

httpx.AsyncClient and AgentContext are mocked.
"""

from __future__ import annotations

import sqlite3
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from agent.repl_health import (
    _check_tool_definitions,
    _probe_mcp_health_detail,
    audit_security_defaults,
    check_readiness,
    check_workflow_definition,
    check_workflow_schema,
)
from agent.security_audit_config import (
    CicdAuditConfig,
    GitAuditConfig,
    GitHubAuditConfig,
    ShellAuditConfig,
)
from db.schema_sql import WORKFLOW_SCHEMA_VERSION


def _async_result(value: object) -> AsyncMock:
    """Return an AsyncMock whose call returns the given value as a coroutine."""
    m = AsyncMock()
    m.return_value = value
    return m


# ── _probe_mcp_health_detail() ────────────────────────────────────────────────


class TestProbeMcpHealthDetail:
    @pytest.mark.asyncio
    async def test_reachable_true_restart_false_when_200_no_body_field(self) -> None:
        """HTTP 200 with no restart_recommended field: reachable=True, restart_recommended=False."""
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"status": "ok", "ready": True}
        http.get = _async_result(resp)

        result = await _probe_mcp_health_detail(http, "http://localhost:8000")

        assert result.reachable is True
        assert result.status_code == 200
        assert result.restart_recommended is False
        assert result.operator_action_required is False
        http.get.assert_called_once_with("http://localhost:8000/health", timeout=5.0)

    @pytest.mark.asyncio
    async def test_reachable_true_restart_true_when_503_and_restart_recommended(
        self,
    ) -> None:
        """HTTP 503 + restart_recommended=true in body: reachable=True, restart_recommended=True."""
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 503
        resp.json.return_value = {
            "status": "degraded",
            "ready": False,
            "restart_recommended": True,
            "operator_action_required": False,
        }
        http.get = _async_result(resp)

        result = await _probe_mcp_health_detail(http, "http://localhost:8000")

        assert result.reachable is True
        assert result.status_code == 503
        assert result.restart_recommended is True
        assert result.operator_action_required is False

    @pytest.mark.asyncio
    async def test_reachable_false_on_connection_exception(self) -> None:
        """Connection failure: reachable=False, status_code=None."""
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get.side_effect = httpx.ConnectError("fail")

        result = await _probe_mcp_health_detail(http, "http://localhost:8000")

        assert result.reachable is False
        assert result.status_code is None
        assert result.restart_recommended is False
        assert result.operator_action_required is False
        assert result.body == {}

    @pytest.mark.asyncio
    async def test_reachable_true_parse_failed_on_malformed_json_body(self) -> None:
        """HTTP 200 with a body that fails JSON parsing: parse_failed=True, parse_error populated."""
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = ValueError("Expecting value: line 1 column 1 (char 0)")
        resp.text = "not json"
        http.get = _async_result(resp)

        result = await _probe_mcp_health_detail(http, "http://localhost:8000")

        assert result.reachable is True
        assert result.status_code == 200
        assert result.restart_recommended is False
        assert result.operator_action_required is False
        assert result.body == {}
        assert result.parse_failed is True
        assert result.parse_error is not None
        assert "not json" in result.parse_error


# ── _check_tool_definitions() ──────────────────────────────────────────────────


class TestCheckToolDefinitions:
    @pytest.mark.asyncio
    async def test_no_mismatch_returns_empty(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
            {"function": {"name": "write_file"}},
        ]

        with patch(
            "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
        ) as mock_collect:
            mock_collect.return_value = ({"read_file", "write_file"}, [])
            result = await _check_tool_definitions(ctx, strict=False)

        assert not result.has_issues

    @pytest.mark.asyncio
    async def test_returns_warning_on_missing_in_server(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
            {"function": {"name": "write_file"}},
        ]

        with patch(
            "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
        ) as mock_collect:
            mock_collect.return_value = ({"read_file"}, [])
            result = await _check_tool_definitions(ctx, strict=False)

        msgs = result.warning_messages()
        assert len(msgs) == 1
        assert "write_file" in msgs[0]

    @pytest.mark.asyncio
    async def test_logs_warning_on_missing_in_cfg(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
        ]

        with patch(
            "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
        ) as mock_collect:
            mock_collect.return_value = ({"read_file", "delete_file"}, [])
            result = await _check_tool_definitions(ctx, strict=False)

        assert not result.has_issues

    @pytest.mark.asyncio
    async def test_raises_in_strict_mode(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
        ]

        with patch(
            "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
        ) as mock_collect:
            mock_collect.return_value = ({"read_file", "delete_file"}, [])
            with pytest.raises(RuntimeError, match="Strict mode"):
                await _check_tool_definitions(ctx, strict=True)

    @pytest.mark.asyncio
    async def test_returns_empty_when_all_servers_unreachable(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
        ]

        with patch(
            "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
        ) as mock_collect:
            mock_collect.return_value = (set(), [])
            result = await _check_tool_definitions(ctx, strict=False)

        assert not result.has_issues

    @pytest.mark.asyncio
    async def test_raises_in_strict_mode_when_all_unreachable(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
        ]

        with patch(
            "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
        ) as mock_collect:
            mock_collect.return_value = (
                set(),
                ["srv-a"],
            )  # empty names, non-empty unreachable
            with pytest.raises(
                RuntimeError, match="Strict mode: all MCP servers unreachable"
            ):
                await _check_tool_definitions(ctx, strict=True)

    @pytest.mark.asyncio
    async def test_partial_unreachable_non_strict_returns_warning_if_mismatch(
        self,
    ) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
            {"function": {"name": "write_file"}},
        ]

        with patch(
            "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
        ) as mock_collect:
            mock_collect.return_value = ({"read_file"}, ["srv-b"])
            result = await _check_tool_definitions(ctx, strict=False)

        msgs = result.warning_messages()
        assert len(msgs) == 1
        assert "write_file" in msgs[0]

    @pytest.mark.asyncio
    async def test_partial_unreachable_strict_raises(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
            {"function": {"name": "write_file"}},
        ]

        with patch(
            "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
        ) as mock_collect:
            mock_collect.return_value = ({"read_file"}, ["srv-b"])
            with pytest.raises(RuntimeError, match="Strict mode"):
                await _check_tool_definitions(ctx, strict=True)

    @pytest.mark.asyncio
    async def test_all_unreachable_non_strict_skips_validation(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
        ]

        with patch(
            "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
        ) as mock_collect:
            mock_collect.return_value = (set(), ["srv-a"])
            result = await _check_tool_definitions(ctx, strict=False)

        assert not result.has_issues


# ── check_service_health() ────────────────────────────────────────────────────


class TestCheckServiceHealth:
    @pytest.mark.asyncio
    async def test_returns_empty_when_all_healthy(self) -> None:
        from agent.repl_health import check_service_health

        ctx = MagicMock()
        ctx.cfg.llm.llm_url = "http://localhost:8000/v1/chat/completions"
        ctx.cfg.rag.embed_url = "http://localhost:8080/v1/embeddings"
        resp = MagicMock()
        resp.status_code = 200
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(resp)
        ctx.services_required.http = http

        result = await check_service_health(ctx)

        assert not result.has_issues

    @pytest.mark.asyncio
    async def test_returns_warning_on_non_200(self) -> None:
        from agent.repl_health import check_service_health

        ctx = MagicMock()
        ctx.cfg.llm.llm_url = "http://localhost:8000/v1/chat/completions"
        ctx.cfg.rag.embed_url = ""
        resp = MagicMock()
        resp.status_code = 503
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(resp)
        ctx.services_required.http = http

        result = await check_service_health(ctx)

        msgs = result.warning_messages()
        assert len(msgs) == 1
        assert "503" in msgs[0]

    @pytest.mark.asyncio
    async def test_returns_warning_on_exception(self) -> None:
        from agent.repl_health import check_service_health

        ctx = MagicMock()
        ctx.cfg.llm.llm_url = "http://localhost:8000/v1/chat/completions"
        ctx.cfg.rag.embed_url = ""
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx.services_required.http = http

        result = await check_service_health(ctx)

        msgs = result.warning_messages()
        assert len(msgs) == 1
        assert "refused" in msgs[0]

    @pytest.mark.asyncio
    async def test_skips_empty_urls(self) -> None:
        from agent.repl_health import check_service_health

        ctx = MagicMock()
        ctx.cfg.llm.llm_url = ""
        ctx.cfg.rag.embed_url = ""

        result = await check_service_health(ctx)

        assert not result.has_issues


# ── audit_security_defaults with production mode ─────────────────────────────


class TestAuditSecurityDefaults:
    """Tests for audit_security_defaults with production mode enforcement."""

    def _make_ctx(
        self,
        servers: dict[str, dict] | None = None,
        security_profile: str = "local",
    ) -> MagicMock:
        """Build a minimal mocked AgentContext for testing."""
        from shared.mcp_config import McpServerConfig, SecurityProfile, TransportType

        mcp_servers: dict[str, Any] = {}
        if servers:
            for key, vals in servers.items():
                transport_str = vals.get("transport", "http")
                transport = TransportType(transport_str)
                url = (
                    vals.get("url", "http://127.0.0.1:8000")
                    if transport == TransportType.HTTP
                    else ""
                )
                mcp_servers[key] = McpServerConfig(
                    transport=transport,
                    url=url,
                    auth_token=vals.get("auth_token", ""),
                )

        ctx = MagicMock()
        ctx.cfg.mcp.mcp_servers = mcp_servers
        ctx.cfg.mcp.security_profile = SecurityProfile(security_profile)
        ctx.cfg.mcp.security_lockdown_enabled = False
        ctx.cfg.shell_policy = None
        ctx.cfg.github = None
        ctx.cfg.tool = MagicMock()
        ctx.cfg.tool.allowed_tools = ["shell_run"]
        ctx.cfg.approval = MagicMock()
        ctx.cfg.approval.tool_safety_tiers = {}
        return ctx

    def test_local_mode_no_auth_returns_warnings(self) -> None:
        """Local mode with missing auth_token returns warnings, no exception."""
        from shared.mcp_config import SecurityProfile

        ctx = self._make_ctx(
            servers={"web_search": {"auth_token": ""}},
            security_profile="local",
        )
        ctx.cfg.mcp.security_profile = SecurityProfile.LOCAL
        warnings = audit_security_defaults(ctx, production_mode=False)
        auth_warnings = [w for w in warnings if "web_search" in w]
        assert len(auth_warnings) == 1

    def test_production_mode_no_auth_raises(self) -> None:
        """Production mode with missing auth_token raises RuntimeError."""
        from shared.mcp_config import SecurityProfile

        ctx = self._make_ctx(
            servers={"web_search": {"auth_token": ""}, "file_read": {"auth_token": ""}},
            security_profile="production",
        )
        ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
        with pytest.raises(RuntimeError, match="Production mode requires auth_token"):
            audit_security_defaults(ctx, production_mode=True)

    def test_production_mode_all_authed_no_error(self) -> None:
        """Production mode with all HTTP servers having auth_token → no error."""
        from shared.mcp_config import SecurityProfile

        ctx = self._make_ctx(
            servers={
                "web_search": {"auth_token": "tok1"},
                "file_read": {"auth_token": "tok2"},
            },
            security_profile="production",
        )
        ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
        shell_cfg = ShellAuditConfig(
            sandbox_backend="firejail", command_allowlist=["ls"]
        )
        cicd_cfg = CicdAuditConfig(workflow_allowlist=["test"])
        with patch("agent.repl_health.load_shell_audit_config", return_value=shell_cfg):
            with patch("agent.repl_health.load_git_audit_config", return_value=None):
                with patch(
                    "agent.repl_health.load_github_audit_config", return_value=None
                ):
                    with patch(
                        "agent.repl_health.load_cicd_audit_config",
                        return_value=cicd_cfg,
                    ):
                        with patch("shutil.which", return_value="/usr/bin/firejail"):
                            warnings = audit_security_defaults(
                                ctx, production_mode=True
                            )
        auth_warnings = [w for w in warnings if "auth_token" in w]
        assert len(auth_warnings) == 0

    def test_shell_config_load_failure_returns_warning_in_local_mode(self) -> None:
        """load_shell_audit_config() raising RuntimeError in local mode → warning returned, no raise."""
        ctx = self._make_ctx()
        with patch(
            "agent.repl_health.load_shell_audit_config",
            side_effect=RuntimeError(
                "Security audit: failed to load shell config: no file"
            ),
        ):
            warnings = audit_security_defaults(ctx, production_mode=False)
        shell_warnings = [w for w in warnings if "shell config" in w.lower()]
        assert len(shell_warnings) == 1

    def test_git_config_empty_allowed_repo_paths_warns(self) -> None:
        """git.allowed_repo_paths empty triggers a fail-closed warning."""
        ctx = self._make_ctx()
        empty_git = GitAuditConfig(allowed_repo_paths=[])
        with patch("agent.repl_health.load_shell_audit_config", return_value=None):
            with patch(
                "agent.repl_health.load_git_audit_config", return_value=empty_git
            ):
                warnings = audit_security_defaults(ctx, production_mode=False)
        assert any("git.allowed_repo_paths" in w for w in warnings)

    def test_shell_sandbox_none_warns(self) -> None:
        """shell_sandbox_backend=none triggers a warning."""
        ctx = self._make_ctx()
        shell_cfg = ShellAuditConfig(sandbox_backend="none", command_allowlist=["ls"])
        with patch("agent.repl_health.load_shell_audit_config", return_value=shell_cfg):
            with patch("agent.repl_health.load_git_audit_config", return_value=None):
                warnings = audit_security_defaults(ctx, production_mode=False)
        assert any("shell_sandbox_backend=none" in w for w in warnings)

    def test_shell_sandbox_none_raises_in_production(self) -> None:
        """shell_sandbox_backend=none raises RuntimeError in production mode."""
        ctx = self._make_ctx()
        shell_cfg = ShellAuditConfig(sandbox_backend="none", command_allowlist=["ls"])
        with patch("agent.repl_health.load_shell_audit_config", return_value=shell_cfg):
            with patch("agent.repl_health.load_git_audit_config", return_value=None):
                with pytest.raises(
                    RuntimeError, match="Production mode requires shell sandbox"
                ):
                    audit_security_defaults(ctx, production_mode=True)

    def test_shell_sandbox_non_firejail_warns(self) -> None:
        """shell_sandbox_backend not 'firejail' and not 'none' → warning about firejail."""
        ctx = self._make_ctx()
        shell_cfg = ShellAuditConfig(sandbox_backend="docker", command_allowlist=["ls"])
        with patch("agent.repl_health.load_shell_audit_config", return_value=shell_cfg):
            with patch("agent.repl_health.load_git_audit_config", return_value=None):
                warnings = audit_security_defaults(ctx, production_mode=False)
        assert any("firejail" in w for w in warnings)

    def test_firejail_binary_missing_raises(self) -> None:
        """shell_sandbox_backend=firejail but firejail not in PATH → RuntimeError."""
        ctx = self._make_ctx()
        shell_cfg = ShellAuditConfig(
            sandbox_backend="firejail", command_allowlist=["ls"]
        )
        with patch("agent.repl_health.load_shell_audit_config", return_value=shell_cfg):
            with patch("agent.repl_health.load_git_audit_config", return_value=None):
                with patch("shutil.which", return_value=None):
                    with pytest.raises(RuntimeError, match="firejail binary not found"):
                        audit_security_defaults(ctx, production_mode=False)

    def test_firejail_binary_present_no_error(self) -> None:
        """shell_sandbox_backend=firejail and firejail found → no sandbox error."""
        ctx = self._make_ctx()
        shell_cfg = ShellAuditConfig(
            sandbox_backend="firejail", command_allowlist=["ls"]
        )
        with patch("agent.repl_health.load_shell_audit_config", return_value=shell_cfg):
            with patch("agent.repl_health.load_git_audit_config", return_value=None):
                with patch("shutil.which", return_value="/usr/bin/firejail"):
                    warnings = audit_security_defaults(ctx, production_mode=False)
        assert not any("firejail binary not found" in w for w in warnings)

    def test_security_posture_summary_included(self) -> None:
        """Summary line appended when any fail-closed or fail-open setting is empty."""
        ctx = self._make_ctx()
        empty_git = GitAuditConfig(allowed_repo_paths=[])
        with patch("agent.repl_health.load_shell_audit_config", return_value=None):
            with patch(
                "agent.repl_health.load_git_audit_config", return_value=empty_git
            ):
                warnings = audit_security_defaults(ctx, production_mode=False)
        summary_lines = [w for w in warnings if "Security posture summary" in w]
        assert len(summary_lines) == 1
        assert "fail-closed" in summary_lines[0]

    def test_cicd_empty_workflow_allowlist_warns(self) -> None:
        """cicd.workflow_allowlist empty → DENY-ALL warning (fail-closed; both dev and production)."""
        ctx = self._make_ctx()
        empty_cicd = CicdAuditConfig(workflow_allowlist=[])
        with (
            patch("agent.repl_health.load_shell_audit_config", return_value=None),
            patch("agent.repl_health.load_git_audit_config", return_value=None),
            patch("agent.repl_health.load_github_audit_config", return_value=None),
            patch("agent.repl_health.load_cicd_audit_config", return_value=empty_cicd),
        ):
            warnings_dev = audit_security_defaults(ctx, production_mode=False)
        assert any("cicd.workflow_allowlist" in w for w in warnings_dev)
        assert any("DENY-ALL" in w for w in warnings_dev)

    def test_github_allow_force_push_warns(self) -> None:
        """github.allow_force_push=True surfaces a security warning."""
        ctx = self._make_ctx()
        gh_cfg = GitHubAuditConfig(
            allowed_repos=["owner/repo"],
            allow_force_push=True,
            require_pr_review=True,
        )
        with (
            patch("agent.repl_health.load_shell_audit_config", return_value=None),
            patch("agent.repl_health.load_git_audit_config", return_value=None),
            patch("agent.repl_health.load_github_audit_config", return_value=gh_cfg),
            patch("agent.repl_health.load_cicd_audit_config", return_value=None),
        ):
            warnings = audit_security_defaults(ctx, production_mode=False)
        assert any("allow_force_push=true" in w for w in warnings)

    def test_github_require_pr_review_false_warns(self) -> None:
        """github.require_pr_review=False surfaces a security warning."""
        ctx = self._make_ctx()
        gh_cfg = GitHubAuditConfig(
            allowed_repos=["owner/repo"],
            allow_force_push=False,
            require_pr_review=False,
        )
        with (
            patch("agent.repl_health.load_shell_audit_config", return_value=None),
            patch("agent.repl_health.load_git_audit_config", return_value=None),
            patch("agent.repl_health.load_github_audit_config", return_value=gh_cfg),
            patch("agent.repl_health.load_cicd_audit_config", return_value=None),
        ):
            warnings = audit_security_defaults(ctx, production_mode=False)
        assert any("require_pr_review=false" in w for w in warnings)

    def test_github_fail_closed_no_error_in_production(self) -> None:
        ctx = self._make_ctx(
            servers={"svc": {"auth_token": "tok"}}, security_profile="production"
        )
        gh_cfg = GitHubAuditConfig(
            allowed_repos=["owner/repo"],
            allow_force_push=False,
            require_pr_review=True,
        )
        with (
            patch("agent.repl_health.load_shell_audit_config", return_value=None),
            patch("agent.repl_health.load_git_audit_config", return_value=None),
            patch("agent.repl_health.load_github_audit_config", return_value=gh_cfg),
            patch("agent.repl_health.load_cicd_audit_config", return_value=None),
        ):
            audit_security_defaults(ctx, production_mode=True)  # must not raise

    def test_production_config_tool_definitions_strict_false_raises(self) -> None:
        ctx = self._make_ctx(
            servers={"svc": {"auth_token": "tok"}}, security_profile="production"
        )
        ctx.cfg.tool.tool_definitions_strict = False
        ctx.cfg.tool.routing_drift_strict = True
        with (
            patch("agent.repl_health.load_shell_audit_config", return_value=None),
            patch("agent.repl_health.load_git_audit_config", return_value=None),
            patch("agent.repl_health.load_github_audit_config", return_value=None),
            patch("agent.repl_health.load_cicd_audit_config", return_value=None),
        ):
            with pytest.raises(RuntimeError, match="tool_definitions_strict"):
                audit_security_defaults(ctx, production_mode=True)

    def test_production_config_routing_drift_strict_false_raises(self) -> None:
        ctx = self._make_ctx(
            servers={"svc": {"auth_token": "tok"}}, security_profile="production"
        )
        ctx.cfg.tool.tool_definitions_strict = True
        ctx.cfg.tool.routing_drift_strict = False
        with (
            patch("agent.repl_health.load_shell_audit_config", return_value=None),
            patch("agent.repl_health.load_git_audit_config", return_value=None),
            patch("agent.repl_health.load_github_audit_config", return_value=None),
            patch("agent.repl_health.load_cicd_audit_config", return_value=None),
        ):
            with pytest.raises(RuntimeError, match="routing_drift_strict"):
                audit_security_defaults(ctx, production_mode=True)

    def test_production_config_false_warns_in_local(self) -> None:
        ctx = self._make_ctx(servers={"svc": {"auth_token": "tok"}})
        ctx.cfg.tool.tool_definitions_strict = False
        ctx.cfg.tool.routing_drift_strict = False
        with (
            patch("agent.repl_health.load_shell_audit_config", return_value=None),
            patch("agent.repl_health.load_git_audit_config", return_value=None),
            patch("agent.repl_health.load_github_audit_config", return_value=None),
            patch("agent.repl_health.load_cicd_audit_config", return_value=None),
        ):
            warnings = audit_security_defaults(ctx, production_mode=False)
        assert any("tool_definitions_strict" in w for w in warnings)

    def test_production_config_all_true_no_error(self) -> None:
        ctx = self._make_ctx(
            servers={"svc": {"auth_token": "tok"}}, security_profile="production"
        )
        ctx.cfg.tool.tool_definitions_strict = True
        ctx.cfg.tool.routing_drift_strict = True
        with (
            patch("agent.repl_health.load_shell_audit_config", return_value=None),
            patch("agent.repl_health.load_git_audit_config", return_value=None),
            patch("agent.repl_health.load_github_audit_config", return_value=None),
            patch("agent.repl_health.load_cicd_audit_config", return_value=None),
        ):
            audit_security_defaults(ctx, production_mode=True)  # must not raise

    def test_unknown_tool_safety_tiers_local_warns(self) -> None:
        ctx = self._make_ctx(servers={"svc": {"auth_token": "tok"}})
        ctx.cfg.approval.tool_safety_tiers = {"nonexistent_tool": "READ_ONLY"}
        with (
            patch("agent.repl_health.load_shell_audit_config", return_value=None),
            patch("agent.repl_health.load_git_audit_config", return_value=None),
            patch("agent.repl_health.load_github_audit_config", return_value=None),
            patch("agent.repl_health.load_cicd_audit_config", return_value=None),
        ):
            warnings = audit_security_defaults(ctx, production_mode=False)
        assert any("nonexistent_tool" in w for w in warnings)

    def test_unknown_tool_safety_tiers_production_raises(self) -> None:
        ctx = self._make_ctx(
            servers={"svc": {"auth_token": "tok"}}, security_profile="production"
        )
        ctx.cfg.approval.tool_safety_tiers = {"nonexistent_tool": "READ_ONLY"}
        with (
            patch("agent.repl_health.load_shell_audit_config", return_value=None),
            patch("agent.repl_health.load_git_audit_config", return_value=None),
            patch("agent.repl_health.load_github_audit_config", return_value=None),
            patch("agent.repl_health.load_cicd_audit_config", return_value=None),
        ):
            with pytest.raises(RuntimeError):
                audit_security_defaults(ctx, production_mode=True)

    def test_unknown_tool_safety_tiers_known_keys_no_error(self) -> None:
        ctx = self._make_ctx(
            servers={"svc": {"auth_token": "tok"}}, security_profile="production"
        )
        with (
            patch("agent.repl_health.load_shell_audit_config", return_value=None),
            patch("agent.repl_health.load_git_audit_config", return_value=None),
            patch("agent.repl_health.load_github_audit_config", return_value=None),
            patch("agent.repl_health.load_cicd_audit_config", return_value=None),
        ):
            audit_security_defaults(ctx, production_mode=True)  # must not raise


# ── check_readiness() — production vs development mode ───────────────────────


class TestCheckReadiness:
    """Tests for check_readiness() production/dev mode behavior."""

    def _make_ctx(self, mock_http: object) -> MagicMock:
        ctx = MagicMock()
        ctx.cfg.llm.llm_url = "http://127.0.0.1:8080/v1/chat"
        ctx.cfg.rag.embed_url = "http://127.0.0.1:8081/embedding"
        ctx.services_required.http = mock_http
        return ctx

    @pytest.mark.asyncio
    async def test_production_all_healthy_no_raise(self) -> None:
        resp = MagicMock()
        resp.status_code = 200
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(resp)
        ctx = self._make_ctx(http)
        result = await check_readiness(ctx, production_mode=True)
        assert not result.has_issues

    @pytest.mark.asyncio
    async def test_production_service_down_raises(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        ctx = self._make_ctx(http)
        with pytest.raises(RuntimeError, match="Startup readiness check failed"):
            await check_readiness(ctx, production_mode=True)

    @pytest.mark.asyncio
    async def test_production_non_200_raises(self) -> None:
        resp = MagicMock()
        resp.status_code = 503
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(resp)
        ctx = self._make_ctx(http)
        with pytest.raises(RuntimeError, match="Startup readiness check failed"):
            await check_readiness(ctx, production_mode=True)

    @pytest.mark.asyncio
    async def test_dev_mode_service_down_warns_only(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx = self._make_ctx(http)
        result = await check_readiness(ctx, production_mode=False)
        assert result.has_issues
        assert len(result.warning_messages()) > 0

    @pytest.mark.asyncio
    async def test_dev_mode_healthy_no_issues(self) -> None:
        resp = MagicMock()
        resp.status_code = 200
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(resp)
        ctx = self._make_ctx(http)
        result = await check_readiness(ctx, production_mode=False)
        assert not result.has_issues

    @pytest.mark.asyncio
    async def test_error_message_contains_service_label(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx = self._make_ctx(http)
        with pytest.raises(RuntimeError) as exc_info:
            await check_readiness(ctx, production_mode=True)
        assert "llm" in str(exc_info.value)


class TestCheckWorkflowDefinition:
    """Tests for check_workflow_definition() preflight helper."""

    def test_missing_file_raises(self, tmp_path) -> None:
        """Missing default.json raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            check_workflow_definition(workflows_dir=tmp_path)
        assert "not found" in str(exc_info.value)
        assert "default.json" in str(exc_info.value)

    def test_present_file_passes(self, tmp_path) -> None:
        """Existing default.json raises no exception."""
        (tmp_path / "default.json").write_text("{}")
        check_workflow_definition(workflows_dir=tmp_path)  # must not raise

    def test_error_message_includes_remediation(self, tmp_path) -> None:
        """RuntimeError message includes expected remediation hint."""
        with pytest.raises(RuntimeError) as exc_info:
            check_workflow_definition(workflows_dir=tmp_path)
        assert "default.json" in str(exc_info.value)


def _create_workflow_db(
    tmp_path: Any,
    *,
    exclude_table: str | None = None,
    missing_column: tuple[str, str] | None = None,
    schema_version: str | None = WORKFLOW_SCHEMA_VERSION,
) -> str:
    """Create a minimal workflow SQLite DB for testing check_workflow_schema().

    schema_version=None creates an empty workflow_schema_version table (simulates
    a pre-existing DB created before any version was ever recorded).
    """
    db_path = str(tmp_path / "workflow.sqlite")
    conn = sqlite3.connect(db_path)
    schemas = {
        "tasks": (
            "CREATE TABLE tasks (task_id TEXT, session_id TEXT, workflow_id TEXT, status TEXT, created_at TEXT)"
        ),
        "attempts": (
            "CREATE TABLE attempts (attempt_id TEXT, task_id TEXT, stage_id TEXT, status TEXT)"
        ),
        "processed_events": (
            "CREATE TABLE processed_events (event_id TEXT, task_id TEXT)"
        ),
        "artifacts": "CREATE TABLE artifacts (artifact_id TEXT, task_id TEXT)",
        "approvals": (
            "CREATE TABLE approvals (approval_id TEXT, task_id TEXT, status TEXT)"
        ),
    }
    for table, ddl in schemas.items():
        if table == exclude_table:
            continue
        if missing_column and missing_column[0] == table:
            col = missing_column[1]
            ddl = ddl.replace(f", {col} TEXT", "").replace(f"{col} TEXT, ", "")
        conn.execute(ddl)
    if exclude_table != "workflow_schema_version":
        conn.execute(
            "CREATE TABLE workflow_schema_version (version TEXT NOT NULL, applied_at TEXT NOT NULL)"
        )
        if schema_version is not None:
            conn.execute(
                "INSERT INTO workflow_schema_version (version, applied_at) VALUES (?, ?)",
                (schema_version, "2026-01-01T00:00:00Z"),
            )
    conn.commit()
    conn.close()
    return db_path


class TestCheckWorkflowSchema:
    """Tests for check_workflow_schema() preflight helper."""

    def test_valid_schema_passes(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path)
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is True

    def test_missing_tasks_table_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, exclude_table="tasks")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "tasks" in result.error

    def test_missing_attempts_table_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, exclude_table="attempts")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "attempts" in result.error

    def test_missing_processed_events_table_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, exclude_table="processed_events")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "processed_events" in result.error

    def test_missing_artifacts_table_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, exclude_table="artifacts")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "artifacts" in result.error

    def test_missing_approvals_table_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, exclude_table="approvals")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "approvals" in result.error

    def test_missing_required_column_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, missing_column=("tasks", "workflow_id"))
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "workflow_id" in result.error

    def test_matching_schema_version_passes(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, schema_version=WORKFLOW_SCHEMA_VERSION)
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is True

    def test_missing_schema_version_row_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, schema_version=None)
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "schema version mismatch" in result.error

    def test_mismatched_schema_version_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, schema_version="0.9.0")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "schema version mismatch" in result.error

    def test_missing_workflow_schema_version_table_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, exclude_table="workflow_schema_version")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "workflow_schema_version" in result.error

    def test_missing_db_file_returns_error(self, tmp_path: Any) -> None:
        nonexistent = str(tmp_path / "nonexistent.db")
        result = check_workflow_schema(db_path=nonexistent)
        assert result.valid is False
        assert result.error is not None and "Workflow DB not found" in result.error
