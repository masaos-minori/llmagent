"""
tests/test_llm_client.py
Unit tests for LLMTransportError, RobustSSEParser, and LLMClient.stream().
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable

import httpx
import pytest
import respx
from shared.llm_client import (
    LLMClient,
    LLMTransportError,
    RobustSSEParser,
    _anext_or_done,
)
from shared.tool_executor import TransportErrorInfo

# ── LLMTransportError ─────────────────────────────────────────────────────────


class TestLLMTransportError:
    def test_fields_preserved(self) -> None:
        err = LLMTransportError(
            kind="HTTP_STATUS_FATAL",
            phase="pre_stream",
            url="http://example.com",
            status_code=500,
            retryable=False,
            partial_text="hello",
            detail="server error",
        )
        assert err.kind == "HTTP_STATUS_FATAL"
        assert err.phase == "pre_stream"
        assert err.url == "http://example.com"
        assert err.status_code == 500
        assert err.retryable is False
        assert err.partial_text == "hello"
        assert err.detail == "server error"

    def test_str_representation(self) -> None:
        err = LLMTransportError(
            kind="HEARTBEAT_TIMEOUT", phase="in_stream", url="", retryable=True
        )
        assert "HEARTBEAT_TIMEOUT" in str(err)
        assert "in_stream" in str(err)

    def test_is_exception(self) -> None:
        err = LLMTransportError(kind="CONNECT_ERROR", phase="pre_stream", url="")
        assert isinstance(err, Exception)

    def test_partial_text_mutable(self) -> None:
        err = LLMTransportError(kind="PREMATURE_EOF", phase="in_stream", url="")
        assert err.partial_text == ""
        err.partial_text = "partial output"
        assert err.partial_text == "partial output"


# ── RobustSSEParser ───────────────────────────────────────────────────────────


class TestRobustSSEParserFeed:
    def _parser(
        self, malformed_retry: int = 2, heartbeat_timeout: float = 0.0
    ) -> RobustSSEParser:
        return RobustSSEParser(
            malformed_retry=malformed_retry, heartbeat_timeout=heartbeat_timeout
        )

    def test_single_data_line(self) -> None:
        parser = self._parser()
        raw = b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n'
        payloads, is_done = parser.feed(raw)
        assert len(payloads) == 1
        assert '"hi"' in payloads[0]
        assert is_done is False

    def test_done_signal(self) -> None:
        parser = self._parser()
        raw = b"data: [DONE]\n\n"
        payloads, is_done = parser.feed(raw)
        assert payloads == []
        assert is_done is True

    def test_comment_line_skipped(self) -> None:
        parser = self._parser()
        raw = b": keepalive\ndata: [DONE]\n\n"
        payloads, is_done = parser.feed(raw)
        assert payloads == []
        assert is_done is True

    def test_blank_line_skipped(self) -> None:
        parser = self._parser()
        raw = b"\ndata: [DONE]\n\n"
        payloads, is_done = parser.feed(raw)
        assert is_done is True

    def test_multiple_chunks(self) -> None:
        parser = self._parser()
        chunk1 = b'data: {"choices":[{"delta":{"content":"a"}}]}\n\n'
        chunk2 = b'data: {"choices":[{"delta":{"content":"b"}}]}\n\n'
        p1, _ = parser.feed(chunk1)
        p2, _ = parser.feed(chunk2)
        assert len(p1) == 1
        assert len(p2) == 1

    def test_partial_utf8_across_chunks(self) -> None:
        parser = self._parser()
        # Split a 3-byte UTF-8 sequence (e.g. U+3042 = \xe3\x81\x82) across two chunks
        full_json = '{"choices":[{"delta":{"content":"あ"}}]}'
        full_bytes = f"data: {full_json}\n\n".encode()
        # Split mid-character (byte 1 of the 3-byte sequence is in the first payload)
        split = len(f"data: {full_json}".encode()) - 3
        part1 = full_bytes[:split]
        part2 = full_bytes[split:]
        p1, done1 = parser.feed(part1)
        p2, done2 = parser.feed(part2)
        # Total payload should reconstruct correctly
        all_payloads = p1 + p2
        assert len(all_payloads) == 1

    def test_malformed_json_within_budget(self) -> None:
        parser = self._parser(malformed_retry=2)
        bad = b"data: {broken json}\n\n"
        payloads, _ = parser.feed(bad)
        assert payloads == []
        assert parser.stat_parse_errors == 1

    def test_malformed_json_exceeds_budget_raises(self) -> None:
        parser = self._parser(malformed_retry=1)
        bad = b"data: {broken}\n\n"
        parser.feed(bad)  # count = 1, budget = 1, not yet exceeded
        with pytest.raises(LLMTransportError) as exc_info:
            parser.feed(bad)  # count = 2, exceeds budget (> 1)
        assert exc_info.value.kind == "MALFORMED_SSE_FRAME"

    def test_data_prefix_with_space(self) -> None:
        parser = self._parser()
        raw = b'data: {"choices":[{"delta":{}}]}\n\n'
        payloads, _ = parser.feed(raw)
        assert len(payloads) == 1

    def test_data_prefix_without_space(self) -> None:
        parser = self._parser()
        raw = b'data:{"choices":[{"delta":{}}]}\n\n'
        payloads, _ = parser.feed(raw)
        assert len(payloads) == 1

    def test_crlf_line_endings(self) -> None:
        parser = self._parser()
        raw = b'data: {"choices":[{"delta":{"content":"x"}}]}\r\n\r\n'
        payloads, _ = parser.feed(raw)
        assert len(payloads) == 1


class TestRobustSSEParserHeartbeat:
    def test_no_timeout_when_disabled(self) -> None:
        parser = RobustSSEParser(malformed_retry=0, heartbeat_timeout=0.0)
        # Should not raise even if called immediately
        parser.check_heartbeat("http://example.com")

    def test_no_timeout_within_window(self) -> None:
        parser = RobustSSEParser(malformed_retry=0, heartbeat_timeout=60.0)
        parser.check_heartbeat("http://example.com")  # just constructed: within window

    def test_timeout_after_inactivity(self) -> None:
        import time

        parser = RobustSSEParser(malformed_retry=0, heartbeat_timeout=0.001)
        time.sleep(0.01)
        with pytest.raises(LLMTransportError) as exc_info:
            parser.check_heartbeat("http://example.com")
        assert exc_info.value.kind == "HEARTBEAT_TIMEOUT"
        assert exc_info.value.retryable is True

    def test_event_resets_heartbeat(self) -> None:
        import time

        parser = RobustSSEParser(malformed_retry=0, heartbeat_timeout=0.01)
        time.sleep(0.02)
        # Feed a valid event to reset the clock
        parser.feed(b'data: {"choices":[{"delta":{}}]}\n\n')
        # Should not raise now
        parser.check_heartbeat("http://example.com")


# ── _anext_or_done helper ─────────────────────────────────────────────────────


class TestAnextOrDone:
    @pytest.mark.asyncio
    async def test_returns_item_and_false(self) -> None:
        async def _gen() -> AsyncIterator[bytes]:
            yield b"chunk"

        aiter = _gen().__aiter__()
        item, done = await _anext_or_done(aiter)
        assert item == b"chunk"
        assert done is False

    @pytest.mark.asyncio
    async def test_returns_sentinel_and_true_on_exhaustion(self) -> None:
        async def _gen() -> AsyncIterator[bytes]:
            return
            yield  # make it an async generator

        aiter = _gen().__aiter__()
        item, done = await _anext_or_done(aiter)
        assert done is True


# ── LLMClient.stream() ────────────────────────────────────────────────────────


def _make_client(
    on_token: Callable[[str], None] | None = None,
    on_usage: Callable[[int, int], None] | None = None,
    sse_heartbeat_timeout: float = 0.0,
    sse_malformed_retry: int = 2,
    sse_reconnect_max: int = 0,
    llm_stream_retry_on_heartbeat_timeout: bool = True,
    llm_stream_retry_on_malformed_chunk: bool = False,
) -> LLMClient:
    http = httpx.AsyncClient()
    return LLMClient(
        http,
        max_retries=1,
        retry_base_delay=0.0,
        temperature=0.2,
        max_tokens=128,
        on_token=on_token,
        on_usage=on_usage,
        sse_heartbeat_timeout=sse_heartbeat_timeout,
        sse_malformed_retry=sse_malformed_retry,
        sse_reconnect_max=sse_reconnect_max,
        llm_stream_retry_on_heartbeat_timeout=llm_stream_retry_on_heartbeat_timeout,
        llm_stream_retry_on_malformed_chunk=llm_stream_retry_on_malformed_chunk,
    )


SSE_HELLO = (
    b'data: {"choices":[{"delta":{"content":"hello"},"finish_reason":null}]}\n\n'
    b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
    b"data: [DONE]\n\n"
)


class TestLLMClientStream:
    @pytest.mark.asyncio
    async def test_successful_stream_returns_response(self) -> None:
        tokens: list[str] = []
        client = _make_client(on_token=tokens.append, sse_reconnect_max=0)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=SSE_HELLO)
            )
            result = await client.stream(
                "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
            )

        assert "hello" in result.message.get("content", "")
        assert "hello" in tokens

    @pytest.mark.asyncio
    async def test_http_fatal_error_raises(self) -> None:
        client = _make_client(sse_reconnect_max=0)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(500, content=b"internal error")
            )
            with pytest.raises(LLMTransportError) as exc_info:
                await client.stream(
                    "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
                )
        assert exc_info.value.kind == "HTTP_STATUS_FATAL"
        assert exc_info.value.phase == "pre_stream"
        assert exc_info.value.retryable is False

    @pytest.mark.asyncio
    async def test_http_retryable_error_sets_flag(self) -> None:
        client = _make_client(sse_reconnect_max=0)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(429, content=b"rate limited")
            )
            with pytest.raises(LLMTransportError) as exc_info:
                await client.stream(
                    "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
                )
        assert exc_info.value.kind == "HTTP_STATUS_RETRYABLE"
        assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_connect_error_raises(self) -> None:
        client = _make_client(sse_reconnect_max=0)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                side_effect=httpx.ConnectError("refused")
            )
            with pytest.raises(LLMTransportError) as exc_info:
                await client.stream(
                    "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
                )
        assert exc_info.value.kind == "CONNECT_ERROR"
        assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_partial_text_set_on_in_stream_error(self) -> None:
        # Deliver partial content then raise on the next chunk
        partial_content = b'data: {"choices":[{"delta":{"content":"partial"},"finish_reason":null}]}\n\n'

        async def _byte_gen() -> AsyncIterator[bytes]:
            yield partial_content
            raise httpx.ReadTimeout("timeout")  # noqa: B904 — simulated error

        client = _make_client(sse_reconnect_max=0)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, stream=_MockStream(_byte_gen()))
            )
            with pytest.raises(LLMTransportError) as exc_info:
                await client.stream(
                    "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
                )
        assert exc_info.value.partial_text == "partial"

    @pytest.mark.asyncio
    async def test_reconnect_on_retryable_error(self) -> None:
        call_count = [0]

        with respx.mock:
            # First call: connect error (retryable, no partial)
            # Second call: success
            def _side_effect(request: httpx.Request) -> httpx.Response:
                call_count[0] += 1
                if call_count[0] == 1:
                    raise httpx.ConnectError("first attempt failed")
                return httpx.Response(200, content=SSE_HELLO)

            respx.post("http://llm/v1/chat").mock(side_effect=_side_effect)
            client = _make_client(
                sse_reconnect_max=1,
                sse_heartbeat_timeout=0.0,
            )
            result = await client.stream(
                "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
            )

        assert call_count[0] == 2
        assert client.stat_reconnects == 1
        assert "hello" in result.message.get("content", "")

    @pytest.mark.asyncio
    async def test_no_reconnect_on_partial_output(self) -> None:
        partial_content = (
            b'data: {"choices":[{"delta":{"content":"part"},"finish_reason":null}]}\n\n'
        )

        async def _byte_gen() -> AsyncIterator[bytes]:
            yield partial_content
            raise httpx.ConnectError("dropped")  # noqa: B904

        client = _make_client(sse_reconnect_max=2, sse_heartbeat_timeout=0.0)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, stream=_MockStream(_byte_gen()))
            )
            with pytest.raises(LLMTransportError) as exc_info:
                await client.stream(
                    "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
                )
        # Should not reconnect; partial_text should be preserved
        assert exc_info.value.partial_text == "part"
        assert client.stat_reconnects == 0

    @pytest.mark.asyncio
    async def test_heartbeat_timeout_stats(self) -> None:
        client = _make_client(
            sse_heartbeat_timeout=0.01,
            sse_reconnect_max=0,
            llm_stream_retry_on_heartbeat_timeout=False,
        )

        async def _slow_bytes() -> AsyncIterator[bytes]:
            await asyncio.sleep(1.0)
            yield b""

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, stream=_MockStream(_slow_bytes()))
            )
            with pytest.raises(LLMTransportError) as exc_info:
                await client.stream(
                    "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
                )
        assert exc_info.value.kind == "HEARTBEAT_TIMEOUT"
        assert client.stat_heartbeat_timeouts == 1

    @pytest.mark.asyncio
    async def test_stat_parse_errors_incremented(self) -> None:
        bad_sse = (
            b"data: {bad json}\n\n"
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            b"data: [DONE]\n\n"
        )
        client = _make_client(sse_reconnect_max=0, sse_malformed_retry=5)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=bad_sse)
            )
            await client.stream(
                "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
            )
        assert client.stat_parse_errors >= 1

    @pytest.mark.asyncio
    async def test_unknown_sse_field_ignored(self) -> None:
        # "event:" and "id:" fields must be silently ignored (not payload)
        sse_with_event_field = (
            b"event: update\n"
            b'data: {"choices":[{"delta":{"content":"hi"},"finish_reason":null}]}\n\n'
            b"data: [DONE]\n\n"
        )
        client = _make_client(sse_reconnect_max=0)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_with_event_field)
            )
            result = await client.stream(
                "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
            )
        assert "hi" in result.message.get("content", "")

    @pytest.mark.asyncio
    async def test_on_usage_callback_called(self) -> None:
        usages: list[tuple[int, int]] = []

        def _on_usage(pt: int, ct: int) -> None:
            usages.append((pt, ct))

        sse_with_usage = (
            b'data: {"choices":[{"delta":{"content":"x"},"finish_reason":"stop"}],'
            b'"usage":{"prompt_tokens":10,"completion_tokens":5}}\n\n'
            b"data: [DONE]\n\n"
        )
        client = _make_client(on_usage=_on_usage, sse_reconnect_max=0)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_with_usage)
            )
            await client.stream(
                "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
            )
        assert len(usages) == 1
        assert usages[0] == (10, 5)

    @pytest.mark.asyncio
    async def test_stream_exhausted_without_done_signal(self) -> None:
        # Stream that ends naturally without [DONE] still succeeds
        sse_no_done = (
            b'data: {"choices":[{"delta":{"content":"ok"},"finish_reason":"stop"}]}\n\n'
        )
        client = _make_client(sse_reconnect_max=0)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, content=sse_no_done)
            )
            result = await client.stream(
                "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
            )
        assert "ok" in result.message.get("content", "")

    @pytest.mark.asyncio
    async def test_unknown_exception_propagates(self) -> None:
        """RuntimeError from byte stream propagates directly (not wrapped in LLMTransportError)
        because except Exception was narrowed to specific HTTP/stream exception types."""

        async def _byte_gen() -> AsyncIterator[bytes]:
            yield b'data: {"choices":[{"delta":{},"finish_reason":null}]}\n\n'
            raise RuntimeError("unexpected failure")  # noqa: B904

        client = _make_client(sse_reconnect_max=0)

        with respx.mock:
            respx.post("http://llm/v1/chat").mock(
                return_value=httpx.Response(200, stream=_MockStream(_byte_gen()))
            )
            with pytest.raises(RuntimeError, match="unexpected failure"):
                await client.stream(
                    "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
                )

    @pytest.mark.asyncio
    async def test_malformed_sse_reconnect_when_flag_enabled(self) -> None:
        call_count = [0]
        # First call: malformed SSE triggers MALFORMED_SSE_FRAME (no partial)
        # Second call: success
        malformed_then_ok = [
            b"data: {bad}\n\n",  # malformed (budget=0 so raises immediately)
            SSE_HELLO,
        ]

        def _side_effect(request: httpx.Request) -> httpx.Response:
            call_count[0] += 1
            return httpx.Response(200, content=malformed_then_ok[call_count[0] - 1])

        client = _make_client(
            sse_reconnect_max=1,
            sse_malformed_retry=0,  # budget=0 → raises on first malformed frame
            llm_stream_retry_on_malformed_chunk=True,
        )
        with respx.mock:
            respx.post("http://llm/v1/chat").mock(side_effect=_side_effect)
            result = await client.stream(
                "http://llm/v1/chat", [{"role": "user", "content": "hi"}], []
            )
        assert call_count[0] == 2
        assert "hello" in result.message.get("content", "")


# ── AgentConfig SSE validation ────────────────────────────────────────────────


class TestAgentConfigSseValidation:
    def _build(self, **overrides: object) -> None:
        from agent.config import build_agent_config

        base: dict = {
            "context_char_limit": 8000,
            "context_compress_turns": 4,
            "tool_cache_ttl": 300,
            "top_k_search": 20,
            "top_k_rerank": 15,
            "rag_top_k": 5,
            "llm_max_retries": 3,
            "llm_retry_base_delay": 1.0,
            "rag_min_score": 0.0,
            "max_chunks_per_doc": 2,
            "two_stage_max_docs": 2,
            "use_two_stage_fetch": False,
            "serial_tool_calls": False,
            "auto_inject_notes": True,
            "use_tool_summarize": False,
            "tool_summarize_threshold": 3000,
            "use_semantic_cache": False,
            "semantic_cache_threshold": 0.92,
            "semantic_cache_max_size": 100,
            "tool_definitions_strict": False,
            "mcp_watchdog_interval": 0.0,
            "mcp_watchdog_max_restarts": 3,
            "llm_temperature": 0.2,
            "llm_max_tokens": 1024,
            "use_refiner": False,
            "refiner_max_tokens": 512,
            "refiner_timeout": 30.0,
            "refiner_max_chars_per_chunk": 300,
            "tool_dedup_max_repeats": 3,
            "tool_cycle_detect_window": 2,
            "tool_error_max_consecutive": 3,
            # Provide a stdio server so _build_mcp_servers skips legacy URL validation
            "mcp_servers": {
                "dummy": {
                    "transport": "stdio",
                    "cmd": ["echo"],
                    "url": "",
                    "openrc_service": "",
                }
            },
            **overrides,
        }
        build_agent_config(base)

    def test_negative_sse_heartbeat_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="sse_heartbeat_timeout"):
            self._build(sse_heartbeat_timeout=-1.0)

    def test_negative_sse_malformed_retry_raises(self) -> None:
        with pytest.raises(ValueError, match="sse_malformed_retry"):
            self._build(sse_malformed_retry=-1)

    def test_negative_sse_reconnect_max_raises(self) -> None:
        with pytest.raises(ValueError, match="sse_reconnect_max"):
            self._build(sse_reconnect_max=-1)

    def test_zero_sse_heartbeat_timeout_is_valid(self) -> None:
        self._build(sse_heartbeat_timeout=0.0)

    def test_zero_sse_malformed_retry_is_valid(self) -> None:
        self._build(sse_malformed_retry=0)

    def test_zero_sse_reconnect_max_is_valid(self) -> None:
        self._build(sse_reconnect_max=0)


# ── format_transport_error ────────────────────────────────────────────────────


class TestFormatTransportError:
    def _call(
        self,
        source: str = "llm",
        phase: str = "pre_stream",
        kind: str = "HTTP_STATUS_FATAL",
        url: str = "http://llm/v1/chat",
        status_code: int | None = 500,
        retryable: bool = False,
        partial: bool = False,
    ) -> TransportErrorInfo:
        from shared.tool_executor import format_transport_error  # noqa: PLC0415

        return format_transport_error(
            source=source,
            phase=phase,
            kind=kind,
            url=url,
            status_code=status_code,
            retryable=retryable,
            partial=partial,
        )

    def test_returns_summary_and_detail(self) -> None:
        result = self._call()
        assert result.summary
        assert result.detail

    def test_summary_contains_source_and_kind(self) -> None:
        result = self._call(source="llm", kind="HTTP_STATUS_FATAL")
        assert "LLM" in result.summary
        assert "HTTP_STATUS_FATAL" in result.summary

    def test_detail_is_valid_json(self) -> None:
        import orjson

        result = self._call()
        data = orjson.loads(result.detail)
        assert data["source"] == "llm"
        assert data["kind"] == "HTTP_STATUS_FATAL"
        assert data["retryable"] is False

    def test_tool_source(self) -> None:
        result = self._call(source="tool", kind="CONNECT_ERROR", phase="tool_http")
        assert "TOOL" in result.summary

    def test_partial_flag_in_detail(self) -> None:
        import orjson

        result = self._call(partial=True)
        data = orjson.loads(result.detail)
        assert data["partial"] is True


# ── Test helpers ──────────────────────────────────────────────────────────────


class _MockStream(httpx.AsyncByteStream):
    """Minimal httpx-compatible async byte stream for testing."""

    def __init__(self, gen: AsyncIterator[bytes]) -> None:
        self._gen = gen

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self._gen:
            yield chunk

    async def aclose(self) -> None:
        pass


# ── apply_config ──────────────────────────────────────────────────────────────


class TestLLMClientApplyConfig:
    def _make_client(self) -> LLMClient:
        from unittest.mock import AsyncMock

        import httpx
        from shared.llm_client import LLMClient

        return LLMClient(
            http=AsyncMock(spec=httpx.AsyncClient),
            max_retries=3,
            retry_base_delay=1.0,
            temperature=0.2,
            max_tokens=1024,
        )

    def test_apply_config_temperature(self) -> None:
        client = self._make_client()
        client.apply_config(temperature=0.5)
        assert client._temperature == 0.5

    def test_apply_config_max_tokens(self) -> None:
        client = self._make_client()
        client.apply_config(max_tokens=2048)
        assert client._max_tokens == 2048

    def test_apply_config_max_retries(self) -> None:
        client = self._make_client()
        client.apply_config(max_retries=5)
        assert client._max_retries == 5

    def test_apply_config_sse_params(self) -> None:
        client = self._make_client()
        client.apply_config(
            sse_heartbeat_timeout=60.0, sse_malformed_retry=3, sse_reconnect_max=2
        )
        assert client._sse_heartbeat_timeout == 60.0
        assert client._sse_malformed_retry == 3
        assert client._sse_reconnect_max == 2

    def test_apply_config_none_args_are_no_op(self) -> None:
        client = self._make_client()
        client.apply_config()
        assert client._temperature == 0.2
        assert client._max_tokens == 1024
