"""tests/test_cmd_mcp.py
Unit tests for agent.commands.cmd_mcp._McpMixin._cmd_mcp_status() and _cmd_mcp().
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from agent.commands.cmd_mcp import _McpMixin
from agent.commands.exceptions import UnknownSubcommandError
from agent.config_dataclasses import MCPConfig
from agent.lifecycle import LifecycleState
from agent.services.config_pending_state import PendingConfigState, PendingMcpRecord
from agent.services.enums import McpAvailability, McpTier
from agent.services.mcp_status import McpStatusService
from agent.services.models import McpProbeResult
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.mcp_health import McpServerHealthState
from shared.runtime_tool import RuntimeTool, build_runtime_tool
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
    return McpServerConfig(
        transport=TransportType.HTTP, url=url, cmd=[], auth_token="test-token"
    )


def _stdio(
    cmd: list[str] | None = None, startup_mode: StartupMode = StartupMode.PERSISTENT
) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url="http://127.0.0.1:8000",
        cmd=cmd or ["python", "s.py"],
        auth_token="test-token",
        startup_mode=startup_mode,
    )


def _registry_with(*tools: RuntimeTool) -> RuntimeToolRegistry:
    tool_map = {t.name: t for t in tools}
    return RuntimeToolRegistry(
        tools=tool_map, allowed_servers=frozenset(t.server_key for t in tools)
    )


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
        assert "(no RuntimeToolRegistry available)" in out
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
        from agent.services.config_outcome_classification import diff_mcp_definitions

        old_srv = _http(url="http://localhost:8080")
        ctx = _Ctx({"svc": old_srv})
        mcp = _Mcp(ctx)

        new_srv = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9999",
            cmd=[],
            auth_token="test-token",
        )
        records = diff_mcp_definitions(
            ctx.cfg.mcp,
            MCPConfig(mcp_servers={"svc": new_srv, "new_one": new_srv}),
        )
        paths = [path for record in records for path in record.field_paths]

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
        assert "mcp_servers/svc.url" in paths
        assert "mcp_servers/new_one" in paths
        assert old_srv.url == "http://localhost:8080"  # live definition untouched
        assert [r.change for r in records if r.server_key == "new_one"] == ["added"]

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
        """UNAVAILABLE servers get their own block without reason suffix."""
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)

        registry = MagicMock()
        registry.get_state.return_value = McpServerHealthState.UNAVAILABLE
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
    async def test_unavailable_server_without_reason(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """UNAVAILABLE servers omit the trailing colon text."""
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)

        registry = MagicMock()
        registry.get_state.return_value = McpServerHealthState.UNAVAILABLE
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
    async def test_unconfirmed_retained_process_shown_in_status(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """REQ-009, REQ-011: a retained exit-unconfirmed process stays named in status."""
        ctx = _Ctx({"svc": _http()})
        ctx.services_required.lifecycle.get_transport_state.return_value = (
            LifecycleState.EXIT_UNCONFIRMED
        )
        ctx.services_required.lifecycle.get_process_snapshot.return_value = {
            "server_key": "svc",
            "managed": True,
            "pid": 4242,
            "pgid": 4242,
            "running": True,
            "last_exit_code": None,
            "stderr_log": "",
            "termination_outcome": "exit_unconfirmed",
        }
        mcp = _Mcp(ctx)

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            rows = await McpStatusService(ctx).probe_all()
            assert rows[0].lifecycle_state == "exit_unconfirmed"
            assert rows[0].pid == 4242
            assert rows[0].pgid == 4242
            assert rows[0].last_shutdown_result == "exit_unconfirmed"
            assert rows[0].restart_recommended is True
            assert rows[0].operator_action_required is True
            assert rows[0].health_reason == "exit_unconfirmed"

            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "exit_unconfirmed" in out
        assert "4242" in out

    @pytest.mark.asyncio
    async def test_signal_not_delivered_process_shown_in_status(self) -> None:
        """REQ-009: a signal-not-delivered outcome maps to its own state and reason."""
        ctx = _Ctx({"svc": _http()})
        ctx.services_required.lifecycle.get_transport_state.return_value = (
            LifecycleState.SIGNAL_NOT_DELIVERED
        )
        ctx.services_required.lifecycle.get_process_snapshot.return_value = {
            "server_key": "svc",
            "managed": True,
            "pid": 4343,
            "pgid": 4343,
            "running": True,
            "last_exit_code": None,
            "stderr_log": "",
            "termination_outcome": "signal_not_delivered",
        }

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            rows = await McpStatusService(ctx).probe_all()

        assert rows[0].lifecycle_state == "signal_not_delivered"
        assert rows[0].last_shutdown_result == "signal_not_delivered"
        assert rows[0].restart_recommended is True
        assert rows[0].operator_action_required is True
        assert rows[0].health_reason == "signal_not_delivered"

    @pytest.mark.asyncio
    async def test_degraded_server_shown_with_reason(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """DEGRADED servers get their own block without reason suffix."""
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)

        registry = MagicMock()
        registry.get_state.return_value = McpServerHealthState.DEGRADED
        ctx.services_required.health_registry = registry

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "  Degraded servers:" in out
        assert "    [DEGRADED] svc" in out
        assert "[DEGRADED] svc:" not in out

    @pytest.mark.asyncio
    async def test_no_unavailable_block_when_all_healthy(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """No 'Unavailable servers' block appears when no server is UNAVAILABLE."""
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)

        registry = MagicMock()
        registry.get_state.return_value = McpServerHealthState.HEALTHY
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
            auth_token="test-token",
        )
        tiers = {"write_file": "WRITE_SAFE", "edit_file": "WRITE_SAFE"}
        ctx = _Ctx({"writer": cfg}, tool_safety_tiers=tiers)
        # Tier is derived from the runtime registry (not the removed McpServerConfig
        # tool_names field); expose the two write tools on this server so the WRITE
        # column resolves to WRITE_SAFE.
        ctx.services_required.runtime_tools = _registry_with(
            build_runtime_tool(
                name="write_file",
                server_key="writer",
                server_url="",
                description="Write a file",
                input_schema={"type": "object"},
                raw_definition={},
                status="active",
                is_write=True,
                requires_serial=False,
                resource_scope_kind="",
                resource_scope_keys={},
                agent_safety_tier="WRITE_SAFE",
                policy_version="2.1",
                preview_capability="none",
                idempotency_required=True,
                reconciliation_policy="local_state",
                retry_policy="never",
                side_effect_class="local_write",
                enabled_for_llm=True,
                capabilities=(),
            ),
            build_runtime_tool(
                name="edit_file",
                server_key="writer",
                server_url="",
                description="Edit a file",
                input_schema={"type": "object"},
                raw_definition={},
                status="active",
                is_write=True,
                requires_serial=False,
                resource_scope_kind="",
                resource_scope_keys={},
                agent_safety_tier="WRITE_SAFE",
                policy_version="2.1",
                preview_capability="none",
                idempotency_required=True,
                reconciliation_policy="local_state",
                retry_policy="never",
                side_effect_class="local_write",
                enabled_for_llm=True,
                capabilities=(),
            ),
        )
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
            auth_token="test-token",
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
                "agent.tool_run_recorder.get_serialization_stats",
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
                "agent.tool_run_recorder.get_serialization_stats",
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
            build_runtime_tool(
                name="read_file",
                server_key="file_read",
                server_url="http://127.0.0.1:8001",
                description="Read a file",
                input_schema={"type": "object"},
                raw_definition={},
                status="active",
                is_write=False,
                requires_serial=True,
                resource_scope_kind="",
                resource_scope_keys={},
                agent_safety_tier="READ_ONLY",
                policy_version="2.1",
                preview_capability="none",
                idempotency_required=False,
                reconciliation_policy="not_required",
                retry_policy="safe_read_retry",
                side_effect_class="read_only",
                enabled_for_llm=True,
                capabilities=(),
            ),
            build_runtime_tool(
                name="git_push",
                server_key="git",
                server_url="http://127.0.0.1:8002",
                description="Push to git",
                input_schema={"type": "object"},
                raw_definition={},
                status="inactive",
                is_write=True,
                requires_serial=True,
                resource_scope_kind="",
                resource_scope_keys={},
                agent_safety_tier="WRITE_DANGEROUS",
                policy_version="2.1",
                preview_capability="none",
                idempotency_required=True,
                reconciliation_policy="external_state",
                retry_policy="reconcile_then_retry",
                side_effect_class="external_write",
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
        ctx.services_required.runtime_tools = RuntimeToolRegistry(
            allowed_servers=frozenset()
        )
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
    async def test_status_line_reports_registry_totals(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """The Tools line reports LLM-visible / disabled / unavailable totals from
        RuntimeToolRegistry.diagnostics(), not the static config count."""
        ctx = _Ctx({"svc": _http()})
        registry = _registry_with(
            build_runtime_tool(
                name="read_file",
                server_key="file_read",
                server_url="http://127.0.0.1:8001",
                description="Read a file",
                input_schema={"type": "object"},
                raw_definition={},
                status="active",
                is_write=False,
                requires_serial=True,
                resource_scope_kind="",
                resource_scope_keys={},
                agent_safety_tier="READ_ONLY",
                policy_version="2.1",
                preview_capability="none",
                idempotency_required=False,
                reconciliation_policy="not_required",
                retry_policy="safe_read_retry",
                side_effect_class="read_only",
                enabled_for_llm=True,
                capabilities=(),
            ),
            build_runtime_tool(
                name="git_push",
                server_key="git",
                server_url="http://127.0.0.1:8002",
                description="Push to git",
                input_schema={"type": "object"},
                raw_definition={},
                status="inactive",
                is_write=True,
                requires_serial=True,
                resource_scope_kind="",
                resource_scope_keys={},
                agent_safety_tier="WRITE_DANGEROUS",
                policy_version="2.1",
                preview_capability="none",
                idempotency_required=True,
                reconciliation_policy="external_state",
                retry_policy="reconcile_then_retry",
                side_effect_class="external_write",
                enabled_for_llm=False,
                capabilities=(),
            ),
            build_runtime_tool(
                name="blocked_tool",
                server_key="blocked",
                server_url="http://127.0.0.1:8003",
                description="Blocked tool",
                input_schema={"type": "object"},
                raw_definition={"disabled_reason": "unavailable"},
                status="unavailable",
                is_write=False,
                requires_serial=True,
                resource_scope_kind="",
                resource_scope_keys={},
                agent_safety_tier="READ_ONLY",
                policy_version="2.1",
                preview_capability="none",
                idempotency_required=False,
                reconciliation_policy="not_required",
                retry_policy="safe_read_retry",
                side_effect_class="read_only",
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
        # 1 LLM-visible (read_file), 2 disabled (git_push + blocked_tool),
        # 1 unavailable (blocked_tool).
        assert "1 LLM-visible / 2 disabled / 1 unavailable" in out
        assert "config/tools_definitions.toml" not in out

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
            job_registry=object(),
            memory=None,
        )
        assert svc.memory is None
        assert svc.lifecycle is not None


# ── /mcp status pending-restart rows (row 21, row 22) ──────────────────────────


def _ctx_with_pending(*records: PendingMcpRecord) -> _Ctx:
    """Ctx whose container carries the pending MCP records `/reload` classified.

    `factory.py` puts the process-wide `PendingConfigState` on `AppServices`, so the
    command reads the pending rows through the ctx rather than deriving them from the
    live config (REQ-009).
    """
    ctx = _Ctx({"fixture_server": _http()})
    state = PendingConfigState()
    state.set_mcp_records(list(records))
    ctx.services = MagicMock()
    ctx.services.pending_config = state
    return ctx


class TestCmdMcpStatusPendingRows:
    """REQ-008, AC-4: a pending definition is a pending row, never a live probe row."""

    @pytest.mark.asyncio
    async def test_an_added_definition_is_a_pending_row_not_a_probe_row(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _ctx_with_pending(
            PendingMcpRecord(
                server_key="added_server",
                change="added",
                field_paths=("mcp_servers/added_server",),
            )
        )
        mcp = _Mcp(ctx)
        mc = _mock_client()
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()
        out = capsys.readouterr().out
        assert "Pending restart (MCP definitions):" in out
        assert "[added_server] added: mcp_servers/added_server" in out
        # AC-4 separation: the live probe section, which ends at the pending heading,
        # contains no row for a definition that has no live process.
        live_section = out.split("Pending restart (MCP definitions):")[0]
        assert "added_server" not in live_section

    @pytest.mark.asyncio
    async def test_a_changed_definition_names_the_field_path_not_the_value(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _ctx_with_pending(
            PendingMcpRecord(
                server_key="fixture_server",
                change="changed",
                field_paths=("mcp_servers/fixture_server.auth_token",),
            )
        )
        mcp = _Mcp(ctx)
        mc = _mock_client()
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()
        out = capsys.readouterr().out
        assert "[fixture_server] changed: mcp_servers/fixture_server.auth_token" in out
        assert "test-token" not in out  # the row names the field, never the secret

    @pytest.mark.asyncio
    async def test_a_removed_definition_is_reported_as_pending(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _ctx_with_pending(
            PendingMcpRecord(
                server_key="fixture_server",
                change="removed",
                field_paths=("mcp_servers/fixture_server",),
            )
        )
        mcp = _Mcp(ctx)
        mc = _mock_client()
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()
        out = capsys.readouterr().out
        assert "[fixture_server] removed: mcp_servers/fixture_server" in out

    @pytest.mark.asyncio
    async def test_no_pending_section_when_nothing_is_pending(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """The live status output is unchanged when no restart is pending."""
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)
        mc = _mock_client()
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()
        out = capsys.readouterr().out
        assert "svc" in out
        assert "Pending restart" not in out

    @pytest.mark.asyncio
    async def test_an_empty_pending_state_prints_no_pending_section(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """A container with the state but no records has nothing to show."""
        ctx = _ctx_with_pending()
        mcp = _Mcp(ctx)
        mc = _mock_client()
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()
        out = capsys.readouterr().out
        assert "Pending restart" not in out


class TestCmdMcpStatusHealthInterpretation:
    """The health-interpretation section stays separate from the pending section."""

    @pytest.mark.asyncio
    async def test_interpretation_lines_are_printed_for_a_server_with_issues(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)
        row = McpProbeResult(
            key="svc",
            transport="http",
            startup_mode="persistent",
            auth=True,
            tier=McpTier.READ_ONLY,
            role="read",
            availability=McpAvailability.OK,
            health="ok",
            endpoint="http://127.0.0.1:8000",
            reachable=True,
            body={
                "status": "degraded",
                "ready": False,
                "dependencies": [
                    {"name": "db", "status": "fail", "reason": "unreachable"}
                ],
            },
            dependency_summary=["db: unreachable"],
        )
        with patch.object(
            McpStatusService, "probe_all", new=AsyncMock(return_value=[row])
        ):
            await mcp._cmd_mcp_status()
        out = capsys.readouterr().out
        assert "Health interpretation:" in out
        assert "db: unreachable" in out
        assert "Pending restart" not in out

    @pytest.mark.asyncio
    async def test_no_interpretation_section_when_no_server_has_issues(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)
        row = McpProbeResult(
            key="svc",
            transport="http",
            startup_mode="persistent",
            auth=False,
            tier=McpTier.READ_ONLY,
            role="read",
            availability=McpAvailability.OK,
            health="ok",
            endpoint="http://127.0.0.1:8000",
        )
        with patch.object(
            McpStatusService, "probe_all", new=AsyncMock(return_value=[row])
        ):
            await mcp._cmd_mcp_status()
        out = capsys.readouterr().out
        assert "Health interpretation:" not in out


class TestCmdMcpTools:
    """`/mcp tools` renders the RuntimeToolRegistry diagnostics table."""

    @pytest.mark.asyncio
    async def test_the_diagnostics_table_is_printed(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx({"svc": _http()})
        registry = MagicMock()
        registry.diagnostics.return_value = [
            {
                "name": "read_file",
                "server_key": "svc",
                "config_dependent": False,
                "enabled": True,
                "disabled_reason": None,
                "enabled_for_llm": True,
            }
        ]
        ctx.services_required.runtime_tools = registry
        mcp = _Mcp(ctx)

        await mcp._cmd_mcp_tools()

        out = capsys.readouterr().out
        assert "LLM_VISIBLE" in out
        assert "read_file" in out

    @pytest.mark.asyncio
    async def test_no_registry_prints_the_missing_registry_line(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx({"svc": _http()})
        ctx.services_required.runtime_tools = None
        mcp = _Mcp(ctx)

        await mcp._cmd_mcp_tools()

        assert "No RuntimeToolRegistry available." in capsys.readouterr().out

    @pytest.mark.asyncio
    async def test_no_registered_tools_prints_the_empty_line(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx({"svc": _http()})
        registry = MagicMock()
        registry.diagnostics.return_value = []
        ctx.services_required.runtime_tools = registry
        mcp = _Mcp(ctx)

        await mcp._cmd_mcp_tools()

        assert "No tools registered." in capsys.readouterr().out


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
