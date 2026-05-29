"""tests/test_lifecycle.py
Unit tests for agent.lifecycle.ServerLifecycleManager.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.lifecycle import ServerLifecycleManager
from shared.mcp_config import McpServerConfig


def _http_cfg(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig("http", url, [], "")


def _stdio_persistent() -> McpServerConfig:
    return McpServerConfig("stdio", "", ["python", "s.py"], "")


def _stdio_ondemand(cmd: list[str] | None = None) -> McpServerConfig:
    return McpServerConfig(
        "stdio", "", cmd or ["python", "s.py"], "", startup_mode="ondemand"
    )


def _mock_tool_executor() -> MagicMock:
    ex = MagicMock()
    ex.set_transport = MagicMock()
    return ex


class TestEnsureReady:
    @pytest.mark.asyncio
    async def test_http_server_noop(self) -> None:
        configs = {"web": _http_cfg()}
        ex = _mock_tool_executor()
        mgr = ServerLifecycleManager(configs, ex, {})
        # Must not raise and must not attempt subprocess startup
        await mgr.ensure_ready("web")
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_persistent_stdio_noop(self) -> None:
        configs = {"file": _stdio_persistent()}
        ex = _mock_tool_executor()
        mgr = ServerLifecycleManager(configs, ex, {})
        await mgr.ensure_ready("file")
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_ondemand_already_alive_noop(self) -> None:
        transport = MagicMock()
        transport.is_alive.return_value = True
        configs = {"od": _stdio_ondemand()}
        ex = _mock_tool_executor()
        mgr = ServerLifecycleManager(configs, ex, {"od": transport})
        await mgr.ensure_ready("od")
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_ondemand_starts_when_not_alive(self) -> None:
        configs = {"od": _stdio_ondemand(["python", "srv.py"])}
        ex = _mock_tool_executor()
        stdio_procs: dict = {}

        with patch("agent.lifecycle.StdioTransport") as MockTransport:
            mock_t = AsyncMock()
            mock_t.is_alive.return_value = True
            MockTransport.return_value = mock_t

            mgr = ServerLifecycleManager(configs, ex, stdio_procs)
            await mgr.ensure_ready("od")

        MockTransport.assert_called_once_with(["python", "srv.py"], server_key="od")
        mock_t.start.assert_awaited_once()
        ex.set_transport.assert_called_once_with("od", mock_t)
        assert stdio_procs["od"] is mock_t

    @pytest.mark.asyncio
    async def test_ondemand_no_cmd_logs_warning(self) -> None:
        cfg = McpServerConfig(
            "stdio", "", ["python", "s.py"], "", startup_mode="ondemand"
        )
        cfg.cmd = []  # empty cmd after construction
        configs = {"od": cfg}
        ex = _mock_tool_executor()
        mgr = ServerLifecycleManager(configs, ex, {})
        # Must not raise; logs a warning
        await mgr.ensure_ready("od")
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_server_key_noop(self) -> None:
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = ServerLifecycleManager(configs, ex, {})
        await mgr.ensure_ready("nonexistent")
        ex.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_concurrent_ondemand_starts_only_once(self) -> None:
        configs = {"od": _stdio_ondemand(["python", "srv.py"])}
        ex = _mock_tool_executor()
        stdio_procs: dict = {}
        start_count = 0

        async def fake_start() -> None:
            nonlocal start_count
            await asyncio.sleep(0)  # yield to allow interleaving
            start_count += 1

        with patch("agent.lifecycle.StdioTransport") as MockTransport:
            mock_t = MagicMock()
            mock_t.is_alive = MagicMock(return_value=True)
            mock_t.start = fake_start
            MockTransport.return_value = mock_t

            mgr = ServerLifecycleManager(configs, ex, stdio_procs)
            # Fire three concurrent ensure_ready calls
            await asyncio.gather(
                mgr.ensure_ready("od"),
                mgr.ensure_ready("od"),
                mgr.ensure_ready("od"),
            )

        assert start_count == 1


class TestShutdownAll:
    @pytest.mark.asyncio
    async def test_stops_all_running_transports(self) -> None:
        t1 = AsyncMock()
        t2 = AsyncMock()
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = ServerLifecycleManager(configs, ex, {"a": t1, "b": t2})
        await mgr.shutdown_all()
        t1.stop.assert_awaited_once()
        t2.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_shutdown_tolerates_stop_errors(self) -> None:
        t1 = AsyncMock()
        t1.stop.side_effect = RuntimeError("crash")
        configs: dict[str, McpServerConfig] = {}
        ex = _mock_tool_executor()
        mgr = ServerLifecycleManager(configs, ex, {"a": t1})
        # Must not propagate the exception
        await mgr.shutdown_all()
