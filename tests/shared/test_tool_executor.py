"""tests/test_tool_executor.py
Unit tests for tool executor infrastructure: HttpTransport retry behavior,
error boundary classification, and HealthRegistry recording.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from shared.http_transport import HttpTransport, TransportError
from shared.mcp_config import (
    McpServerConfig,
    McpServerHealthRegistry,
    McpServerHealthState,
    StartupMode,
    TransportType,
)
from shared.runtime_tool import build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_executor import ToolExecutor
from shared.transport_dto import ToolCallResult


class TestHttpTransportRetry:
    @pytest.mark.asyncio
    async def test_retries_on_429_and_succeeds(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                req = httpx.Request("POST", url)
                if call_count < 3:
                    return httpx.Response(
                        429, request=req, json={"result": "", "is_error": False}
                    )
                return httpx.Response(
                    200, request=req, json={"result": "ok", "is_error": False}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with patch("asyncio.sleep", return_value=None):
            result = await transport.call("write_file", {"path": "a"})
        assert result.output == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retries_exhausted_returns_error(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                req = httpx.Request("POST", url)
                return httpx.Response(
                    429, request=req, json={"result": "", "is_error": False}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with patch("asyncio.sleep", return_value=None):
            with pytest.raises(Exception) as exc_info:
                await transport.call("write_file", {"path": "a"})
        assert call_count == 3
        assert "Retry exhausted" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retries_on_502_and_succeeds(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                req = httpx.Request("POST", url)
                if call_count < 3:
                    return httpx.Response(
                        502, request=req, json={"result": "", "is_error": False}
                    )
                return httpx.Response(
                    200, request=req, json={"result": "ok", "is_error": False}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with patch("asyncio.sleep", return_value=None):
            result = await transport.call("write_file", {"path": "a"})
        assert result.output == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retries_on_503_and_succeeds(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                req = httpx.Request("POST", url)
                if call_count < 3:
                    return httpx.Response(
                        503, request=req, json={"result": "", "is_error": False}
                    )
                return httpx.Response(
                    200, request=req, json={"result": "ok", "is_error": False}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with patch("asyncio.sleep", return_value=None):
            result = await transport.call("write_file", {"path": "a"})
        assert result.output == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retries_on_504_and_succeeds(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                req = httpx.Request("POST", url)
                if call_count < 3:
                    return httpx.Response(
                        504, request=req, json={"result": "", "is_error": False}
                    )
                return httpx.Response(
                    200, request=req, json={"result": "ok", "is_error": False}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with patch("asyncio.sleep", return_value=None):
            result = await transport.call("write_file", {"path": "a"})
        assert result.output == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_timeout_is_non_retryable(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                raise httpx.TimeoutException("timed out")

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with pytest.raises(TransportError) as exc_info:
            await transport.call("write_file", {"path": "a"})
        assert call_count == 1
        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_non_retryable_http_status_not_retried(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                req = httpx.Request("POST", url)
                return httpx.Response(
                    500, request=req, json={"result": "", "is_error": True}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with pytest.raises(TransportError):
            await transport.call("write_file", {"path": "a"})
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_non_retryable_400_status_not_retried(self) -> None:
        call_count = 0

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                nonlocal call_count
                call_count += 1
                req = httpx.Request("POST", url)
                return httpx.Response(
                    400, request=req, json={"result": "", "is_error": True}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )
        with pytest.raises(TransportError):
            await transport.call("write_file", {"path": "a"})
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_delay_values_via_sleep_mock(self) -> None:
        sleep_calls: list[float] = []

        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                req = httpx.Request("POST", url)
                return httpx.Response(
                    429, request=req, json={"result": "", "is_error": False}
                )

        transport = HttpTransport(
            _FakeClient(),  # type: ignore[arg-type]
            base_url="http://localhost:8080",
            server_key="test",
        )

        async def capture_sleep(*args: Any, **kwargs: Any) -> None:
            sleep_calls.extend(args)

        with patch("asyncio.sleep", side_effect=capture_sleep):
            try:
                await transport.call("write_file", {"path": "a"})
            except TransportError:
                pass  # Expected — all retries exhausted

        # attempt 0→sleep(4), attempt 1→sleep(2), attempt 2→sleep(1), then exhausted
        assert len(sleep_calls) == 3
        assert sleep_calls[0] == 4
        assert sleep_calls[1] == 2
        assert sleep_calls[2] == 1


def _http_cfg(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=url,
        startup_mode=StartupMode.PERSISTENT,
        auth_token="test-token",
    )


def _make_executor(
    configs: dict[str, McpServerConfig] | None = None,
) -> ToolExecutor:
    resolved_configs = configs or {"file_read": _http_cfg()}
    http = MagicMock(spec=httpx.AsyncClient)
    ex = ToolExecutor(
        http,
        server_configs=resolved_configs,
    )
    if "file_read" in resolved_configs:
        # Wire read_text_file -> file_read routing, mirroring the production flow
        # where ToolExecutor.set_runtime_registry() is called after discovery completes.
        tool = build_runtime_tool(
            name="read_text_file",
            server_key="file_read",
            status="active",
            is_write=False,
            requires_serial=False,
            resource_scope_kind="",
            resource_scope_keys=(),
            agent_safety_tier="READ_ONLY",
            enabled_for_llm=True,
            capabilities=(),
        )
        ex.set_runtime_registry(RuntimeToolRegistry(tools={"read_text_file": tool}))
    return ex


class TestToolExecutorErrorClassification:
    """Regression tests: error_type classification, stat counters, and HealthRegistry
    recording in ToolExecutor._raw_execute()."""

    @pytest.mark.asyncio
    async def test_http_200_success_error_type_empty(self) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor()
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok",
                is_error=False,
                request_id="req-1",
                server_key="file_read",
                error_type="",
            )
        )
        ex._transports["file_read"] = mock_transport  # type: ignore[assignment]  -- AsyncMock duck-types HttpTransport

        result = await ex._raw_execute("read_text_file", {})

        assert result.is_error is False
        assert result.error_type == ""
        assert registry.get_state("file_read") == McpServerHealthState.HEALTHY

    @pytest.mark.asyncio
    async def test_http_200_tool_error_increments_stat_tool_errors(self) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor()
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="tool error msg",
                is_error=True,
                request_id="",
                server_key="file_read",
                error_type="tool",
            )
        )
        ex._transports["file_read"] = mock_transport  # type: ignore[assignment]  -- AsyncMock duck-types HttpTransport

        result = await ex._raw_execute("read_text_file", {})

        assert result.is_error is True
        assert result.error_type == "tool"
        assert ex.stat_tool_errors.get("file_read", 0) == 1
        assert registry.get_state("file_read") == McpServerHealthState.HEALTHY

    @pytest.mark.asyncio
    async def test_http_500_transport_error_classification(self) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor()
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(side_effect=TransportError("HTTP 500"))
        ex._transports["file_read"] = mock_transport  # type: ignore[assignment]  -- AsyncMock duck-types HttpTransport

        result = await ex._raw_execute("read_text_file", {})

        assert result.is_error is True
        assert result.error_type == "transport"
        assert ex.stat_transport_errors.get("file_read", 0) == 1
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED

    @pytest.mark.asyncio
    async def test_http_503_retry_exhaustion_is_transport_error(self) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor()
        ex.set_health_registry(registry)

        class _FakeClient503:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                req = httpx.Request("POST", url)
                return httpx.Response(
                    503, request=req, json={"result": "", "is_error": False}
                )

        transport = HttpTransport(
            _FakeClient503(),  # type: ignore[arg-type]  -- duck-typed fake for test
            base_url="http://127.0.0.1:8000",
            server_key="file_read",
        )
        ex._transports["file_read"] = transport

        with patch("asyncio.sleep", return_value=None):
            result = await ex._raw_execute("read_text_file", {})

        assert result.error_type == "transport"
        assert ex.stat_transport_errors.get("file_read", 0) == 1
        assert "Retry exhausted" in result.output

    @pytest.mark.asyncio
    async def test_timeout_is_transport_error(self) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor()
        ex.set_health_registry(registry)

        class _FakeClientTimeout:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                raise httpx.TimeoutException("timed out")

        transport = HttpTransport(
            _FakeClientTimeout(),  # type: ignore[arg-type]  -- duck-typed fake for test
            base_url="http://127.0.0.1:8000",
            server_key="file_read",
        )
        ex._transports["file_read"] = transport

        result = await ex._raw_execute("read_text_file", {})

        assert result.error_type == "transport"
        assert ex.stat_transport_errors.get("file_read", 0) == 1
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "body",
        [
            b"[1, 2]",
            b'{"is_error": false}',
            b'{"result": "x", "is_error": 1}',
        ],
    )
    async def test_malformed_response_is_transport_error(self, body: bytes) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor()
        ex.set_health_registry(registry)

        class _FakeClientMalformed:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                req = httpx.Request("POST", url)
                return httpx.Response(200, request=req, content=body)

        transport = HttpTransport(
            _FakeClientMalformed(),  # type: ignore[arg-type]  -- duck-typed fake for test
            base_url="http://127.0.0.1:8000",
            server_key="file_read",
        )
        ex._transports["file_read"] = transport

        result = await ex._raw_execute("read_text_file", {})

        assert result.error_type == "transport"
        assert ex.stat_transport_errors.get("file_read", 0) == 1


# ── H-5: ensure_ready failure → ToolCallResult error ─────────────────────────


def _make_executor_with_mock_lifecycle(
    ensure_ready_side_effect: BaseException | None = None,
) -> tuple[ToolExecutor, AsyncMock, MagicMock, AsyncMock]:
    http_mock = AsyncMock()
    executor = ToolExecutor(
        http_mock,
        server_configs={},
        concurrency_limits={},
    )
    mock_lifecycle = AsyncMock()
    if ensure_ready_side_effect is not None:
        mock_lifecycle.ensure_ready.side_effect = ensure_ready_side_effect
    executor.set_lifecycle(mock_lifecycle)

    mock_registry = MagicMock()
    mock_registry.get_state.return_value = McpServerHealthState.HEALTHY
    mock_registry.is_unavailable.return_value = False
    executor.set_health_registry(mock_registry)

    mock_transport = AsyncMock()
    executor._transports["test_server"] = mock_transport
    executor._resolver.resolve = MagicMock(return_value="test_server")

    return executor, mock_lifecycle, mock_registry, mock_transport


class TestUnknownToolError:
    @pytest.mark.asyncio
    async def test_unknown_tool_raises_value_error(self) -> None:
        ex = _make_executor()
        with pytest.raises(ValueError, match=r"Unknown tool"):
            await ex._raw_execute("totally_unknown_tool", {})


class TestCheckStartupMode:
    """Regression: _check_startup_mode() still returns a disabled-server error for
    startup_mode == StartupMode.NONE after ToolRouteResolver's discovery_map/known_tools
    parameters were removed (server_configs is unaffected by that change)."""

    def test_returns_error_result_for_disabled_server(self) -> None:
        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9",
            startup_mode=StartupMode.NONE,
            auth_token="test-token",
        )
        ex = _make_executor(configs={"disabled_server": cfg})
        result = ex._check_startup_mode("disabled_server")
        assert result is not None
        assert result.is_error is True
        assert "disabled_server" in result.output
        assert "startup_mode=none" in result.output

    def test_returns_none_for_enabled_server(self) -> None:
        ex = _make_executor()
        assert ex._check_startup_mode("file_read") is None

    def test_returns_none_for_unknown_server_key(self) -> None:
        ex = _make_executor()
        assert ex._check_startup_mode("no_such_server") is None
