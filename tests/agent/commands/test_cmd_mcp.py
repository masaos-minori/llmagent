"""tests/test_cmd_mcp.py
Unit tests for agent.commands.cmd_mcp._McpMixin._cmd_mcp_status() and _cmd_mcp().
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from agent.commands.cmd_mcp import _McpMixin
from agent.commands.exceptions import UnknownSubcommandError
from agent.lifecycle import LifecycleState
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.mcp_health import McpServerHealthState
from shared.runtime_tool import RuntimeTool
from shared.runtime_tool_registry import RuntimeToolRegistry


class _Ctx:
    """Minimal stub for AgentContext."""

    def __init__(
        self,
        mcp_servers: dict[str, McpServerConfig] | None = None,
        tool_defs: list | None = None,
        stdio_procs: dict | None = None,
        tool_safety_tiers: dict | None = None,
    ) -> None:
        self.cfg = MagicMock()
        self.cfg.tool.tool_definitions = tool_defs or []
        self.cfg.mcp.mcp_servers = mcp_servers or {}
        self.cfg.approval.tool_safety_tiers = (
            tool_safety_tiers if tool_safety_tiers is not None else {}
        )
        self.services = MagicMock()
        self.services.stdio_procs = stdio_procs or {}
        self.services_required = MagicMock()
        self.services_required.health_registry = None
        self.services_required.audit_logger = None
        self.services_required.runtime_tools = None
        self.services_required.lifecycle = MagicMock()
        self.services_required.lifecycle.get_transport_state.return_value = (
            LifecycleState.UNKNOWN
        )
        self.services_required.lifecycle.get_process_snapshot.return_value = None
        self.stats = MagicMock()
        self.stats.stat_serialization_events = []


class _Mcp(_McpMixin):
    def __init__(self, ctx: _Ctx) -> None:
        self._ctx = ctx  # type: ignore[assignment]


def _http(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig(transport=TransportType.HTTP, url=url, cmd=[], auth_token="")


def _stdio(
    cmd: list[str] | None = None, startup_mode: StartupMode = StartupMode.PERSISTENT
) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url="http://127.0.0.1:8000",
        cmd=cmd or ["python", "s.py"],
        auth_token="",
        startup_mode=startup_mode,
    )


def _registry_with(*tools: RuntimeTool) -> RuntimeToolRegistry:
    tool_map = {t.name: t for t in tools}
    return RuntimeToolRegistry(tools=tool_map)


def _mock_client() -> AsyncMock:
    """Build an AsyncClient stub whose default /health response stays synchronous.

    httpx.Response.json() is not a coroutine; an un-spec'd AsyncMock makes every
    attribute async, including json(), which then returns a coroutine instead of a
    dict to callers (_probe_mcp_health_detail) that call it without await. The
    default response's status_code is deliberately left unconfigured (not 200) so
    existing callers that rely on "unset client → non-OK → http_error" keep working;
    override `mc.get` with an explicit resp when a specific status/body is needed.
    """
    mc = AsyncMock(spec=httpx.AsyncClient)
    mc.__aenter__ = AsyncMock(return_value=mc)
    mc.__aexit__ = AsyncMock(return_value=False)
    resp = MagicMock()
    resp.json.return_value = {}
    mc.get = AsyncMock(return_value=resp)
    return mc


class TestCmdMcpStatus:
    @pytest.mark.asyncio
    async def test_http_ok(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _Ctx({"svc": _http()}, tool_defs=["t1", "t2"])
        mcp = _Mcp(ctx)

        resp = MagicMock()
        resp.status_code = 200
        mc = _mock_client()
        mc.get = AsyncMock(return_value=resp)

        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "2 (from config/tools_definitions.toml)" in out
        assert "OK" in out
        assert "svc" in out

    @pytest.mark.asyncio
    async def test_http_non_200(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)

        resp = MagicMock()
        resp.status_code = 503
        mc = _mock_client()
        mc.get = AsyncMock(return_value=resp)

        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "http_error" in out

    @pytest.mark.asyncio
    async def test_http_connection_error(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)

        mc = _mock_client()
        mc.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "fail" in out

    @pytest.mark.asyncio
    async def test_status_unchanged_after_reload_classification(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """Reload classification must not change what /mcp status shows (M-5)."""
        from agent.services.config_reload import ConfigReloadService

        old_srv = _http(url="http://localhost:8080")
        ctx = _Ctx({"svc": old_srv})
        mcp = _Mcp(ctx)

        new_srv = McpServerConfig(
            transport=TransportType.HTTP, url="http://127.0.0.1:9999", cmd=[]
        )
        reload_svc = ConfigReloadService(ctx)  # type: ignore[arg-type]
        with patch(
            "agent.config_builders._build_mcp_servers",
            return_value={"svc": new_srv, "new_one": new_srv},
        ):
            outcome = reload_svc._classify_mcp_server_changes(ctx, {})  # type: ignore[arg-type]

        resp = MagicMock()
        resp.status_code = 200
        mc = _mock_client()
        mc.get = AsyncMock(return_value=resp)
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "new_one" not in out  # pending server not shown until restart
        assert "http://localhost:8080" in out  # old URL still probed
        assert "9999" not in out  # new URL never probed
        assert "mcp_servers/svc.url" in outcome.needs_restart
        assert "mcp_servers/new_one (new server)" in outcome.needs_restart

    @pytest.mark.asyncio
    async def test_stdio_running(self, capsys: pytest.CaptureFixture) -> None:
        transport = MagicMock()
        transport.is_alive.return_value = True
        ctx = _Ctx({"worker": _stdio()}, stdio_procs={"worker": transport})
        mcp = _Mcp(ctx)

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "http_error" in out
        assert "worker" in out

    @pytest.mark.asyncio
    async def test_stdio_dead(self, capsys: pytest.CaptureFixture) -> None:
        transport = MagicMock()
        transport.is_alive.return_value = False
        ctx = _Ctx({"worker": _stdio()}, stdio_procs={"worker": transport})
        mcp = _Mcp(ctx)

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "http_error" in out

    @pytest.mark.asyncio
    async def test_stdio_not_started_persistent(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx(
            {"worker": _stdio(startup_mode=StartupMode.PERSISTENT)}, stdio_procs={}
        )
        mcp = _Mcp(ctx)

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "http_error" in out

    @pytest.mark.asyncio
    async def test_stdio_ondemand_stopped(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _Ctx(
            {"worker": _stdio(startup_mode=StartupMode.SUBPROCESS)}, stdio_procs={}
        )
        mcp = _Mcp(ctx)

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "http_error" in out

    @pytest.mark.asyncio
    async def test_unavailable_server_shown_with_reason(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """UNAVAILABLE servers get their own block with the recorded reason."""
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)

        registry = MagicMock()
        registry.get_state.return_value = McpServerHealthState.UNAVAILABLE
        registry.get_degraded_reason.return_value = "restart_limit_reached"
        ctx.services_required.health_registry = registry

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "  Unavailable servers:" in out
        assert "    [UNAVAILABLE] svc: restart_limit_reached" in out

    @pytest.mark.asyncio
    async def test_unavailable_server_without_reason(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """UNAVAILABLE servers with no recorded reason omit the trailing colon text."""
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)

        registry = MagicMock()
        registry.get_state.return_value = McpServerHealthState.UNAVAILABLE
        registry.get_degraded_reason.return_value = None
        ctx.services_required.health_registry = registry

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "  Unavailable servers:" in out
        assert "    [UNAVAILABLE] svc" in out
        assert "[UNAVAILABLE] svc:" not in out

    @pytest.mark.asyncio
    async def test_no_unavailable_block_when_all_healthy(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """No 'Unavailable servers' block appears when no server is UNAVAILABLE."""
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)

        registry = MagicMock()
        registry.get_state.return_value = McpServerHealthState.HEALTHY
        registry.get_degraded_reason.return_value = None
        ctx.services_required.health_registry = registry

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "Unavailable servers" not in out


class TestCmdMcpStatusNewColumns:
    @pytest.mark.asyncio
    async def test_column_headers_include_auth_write_role(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx({})
        mcp = _Mcp(ctx)
        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp_status()
        out = capsys.readouterr().out
        assert "AUTH" in out
        assert "WRITE" in out
        assert "ROLE" in out

    @pytest.mark.asyncio
    async def test_auth_column_shows_yes_when_token_set(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:8000",
            cmd=[],
            auth_token="secret",
            role="query",
        )
        ctx = _Ctx({"svc": cfg})
        mcp = _Mcp(ctx)

        resp = MagicMock()
        resp.status_code = 200
        mc = _mock_client()
        mc.get = AsyncMock(return_value=resp)
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        # auth_token is set → "yes"; role "query" should appear
        assert "yes" in out
        assert "query" in out

    @pytest.mark.asyncio
    async def test_write_column_shows_write_safe_for_write_tools(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:8000",
            cmd=[],
            auth_token="",
            tool_names=["write_file", "edit_file"],
        )
        tiers = {"write_file": "WRITE_SAFE", "edit_file": "WRITE_SAFE"}
        ctx = _Ctx({"writer": cfg}, tool_safety_tiers=tiers)
        mcp = _Mcp(ctx)

        resp = MagicMock()
        resp.status_code = 200
        mc = _mock_client()
        mc.get = AsyncMock(return_value=resp)
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "write-safe" in out  # tier-based WRITE column

    @pytest.mark.asyncio
    async def test_write_column_shows_no_for_read_only_tools(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:8000",
            cmd=[],
            auth_token="",
            tool_names=["read_text_file", "list_directory"],
        )
        ctx = _Ctx({"reader": cfg})
        mcp = _Mcp(ctx)

        resp = MagicMock()
        resp.status_code = 200
        mc = _mock_client()
        mc.get = AsyncMock(return_value=resp)
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "no" in out  # write column = no


class TestCmdMcp:
    @pytest.mark.asyncio
    async def test_no_args_dispatches_to_status(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx({})
        mcp = _Mcp(ctx)

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp("")

        out = capsys.readouterr().out
        assert "SERVER" in out

    @pytest.mark.asyncio
    async def test_unknown_subcommand_raises_error(self) -> None:
        ctx = _Ctx({})
        mcp = _Mcp(ctx)
        with pytest.raises(
            UnknownSubcommandError, match="Unknown subcommand 'invalid'"
        ):
            await mcp._cmd_mcp("invalid")

    @pytest.mark.asyncio
    async def test_invalid_subcommand_shows_usage(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx({})
        mcp = _Mcp(ctx)
        with pytest.raises(
            UnknownSubcommandError, match="Unknown subcommand 'install'"
        ):
            await mcp._cmd_mcp("install")

    @pytest.mark.asyncio
    async def test_status_subcommand_works(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _Ctx({})
        mcp = _Mcp(ctx)

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp("status")

        out = capsys.readouterr().out
        assert "SERVER" in out


class TestCmdMcpStatusSerialization:
    @pytest.mark.asyncio
    async def test_serialization_stats_shown_when_events_present(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx({})
        ctx.services_required.health_registry = None
        # Provide real stat_serialization_events so iteration works
        ctx.stats = MagicMock()
        ctx.stats.stat_serialization_events = [
            {
                "trigger_tool": "write_file",
                "affected_count": 2,
                "serial_reason": "side_effect",
            },
            {
                "trigger_tool": "write_file",
                "affected_count": 1,
                "serial_reason": "side_effect",
            },
        ]
        mcp = _Mcp(ctx)
        with (
            patch(
                "agent.services.mcp_status.httpx.AsyncClient",
                return_value=_mock_client(),
            ),
            patch(
                "agent.tool_runner.get_serialization_stats",
                return_value={
                    "total_events": 2,
                    "total_tools_affected": 3,
                    "tools_affected_last_round": 1,
                },
            ),
        ):
            await mcp._cmd_mcp_status()
        out = capsys.readouterr().out
        assert "Serialization" in out
        assert "2 events" in out
        assert "side_effect" in out
        assert "write_file" in out

    @pytest.mark.asyncio
    async def test_serialization_stats_hidden_when_no_events(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx({})
        ctx.stats = MagicMock()
        ctx.stats.stat_serialization_events = []
        mcp = _Mcp(ctx)
        with (
            patch(
                "agent.services.mcp_status.httpx.AsyncClient",
                return_value=_mock_client(),
            ),
            patch(
                "agent.tool_runner.get_serialization_stats",
                return_value={
                    "total_events": 0,
                    "total_tools_affected": 0,
                    "tools_affected_last_round": 0,
                },
            ),
        ):
            await mcp._cmd_mcp_status()
        out = capsys.readouterr().out
        assert "Serialization" not in out


class TestCmdMcpStatusToolDiagnostics:
    @pytest.mark.asyncio
    async def test_tool_diagnostics_table_shows_disabled_and_enabled_tools(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """Both disabled and enabled tools appear in the diagnostics table."""
        ctx = _Ctx({"svc": _http()})
        registry = _registry_with(
            RuntimeTool(
                name="read_file",
                server_key="file_read",
                server_url="http://127.0.0.1:8001",
                description="Read a file",
                input_schema={"type": "object"},
                raw_definition={},
                status="active",
                is_write=False,
                requires_serial=True,
                resource_scope="",
                agent_safety_tier="READ_ONLY",
                requires_approval=False,
                enabled_for_llm=True,
                capabilities=(),
            ),
            RuntimeTool(
                name="git_push",
                server_key="git",
                server_url="http://127.0.0.1:8002",
                description="Push to git",
                input_schema={"type": "object"},
                raw_definition={},
                status="inactive",
                is_write=True,
                requires_serial=True,
                resource_scope="",
                agent_safety_tier="WRITE_DANGEROUS",
                requires_approval=True,
                enabled_for_llm=False,
                capabilities=(),
            ),
        )
        ctx.services_required.runtime_tools = registry
        mcp = _Mcp(ctx)

        resp = MagicMock()
        resp.status_code = 200
        mc = _mock_client()
        mc.get = AsyncMock(return_value=resp)
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "Tools (RuntimeToolRegistry)" in out
        assert "read_file" in out
        assert "git_push" in out
        assert "inactive" in out

    @pytest.mark.asyncio
    async def test_tool_diagnostics_table_absent_when_registry_none(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """No diagnostics section when runtime_tools is None."""
        ctx = _Ctx({"svc": _http()})
        ctx.services_required.runtime_tools = None
        mcp = _Mcp(ctx)

        resp = MagicMock()
        resp.status_code = 200
        mc = _mock_client()
        mc.get = AsyncMock(return_value=resp)
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "Tools (RuntimeToolRegistry)" not in out

    @pytest.mark.asyncio
    async def test_tool_diagnostics_table_absent_when_registry_empty(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """No diagnostics section when registry has zero tools."""
        ctx = _Ctx({"svc": _http()})
        ctx.services_required.runtime_tools = RuntimeToolRegistry()
        mcp = _Mcp(ctx)

        resp = MagicMock()
        resp.status_code = 200
        mc = _mock_client()
        mc.get = AsyncMock(return_value=resp)
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "Tools (RuntimeToolRegistry)" not in out


class TestAppServicesMemoryOptional:
    def test_memory_is_none_when_not_enabled(self) -> None:
        from unittest.mock import MagicMock

        from agent.context import AppServices

        svc = AppServices(
            http=MagicMock(),
            llm=MagicMock(),
            tools=MagicMock(),
            lifecycle=MagicMock(),
            hist_mgr=MagicMock(),
            audit_logger=MagicMock(),
            memory=None,
        )
        assert svc.memory is None
        assert svc.lifecycle is not None


# ── /mcp command definition verification ────────────────────────────────────────


class TestMcpCommandDefinition:
    """Verify /mcp CommandDef in registry.py does not reference install."""

    def test_mcp_help_does_not_include_install(self):
        from agent.commands.registry import _COMMANDS

        mcp_def = next(cd for cd in _COMMANDS if cd.name == "/mcp")
        assert "install" not in mcp_def.help.lower()

    def test_mcp_is_prefix_async_command(self):
        from agent.commands.registry import _COMMANDS

        mcp_def = next(cd for cd in _COMMANDS if cd.name == "/mcp")
        assert mcp_def.prefix is True
        assert mcp_def.is_async is True

    def test_mcp_action_no_install(self):
        from agent.commands.enums import McpAction

        assert not hasattr(McpAction, "INSTALL")
