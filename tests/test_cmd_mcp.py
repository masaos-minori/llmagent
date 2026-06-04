"""tests/test_cmd_mcp.py
Unit tests for agent.commands.cmd_mcp._McpMixin._cmd_mcp_status() and _cmd_mcp().
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from agent.commands.cmd_mcp import _McpMixin
from shared.mcp_config import McpServerConfig


class _Ctx:
    """Minimal stub for AgentContext."""

    def __init__(
        self,
        mcp_servers: dict[str, McpServerConfig],
        tool_defs: list | None = None,
        stdio_procs: dict | None = None,
    ) -> None:
        self.cfg = MagicMock()
        self.cfg.tool.tool_definitions = tool_defs or []
        self.cfg.mcp.mcp_servers = mcp_servers
        self.services = MagicMock()
        self.services.stdio_procs = stdio_procs or {}


class _Mcp(_McpMixin):
    def __init__(self, ctx: _Ctx) -> None:
        self._ctx = ctx  # type: ignore[assignment]


def _http(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig("http", url, [], "")


def _stdio(
    cmd: list[str] | None = None, startup_mode: str = "persistent"
) -> McpServerConfig:
    return McpServerConfig(
        "stdio", "", cmd or ["python", "s.py"], "", startup_mode=startup_mode
    )


def _mock_client() -> AsyncMock:
    mc = AsyncMock()
    mc.__aenter__ = AsyncMock(return_value=mc)
    mc.__aexit__ = AsyncMock(return_value=False)
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
        assert "2 (from config/agent.toml)" in out
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
        assert "HTTP 503" in out

    @pytest.mark.asyncio
    async def test_http_connection_error(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _Ctx({"svc": _http()})
        mcp = _Mcp(ctx)

        mc = _mock_client()
        mc.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "FAIL" in out

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
        assert "RUNNING" in out
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
        assert "DEAD" in out

    @pytest.mark.asyncio
    async def test_stdio_not_started_persistent(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        ctx = _Ctx({"worker": _stdio(startup_mode="persistent")}, stdio_procs={})
        mcp = _Mcp(ctx)

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "NOT_STARTED" in out

    @pytest.mark.asyncio
    async def test_stdio_ondemand_stopped(self, capsys: pytest.CaptureFixture) -> None:
        ctx = _Ctx({"worker": _stdio(startup_mode="ondemand")}, stdio_procs={})
        mcp = _Mcp(ctx)

        with patch(
            "agent.services.mcp_status.httpx.AsyncClient", return_value=_mock_client()
        ):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "STOPPED" in out


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
            "http", "http://127.0.0.1:8000", [], "", auth_token="secret", role="query"
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
    async def test_write_column_shows_yes_for_write_tools(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cfg = McpServerConfig(
            "http",
            "http://127.0.0.1:8000",
            [],
            "",
            tool_names=["write_file", "edit_file"],
        )
        ctx = _Ctx({"writer": cfg})
        mcp = _Mcp(ctx)

        resp = MagicMock()
        resp.status_code = 200
        mc = _mock_client()
        mc.get = AsyncMock(return_value=resp)
        with patch("agent.services.mcp_status.httpx.AsyncClient", return_value=mc):
            await mcp._cmd_mcp_status()

        out = capsys.readouterr().out
        assert "yes" in out  # write column

    @pytest.mark.asyncio
    async def test_write_column_shows_no_for_read_only_tools(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cfg = McpServerConfig(
            "http",
            "http://127.0.0.1:8000",
            [],
            "",
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
