"""tests/shared/test_tool_transport_invoker.py
Tests for ToolTransportInvoker.invoke(): health, lifecycle, semaphore, recording.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from shared.http_transport import HttpTransport, TransportError
from shared.mcp_config import (
    McpServerConfig,
    McpServerHealthRegistry,
    TransportType,
)
from shared.tool_transport_invoker import ToolTransportInvoker
from shared.transport_dto import ToolCallResult


def _http_cfg(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig(transport=TransportType.HTTP, url=url)


def _make_invoker(
    configs: dict[str, McpServerConfig] | None = None,
    concurrency_limits: dict[str, int] | None = None,
) -> ToolTransportInvoker:
    http = MagicMock(spec=httpx.AsyncClient)
    return ToolTransportInvoker(
        http=http,
        server_configs=configs or {"srv": _http_cfg()},
        concurrency_limits=concurrency_limits,
    )


class TestToolTransportInvoker:
    @pytest.mark.asyncio
    async def test_health_unavailable_returns_error_result(self) -> None:
        invoker = _make_invoker()
        registry = McpServerHealthRegistry(failure_threshold=1)
        registry.record_failure(
            "srv"
        )  # state -> UNAVAILABLE immediately at threshold=1
        invoker.set_health_registry(registry)

        result = await invoker.invoke("srv", "some_tool", {})

        assert result.is_error is True
        assert result.error_type == "tool"
        assert "unavailable" in result.output.lower()

    @pytest.mark.asyncio
    async def test_lifecycle_ensure_ready_called(self) -> None:
        invoker = _make_invoker()
        lifecycle = AsyncMock()
        invoker.set_lifecycle(lifecycle)

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="", server_key="srv"
            )
        )
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        await invoker.invoke("srv", "some_tool", {})

        lifecycle.ensure_ready.assert_awaited_once_with("srv")

    @pytest.mark.asyncio
    async def test_success_records_health_success(self) -> None:
        invoker = _make_invoker()
        registry = McpServerHealthRegistry()
        registry.record_success = MagicMock(wraps=registry.record_success)  # type: ignore[method-assign]
        invoker.set_health_registry(registry)

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="", server_key="srv"
            )
        )
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        await invoker.invoke("srv", "some_tool", {})

        assert registry.record_success.call_count == 1

    @pytest.mark.asyncio
    async def test_tool_error_increments_stat_tool_errors(self) -> None:
        invoker = _make_invoker()

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="tool err",
                is_error=True,
                request_id="",
                server_key="srv",
                error_type="tool",
            )
        )
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        await invoker.invoke("srv", "some_tool", {})

        assert invoker.stat_tool_errors.get("srv", 0) == 1

    @pytest.mark.asyncio
    async def test_transport_error_increments_stat_transport_errors(self) -> None:
        invoker = _make_invoker()

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(side_effect=TransportError("failed"))
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        await invoker.invoke("srv", "some_tool", {})

        assert invoker.stat_transport_errors.get("srv", 0) == 1

    @pytest.mark.asyncio
    async def test_transport_error_records_health_failure(self) -> None:
        invoker = _make_invoker()
        registry = McpServerHealthRegistry()
        registry.record_failure = MagicMock(wraps=registry.record_failure)  # type: ignore[method-assign]
        invoker.set_health_registry(registry)

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(side_effect=TransportError("failed"))
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        await invoker.invoke("srv", "some_tool", {})

        assert registry.record_failure.call_count == 1

    @pytest.mark.asyncio
    async def test_transport_error_returns_error_type_transport(self) -> None:
        invoker = _make_invoker()

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(side_effect=TransportError("network down"))
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        result = await invoker.invoke("srv", "some_tool", {})

        assert result.is_error is True
        assert result.error_type == "transport"

    @pytest.mark.asyncio
    async def test_semaphore_applied_with_concurrency_limit(self) -> None:
        invoker = _make_invoker(concurrency_limits={"srv": 1})

        call_count = 0

        async def _slow_call(name: str, args: dict[str, Any]) -> ToolCallResult:
            nonlocal call_count
            call_count += 1
            return ToolCallResult(
                output="ok", is_error=False, request_id="", server_key="srv"
            )

        mock_transport = MagicMock(spec=HttpTransport)
        mock_transport.call = _slow_call
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        result = await invoker.invoke("srv", "some_tool", {})

        assert result.output == "ok"
        assert call_count == 1
