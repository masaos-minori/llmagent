# Implementation: Create `tests/shared/test_tool_transport_invoker.py`

## Goal

Create a new test file `tests/shared/test_tool_transport_invoker.py` with 8 async tests for
`ToolTransportInvoker.invoke()`, covering health gating, lifecycle readiness, semaphore application,
success recording, tool-error stat increment, transport-error stat increment, health failure
recording, and transport-error result classification.

## Scope

- In-Scope: New file `tests/shared/test_tool_transport_invoker.py` with `TestToolTransportInvoker`
  class (8 test methods).
- Out-of-Scope: No changes to production code. Prerequisites: `tool_transport_invoker.py`,
  `tool_lifecycle.py`, and `tests/shared/__init__.py` must exist.

## Assumptions

1. `scripts/shared/tool_transport_invoker.py` already exists.
2. `tests/shared/__init__.py` already exists.
3. `McpServerConfig`, `McpServerHealthRegistry`, `McpServerHealthState`, `TransportType` are
   importable from `shared.mcp_config`.
4. `HttpTransport`, `TransportError` are importable from `shared.http_transport`.
5. `AsyncMock`, `MagicMock` are available from `unittest.mock`.
6. `uv run pytest` with `asyncio_mode = "auto"` is the test runner.

## Implementation

### Target file

`tests/shared/test_tool_transport_invoker.py` (new file)

### Procedure

1. Create `tests/shared/test_tool_transport_invoker.py` with the content below.
2. Run `uv run ruff format tests/shared/test_tool_transport_invoker.py`.
3. Run `uv run ruff check tests/shared/test_tool_transport_invoker.py` — expect 0 errors.
4. Run `uv run pytest tests/shared/test_tool_transport_invoker.py -v` — expect 8 passed.

### Method

```python
"""tests/shared/test_tool_transport_invoker.py
Tests for ToolTransportInvoker.invoke(): health, lifecycle, semaphore, recording.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from shared.http_transport import HttpTransport, TransportError
from shared.mcp_config import McpServerConfig, McpServerHealthRegistry, McpServerHealthState, TransportType
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
        registry.record_failure("srv")  # state -> UNAVAILABLE immediately at threshold=1
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
            return_value=ToolCallResult(output="ok", is_error=False, request_id="", server_key="srv")
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
            return_value=ToolCallResult(output="ok", is_error=False, request_id="", server_key="srv")
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
                output="tool err", is_error=True, request_id="", server_key="srv", error_type="tool"
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
            return ToolCallResult(output="ok", is_error=False, request_id="", server_key="srv")

        mock_transport = MagicMock(spec=HttpTransport)
        mock_transport.call = _slow_call
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]

        result = await invoker.invoke("srv", "some_tool", {})

        assert result.output == "ok"
        assert call_count == 1
```

### Details

- `test_health_unavailable_returns_error_result` sets `failure_threshold=1` so a single
  `record_failure` call pushes the state to `UNAVAILABLE`.
- `mock_transport.call = AsyncMock(...)` replaces `call()` on the injected mock transport.
  `# type: ignore[assignment]` is required since `_transports` is typed as `dict[str, HttpTransport]`.
- `registry.record_success = MagicMock(wraps=...)` is the spy pattern used in `test_tool_executor.py`.
- `test_semaphore_applied_with_concurrency_limit` uses a synchronous-style coroutine function
  (no sleep) to verify the semaphore is initialized and allows one call through.

## Validation plan

```bash
# Lint
uv run ruff check tests/shared/test_tool_transport_invoker.py
# Expected: 0 errors

# Run 8 tests
uv run pytest tests/shared/test_tool_transport_invoker.py -v
# Expected: 8 passed

# Regression
uv run pytest tests/test_tool_executor.py -q
# Expected: all pass
```
