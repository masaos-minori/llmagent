"""tests/test_startup.py
Behavior-lock tests for agent/startup.py: StartupOrchestrator._start_servers().

Migrated from TestStartSubprocessServers in tests/test_repl.py when
_start_subprocess_servers was moved to StartupOrchestrator._start_servers().
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.startup import StartupOrchestrator
from shared.mcp_config import McpServerConfig

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_startup(mcp_servers: dict[str, McpServerConfig]) -> StartupOrchestrator:
    """Return a StartupOrchestrator with mocked ctx/view for _start_servers() tests."""
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = mcp_servers
    ctx.services.tools = MagicMock()
    ctx.services.tools.set_transport = MagicMock()
    ctx.services.lifecycle = AsyncMock()
    ctx.services.lifecycle.start_http_subprocess = AsyncMock()
    ctx.services.stdio_procs = {}
    view = MagicMock()
    view.write_warning = MagicMock()
    return StartupOrchestrator(ctx, view)


def _http_subprocess_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport="http",
        url="http://127.0.0.1:9999",
        cmd=["uvicorn", "srv:app"],
        openrc_service="",
        startup_mode="subprocess",
    )


def _stdio_persistent_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport="stdio",
        url="",
        cmd=["python", "server.py"],
        openrc_service="",
        startup_mode="persistent",
    )


def _stdio_ondemand_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport="stdio",
        url="",
        cmd=["python", "server.py"],
        openrc_service="",
        startup_mode="ondemand",
    )


# ── StartupOrchestrator._start_servers ────────────────────────────────────────


class TestStartupOrchestratorStartServers:
    """Tests for StartupOrchestrator._start_servers()."""

    @pytest.mark.asyncio
    async def test_http_subprocess_calls_lifecycle(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})

        await startup._start_servers()

        startup._ctx.services.lifecycle.start_http_subprocess.assert_called_once_with(
            "web", cfg
        )

    @pytest.mark.asyncio
    async def test_http_subprocess_failure_is_swallowed(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})
        startup._ctx.services.lifecycle.start_http_subprocess.side_effect = (
            RuntimeError("port busy")
        )

        # Must not raise; failure is logged and printed as warning
        await startup._start_servers()

    @pytest.mark.asyncio
    async def test_persistent_stdio_registers_transport(self) -> None:
        cfg = _stdio_persistent_cfg()
        startup = _make_startup({"git": cfg})

        with patch("agent.startup.StdioTransport", autospec=True) as mock_transport_cls:
            mock_transport = AsyncMock()
            mock_transport.start = AsyncMock()
            mock_transport_cls.return_value = mock_transport

            await startup._start_servers()

        mock_transport.start.assert_called_once()
        startup._ctx.services.tools.set_transport.assert_called_once_with(
            "git", mock_transport
        )
        assert startup._ctx.services.stdio_procs["git"] is mock_transport

    @pytest.mark.asyncio
    async def test_persistent_stdio_failure_is_swallowed(self) -> None:
        cfg = _stdio_persistent_cfg()
        startup = _make_startup({"git": cfg})

        with patch("agent.startup.StdioTransport", autospec=True) as mock_transport_cls:
            mock_transport = AsyncMock()
            mock_transport.start.side_effect = OSError("cannot start")
            mock_transport_cls.return_value = mock_transport

            # Must not raise
            await startup._start_servers()

        startup._ctx.services.tools.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_ondemand_stdio_server_skipped(self) -> None:
        cfg = _stdio_ondemand_cfg()
        startup = _make_startup({"lazy": cfg})

        with patch("agent.startup.StdioTransport", autospec=True) as mock_transport_cls:
            await startup._start_servers()

        mock_transport_cls.assert_not_called()
        startup._ctx.services.lifecycle.start_http_subprocess.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_servers_all_processed(self) -> None:
        startup = _make_startup(
            {
                "http_srv": _http_subprocess_cfg(),
                "stdio_srv": _stdio_persistent_cfg(),
            }
        )

        with patch("agent.startup.StdioTransport", autospec=True) as mock_transport_cls:
            mock_transport = AsyncMock()
            mock_transport.start = AsyncMock()
            mock_transport_cls.return_value = mock_transport

            await startup._start_servers()

        startup._ctx.services.lifecycle.start_http_subprocess.assert_called_once()
        mock_transport.start.assert_called_once()
