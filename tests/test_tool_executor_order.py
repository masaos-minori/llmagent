"""Tests locking down ToolExecutor execution order across all branches."""

from __future__ import annotations

import time
from collections import OrderedDict
from unittest.mock import AsyncMock, MagicMock

import pytest
from shared.mcp_health import McpServerHealthState
from shared.tool_cache import CacheEntry
from shared.tool_executor import ToolExecutor, TransportError
from shared.transport_dto import ToolCallResult


def _make_executor() -> tuple[ToolExecutor, dict[str, MagicMock]]:
    """Build a ToolExecutor via __new__ with all mock dependencies."""
    executor = ToolExecutor.__new__(ToolExecutor)

    mock_plugin = MagicMock()
    mock_plugin.try_execute = AsyncMock(return_value=None)
    mock_resolver = MagicMock()
    mock_lifecycle = MagicMock()
    mock_lifecycle.ensure_ready = AsyncMock(return_value=None)
    mock_health = MagicMock()
    mock_health.get_state.return_value = McpServerHealthState.HEALTHY
    mock_health.is_unavailable.return_value = False
    mock_transport = MagicMock()
    mock_transport.call = AsyncMock(
        return_value=ToolCallResult(
            output="ok", is_error=False, request_id="", server_key="srv1"
        )
    )

    executor._plugin_invoker = mock_plugin
    executor._resolver = mock_resolver
    executor._lifecycle = mock_lifecycle
    executor._health_registry = mock_health
    executor._transports = {"srv1": mock_transport}
    executor._cache: OrderedDict[str, CacheEntry] = OrderedDict()
    executor._cache_ttl = 300.0
    executor._cache_max_size = 0
    executor._inflight: dict[str, object] = {}
    executor._semaphores = None
    executor._concurrency_limits = {}
    executor.stat_cache_hits = 0
    executor.stat_tool_errors: dict[str, int] = {}
    executor.stat_transport_errors: dict[str, int] = {}
    executor._tool_error_threshold = 3

    return executor, {
        "plugin": mock_plugin,
        "resolver": mock_resolver,
        "lifecycle": mock_lifecycle,
        "health": mock_health,
        "transport": mock_transport,
    }


# --- plugin hit bypasses cache and MCP ---


@pytest.mark.asyncio
async def test_plugin_hit_bypasses_cache_and_mcp():
    call_order: list[str] = []
    executor, mocks = _make_executor()

    plugin_result = ToolCallResult(
        output="plugin_result", is_error=False, request_id="", server_key=""
    )
    mocks["plugin"].try_execute = AsyncMock(
        side_effect=lambda n, a: _append_and_return(call_order, "plugin", plugin_result)
    )
    mocks["resolver"].resolve.side_effect = lambda n: _append_and_return(
        call_order, "resolve", "srv1"
    )

    result = await executor.execute("plugin_tool", {})
    assert "plugin" in call_order
    assert "resolve" not in call_order
    assert result.output == "plugin_result"


# --- cache hit bypasses route/health/lifecycle/transport ---


@pytest.mark.asyncio
async def test_cache_hit_bypasses_raw_execute():
    executor, mocks = _make_executor()
    executor._cache["tool_a:{}"] = CacheEntry(
        output="cached", is_error=False, cached_at=time.time()
    )

    mocks["resolver"].resolve.side_effect = ValueError("should not be called")

    result = await executor.execute("tool_a", {})
    assert result.output == "cached"
    mocks["resolver"].resolve.assert_not_called()


# --- record_success NOT called on cache hit ---


@pytest.mark.asyncio
async def test_cache_hit_no_health_update():
    executor, mocks = _make_executor()
    executor._cache["tool_a:{}"] = CacheEntry(
        output="cached", is_error=False, cached_at=time.time()
    )

    await executor.execute("tool_a", {})
    mocks["health"].record_success.assert_not_called()


# --- unknown tool raises ValueError before health check ---


@pytest.mark.asyncio
async def test_unknown_tool_raises_value_error():
    executor, mocks = _make_executor()
    mocks["resolver"].resolve.side_effect = ValueError("Unknown tool: 'unknown_tool'")

    with pytest.raises(ValueError, match="Unknown tool"):
        await executor.execute("unknown_tool", {})

    mocks["health"].is_unavailable.assert_not_called()


# --- unavailable server returns error, skips lifecycle ---


@pytest.mark.asyncio
async def test_unavailable_server_skips_lifecycle():
    executor, mocks = _make_executor()
    mocks["resolver"].resolve.return_value = "srv1"
    mocks["health"].get_state.return_value = McpServerHealthState.UNAVAILABLE
    mocks["health"].is_unavailable.return_value = True

    result = await executor.execute("tool_a", {})
    assert result.is_error
    mocks["lifecycle"].ensure_ready.assert_not_called()


# --- lifecycle RuntimeError propagates, transport not called ---


@pytest.mark.asyncio
async def test_lifecycle_error_returns_transport_error_result():
    executor, mocks = _make_executor()
    mocks["resolver"].resolve.return_value = "srv1"
    mocks["lifecycle"].ensure_ready = AsyncMock(
        side_effect=RuntimeError("lifecycle failed")
    )

    result = await executor.execute("tool_a", {})

    assert result.is_error is True
    assert result.error_type == "transport"
    mocks["transport"].call.assert_not_called()


# --- transport success: full path, record_success called ---


@pytest.mark.asyncio
async def test_transport_success_full_path():
    call_order: list[str] = []
    executor, mocks = _make_executor()
    mocks["resolver"].resolve.side_effect = lambda n: _append_and_return(
        call_order, "resolve", "srv1"
    )
    mocks["health"].get_state.side_effect = lambda k: McpServerHealthState.HEALTHY
    mocks["health"].is_unavailable.side_effect = lambda k: _append_and_return(
        call_order, "health", False
    )
    mocks["lifecycle"].ensure_ready = AsyncMock(
        side_effect=lambda k: call_order.append("lifecycle")
    )
    success = ToolCallResult(
        output="ok", is_error=False, request_id="", server_key="srv1"
    )
    mocks["transport"].call = AsyncMock(
        side_effect=lambda n, a: _append_and_return(call_order, "transport", success)
    )

    result = await executor.execute("tool_a", {})
    assert call_order == ["resolve", "health", "lifecycle", "transport"]
    assert not result.is_error
    mocks["health"].record_success.assert_called_once()


# --- transport failure: record_failure called, error_type=transport ---


@pytest.mark.asyncio
async def test_transport_failure_calls_record_error():
    executor, mocks = _make_executor()
    mocks["resolver"].resolve.return_value = "srv1"
    mocks["transport"].call = AsyncMock(
        side_effect=TransportError("connection refused")
    )

    result = await executor.execute("tool_a", {})
    assert result.is_error
    assert result.error_type == "transport"
    mocks["health"].record_failure.assert_called_once()


# --- tool-level error: record_success still called (not record_failure) ---


@pytest.mark.asyncio
async def test_tool_error_still_calls_record_success():
    executor, mocks = _make_executor()
    mocks["resolver"].resolve.return_value = "srv1"
    tool_err = ToolCallResult(
        output="tool error",
        is_error=True,
        request_id="",
        server_key="srv1",
        error_type="tool",
    )
    mocks["transport"].call = AsyncMock(return_value=tool_err)

    result = await executor.execute("tool_a", {})
    assert result.is_error
    assert result.error_type == "tool"
    mocks["health"].record_success.assert_called_once()
    mocks["health"].record_failure.assert_not_called()


# --- helpers ---


def _append_and_return(call_order: list[str], label: str, value: object) -> object:
    call_order.append(label)
    return value
