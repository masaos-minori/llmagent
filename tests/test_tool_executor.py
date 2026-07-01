"""tests/test_tool_executor.py
Unit tests for tool executor infrastructure: HttpTransport retry behavior,
cache stampede protection.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from shared.tool_executor import (
    HttpTransport,
    ToolCallResult,
    ToolExecutor,
    TransportError,
)


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



