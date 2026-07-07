"""tests/test_tool_executor.py
Unit tests for tool executor infrastructure: HttpTransport retry behavior,
cache stampede protection, error boundary classification, and HealthRegistry recording.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from shared import plugin_registry
from shared.mcp_config import (
    McpServerConfig,
    McpServerHealthRegistry,
    McpServerHealthState,
    TransportType,
)
from shared.plugin_tool_invoker import PluginToolInvoker
from shared.tool_cache import CacheEntry
from shared.tool_executor import (
    HttpTransport,
    ToolExecutor,
    TransportError,
)
from shared.transport_dto import ToolCallResult


class TestCacheStampede:
    @pytest.mark.asyncio
    async def test_concurrent_calls_share_inflight_future(self) -> None:
        """Three concurrent calls to _execute_with_cache use one _raw_execute."""
        call_count = 0

        async def _fake_raw_execute(
            tool_name: str, args: dict[str, Any]
        ) -> ToolCallResult:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return ToolCallResult(
                output="ok", is_error=False, request_id="", server_key=""
            )

        executor = ToolExecutor.__new__(ToolExecutor)
        executor._cache = {}
        executor._cache_ttl = 60.0
        executor._cache_max_size = 100
        executor._inflight = {}
        executor.stat_cache_hits = 0
        executor._raw_execute = _fake_raw_execute

        results = await asyncio.gather(
            executor._execute_with_cache("write_file", {"path": "a"}),
            executor._execute_with_cache("write_file", {"path": "a"}),
            executor._execute_with_cache("write_file", {"path": "a"}),
        )
        assert call_count == 1  # only one actual execution
        assert all(r.output == "ok" for r in results)

    @pytest.mark.asyncio
    async def test_inflight_cleared_after_completion(self) -> None:
        """_inflight dict entry is removed after the future resolves."""
        call_count = 0

        async def _fake_raw_execute(
            tool_name: str, args: dict[str, Any]
        ) -> ToolCallResult:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return ToolCallResult(
                output="ok", is_error=False, request_id="", server_key=""
            )

        executor = ToolExecutor.__new__(ToolExecutor)
        executor._cache = {}
        executor._cache_ttl = 60.0
        executor._cache_max_size = 100
        executor._inflight = {}
        executor.stat_cache_hits = 0
        executor._raw_execute = _fake_raw_execute

        await executor._execute_with_cache("write_file", {"path": "a"})
        assert call_count == 1
        assert "write_file:" not in executor._inflight


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
            base_url="http://localhost:8001",
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
            base_url="http://localhost:8001",
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
            base_url="http://localhost:8001",
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
            base_url="http://localhost:8001",
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
            base_url="http://localhost:8001",
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
            base_url="http://localhost:8001",
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
            base_url="http://localhost:8001",
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
            base_url="http://localhost:8001",
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


class TestPluginReturnValidation:
    @pytest.fixture(autouse=True)
    def _reset_registry(self):
        plugin_registry._reset_for_testing()
        yield
        plugin_registry._reset_for_testing()

    def _make_executor(self) -> ToolExecutor:
        executor = ToolExecutor.__new__(ToolExecutor)
        executor._cache = {}
        executor._cache_ttl = 60.0
        executor._cache_max_size = 100
        executor._inflight = {}
        executor.stat_cache_hits = 0
        executor._plugin_invoker = PluginToolInvoker()
        return executor

    @pytest.mark.asyncio
    async def test_non_tuple_return_returns_error_result(self) -> None:
        """Plugin returns str -> ToolCallResult(is_error=True)."""

        async def _fn(args: dict) -> Any:
            return "not_a_tuple"

        plugin_registry._tools["test_tool"] = (_fn, "test")
        result = await self._make_executor().execute("test_tool", {})
        assert result.is_error is True
        assert result.error_type == "plugin_contract"

    @pytest.mark.asyncio
    async def test_one_element_tuple_returns_error_result(self) -> None:
        """Plugin returns ('ok',) -> ToolCallResult(is_error=True)."""

        async def _fn(args: dict) -> Any:
            return ("ok",)

        plugin_registry._tools["test_tool"] = (_fn, "test")
        result = await self._make_executor().execute("test_tool", {})
        assert result.is_error is True
        assert result.error_type == "plugin_contract"

    @pytest.mark.asyncio
    async def test_valid_two_element_tuple(self) -> None:
        """Plugin returns ('ok', False) -> ToolCallResult with output='ok', is_error=False."""

        async def _fn(args: dict) -> Any:
            return ("ok", False)

        plugin_registry._tools["test_tool"] = (_fn, "test")
        result = await self._make_executor().execute("test_tool", {})
        assert result.output == "ok"
        assert result.is_error is False

    @pytest.mark.asyncio
    async def test_three_element_tuple_returns_error_result(self) -> None:
        """Plugin returns ('ok', False, 'extra') -> ToolCallResult(is_error=True)."""

        async def _fn(args: dict) -> Any:
            return ("ok", False, "extra")

        plugin_registry._tools["test_tool"] = (_fn, "test")
        result = await self._make_executor().execute("test_tool", {})
        assert result.is_error is True
        assert result.error_type == "plugin_contract"

    @pytest.mark.asyncio
    async def test_wrong_output_type_returns_error_result(self) -> None:
        """Plugin returns (123, False) -> ToolCallResult(is_error=True)."""

        async def _fn(args: dict) -> Any:
            return (123, False)

        plugin_registry._tools["test_tool"] = (_fn, "test")
        result = await self._make_executor().execute("test_tool", {})
        assert result.is_error is True
        assert result.error_type == "plugin_contract"

    @pytest.mark.asyncio
    async def test_wrong_is_error_type_returns_error_result(self) -> None:
        """Plugin returns ('ok', 'no') -> ToolCallResult(is_error=True)."""

        async def _fn(args: dict) -> Any:
            return ("ok", "no")

        plugin_registry._tools["test_tool"] = (_fn, "test")
        result = await self._make_executor().execute("test_tool", {})
        assert result.is_error is True
        assert result.error_type == "plugin_contract"


class TestToolExecutorErrorBoundary:
    _SK = "test"

    def _make_ex(self, fake_client: Any) -> ToolExecutor:
        cfg = McpServerConfig(transport=TransportType.HTTP, url="http://localhost:9999")
        ex = ToolExecutor(
            http=fake_client,  # type: ignore[arg-type]  -- duck-typed fake for test
            cache_ttl=60.0,
            server_configs={self._SK: cfg},
        )
        ex._resolver = MagicMock()  # type: ignore[assignment]  -- stub resolver for test
        ex._resolver.resolve.return_value = self._SK
        return ex

    def _spy(self, ex: ToolExecutor) -> McpServerHealthRegistry:
        registry = McpServerHealthRegistry()
        registry.record_success = MagicMock(wraps=registry.record_success)  # type: ignore[method-assign]  -- spy
        registry.record_failure = MagicMock(wraps=registry.record_failure)  # type: ignore[method-assign]  -- spy
        ex.set_health_registry(registry)
        return registry

    @pytest.mark.asyncio
    async def test_http_200_is_error_true_increments_tool_error(self) -> None:
        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                return httpx.Response(
                    200,
                    request=httpx.Request("POST", url),
                    json={"result": "err msg", "is_error": True},
                )

        ex = self._make_ex(_FakeClient())
        registry = self._spy(ex)
        result = await ex._raw_execute("write_file", {})
        assert result.error_type == "tool"
        assert ex.stat_tool_errors.get(self._SK, 0) == 1
        assert registry.record_success.call_count == 1
        assert registry.record_failure.call_count == 0

    @pytest.mark.asyncio
    async def test_http_500_raises_transport_error_internally(self) -> None:
        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                return httpx.Response(
                    500,
                    request=httpx.Request("POST", url),
                    json={"result": "", "is_error": False},
                )

        ex = self._make_ex(_FakeClient())
        registry = self._spy(ex)
        result = await ex._raw_execute("write_file", {})
        assert result.error_type == "transport"
        assert ex.stat_transport_errors.get(self._SK, 0) == 1
        assert registry.record_failure.call_count == 1
        assert registry.record_success.call_count == 0

    @pytest.mark.asyncio
    async def test_timeout_classified_as_transport_error(self) -> None:
        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                raise httpx.TimeoutException("timed out")

        ex = self._make_ex(_FakeClient())
        registry = self._spy(ex)
        result = await ex._raw_execute("write_file", {})
        assert result.error_type == "transport"
        assert ex.stat_transport_errors.get(self._SK, 0) == 1
        assert registry.record_failure.call_count == 1

    @pytest.mark.asyncio
    async def test_malformed_response_classified_as_transport_error(self) -> None:
        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                return httpx.Response(
                    200,
                    request=httpx.Request("POST", url),
                    json={"no_result_key": "bad"},
                )

        ex = self._make_ex(_FakeClient())
        registry = self._spy(ex)
        result = await ex._raw_execute("write_file", {})
        assert result.error_type == "transport"
        assert ex.stat_transport_errors.get(self._SK, 0) == 1
        assert registry.record_failure.call_count == 1

    @pytest.mark.asyncio
    async def test_503_retry_exhausted_becomes_transport_error(self) -> None:
        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                return httpx.Response(
                    503,
                    request=httpx.Request("POST", url),
                    json={"result": "", "is_error": False},
                )

        ex = self._make_ex(_FakeClient())
        registry = self._spy(ex)
        with patch("asyncio.sleep", return_value=None):
            result = await ex._raw_execute("write_file", {})
        assert result.error_type == "transport"
        assert ex.stat_transport_errors.get(self._SK, 0) == 1
        assert registry.record_failure.call_count == 1

    @pytest.mark.asyncio
    async def test_tool_error_calls_record_success(self) -> None:
        class _FakeClient:
            async def post(self, url: str, **kw: Any) -> httpx.Response:
                return httpx.Response(
                    200,
                    request=httpx.Request("POST", url),
                    json={"result": "err msg", "is_error": True},
                )

        ex = self._make_ex(_FakeClient())
        registry = self._spy(ex)
        await ex._raw_execute("write_file", {})
        assert registry.record_success.call_count == 1
        assert registry.record_failure.call_count == 0


def _http_cfg(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig(transport=TransportType.HTTP, url=url)


def _make_executor(
    configs: dict[str, McpServerConfig] | None = None,
) -> ToolExecutor:
    http = MagicMock(spec=httpx.AsyncClient)
    return ToolExecutor(
        http,
        cache_ttl=60.0,
        server_configs=configs or {"file_read": _http_cfg()},
    )


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

    @pytest.mark.asyncio
    async def test_cache_hit_no_health_registry_update(self) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor()
        ex._cache_ttl = 3600.0
        ex.set_health_registry(registry)

        cache_key = "read_text_file:{}"
        ex._cache[cache_key] = CacheEntry(
            output="cached", is_error=False, cached_at=time.time()
        )

        result = await ex._execute_with_cache("read_text_file", {})

        assert result.request_id == ""
        assert ex.stat_cache_hits == 1
        assert registry.get_state("file_read") == McpServerHealthState.HEALTHY


# ── H-5: ensure_ready failure → ToolCallResult error ─────────────────────────


def _make_executor_with_mock_lifecycle(
    ensure_ready_side_effect: BaseException | None = None,
) -> tuple[ToolExecutor, AsyncMock, MagicMock, AsyncMock]:
    http_mock = AsyncMock()
    executor = ToolExecutor(
        http_mock,
        cache_ttl=0,
        server_configs={},
        cache_max_size=0,
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


class TestEnsureReadyFailureHandling:
    @pytest.mark.asyncio
    async def test_runtime_error_returns_transport_error(self) -> None:
        executor, _, _, mock_transport = _make_executor_with_mock_lifecycle(
            ensure_ready_side_effect=RuntimeError("startup failed")
        )
        result = await executor._raw_execute("test_tool", {})
        assert result.is_error is True
        assert result.error_type == "transport"
        assert "ensure_ready failed" in result.output
        mock_transport.call.assert_not_called()

    @pytest.mark.asyncio
    async def test_os_error_returns_transport_error(self) -> None:
        executor, _, _, mock_transport = _make_executor_with_mock_lifecycle(
            ensure_ready_side_effect=OSError("command not found")
        )
        result = await executor._raw_execute("test_tool", {})
        assert result.is_error is True
        assert result.error_type == "transport"
        mock_transport.call.assert_not_called()

    @pytest.mark.asyncio
    async def test_error_calls_record_failure(self) -> None:
        executor, _, mock_registry, _ = _make_executor_with_mock_lifecycle(
            ensure_ready_side_effect=RuntimeError("startup failed")
        )
        await executor._raw_execute("test_tool", {})
        mock_registry.record_failure.assert_called_once_with("test_server")

    @pytest.mark.asyncio
    async def test_transport_not_called_after_lifecycle_error(self) -> None:
        executor, _, _, mock_transport = _make_executor_with_mock_lifecycle(
            ensure_ready_side_effect=RuntimeError("startup failed")
        )
        await executor._raw_execute("test_tool", {})
        mock_transport.call.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_successful_lifecycle_calls_transport(self) -> None:
        executor, _, _, mock_transport = _make_executor_with_mock_lifecycle(
            ensure_ready_side_effect=None
        )
        mock_transport.call.return_value = ToolCallResult(
            output="ok", is_error=False, request_id="", server_key="test_server"
        )
        result = await executor._raw_execute("test_tool", {})
        assert result.is_error is False
        mock_transport.call.assert_awaited_once()
