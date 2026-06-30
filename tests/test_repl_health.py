"""
tests/test_repl_health.py
Unit tests for repl_health module-level functions.

httpx.AsyncClient, StdioTransport, and AgentContext are mocked.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from agent.repl_health import (
    _check_tool_definitions,
    _fetch_stdio_tools,
    audit_security_defaults,
    check_readiness,
    check_workflow_definition,
    probe_mcp_health,
)
from shared.tool_executor import StdioTransport, ToolCallResult


def _async_result(value: object) -> AsyncMock:
    """Return an AsyncMock whose call returns the given value as a coroutine."""
    m = AsyncMock()
    m.return_value = value
    return m


# ── probe_mcp_health() ────────────────────────────────────────────────────────


class TestProbeMcpHealth:
    @pytest.mark.asyncio
    async def test_returns_true_on_200(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 200
        http.get = _async_result(resp)

        result = await probe_mcp_health(http, "http://localhost:8000")
        assert result is True
        http.get.assert_called_once_with("http://localhost:8000/health", timeout=5.0)

    @pytest.mark.asyncio
    async def test_returns_false_on_non_200(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 503
        http.get = _async_result(resp)

        result = await probe_mcp_health(http, "http://localhost:8000")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_exception(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get.side_effect = httpx.ConnectError("fail")

        result = await probe_mcp_health(http, "http://localhost:8000")
        assert result is False


# ── _fetch_stdio_tools() ───────────────────────────────────────────────────────


class TestFetchStdioTools:
    @pytest.mark.asyncio
    async def test_returns_empty_when_not_stdio_transport(self) -> None:
        result = await _fetch_stdio_tools("not a transport")
        assert result == set()

    @pytest.mark.asyncio
    async def test_returns_empty_when_transport_not_alive(self) -> None:
        transport = MagicMock(spec=StdioTransport)
        transport.is_alive.return_value = False
        result = await _fetch_stdio_tools(transport)
        assert result == set()

    @pytest.mark.asyncio
    async def test_returns_empty_when_isinstance_fails(self) -> None:
        transport = MagicMock()
        transport.is_alive.return_value = True
        result = await _fetch_stdio_tools(transport)
        assert result == set()

    @pytest.mark.asyncio
    async def test_returns_tool_names(self) -> None:
        transport = MagicMock(spec=StdioTransport)
        transport.is_alive.return_value = True
        transport.call = _async_result(
            ToolCallResult(
                output='{"tools": ["read_file", "write_file"]}',
                is_error=False,
                request_id="req-123",
                server_key="test",
            )
        )

        result = await _fetch_stdio_tools(transport)
        assert result == {"read_file", "write_file"}

    @pytest.mark.asyncio
    async def test_returns_empty_on_rpc_error(self) -> None:
        transport = MagicMock(spec=StdioTransport)
        transport.is_alive.return_value = True
        transport.call = _async_result(
            ToolCallResult(
                output="error", is_error=True, request_id="req-123", server_key="test"
            )
        )

        result = await _fetch_stdio_tools(transport)
        assert result == set()

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self) -> None:
        transport = MagicMock(spec=StdioTransport)
        transport.is_alive.return_value = True
        transport.call = AsyncMock(side_effect=TimeoutError("timeout"))

        result = await _fetch_stdio_tools(transport)
        assert result == set()

    @pytest.mark.asyncio
    async def test_converts_tool_names_to_strings(self) -> None:
        transport = MagicMock(spec=StdioTransport)
        transport.is_alive.return_value = True
        transport.call = _async_result(
            ToolCallResult(
                output='{"tools": ["read_file", 123]}',
                is_error=False,
                request_id="req-123",
                server_key="test",
            )
        )

        result = await _fetch_stdio_tools(transport)
        assert result == {"read_file", "123"}


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


# ── check_service_health() ────────────────────────────────────────────────────


class TestCheckServiceHealth:
    @pytest.mark.asyncio
    async def test_returns_empty_when_all_healthy(self) -> None:
        from agent.repl_health import check_service_health

        ctx = MagicMock()
        ctx.cfg.llm.llm_url = "http://localhost:8000/v1/chat/completions"
        ctx.cfg.rag.embed_url = "http://localhost:8001/v1/embeddings"
        resp = MagicMock()
        resp.status_code = 200
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(resp)
        ctx.services.http = http

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
        ctx.services.http = http

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
        ctx.services.http = http

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
        from shared.mcp_config import McpServerConfig, SecurityProfile

        mcp_servers: dict[str, Any] = {}
        if servers:
            for key, vals in servers.items():
                transport = vals.get("transport", "http")
                url = (
                    vals.get("url", "http://127.0.0.1:8000")
                    if transport == "http"
                    else ""
                )
                cmd = (
                    vals.get("cmd", ["python", "server.py"])
                    if transport == "stdio"
                    else []
                )
                mcp_servers[key] = McpServerConfig(
                    transport=transport,
                    url=url,
                    cmd=cmd,
                    auth_token=vals.get("auth_token", ""),
                )

        ctx = MagicMock()
        ctx.cfg.mcp.mcp_servers = mcp_servers
        ctx.cfg.mcp.security_profile = SecurityProfile(security_profile)
        ctx.cfg.mcp.security_lockdown_enabled = False
        ctx.cfg.shell_policy = None
        ctx.cfg.github = None
        ctx.cfg.tool = MagicMock()
        ctx.cfg.tool.allowed_tools = []
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
        from mcp.shell.models import ShellConfig as ShellCfg
        from shared.mcp_config import SecurityProfile

        ctx = self._make_ctx(
            servers={
                "web_search": {"auth_token": "tok1"},
                "file_read": {"auth_token": "tok2"},
            },
            security_profile="production",
        )
        ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
        cfg = ShellCfg(shell_sandbox_backend="firejail", command_allowlist=["ls"])
        cicd_cfg = MagicMock(workflow_allowlist=["test"])
        with patch("agent.repl_health.ShellConfig.load", return_value=cfg):
            with patch("mcp.cicd.models.CicdConfig.load", return_value=cicd_cfg):
                with patch("shutil.which", return_value="/usr/bin/firejail"):
                    warnings = audit_security_defaults(ctx, production_mode=True)
        auth_warnings = [w for w in warnings if "auth_token" in w]
        assert len(auth_warnings) == 0

    def test_stdio_servers_ignored_in_production(self) -> None:
        """Stdio servers are not checked for auth_token even in production mode."""
        from mcp.shell.models import ShellConfig as ShellCfg
        from shared.mcp_config import SecurityProfile

        ctx = self._make_ctx(
            servers={
                "stdio_server": {
                    "transport": "stdio",
                    "auth_token": "",
                },
            },
            security_profile="production",
        )
        ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
        cfg = ShellCfg(shell_sandbox_backend="firejail", command_allowlist=["ls"])
        cicd_cfg = MagicMock(workflow_allowlist=["test"])
        with patch("agent.repl_health.ShellConfig.load", return_value=cfg):
            with patch("mcp.cicd.models.CicdConfig.load", return_value=cicd_cfg):
                with patch("shutil.which", return_value="/usr/bin/firejail"):
                    warnings = audit_security_defaults(ctx, production_mode=True)
        stdio_auth_warnings = [w for w in warnings if "stdio_server" in w]
        assert len(stdio_auth_warnings) == 0

    def test_production_mode_mixed_http_stdio(self) -> None:
        """Production mode: HTTP without auth raises, stdio is ignored."""
        from shared.mcp_config import SecurityProfile

        ctx = self._make_ctx(
            servers={
                "http_server": {"auth_token": ""},
                "stdio_server": {
                    "transport": "stdio",
                    "url": "",
                    "auth_token": "",
                },
            },
            security_profile="production",
        )
        ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
        with pytest.raises(RuntimeError, match="Production mode requires auth_token"):
            audit_security_defaults(ctx, production_mode=True)

    def test_shell_config_load_failure_is_silenced(self) -> None:
        """ShellConfig.load() raising an exception does not propagate."""
        ctx = self._make_ctx()
        with patch(
            "agent.repl_health.ShellConfig.load", side_effect=OSError("no file")
        ):
            warnings = audit_security_defaults(ctx, production_mode=False)
        shell_warnings = [w for w in warnings if "shell" in w.lower()]
        assert shell_warnings == []

    def test_git_config_empty_allowed_repo_paths_warns(self) -> None:
        """git.allowed_repo_paths empty triggers a fail-closed warning."""
        from mcp.git.models import GitConfig

        ctx = self._make_ctx()
        empty_cfg = GitConfig(allowed_repo_paths=[])
        with patch("agent.repl_health.GitConfig.load", return_value=empty_cfg):
            with patch("agent.repl_health.ShellConfig.load", side_effect=OSError):
                warnings = audit_security_defaults(ctx, production_mode=False)
        assert any("git.allowed_repo_paths" in w for w in warnings)

    def test_shell_sandbox_none_warns(self) -> None:
        """shell_sandbox_backend=none triggers a warning."""
        from mcp.shell.models import ShellConfig as ShellCfg

        ctx = self._make_ctx()
        cfg = ShellCfg(shell_sandbox_backend="none", command_allowlist=["ls"])
        with patch("agent.repl_health.ShellConfig.load", return_value=cfg):
            with patch("agent.repl_health.GitConfig.load", side_effect=OSError):
                warnings = audit_security_defaults(ctx, production_mode=False)
        assert any("shell_sandbox_backend=none" in w for w in warnings)

    def test_shell_sandbox_none_raises_in_production(self) -> None:
        """shell_sandbox_backend=none raises RuntimeError in production mode."""
        from mcp.shell.models import ShellConfig as ShellCfg

        ctx = self._make_ctx()
        cfg = ShellCfg(shell_sandbox_backend="none", command_allowlist=["ls"])
        with patch("agent.repl_health.ShellConfig.load", return_value=cfg):
            with patch("agent.repl_health.GitConfig.load", side_effect=OSError):
                with pytest.raises(
                    RuntimeError, match="Production mode requires shell sandbox"
                ):
                    audit_security_defaults(ctx, production_mode=True)

    def test_shell_sandbox_non_firejail_warns(self) -> None:
        """shell_sandbox_backend not 'firejail' and not 'none' → warning about firejail."""
        from mcp.shell.models import ShellConfig as ShellCfg

        ctx = self._make_ctx()
        cfg = ShellCfg(shell_sandbox_backend="docker", command_allowlist=["ls"])
        with patch("agent.repl_health.ShellConfig.load", return_value=cfg):
            with patch("agent.repl_health.GitConfig.load", side_effect=OSError):
                warnings = audit_security_defaults(ctx, production_mode=False)
        assert any("firejail" in w for w in warnings)

    def test_firejail_binary_missing_raises(self) -> None:
        """shell_sandbox_backend=firejail but firejail not in PATH → RuntimeError."""
        from mcp.shell.models import ShellConfig as ShellCfg

        ctx = self._make_ctx()
        cfg = ShellCfg(shell_sandbox_backend="firejail", command_allowlist=["ls"])
        with patch("agent.repl_health.ShellConfig.load", return_value=cfg):
            with patch("agent.repl_health.GitConfig.load", side_effect=OSError):
                with patch("shutil.which", return_value=None):
                    with pytest.raises(RuntimeError, match="firejail binary not found"):
                        audit_security_defaults(ctx, production_mode=False)

    def test_firejail_binary_present_no_error(self) -> None:
        """shell_sandbox_backend=firejail and firejail found → no sandbox error."""
        from mcp.shell.models import ShellConfig as ShellCfg

        ctx = self._make_ctx()
        cfg = ShellCfg(shell_sandbox_backend="firejail", command_allowlist=["ls"])
        with patch("agent.repl_health.ShellConfig.load", return_value=cfg):
            with patch("agent.repl_health.GitConfig.load", side_effect=OSError):
                with patch("shutil.which", return_value="/usr/bin/firejail"):
                    warnings = audit_security_defaults(ctx, production_mode=False)
        assert not any("firejail binary not found" in w for w in warnings)

    def test_security_posture_summary_included(self) -> None:
        """Summary line appended when any fail-closed or fail-open setting is empty."""
        from mcp.git.models import GitConfig

        ctx = self._make_ctx()
        empty_git = GitConfig(allowed_repo_paths=[])
        with patch("agent.repl_health.GitConfig.load", return_value=empty_git):
            with patch("agent.repl_health.ShellConfig.load", side_effect=OSError):
                warnings = audit_security_defaults(ctx, production_mode=False)
        summary_lines = [w for w in warnings if "Security posture summary" in w]
        assert len(summary_lines) == 1
        assert "fail-closed" in summary_lines[0]

    def test_cicd_empty_workflow_allowlist_warns(self) -> None:
        """cicd.workflow_allowlist empty → DENY-ALL warning (fail-closed; both dev and production)."""
        from mcp.cicd.models import CicdConfig as CiCd

        ctx = self._make_ctx()
        empty_cicd = CiCd(workflow_allowlist=[])
        with (
            patch("mcp.cicd.models.CicdConfig.load", return_value=empty_cicd),
            patch("agent.repl_health.ShellConfig.load", side_effect=OSError),
            patch("agent.repl_health.GitConfig.load", side_effect=OSError),
        ):
            warnings_dev = audit_security_defaults(ctx, production_mode=False)
        assert any("cicd.workflow_allowlist" in w for w in warnings_dev)
        assert any("DENY-ALL" in w for w in warnings_dev)

    def test_github_allow_force_push_warns(self) -> None:
        """github.allow_force_push=True surfaces a security warning."""
        from mcp.github.models_config import GitHubConfig

        ctx = self._make_ctx()
        cfg = GitHubConfig(allow_force_push=True, require_pr_review=True)
        with (
            patch("mcp.github.models_config.GitHubConfig.load", return_value=cfg),
            patch("agent.repl_health.ShellConfig.load", side_effect=OSError),
            patch("agent.repl_health.GitConfig.load", side_effect=OSError),
        ):
            warnings = audit_security_defaults(ctx, production_mode=False)
        assert any("allow_force_push=true" in w for w in warnings)

    def test_github_require_pr_review_false_warns(self) -> None:
        """github.require_pr_review=False surfaces a security warning."""
        from mcp.github.models_config import GitHubConfig

        ctx = self._make_ctx()
        cfg = GitHubConfig(allow_force_push=False, require_pr_review=False)
        with (
            patch("mcp.github.models_config.GitHubConfig.load", return_value=cfg),
            patch("agent.repl_health.ShellConfig.load", side_effect=OSError),
            patch("agent.repl_health.GitConfig.load", side_effect=OSError),
        ):
            warnings = audit_security_defaults(ctx, production_mode=False)
        assert any("require_pr_review=false" in w for w in warnings)


# ── check_readiness() — production vs development mode ───────────────────────


class TestCheckReadiness:
    """Tests for check_readiness() production/dev mode behavior."""

    def _make_ctx(self, mock_http: object) -> MagicMock:
        ctx = MagicMock()
        ctx.cfg.llm.llm_url = "http://127.0.0.1:8001/v1/chat"
        ctx.cfg.rag.embed_url = "http://127.0.0.1:8003/embedding"
        ctx.services.http = mock_http
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

    def test_disabled_mode_returns_empty(self, tmp_path) -> None:
        """workflow_mode=disabled returns no warnings regardless of file existence."""
        warnings = check_workflow_definition("disabled", workflows_dir=tmp_path)
        assert warnings == []

    def test_auto_mode_missing_file_returns_warning(self, tmp_path) -> None:
        """workflow_mode=auto with missing file returns warning (does not raise)."""
        warnings = check_workflow_definition("auto", workflows_dir=tmp_path)
        assert len(warnings) == 1
        assert "not found" in warnings[0]

    def test_required_mode_missing_file_raises(self, tmp_path) -> None:
        """workflow_mode=required with missing file raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            check_workflow_definition("required", workflows_dir=tmp_path)
        assert "not found" in str(exc_info.value)

    def test_required_mode_file_present_returns_empty(self, tmp_path) -> None:
        """workflow_mode=required with present file returns no warnings."""
        (tmp_path / "default.json").write_text("{}")
        warnings = check_workflow_definition("required", workflows_dir=tmp_path)
        assert warnings == []

    def test_auto_mode_file_present_returns_empty(self, tmp_path) -> None:
        """workflow_mode=auto with present file returns no warnings."""
        (tmp_path / "default.json").write_text("{}")
        warnings = check_workflow_definition("auto", workflows_dir=tmp_path)
        assert warnings == []

    def test_error_message_includes_mode_and_path(self, tmp_path) -> None:
        """RuntimeError message includes current mode and expected path."""
        with pytest.raises(RuntimeError) as exc_info:
            check_workflow_definition("required", workflows_dir=tmp_path)
        msg = str(exc_info.value)
        assert "required" in msg
        assert "default.json" in msg

    def test_auto_mode_warning_includes_remediation(self, tmp_path) -> None:
        """Warning includes remediation hint for operator action."""
        warnings = check_workflow_definition("auto", workflows_dir=tmp_path)
        assert "workflow_mode=disabled" in warnings[0]
