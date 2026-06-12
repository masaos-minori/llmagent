"""
tests/test_repl_health.py
Unit tests for repl_health module-level functions.

httpx.AsyncClient, StdioTransport, and AgentContext are mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from agent.repl_health import (
    _check_tool_definitions,
    _fetch_stdio_tools,
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
    async def test_returns_empty_when_no_mismatch(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
            {"function": {"name": "write_file"}},
        ]

        with patch(
            "agent.repl_health._collect_server_tool_names", new_callable=AsyncMock
        ) as mock_collect:
            mock_collect.return_value = {"read_file", "write_file"}
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
            mock_collect.return_value = {"read_file"}
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
            mock_collect.return_value = {"read_file", "delete_file"}
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
            mock_collect.return_value = {"read_file", "delete_file"}
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
            mock_collect.return_value = set()
            result = await _check_tool_definitions(ctx, strict=False)

        assert not result.has_issues


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
