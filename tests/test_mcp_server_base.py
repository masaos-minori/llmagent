"""tests/test_mcp_server_base.py
Unit tests for MCPServer base class: list_tools(), health(), and the
__list_tools__ introspection protocol.
"""

from __future__ import annotations

import asyncio

import orjson
import pytest
from mcp.server import MCPServer


class _SimpleServer(MCPServer):
    server_name = "test-mcp"
    server_version = "1.0"
    http_host = "127.0.0.1"
    http_port = 9999
    app_module = "test:app"
    mcp_tools = [
        {"name": "tool_a", "description": "Tool A"},
        {"name": "tool_b", "description": "Tool B"},
    ]

    async def dispatch(self, name: str, args: dict) -> tuple[str, bool]:
        if name == "tool_a":
            return "result_a", False
        return f"unknown: {name}", True


class _EmptyServer(MCPServer):
    server_name = "empty-mcp"
    server_version = "1.0"
    http_port = 9998
    app_module = "empty:app"

    async def dispatch(self, name: str, args: dict) -> tuple[str, bool]:
        return "noop", False


class TestListTools:
    def test_returns_tool_names(self) -> None:
        srv = _SimpleServer()
        assert srv.list_tools() == ["tool_a", "tool_b"]

    def test_empty_mcp_tools_attribute_missing_returns_empty_list(self) -> None:
        srv = _EmptyServer()
        assert srv.list_tools() == []


class TestHealth:
    def test_default_health_returns_ok(self) -> None:
        srv = _SimpleServer()
        assert srv.health() == {"status": "ok"}


class TestRunStdio:
    """Test run_stdio() directly by injecting a pre-fed StreamReader."""

    @pytest.mark.asyncio
    async def test_list_tools_rpc_via_run_stdio(self) -> None:
        srv = _SimpleServer()
        request = orjson.dumps({"id": 1, "name": "__list_tools__", "args": {}}) + b"\n"

        pre_fed_reader = asyncio.StreamReader()
        pre_fed_reader.feed_data(request)
        pre_fed_reader.feed_eof()

        written: list[str] = []

        from unittest.mock import AsyncMock, MagicMock, patch  # noqa: PLC0415

        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock(return_value=(MagicMock(), MagicMock()))

        with (
            patch("asyncio.get_running_loop", return_value=mock_loop),
            patch("asyncio.StreamReader", return_value=pre_fed_reader),
            patch("asyncio.StreamReaderProtocol"),
            patch("sys.stdout") as mock_stdout,
        ):
            mock_stdout.write = lambda s: written.append(s)
            mock_stdout.flush = lambda: None
            await srv.run_stdio()

        assert len(written) == 1
        resp = orjson.loads(written[0])
        assert resp["id"] == 1
        assert not resp["is_error"]
        assert orjson.loads(resp["result"])["tools"] == ["tool_a", "tool_b"]

    @pytest.mark.asyncio
    async def test_normal_dispatch_via_run_stdio(self) -> None:
        srv = _SimpleServer()
        request = orjson.dumps({"id": 2, "name": "tool_a", "args": {}}) + b"\n"

        pre_fed_reader = asyncio.StreamReader()
        pre_fed_reader.feed_data(request)
        pre_fed_reader.feed_eof()

        written: list[str] = []

        from unittest.mock import AsyncMock, MagicMock, patch  # noqa: PLC0415

        mock_loop = MagicMock()
        mock_loop.connect_read_pipe = AsyncMock(return_value=(MagicMock(), MagicMock()))

        with (
            patch("asyncio.get_running_loop", return_value=mock_loop),
            patch("asyncio.StreamReader", return_value=pre_fed_reader),
            patch("asyncio.StreamReaderProtocol"),
            patch("sys.stdout") as mock_stdout,
        ):
            mock_stdout.write = lambda s: written.append(s)
            mock_stdout.flush = lambda: None
            await srv.run_stdio()

        assert len(written) == 1
        resp = orjson.loads(written[0])
        assert resp["id"] == 2
        assert not resp["is_error"]
        assert resp["result"] == "result_a"
