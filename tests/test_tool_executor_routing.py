"""tests/test_tool_executor_routing.py
Unit tests for ToolExecutor: resolver integration, lifecycle injection,
set_lifecycle(), and transport-dispatch paths.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from shared.mcp_config import McpServerConfig
from shared.tool_executor import LifecycleProtocol, ToolExecutor


def _http_cfg(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig("http", url, [], "")


def _stdio_cfg() -> McpServerConfig:
    return McpServerConfig("stdio", "", ["python", "s.py"], "")


def _make_executor(
    configs: dict[str, McpServerConfig] | None = None,
    concurrency_limits: dict[str, int] | None = None,
) -> ToolExecutor:
    http = MagicMock(spec=httpx.AsyncClient)
    return ToolExecutor(
        http,
        cache_ttl=60.0,
        server_configs=configs or {"file_read": _http_cfg()},
        concurrency_limits=concurrency_limits,
    )


class TestResolverIntegration:
    def test_resolver_resolves_static_fallback(self) -> None:
        ex = _make_executor({"file_read": _http_cfg()})
        assert ex._resolver.resolve("read_text_file") == "file_read"

    def test_resolver_raises_for_unknown_tool(self) -> None:
        ex = _make_executor()
        with pytest.raises(ValueError, match="Unknown tool"):
            ex._resolver.resolve("no_such_tool")

    def test_concurrency_limits_unknown_key_warns(self, caplog: Any) -> None:
        import logging

        with caplog.at_level(logging.WARNING, logger="shared.tool_executor"):
            _make_executor(
                configs={"file_read": _http_cfg()},
                concurrency_limits={"totally_unknown": 2},
            )
        assert "unknown server key" in caplog.text.lower()

    def test_concurrency_limits_known_key_no_warning(self, caplog: Any) -> None:
        import logging

        with caplog.at_level(logging.WARNING, logger="shared.tool_executor"):
            _make_executor(
                configs={"file_read": _http_cfg()},
                concurrency_limits={"file_read": 2},
            )
        assert "unknown server key" not in caplog.text.lower()


class TestSetLifecycle:
    def test_set_lifecycle_stores_instance(self) -> None:
        ex = _make_executor()
        assert ex._lifecycle is None

        mock_lc = MagicMock(spec=LifecycleProtocol)
        ex.set_lifecycle(mock_lc)
        assert ex._lifecycle is mock_lc

    def test_set_lifecycle_none_clears(self) -> None:
        ex = _make_executor()
        mock_lc = MagicMock(spec=LifecycleProtocol)
        ex.set_lifecycle(mock_lc)
        ex.set_lifecycle(None)
        assert ex._lifecycle is None


class TestRawExecuteWithLifecycle:
    @pytest.mark.asyncio
    async def test_ensure_ready_called_before_transport(self) -> None:
        http = MagicMock(spec=httpx.AsyncClient)
        configs = {"file_read": _http_cfg("http://127.0.0.1:8000")}
        ex = ToolExecutor(http, cache_ttl=60.0, server_configs=configs)

        call_order: list[str] = []

        mock_lc = AsyncMock(spec=LifecycleProtocol)

        async def fake_ensure(key: str) -> None:
            call_order.append(f"ensure:{key}")

        mock_lc.ensure_ready = fake_ensure
        ex.set_lifecycle(mock_lc)

        # Patch the transport to record call order
        mock_transport = AsyncMock()

        def _record_and_ok(*a: object, **kw: object) -> tuple[str, bool]:
            call_order.append("call")
            return ("ok", False)

        mock_transport.call = AsyncMock(side_effect=_record_and_ok)
        ex._transports["file_read"] = mock_transport

        await ex._raw_execute("read_text_file", {})
        assert call_order[0] == "ensure:file_read"
        assert call_order[1] == "call"

    @pytest.mark.asyncio
    async def test_no_lifecycle_skips_ensure_ready(self) -> None:
        http = MagicMock(spec=httpx.AsyncClient)
        configs = {"file_read": _http_cfg()}
        ex = ToolExecutor(http, cache_ttl=60.0, server_configs=configs)
        assert ex._lifecycle is None

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(return_value=("result", False))
        ex._transports["file_read"] = mock_transport

        result, is_err = await ex._raw_execute("read_text_file", {})
        assert not is_err

    @pytest.mark.asyncio
    async def test_no_transport_returns_error(self) -> None:
        http = MagicMock(spec=httpx.AsyncClient)
        configs = {"shell": _stdio_cfg()}
        ex = ToolExecutor(http, cache_ttl=60.0, server_configs=configs)
        # stdio transport starts as None (not yet started)
        result, is_err = await ex._raw_execute("shell_run", {})
        assert is_err
        assert "not started" in result or "No transport" in result
