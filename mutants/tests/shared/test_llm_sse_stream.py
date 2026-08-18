"""
tests/test_llm_sse_stream.py

Unit tests for LlmSseStreamHandler static methods.
Uses respx to mock HTTP requests.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import httpx
import pytest
import respx
from shared.llm_exceptions import LLMTransportError
from shared.llm_sse_stream import LlmSseStreamHandler


class _MockStream(httpx.AsyncByteStream):
    """Minimal httpx-compatible async byte stream for testing."""

    def __init__(self, gen: AsyncIterator[bytes]) -> None:
        self._gen = gen

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self._gen:
            yield chunk

    async def aclose(self) -> None:
        pass


class TestReadNextChunk:
    @pytest.mark.asyncio
    async def test_returns_chunk_and_false_when_data_available(self) -> None:
        async def _byte_gen() -> AsyncIterator[bytes]:
            yield b'data: {"choices":[{"delta":{}}]}\n\n'

        aiter = _byte_gen().__aiter__()
        chunk, done = await LlmSseStreamHandler.read_next_chunk(
            aiter,
            heartbeat_timeout=1.0,
            url="http://example.com",
            llm_stream_retry_on_heartbeat_timeout=True,
        )
        assert chunk == b'data: {"choices":[{"delta":{}}]}\n\n'
        assert done is False

    @pytest.mark.asyncio
    async def test_raises_heartbeat_timeout(self) -> None:
        async def _slow_bytes() -> AsyncIterator[bytes]:
            await asyncio.sleep(1.0)
            yield b""

        aiter = _slow_bytes().__aiter__()
        with pytest.raises(LLMTransportError) as exc_info:
            await LlmSseStreamHandler.read_next_chunk(
                aiter,
                heartbeat_timeout=0.01,
                url="http://example.com",
                llm_stream_retry_on_heartbeat_timeout=True,
            )
        assert exc_info.value.kind == "HEARTBEAT_TIMEOUT"

    @pytest.mark.asyncio
    async def test_no_timeout_when_disabled(self) -> None:
        async def _slow_bytes() -> AsyncIterator[bytes]:
            await asyncio.sleep(0.1)
            yield b'data: {"choices":[{"delta":{}}]}\n\n'

        aiter = _slow_bytes().__aiter__()
        chunk, done = await LlmSseStreamHandler.read_next_chunk(
            aiter,
            heartbeat_timeout=0.0,
            url="http://example.com",
            llm_stream_retry_on_heartbeat_timeout=True,
        )
        assert len(chunk) > 0
        assert done is False

    @pytest.mark.asyncio
    async def test_exhausted_returns_sentinel(self) -> None:
        async def _empty_gen() -> AsyncIterator[bytes]:
            return
            yield  # make it an async generator

        aiter = _empty_gen().__aiter__()
        chunk, done = await LlmSseStreamHandler.read_next_chunk(
            aiter,
            heartbeat_timeout=1.0,
            url="http://example.com",
            llm_stream_retry_on_heartbeat_timeout=True,
        )
        assert chunk == b""
        assert done is True

    @pytest.mark.asyncio
    async def test_retryable_flag_in_error(self) -> None:
        async def _slow_bytes() -> AsyncIterator[bytes]:
            await asyncio.sleep(1.0)
            yield b""

        aiter = _slow_bytes().__aiter__()
        with pytest.raises(LLMTransportError) as exc_info:
            await LlmSseStreamHandler.read_next_chunk(
                aiter,
                heartbeat_timeout=0.01,
                url="http://example.com",
                llm_stream_retry_on_heartbeat_timeout=False,
            )
        assert exc_info.value.retryable is False

    @pytest.mark.asyncio
    async def test_detail_contains_timeout_duration(self) -> None:
        async def _slow_bytes() -> AsyncIterator[bytes]:
            await asyncio.sleep(1.0)
            yield b""

        aiter = _slow_bytes().__aiter__()
        with pytest.raises(LLMTransportError) as exc_info:
            await LlmSseStreamHandler.read_next_chunk(
                aiter,
                heartbeat_timeout=0.01,
                url="http://example.com",
                llm_stream_retry_on_heartbeat_timeout=True,
            )
        assert "no bytes for" in exc_info.value.detail


class TestBuildPayload:
    def test_basic_payload(self) -> None:
        history = [{"role": "user", "content": "hi"}]
        tool_defs = []
        payload = LlmSseStreamHandler._build_payload(history, tool_defs, 0.5, 100)
        assert payload["messages"] == history
        assert payload["tools"] == tool_defs
        assert payload["tool_choice"] == "auto"
        assert payload["temperature"] == 0.5
        assert payload["max_tokens"] == 100
        assert payload["stream"] is True

    def test_non_stream_payload(self) -> None:
        history = [{"role": "user", "content": "hi"}]
        tool_defs = []
        payload = LlmSseStreamHandler._build_payload(
            history, tool_defs, 0.5, 100, stream=False
        )
        assert "stream" not in payload

    def test_tool_defs_passed_through(self) -> None:
        tool_defs = [{"type": "function", "function": {"name": "test"}}]
        payload = LlmSseStreamHandler._build_payload([], tool_defs, 0.0, 10)
        assert payload["tools"] == tool_defs

    def test_default_stream_is_true(self) -> None:
        payload = LlmSseStreamHandler._build_payload([], [], 0.0, 10)
        assert payload["stream"] is True


class TestHandleStatus:
    @pytest.mark.asyncio
    async def test_success_does_not_raise(self) -> None:
        with respx.mock:
            respx.get("http://example.com/status").mock(
                return_value=httpx.Response(200, content=b'{"ok":true}')
            )
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://example.com/status")
            await LlmSseStreamHandler._handle_status(resp, "http://example.com/status")

    @pytest.mark.asyncio
    async def test_http_status_error_raises(self) -> None:
        with respx.mock:
            respx.get("http://example.com/error").mock(
                return_value=httpx.Response(500, content=b"internal error")
            )
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://example.com/error")
            with pytest.raises(LLMTransportError) as exc_info:
                await LlmSseStreamHandler._handle_status(
                    resp, "http://example.com/error"
                )
            assert exc_info.value.kind == "HTTP_STATUS_FATAL"
            assert exc_info.value.status_code == 500
            assert exc_info.value.retryable is False

    @pytest.mark.asyncio
    async def test_429_sets_retryable(self) -> None:
        with respx.mock:
            respx.get("http://example.com/rate").mock(
                return_value=httpx.Response(429, content=b"rate limited")
            )
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://example.com/rate")
            with pytest.raises(LLMTransportError) as exc_info:
                await LlmSseStreamHandler._handle_status(
                    resp, "http://example.com/rate"
                )
            assert exc_info.value.kind == "HTTP_STATUS_RETRYABLE"
            assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_503_sets_retryable(self) -> None:
        with respx.mock:
            respx.get("http://example.com/unavailable").mock(
                return_value=httpx.Response(503, content=b"service unavailable")
            )
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://example.com/unavailable")
            with pytest.raises(LLMTransportError) as exc_info:
                await LlmSseStreamHandler._handle_status(
                    resp, "http://example.com/unavailable"
                )
            assert exc_info.value.kind == "HTTP_STATUS_RETRYABLE"
            assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_400_is_fatal(self) -> None:
        with respx.mock:
            respx.get("http://example.com/bad").mock(
                return_value=httpx.Response(400, content=b"bad request")
            )
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://example.com/bad")
            with pytest.raises(LLMTransportError) as exc_info:
                await LlmSseStreamHandler._handle_status(resp, "http://example.com/bad")
            assert exc_info.value.kind == "HTTP_STATUS_FATAL"
            assert exc_info.value.retryable is False


class TestStreamOnce:
    @pytest.mark.asyncio
    async def test_successful_stream_returns_response(self) -> None:
        sse_content = (
            b'data: {"choices":[{"delta":{"content":"hello"},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_content)
            )
            result = await LlmSseStreamHandler.stream_once(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                llm_stream_retry_on_heartbeat_timeout=True,
            )
        finish_reason, content_parts, tool_calls_map, parse_errors = result
        assert finish_reason == "stop"
        assert content_parts == ["hello"]
        assert tool_calls_map == {}
        assert parse_errors == 0

    @pytest.mark.asyncio
    async def test_premature_eof_without_finish_reason_raises(self) -> None:
        """Stream ends without [DONE] and without finish_reason — raises PREMATURE_EOF."""
        sse_content = b'data: {"choices":[{"delta":{"content":"partial"},"finish_reason":null}]}\n\n'
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_content)
            )
            with pytest.raises(LLMTransportError) as exc_info:
                await LlmSseStreamHandler.stream_once(
                    httpx.AsyncClient(),
                    "http://llm/v1/chat",
                    [{"role": "user", "content": "hi"}],
                    [],
                    0.5,
                    100,
                    malformed_retry=2,
                    heartbeat_timeout=0.0,
                    llm_stream_retry_on_heartbeat_timeout=True,
                )
        assert exc_info.value.kind == "PREMATURE_EOF"
        assert exc_info.value.partial_text == "partial"

    @pytest.mark.asyncio
    async def test_connect_error_propagates(self) -> None:
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                side_effect=httpx.ConnectError("refused")
            )
            with pytest.raises(LLMTransportError) as exc_info:
                await LlmSseStreamHandler.stream_once(
                    httpx.AsyncClient(),
                    "http://llm/v1/chat",
                    [{"role": "user", "content": "hi"}],
                    [],
                    0.5,
                    100,
                    malformed_retry=2,
                    heartbeat_timeout=0.0,
                    llm_stream_retry_on_heartbeat_timeout=True,
                )
        assert exc_info.value.kind == "CONNECT_ERROR"
        assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_read_timeout_wrapped(self) -> None:
        partial_content = b'data: {"choices":[{"delta":{"content":"partial"},"finish_reason":null}]}\n\n'

        async def _byte_gen():
            yield partial_content
            raise httpx.ReadTimeout("timeout")

        coro = _byte_gen()
        aiter_obj = coro.__aiter__()  # type: ignore[attr-defined]

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, stream=_MockStream(aiter_obj))
            )
            with pytest.raises(LLMTransportError) as exc_info:
                await LlmSseStreamHandler.stream_once(
                    httpx.AsyncClient(),
                    "http://llm/v1/chat",
                    [{"role": "user", "content": "hi"}],
                    [],
                    0.5,
                    100,
                    malformed_retry=2,
                    heartbeat_timeout=0.0,
                    llm_stream_retry_on_heartbeat_timeout=True,
                )
        assert exc_info.value.kind == "READ_TIMEOUT"
        assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_parse_errors_accumulated_via_ref(self) -> None:
        bad_sse = b'data: {bad json}\n\ndata: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n'
        stat_errors = [0]
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=bad_sse)
            )
            await LlmSseStreamHandler.stream_once(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=5,
                heartbeat_timeout=0.0,
                llm_stream_retry_on_heartbeat_timeout=True,
                stat_parse_errors_ref=stat_errors,
            )
        assert stat_errors[0] >= 1

    @pytest.mark.asyncio
    async def test_partial_text_set_on_in_stream_error(self) -> None:
        partial_content = b'data: {"choices":[{"delta":{"content":"partial"},"finish_reason":null}]}\n\n'

        class _MockStream(httpx.AsyncByteStream):
            async def __aiter__(self) -> AsyncIterator[bytes]:
                yield partial_content
                raise httpx.ReadTimeout("timeout")  # noqa: B904

            async def aclose(self) -> None:
                pass

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, stream=_MockStream())
            )
            with pytest.raises(LLMTransportError) as exc_info:
                await LlmSseStreamHandler.stream_once(
                    httpx.AsyncClient(),
                    "http://llm/v1/chat",
                    [{"role": "user", "content": "hi"}],
                    [],
                    0.5,
                    100,
                    malformed_retry=2,
                    heartbeat_timeout=0.0,
                    llm_stream_retry_on_heartbeat_timeout=True,
                )
        assert exc_info.value.partial_text == "partial"

    @pytest.mark.asyncio
    async def test_tool_call_delta_processed(self) -> None:
        sse_with_tool_call = (
            b'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_1","function":{"name":"test"}}]},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{},"finish_reason":"tool_calls"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_with_tool_call)
            )
            _, content_parts, tool_calls_map, _ = await LlmSseStreamHandler.stream_once(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                llm_stream_retry_on_heartbeat_timeout=True,
            )
        assert len(tool_calls_map) == 1
        assert tool_calls_map[0]["id"] == "call_1"
        assert tool_calls_map[0]["function"]["name"] == "test"

    @pytest.mark.asyncio
    async def test_on_token_callback_called(self) -> None:
        tokens: list[str] = []
        sse_content = (
            b'data: {"choices":[{"delta":{"content":"a"},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{"content":"b"},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_content)
            )
            await LlmSseStreamHandler.stream_once(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                llm_stream_retry_on_heartbeat_timeout=True,
                on_token=tokens.append,
            )
        assert tokens == ["a", "b"]

    @pytest.mark.asyncio
    async def test_on_usage_callback_called(self) -> None:
        usages: list[tuple[int, int]] = []
        sse_with_usage = (
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":10,"completion_tokens":5}}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_with_usage)
            )
            await LlmSseStreamHandler.stream_once(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                llm_stream_retry_on_heartbeat_timeout=True,
                on_usage=lambda pt, ct: usages.append((pt, ct)),
            )
        assert usages == [(10, 5)]

    @pytest.mark.asyncio
    async def test_exhausted_with_is_done_and_no_finish_reason_returns_normally(
        self,
    ) -> None:
        """Stream ends with [DONE] but no finish_reason ever set — returns normally, no raise."""
        sse_content = (
            b'data: {"choices":[{"delta":{"content":"hi"},"finish_reason":null}]}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_content)
            )
            result = await LlmSseStreamHandler.stream_once(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                llm_stream_retry_on_heartbeat_timeout=True,
            )
        finish_reason, content_parts, _, _ = result
        assert finish_reason is None
        assert content_parts == ["hi"]

    @pytest.mark.asyncio
    async def test_finish_reason_and_done_in_same_chunk_breaks_immediately(
        self,
    ) -> None:
        """A single fed chunk carrying both finish_reason and [DONE] breaks the loop right away."""
        combined_chunk = (
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=combined_chunk)
            )
            result = await LlmSseStreamHandler.stream_once(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                llm_stream_retry_on_heartbeat_timeout=True,
            )
        finish_reason, content_parts, _, _ = result
        assert finish_reason == "stop"
        assert content_parts == []

    @pytest.mark.asyncio
    async def test_multiple_chunks_before_exit_accumulate_in_order(self) -> None:
        """At least three separate chunks are processed before [DONE]; content accumulates in order."""

        async def _byte_gen() -> AsyncIterator[bytes]:
            yield b'data: {"choices":[{"delta":{"content":"a"},"finish_reason":null}]}\n\n'
            yield b'data: {"choices":[{"delta":{"content":"b"},"finish_reason":null}]}\n\n'
            yield b'data: {"choices":[{"delta":{"content":"c"},"finish_reason":null}]}\n\n'
            yield b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            yield b"data: [DONE]\n\n"

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(
                    200, stream=_MockStream(_byte_gen().__aiter__())
                )
            )
            result = await LlmSseStreamHandler.stream_once(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                llm_stream_retry_on_heartbeat_timeout=True,
            )
        finish_reason, content_parts, _, _ = result
        assert content_parts == ["a", "b", "c"]
        assert finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_parse_errors_accumulated_across_multiple_chunks(self) -> None:
        """stat_parse_errors_ref sums malformed-frame counts across separate chunks, not just the last one."""

        async def _byte_gen() -> AsyncIterator[bytes]:
            yield b"data: {bad json 1}\n\n"
            yield b'data: {"choices":[{"delta":{"content":"a"},"finish_reason":null}]}\n\n'
            yield b"data: {bad json 2}\n\n"
            yield b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            yield b"data: [DONE]\n\n"

        stat_errors = [0]
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(
                    200, stream=_MockStream(_byte_gen().__aiter__())
                )
            )
            await LlmSseStreamHandler.stream_once(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=5,
                heartbeat_timeout=0.0,
                llm_stream_retry_on_heartbeat_timeout=True,
                stat_parse_errors_ref=stat_errors,
            )
        assert stat_errors[0] == 2
