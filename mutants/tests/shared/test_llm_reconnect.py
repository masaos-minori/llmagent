#!/usr/bin/env python3
"""Tests for scripts/shared/llm_reconnect.py."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from shared.llm_exceptions import LLMTransportError
from shared.llm_reconnect import LlmReconnectHandler
from shared.llm_types import LLMResponse


class _MockStream(httpx.AsyncByteStream):
    """Minimal httpx-compatible async byte stream for testing."""

    def __init__(self, gen: AsyncIterator[bytes]) -> None:
        self._gen = gen

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self._gen:
            yield chunk

    async def aclose(self) -> None:
        pass


# ── resolve_retryable ────────────────────────────────────────────────────────


class TestResolveRetryable:
    def test_heartbeat_timeout_with_retry_enabled(self) -> None:
        e = LLMTransportError(
            "HEARTBEAT_TIMEOUT", "pre_stream", "http://example.com", retryable=False
        )
        assert LlmReconnectHandler.resolve_retryable(e, True, False) is True

    def test_heartbeat_timeout_with_retry_disabled(self) -> None:
        e = LLMTransportError(
            "HEARTBEAT_TIMEOUT", "pre_stream", "http://example.com", retryable=False
        )
        assert LlmReconnectHandler.resolve_retryable(e, False, False) is False

    def test_malformed_sse_frame_with_retry_enabled(self) -> None:
        e = LLMTransportError(
            "MALFORMED_SSE_FRAME", "in_stream", "http://example.com", retryable=False
        )
        assert LlmReconnectHandler.resolve_retryable(e, False, True) is True

    def test_malformed_sse_frame_with_retry_disabled(self) -> None:
        e = LLMTransportError(
            "MALFORMED_SSE_FRAME", "in_stream", "http://example.com", retryable=False
        )
        assert LlmReconnectHandler.resolve_retryable(e, False, False) is False

    def test_connect_error_uses_original_retryable_true(self) -> None:
        e = LLMTransportError(
            "CONNECT_ERROR", "pre_stream", "http://example.com", retryable=True
        )
        assert LlmReconnectHandler.resolve_retryable(e, False, False) is True

    def test_connect_error_uses_original_retryable_false(self) -> None:
        e = LLMTransportError(
            "CONNECT_ERROR", "pre_stream", "http://example.com", retryable=False
        )
        assert LlmReconnectHandler.resolve_retryable(e, True, True) is False

    def test_http_status_fatal_not_retryable(self) -> None:
        e = LLMTransportError(
            "HTTP_STATUS_FATAL",
            "pre_stream",
            "http://example.com",
            status_code=500,
            retryable=False,
        )
        assert LlmReconnectHandler.resolve_retryable(e, True, True) is False

    def test_http_status_retryable_preserved(self) -> None:
        e = LLMTransportError(
            "HTTP_STATUS_RETRYABLE",
            "pre_stream",
            "http://example.com",
            status_code=429,
            retryable=True,
        )
        assert LlmReconnectHandler.resolve_retryable(e, False, False) is True

    def test_premature_eof_not_retryable(self) -> None:
        e = LLMTransportError(
            "PREMATURE_EOF", "in_stream", "http://example.com", retryable=False
        )
        assert LlmReconnectHandler.resolve_retryable(e, True, True) is False

    def test_unknown_kind_uses_original_retryable(self) -> None:
        e = LLMTransportError(
            "UNKNOWN_STREAM_ERROR", "in_stream", "http://example.com", retryable=True
        )
        assert LlmReconnectHandler.resolve_retryable(e, False, False) is True


# ── _evaluate_stream_error ────────────────────────────────────────────────────


class TestEvaluateStreamError:
    def test_heartbeat_timeout_increments_count_and_sets_stat(self) -> None:
        e = LLMTransportError(
            "HEARTBEAT_TIMEOUT", "in_stream", "http://example.com", retryable=False
        )
        should_retry, count = LlmReconnectHandler._evaluate_stream_error(
            e, [], {}, True, False, 0
        )
        assert should_retry is True
        assert count == 1
        assert e.stat_heartbeat_timeouts == 1

    def test_heartbeat_timeout_count_accumulates_across_calls(self) -> None:
        e = LLMTransportError("HEARTBEAT_TIMEOUT", "in_stream", "http://example.com")
        _, count = LlmReconnectHandler._evaluate_stream_error(e, [], {}, True, False, 2)
        assert count == 3
        assert e.stat_heartbeat_timeouts == 3

    def test_has_partial_content_blocks_retry_even_if_retryable(self) -> None:
        e = LLMTransportError(
            "CONNECT_ERROR", "pre_stream", "http://example.com", retryable=True
        )
        should_retry, count = LlmReconnectHandler._evaluate_stream_error(
            e, ["partial"], {}, True, True, 0
        )
        assert should_retry is False
        assert count == 0

    def test_non_retryable_blocks_retry(self) -> None:
        e = LLMTransportError(
            "CONNECT_ERROR", "pre_stream", "http://example.com", retryable=False
        )
        should_retry, count = LlmReconnectHandler._evaluate_stream_error(
            e, [], {}, True, True, 0
        )
        assert should_retry is False
        assert count == 0


# ── stream (reconnect logic) ─────────────────────────────────────────────────


def _make_sse_response(content: str, finish_reason: str | None = "stop") -> bytes:
    delta = f'{{"choices":[{{"delta":{{"content":"{content}"}},\\"finish_reason\\":null}}]}}\\n\\n'
    if finish_reason is None:
        done = 'data: {"choices":[{"delta":{},"finish_reason":null}]}\n\n'
    else:
        done = (
            'data: {"choices":[{"delta":{},"finish_reason":"'
            + finish_reason
            + '"}]}\n\n'
        )
    return delta.encode() + done.encode() + b"data: [DONE]\n\n"


class TestStreamSuccess:
    @pytest.mark.asyncio
    async def test_successful_stream_no_reconnect(self) -> None:
        sse_content = (
            b'data: {"choices":[{"delta":{"content":"hello"},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_content)
            )
            result = await LlmReconnectHandler.stream(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                reconnect_max=3,
                retry_base_delay=1.0,
                llm_stream_retry_on_heartbeat_timeout=True,
                llm_stream_retry_on_malformed_chunk=True,
            )
        (
            response,
            reconnect_count,
            hb_timeout_count,
            parse_errors,
            partial_completions,
        ) = result
        assert isinstance(response, LLMResponse)
        assert response.message.get("content") == "hello"
        assert reconnect_count == 0
        assert hb_timeout_count == 0
        assert parse_errors == 0
        assert partial_completions == 0

    @pytest.mark.asyncio
    async def test_tool_call_delta_processed(self) -> None:
        sse_content = (
            b'data: {"choices":[{"delta":{"tool_calls":[{"id":"call_1","type":"function","index":0,"function":{"name":"test"}}]},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{"tool_calls":[{"id":"call_1","type":"function","index":0,"function":{"arguments":"{"a":1}"}}]},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{},"finish_reason":"tool_calls"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_content)
            )
            result = await LlmReconnectHandler.stream(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                reconnect_max=3,
                retry_base_delay=1.0,
                llm_stream_retry_on_heartbeat_timeout=True,
                llm_stream_retry_on_malformed_chunk=True,
            )
        response, reconnect_count, _, parse_errors, _ = result
        assert isinstance(response, LLMResponse)
        tc_list = response.message.get("tool_calls") or []
        assert len(tc_list) == 1
        assert tc_list[0]["id"] == "call_1"
        assert tc_list[0]["function"]["name"] == "test"
        assert reconnect_count == 0

    @pytest.mark.asyncio
    async def test_on_token_callback_called(self) -> None:
        tokens_received = []

        def on_token(token: str) -> None:
            tokens_received.append(token)

        sse_content = (
            b'data: {"choices":[{"delta":{"content":"h"},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{"content":"i"},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_content)
            )
            await LlmReconnectHandler.stream(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                reconnect_max=3,
                retry_base_delay=1.0,
                llm_stream_retry_on_heartbeat_timeout=True,
                llm_stream_retry_on_malformed_chunk=True,
                on_token=on_token,
            )
        assert "h" in tokens_received
        assert "i" in tokens_received

    @pytest.mark.asyncio
    async def test_on_usage_callback_called(self) -> None:
        usage_received = []

        def on_usage(prompt_tokens: int, completion_tokens: int) -> None:
            usage_received.append((prompt_tokens, completion_tokens))

        sse_content = (
            b'data: {"usage":{"prompt_tokens":10,"completion_tokens":5}}\n\n'
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_content)
            )
            await LlmReconnectHandler.stream(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                reconnect_max=3,
                retry_base_delay=1.0,
                llm_stream_retry_on_heartbeat_timeout=True,
                llm_stream_retry_on_malformed_chunk=True,
                on_usage=on_usage,
            )
        assert usage_received == [(10, 5)]

    @pytest.mark.asyncio
    async def test_finish_reason_none_returns_none(self) -> None:
        sse_content = (
            b'data: {"choices":[{"delta":{},"finish_reason":null}]}\n\ndata: [DONE]\n\n'
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_content)
            )
            result = await LlmReconnectHandler.stream(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                reconnect_max=3,
                retry_base_delay=1.0,
                llm_stream_retry_on_heartbeat_timeout=True,
                llm_stream_retry_on_malformed_chunk=True,
            )
        response, _, _, _, _ = result
        assert response.finish_reason is None

    @pytest.mark.asyncio
    async def test_empty_content_returns_empty_string(self) -> None:
        sse_content = (
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_content)
            )
            result = await LlmReconnectHandler.stream(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                reconnect_max=3,
                retry_base_delay=1.0,
                llm_stream_retry_on_heartbeat_timeout=True,
                llm_stream_retry_on_malformed_chunk=True,
            )
        response, _, _, _, _ = result
        assert response.message.get("content") == ""

    @pytest.mark.asyncio
    async def test_multiple_chunks_accumulated(self) -> None:
        sse_content = (
            b'data: {"choices":[{"delta":{"content":"f"},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{"content":"o"},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{"content":"o"},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_content)
            )
            result = await LlmReconnectHandler.stream(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                reconnect_max=3,
                retry_base_delay=1.0,
                llm_stream_retry_on_heartbeat_timeout=True,
                llm_stream_retry_on_malformed_chunk=True,
            )
        response, _, _, _, _ = result
        assert response.message.get("content") == "foo"


class TestStreamReconnect:
    @pytest.mark.asyncio
    async def test_reconnect_on_connect_error_with_success(self) -> None:
        call_count = [0]

        def _side_effect(request: httpx.Request) -> httpx.Response:
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.ConnectError("refused")
            sse_content = (
                b'data: {"choices":[{"delta":{"content":"reconnected"},"finish_reason":null}]}\n\n'
                b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
                b"data: [DONE]\n\n"
            )
            return httpx.Response(200, content=sse_content)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(side_effect=_side_effect)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await LlmReconnectHandler.stream(
                    httpx.AsyncClient(),
                    "http://llm/v1/chat",
                    [{"role": "user", "content": "hi"}],
                    [],
                    0.5,
                    100,
                    malformed_retry=2,
                    heartbeat_timeout=0.0,
                    reconnect_max=3,
                    retry_base_delay=0.001,
                    llm_stream_retry_on_heartbeat_timeout=True,
                    llm_stream_retry_on_malformed_chunk=True,
                )
        (
            response,
            reconnect_count,
            hb_timeout_count,
            parse_errors,
            partial_completions,
        ) = result
        assert isinstance(response, LLMResponse)
        assert response.message.get("content") == "reconnected"
        assert reconnect_count == 1
        assert hb_timeout_count == 0
        assert parse_errors == 0
        assert partial_completions == 1

    @pytest.mark.asyncio
    async def test_reconnect_exhausted_raises(self) -> None:
        call_count = [0]

        def _side_effect(request: httpx.Request) -> httpx.Response:
            call_count[0] += 1
            raise httpx.ConnectError("refused")

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(side_effect=_side_effect)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(LLMTransportError) as exc_info:
                    await LlmReconnectHandler.stream(
                        httpx.AsyncClient(),
                        "http://llm/v1/chat",
                        [{"role": "user", "content": "hi"}],
                        [],
                        0.5,
                        100,
                        malformed_retry=2,
                        heartbeat_timeout=0.0,
                        reconnect_max=2,
                        retry_base_delay=0.001,
                        llm_stream_retry_on_heartbeat_timeout=True,
                        llm_stream_retry_on_malformed_chunk=True,
                    )
        assert exc_info.value.kind == "CONNECT_ERROR"
        assert exc_info.value.retryable is True
        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_no_reconnect_when_fatal_error(self) -> None:
        call_count = [0]

        def _side_effect(request: httpx.Request) -> httpx.Response:
            call_count[0] += 1
            return httpx.Response(500, content=b"error")

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(side_effect=_side_effect)
            with pytest.raises(LLMTransportError) as exc_info:
                await LlmReconnectHandler.stream(
                    httpx.AsyncClient(),
                    "http://llm/v1/chat",
                    [{"role": "user", "content": "hi"}],
                    [],
                    0.5,
                    100,
                    malformed_retry=2,
                    heartbeat_timeout=0.0,
                    reconnect_max=3,
                    retry_base_delay=0.001,
                    llm_stream_retry_on_heartbeat_timeout=True,
                    llm_stream_retry_on_malformed_chunk=True,
                )
        assert exc_info.value.status_code == 500
        assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_no_partial_data_raises_even_if_retryable(self) -> None:
        """No content_parts and no tool_calls_map — fatal even for retryable errors."""
        call_count = [0]

        def _side_effect(request: httpx.Request) -> httpx.Response:
            call_count[0] += 1
            raise httpx.RemoteProtocolError("protocol error")

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(side_effect=_side_effect)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(LLMTransportError) as exc_info:
                    await LlmReconnectHandler.stream(
                        httpx.AsyncClient(),
                        "http://llm/v1/chat",
                        [{"role": "user", "content": "hi"}],
                        [],
                        0.5,
                        100,
                        malformed_retry=2,
                        heartbeat_timeout=0.0,
                        reconnect_max=3,
                        retry_base_delay=0.001,
                        llm_stream_retry_on_heartbeat_timeout=True,
                        llm_stream_retry_on_malformed_chunk=True,
                    )
        assert exc_info.value.kind == "UNKNOWN_STREAM_ERROR"
        assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_reconnect_with_partial_text_preserves_it(self) -> None:
        """Partial text exists + non-retryable error → raise immediately, no reconnect."""
        partial_content = b'data: {"choices":[{"delta":{"content":"partial"},"finish_reason":null}]}\n\n'

        async def _byte_gen():
            yield partial_content
            raise httpx.RemoteProtocolError("protocol error")

        aiter_obj = _byte_gen().__aiter__()  # type: ignore[attr-defined]

        call_count = [0]

        def _side_effect(request: httpx.Request) -> httpx.Response:
            call_count[0] += 1
            if call_count[0] == 1:
                return httpx.Response(200, stream=_MockStream(aiter_obj))
            sse_content = (
                b'data: {"choices":[{"delta":{"content":"after"},"finish_reason":null}]}\n\n'
                b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
                b"data: [DONE]\n\n"
            )
            return httpx.Response(200, content=sse_content)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(side_effect=_side_effect)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(LLMTransportError) as exc_info:
                    await LlmReconnectHandler.stream(
                        httpx.AsyncClient(),
                        "http://llm/v1/chat",
                        [{"role": "user", "content": "hi"}],
                        [],
                        0.5,
                        100,
                        malformed_retry=2,
                        heartbeat_timeout=0.0,
                        reconnect_max=3,
                        retry_base_delay=0.001,
                        llm_stream_retry_on_heartbeat_timeout=True,
                        llm_stream_retry_on_malformed_chunk=True,
                    )
        assert exc_info.value.kind == "UNKNOWN_STREAM_ERROR"
        assert exc_info.value.retryable is False
        assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_heartbeat_timeout_counts_incremented(self) -> None:
        """HB_TIMEOUT_COUNT only increments for HEARTBEAT_TIMEOUT kind errors."""
        call_count = [0]

        def _side_effect(request: httpx.Request) -> httpx.Response:
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.ReadTimeout("timeout")
            sse_content = (
                b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
                b"data: [DONE]\n\n"
            )
            return httpx.Response(200, content=sse_content)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(side_effect=_side_effect)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await LlmReconnectHandler.stream(
                    httpx.AsyncClient(),
                    "http://llm/v1/chat",
                    [{"role": "user", "content": "hi"}],
                    [],
                    0.5,
                    100,
                    malformed_retry=2,
                    heartbeat_timeout=0.0,
                    reconnect_max=3,
                    retry_base_delay=0.001,
                    llm_stream_retry_on_heartbeat_timeout=True,
                    llm_stream_retry_on_malformed_chunk=False,
                )
        response, reconnect_count, hb_timeout_count, _, _ = result
        assert isinstance(response, LLMResponse)
        assert reconnect_count == 1
        assert hb_timeout_count == 0

    @pytest.mark.asyncio
    async def test_multiple_reconnects_accumulate_counts(self) -> None:
        """Multiple reconnects accumulate counts across all attempts."""
        call_count = [0]

        def _side_effect(request: httpx.Request) -> httpx.Response:
            call_count[0] += 1
            if call_count[0] <= 2:

                async def _gen():
                    if False:
                        yield b""
                    raise httpx.ReadTimeout("timeout")

                aiter_obj = _gen().__aiter__()  # type: ignore[attr-defined]
                return httpx.Response(200, stream=_MockStream(aiter_obj))
            sse_content = (
                b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
                b"data: [DONE]\n\n"
            )
            return httpx.Response(200, content=sse_content)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(side_effect=_side_effect)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await LlmReconnectHandler.stream(
                    httpx.AsyncClient(),
                    "http://llm/v1/chat",
                    [{"role": "user", "content": "hi"}],
                    [],
                    0.5,
                    100,
                    malformed_retry=2,
                    heartbeat_timeout=0.0,
                    reconnect_max=3,
                    retry_base_delay=0.001,
                    llm_stream_retry_on_heartbeat_timeout=True,
                    llm_stream_retry_on_malformed_chunk=False,
                )
        response, reconnect_count, hb_timeout_count, _, partial_completions = result
        assert isinstance(response, LLMResponse)
        assert reconnect_count == 2
        assert hb_timeout_count == 0
        assert partial_completions == 0

    @pytest.mark.asyncio
    async def test_exponential_backoff_delay_calculation(self) -> None:
        delays_recorded: list[float] = []

        async def mock_sleep(delay: float) -> None:
            delays_recorded.append(delay)

        def _side_effect(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(side_effect=_side_effect)
            with patch("asyncio.sleep", mock_sleep):
                with pytest.raises(LLMTransportError):
                    await LlmReconnectHandler.stream(
                        httpx.AsyncClient(),
                        "http://llm/v1/chat",
                        [{"role": "user", "content": "hi"}],
                        [],
                        0.5,
                        100,
                        malformed_retry=2,
                        heartbeat_timeout=0.0,
                        reconnect_max=3,
                        retry_base_delay=1.0,
                        llm_stream_retry_on_heartbeat_timeout=True,
                        llm_stream_retry_on_malformed_chunk=True,
                    )
        assert len(delays_recorded) == 3
        assert abs(delays_recorded[0] - 1.0) < 0.01
        assert abs(delays_recorded[1] - 2.0) < 0.01
        assert abs(delays_recorded[2] - 4.0) < 0.01

    @pytest.mark.asyncio
    async def test_parse_errors_accumulated_across_attempts(self) -> None:
        bad_sse = b'data: {bad json}\n\ndata: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
        call_count = [0]

        def _side_effect(request: httpx.Request) -> httpx.Response:
            call_count[0] += 1
            if call_count[0] == 1:
                return httpx.Response(200, content=bad_sse)
            sse_content = (
                b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
                b"data: [DONE]\n\n"
            )
            return httpx.Response(200, content=sse_content)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(side_effect=_side_effect)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await LlmReconnectHandler.stream(
                    httpx.AsyncClient(),
                    "http://llm/v1/chat",
                    [{"role": "user", "content": "hi"}],
                    [],
                    0.5,
                    100,
                    malformed_retry=5,
                    heartbeat_timeout=0.0,
                    reconnect_max=3,
                    retry_base_delay=0.001,
                    llm_stream_retry_on_heartbeat_timeout=True,
                    llm_stream_retry_on_malformed_chunk=True,
                )
        response, reconnect_count, _, parse_errors, _ = result
        assert isinstance(response, LLMResponse)
        assert reconnect_count == 0
        assert parse_errors >= 1

    @pytest.mark.asyncio
    async def test_on_token_newline_after_success(self) -> None:
        tokens_received = []

        def on_token(token: str) -> None:
            tokens_received.append(token)

        sse_content = (
            b'data: {"choices":[{"delta":{"content":"hello"},"finish_reason":null}]}\n\n'
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_content)
            )
            await LlmReconnectHandler.stream(
                httpx.AsyncClient(),
                "http://llm/v1/chat",
                [{"role": "user", "content": "hi"}],
                [],
                0.5,
                100,
                malformed_retry=2,
                heartbeat_timeout=0.0,
                reconnect_max=3,
                retry_base_delay=1.0,
                llm_stream_retry_on_heartbeat_timeout=True,
                llm_stream_retry_on_malformed_chunk=True,
                on_token=on_token,
            )
        assert "\n" in tokens_received
