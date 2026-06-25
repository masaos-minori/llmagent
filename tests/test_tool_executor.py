"""tests/test_tool_executor.py
Unit tests for tool executor infrastructure: StdioTransport response parsing,
HttpTransport retry behavior, cache stampede protection, and stop() cleanup.
"""

from __future__ import annotations

import asyncio
import types
from typing import Any
from unittest.mock import patch

import httpx
import orjson
import pytest
from shared.tool_executor import (
    HttpTransport,
    StdioTransport,
    ToolCallResult,
    ToolExecutor,
)


class TestStdioTransportResponseId:
    def test_response_id_mismatch_raises(self) -> None:
        resp_bytes = orjson.dumps({"id": 99, "result": "ok", "is_error": False})
        with pytest.raises(ValueError, match="Response ID mismatch"):
            StdioTransport._parse_stdio_response(resp_bytes, expected_id=1)

    def test_response_id_match_succeeds(self) -> None:
        resp_bytes = orjson.dumps({"id": 1, "result": "ok", "is_error": False})
        result = StdioTransport._parse_stdio_response(resp_bytes, expected_id=1)
        assert result.output == "ok"
        assert not result.is_error

    def test_no_expected_id_skips_validation(self) -> None:
        resp_bytes = orjson.dumps({"id": 99, "result": "ok", "is_error": False})
        result = StdioTransport._parse_stdio_response(resp_bytes)
        assert result.output == "ok"
        assert not result.is_error


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


class TestStdioTransportStop:
    @pytest.mark.asyncio
    async def test_stop_no_zombie_after_kill(self, monkeypatch: Any) -> None:
        """stop() must await wait() after terminate to prevent zombie processes."""
        transport = StdioTransport(cmd=["cat"], server_key="test")

        terminated = False
        killed = False

        class _FakeProc:
            returncode: int | None = None
            stdin: Any = None

            def is_alive(self) -> bool:
                return self.returncode is None

            def terminate(self) -> None:
                nonlocal terminated
                terminated = True

            def kill(self) -> None:
                nonlocal killed
                killed = True

            async def wait(self) -> None:
                pass  # replaced by monkeypatch

        transport._proc = _FakeProc()

        first_call = True

        async def _fake_wait(self) -> None:
            nonlocal first_call
            if first_call:
                first_call = False
                raise TimeoutError("timeout")
            self.returncode = -15  # SIGTERM

        monkeypatch.setattr(
            transport._proc, "wait", types.MethodType(_fake_wait, transport._proc)
        )
        with patch.object(transport._proc, "stdin", None):
            with patch("asyncio.sleep", return_value=None):
                await transport.stop()
        assert terminated is True
        assert killed is False  # kill() should not be called after terminate succeeds
