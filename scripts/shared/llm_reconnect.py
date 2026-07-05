#!/usr/bin/env python3
"""shared/llm_reconnect.py — LLM SSE reconnect-aware streaming."""

import asyncio
import logging
from collections.abc import Callable

import httpx

from shared.llm_exceptions import LLMTransportError
from shared.llm_payload import LlmPayloadHandler
from shared.llm_sse_helpers import LlmSseHelpers
from shared.llm_sse_stream import LlmSseStreamHandler
from shared.llm_types import LLMResponse
from shared.types import AccumulatedToolCall, LLMMessage

logger = logging.getLogger(__name__)


class LlmReconnectHandler:
    """Handle reconnect-aware SSE streaming for LLM connections."""

    @staticmethod
    def resolve_retryable(
        e: LLMTransportError,
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
    ) -> bool:
        """Return effective retryable flag."""
        if e.kind == "HEARTBEAT_TIMEOUT":
            return heartbeat_timeout_retry
        if e.kind == "MALFORMED_SSE_FRAME":
            return malformed_chunk_retry
        return e.retryable

    @staticmethod
    async def stream(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, object]],
        temperature: float,
        max_tokens: int,
        malformed_retry: int,
        heartbeat_timeout: float,
        reconnect_max: int,
        retry_base_delay: float,
        llm_stream_retry_on_heartbeat_timeout: bool,
        llm_stream_retry_on_malformed_chunk: bool,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        stat_parse_errors_ref: list[int] | None = None,
    ) -> tuple[LLMResponse, int, int, int, int]:
        """Stream a chat completion via SSE; returns (LLMResponse, reconnect_count, heartbeat_timeout_count, parse_errors, partial_completions); raises LLMTransportError with partial_text on failure."""
        content_parts: list[str] = []
        tool_calls_map: dict[int, AccumulatedToolCall] = {}
        finish_reason: str | None = None
        reconnect_count = 0
        heartbeat_timeout_count = 0
        parse_errors = 0
        for attempt in range(reconnect_max + 1):
            try:
                (
                    finish_reason,
                    content_parts,
                    tool_calls_map,
                    attempt_parse_errors,
                ) = await LlmSseStreamHandler.stream_once(
                    http,
                    url,
                    history,
                    tool_defs,
                    temperature,
                    max_tokens,
                    malformed_retry,
                    heartbeat_timeout,
                    llm_stream_retry_on_heartbeat_timeout,
                    on_token=on_token,
                    on_usage=on_usage,
                )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                has_partial = (
                    bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
                )
                effective_retryable = LlmReconnectHandler.resolve_retryable(
                    e,
                    llm_stream_retry_on_heartbeat_timeout,
                    llm_stream_retry_on_malformed_chunk,
                )
                if e.kind == "HEARTBEAT_TIMEOUT":
                    heartbeat_timeout_count += 1
                    e.stat_heartbeat_timeouts = heartbeat_timeout_count
                if has_partial or not effective_retryable:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE error (attempt %d/%d): %s, reconnecting in %.1fs",
                    attempt + 1,
                    reconnect_max + 1,
                    e.kind,
                    delay,
                )
                await asyncio.sleep(delay)
                content_parts.clear()
                tool_calls_map.clear()

        if content_parts and on_token:
            on_token("\n")
        raw = LlmSseHelpers.build_stream_response(
            content_parts, tool_calls_map, finish_reason
        )
        llm_response = LlmPayloadHandler.parse_response(raw, on_usage)
        # Track partial completions when we had output but had to reconnect
        partial_completions = reconnect_count if content_parts else 0
        return (
            llm_response,
            reconnect_count,
            heartbeat_timeout_count,
            parse_errors,
            partial_completions,
        )
