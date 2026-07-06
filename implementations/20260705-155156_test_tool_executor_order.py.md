# Implementation: tests/test_tool_executor_order.py — ToolExecutor execution order tests

## Goal

Lock down `ToolExecutor` execution order using call-order recording so any future reordering of plugin check, cache, route resolve, health, lifecycle, transport, and health update is caught immediately.

## Scope

**In**: 9 test cases covering all branches of `execute()` / `_raw_execute()`.

**Out**: Source file changes, transport implementation tests.

## Assumptions

1. `ToolExecutor` importable from `shared.tool_executor`.
2. Dependencies (`plugin_invoker`, `cache`, `resolver`, `health_registry`, `lifecycle`, `transport`) are injected at construction.
3. `execute()` returns an object with `error_type: str` and `is_error: bool`.
4. `TransportError` is a specific exception type for transport failures.
5. Call order is verified via a shared `call_order: list[str]` accumulator.

## Implementation

### Target file
`tests/test_tool_executor_order.py`

### Procedure
Write one test per branch, using call-order recording pattern.

### Method

```python
import pytest
from unittest.mock import MagicMock, AsyncMock, call
from shared.tool_executor import ToolExecutor
from shared.transport import TransportError  # or wherever TransportError is defined


def _make_executor():
    """Build a ToolExecutor with all mock dependencies."""
    mock_plugin = MagicMock()
    mock_cache = MagicMock()
    mock_resolver = MagicMock()
    mock_health = MagicMock()
    mock_lifecycle = MagicMock()
    mock_transport = MagicMock()

    executor = ToolExecutor(
        plugin_invoker=mock_plugin,
        cache=mock_cache,
        resolver=mock_resolver,
        health_registry=mock_health,
        lifecycle=mock_lifecycle,
        transport_registry=mock_transport,
    )
    return executor, {
        "plugin": mock_plugin,
        "cache": mock_cache,
        "resolver": mock_resolver,
        "health": mock_health,
        "lifecycle": mock_lifecycle,
        "transport": mock_transport,
    }


# --- plugin hit bypasses everything ---

@pytest.mark.asyncio
async def test_plugin_hit_bypasses_cache_and_mcp():
    call_order = []
    executor, mocks = _make_executor()

    mocks["plugin"].try_execute.side_effect = lambda n, a: (
        call_order.append("plugin") or {"result": "plugin_result"}
    )
    mocks["cache"].get.side_effect = lambda k: call_order.append("cache") or None

    result = await executor.execute("plugin_tool", {})
    assert "plugin" in call_order
    assert "cache" not in call_order
    assert result is not None


# --- cache hit bypasses route/health/lifecycle/transport ---

@pytest.mark.asyncio
async def test_cache_hit_bypasses_raw_execute():
    call_order = []
    executor, mocks = _make_executor()

    mocks["plugin"].try_execute.side_effect = lambda n, a: (
        call_order.append("plugin") or None
    )
    cached_result = MagicMock(error_type="")
    mocks["cache"].get.side_effect = lambda k: (call_order.append("cache") or cached_result)
    mocks["resolver"].resolve.side_effect = lambda n: call_order.append("resolve") or "srv"

    result = await executor.execute("tool_a", {})
    assert call_order == ["plugin", "cache"]
    assert "resolve" not in call_order


# --- record_success NOT called on cache hit ---

@pytest.mark.asyncio
async def test_cache_hit_no_health_update():
    executor, mocks = _make_executor()
    mocks["plugin"].try_execute.return_value = None
    mocks["cache"].get.return_value = MagicMock(error_type="")

    await executor.execute("tool_a", {})
    mocks["health"].record_success.assert_not_called()


# --- unknown tool raises before health/lifecycle ---

@pytest.mark.asyncio
async def test_unknown_tool_route_error_before_health():
    call_order = []
    executor, mocks = _make_executor()
    mocks["plugin"].try_execute.return_value = None
    mocks["cache"].get.return_value = None
    mocks["resolver"].resolve.side_effect = lambda n: (
        call_order.append("resolve") or (_ for _ in ()).throw(ValueError("unknown tool"))
    )
    mocks["health"].is_unavailable.side_effect = lambda k: call_order.append("health") or False

    result = await executor.execute("unknown_tool", {})
    assert "resolve" in call_order
    assert "health" not in call_order
    assert result.is_error


# --- unavailable server skips lifecycle and transport ---

@pytest.mark.asyncio
async def test_unavailable_server_skips_lifecycle():
    call_order = []
    executor, mocks = _make_executor()
    mocks["plugin"].try_execute.return_value = None
    mocks["cache"].get.return_value = None
    mocks["resolver"].resolve.return_value = "srv1"
    mocks["health"].is_unavailable.side_effect = lambda k: (
        call_order.append("health") or True
    )
    mocks["lifecycle"].ensure_ready.side_effect = lambda k: call_order.append("lifecycle")

    result = await executor.execute("tool_a", {})
    assert "health" in call_order
    assert "lifecycle" not in call_order
    assert result.is_error


# --- lifecycle error skips transport ---

@pytest.mark.asyncio
async def test_lifecycle_error_skips_transport():
    call_order = []
    executor, mocks = _make_executor()
    mocks["plugin"].try_execute.return_value = None
    mocks["cache"].get.return_value = None
    mocks["resolver"].resolve.return_value = "srv1"
    mocks["health"].is_unavailable.return_value = False
    mocks["lifecycle"].ensure_ready.side_effect = RuntimeError("lifecycle failed")
    mocks["transport"].get.side_effect = lambda k: call_order.append("transport")

    result = await executor.execute("tool_a", {})
    assert "transport" not in call_order
    assert result.is_error


# --- transport success: full path, record_success called ---

@pytest.mark.asyncio
async def test_transport_success_full_path():
    call_order = []
    executor, mocks = _make_executor()
    mocks["plugin"].try_execute.return_value = None
    mocks["cache"].get.return_value = None
    mocks["resolver"].resolve.side_effect = lambda n: (
        call_order.append("resolve") or "srv1"
    )
    mocks["health"].is_unavailable.side_effect = lambda k: (
        call_order.append("health") or False
    )
    mocks["lifecycle"].ensure_ready.side_effect = lambda k: call_order.append("lifecycle")
    transport_mock = MagicMock()
    transport_mock.call = AsyncMock(side_effect=lambda n, a: (
        call_order.append("transport") or MagicMock(error_type="", is_error=False)
    ))
    mocks["transport"].get.return_value = transport_mock

    result = await executor.execute("tool_a", {})
    assert call_order == ["resolve", "health", "lifecycle", "transport"]
    assert not result.is_error
    mocks["health"].record_success.assert_called_once()


# --- transport failure: record_transport_error called ---

@pytest.mark.asyncio
async def test_transport_failure_calls_record_error():
    executor, mocks = _make_executor()
    mocks["plugin"].try_execute.return_value = None
    mocks["cache"].get.return_value = None
    mocks["resolver"].resolve.return_value = "srv1"
    mocks["health"].is_unavailable.return_value = False
    mocks["lifecycle"].ensure_ready.return_value = None
    transport_mock = MagicMock()
    transport_mock.call = AsyncMock(side_effect=TransportError("connection refused"))
    mocks["transport"].get.return_value = transport_mock

    result = await executor.execute("tool_a", {})
    assert result.is_error
    assert result.error_type == "transport"
    mocks["health"].record_failure.assert_called_once()


# --- tool-level error: record_success still called ---

@pytest.mark.asyncio
async def test_tool_error_still_calls_record_success():
    executor, mocks = _make_executor()
    mocks["plugin"].try_execute.return_value = None
    mocks["cache"].get.return_value = None
    mocks["resolver"].resolve.return_value = "srv1"
    mocks["health"].is_unavailable.return_value = False
    mocks["lifecycle"].ensure_ready.return_value = None
    transport_mock = MagicMock()
    transport_mock.call = AsyncMock(
        return_value=MagicMock(error_type="tool", is_error=True)
    )
    mocks["transport"].get.return_value = transport_mock

    result = await executor.execute("tool_a", {})
    assert result.is_error
    assert result.error_type == "tool"
    mocks["health"].record_success.assert_called_once()  # tool error ≠ transport error
```

## Validation plan

- `uv run pytest tests/test_tool_executor_order.py -v` — all pass.
- Verify: reordering plugin check after cache → `test_plugin_hit_bypasses_cache_and_mcp` fails.
- Verify: calling `record_success()` on cache hit → `test_cache_hit_no_health_update` fails.
- `ruff check tests/test_tool_executor_order.py` — 0 errors.
