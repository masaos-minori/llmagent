#!/usr/bin/env python3
"""scripts/shared/llm_sse_stream.py — LLM SSE streaming and byte reading."""

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx

from shared.llm_exceptions import LLMTransportError
from shared.llm_sse_helpers import LlmSseHelpers
from shared.llm_transport_errors import LlmTransportErrorHandler
from shared.llm_types import LLMMessage
from shared.sse_parser import RobustSSEParser, _anext_or_done
from shared.types import AccumulatedToolCall

logger = logging.getLogger(__name__)


class LlmSseStreamHandler:
    """Handle SSE streaming for LLM connections."""

    @staticmethod
    async def read_next_chunk(
        byte_iter: AsyncIterator[bytes],
        heartbeat_timeout: float,
        url: str,
        llm_stream_retry_on_heartbeat_timeout: bool,
    ) -> tuple[bytes, bool]:
        """Await the next raw chunk with heartbeat timeout; returns (chunk, exhausted); raises HEARTBEAT_TIMEOUT when no bytes arrive within heartbeat_timeout."""
        try:
            coro = _anext_or_done(byte_iter)
            if heartbeat_timeout > 0:
                return await asyncio.wait_for(coro, timeout=heartbeat_timeout)
            return await coro
        except TimeoutError:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    async def stream_once(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        malformed_retry: int,
        heartbeat_timeout: float,
        llm_stream_retry_on_heartbeat_timeout: bool,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        stat_parse_errors_ref: list[int] | None = None,
    ) -> tuple[str | None, list[str], dict[int, AccumulatedToolCall], int]:
        """Execute one SSE connection attempt; returns (finish_reason, content_parts, tool_calls_map, parse_errors).

        Raises LLMTransportError on any failure.
        """
        parser = RobustSSEParser(
            malformed_retry=malformed_retry,
            heartbeat_timeout=heartbeat_timeout,
        )
        content_parts: list[str] = []
        tool_calls_map: dict[int, AccumulatedToolCall] = {}
        finish_reason: str | None = None

        try:
            async with http.stream(
                "POST",
                url,
                json=LlmSseStreamHandler._build_payload(
                    history, tool_defs, temperature, max_tokens, stream=True
                ),
            ) as resp:
                await LlmSseStreamHandler._handle_status(resp, url)

                byte_iter = resp.aiter_bytes().__aiter__()
                is_done = False
                while True:
                    (
                        finish_reason,
                        is_done,
                        should_break,
                    ) = await LlmSseStreamHandler._process_next_chunk(
                        byte_iter,
                        url,
                        heartbeat_timeout,
                        llm_stream_retry_on_heartbeat_timeout,
                        parser,
                        content_parts,
                        tool_calls_map,
                        stat_parse_errors_ref,
                        on_token,
                        on_usage,
                        finish_reason,
                        is_done,
                    )
                    if should_break:
                        break

        except LLMTransportError:
            raise
        except (
            TimeoutError,
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.RemoteProtocolError,
        ) as e:
            err = LlmTransportErrorHandler.translate_stream_error(e, url)
            if content_parts:
                err.partial_text = "".join(content_parts)
            raise err from e

        parse_errors = parser.stat_parse_errors
        parser.stat_parse_errors = 0
        return finish_reason, content_parts, tool_calls_map, parse_errors

    @staticmethod
    async def _process_next_chunk(
        byte_iter: AsyncIterator[bytes],
        url: str,
        heartbeat_timeout: float,
        llm_stream_retry_on_heartbeat_timeout: bool,
        parser: RobustSSEParser,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        stat_parse_errors_ref: list[int] | None,
        on_token: Callable[[str], None] | None,
        on_usage: Callable[[int, int], None] | None,
        finish_reason: str | None,
        is_done: bool,
    ) -> tuple[str | None, bool, bool]:
        """Read and process a single SSE chunk for one `stream_once` loop iteration.

        Must only be called from inside `stream_once`'s `try` block, so any `httpx`
        exception it does not itself catch is still translated by the enclosing
        `except` clauses there.

        Inputs: `byte_iter`, `url`, `heartbeat_timeout`,
        `llm_stream_retry_on_heartbeat_timeout`, `parser`, `content_parts`,
        `tool_calls_map`, `stat_parse_errors_ref`, `on_token`, `on_usage`, the current
        `finish_reason`, and the previous iteration's `is_done`. `content_parts`,
        `tool_calls_map`, and `stat_parse_errors_ref` are mutated in place.

        Returns `(finish_reason, is_done, should_break)`: the (possibly updated)
        `finish_reason`, the (possibly updated) `is_done`, and whether the caller's
        `while True:` loop should break.

        Raises LLMTransportError with kind="PREMATURE_EOF" if the stream is exhausted
        without having seen `[DONE]` or a `finish_reason`.
        """
        raw_chunk, exhausted = await LlmSseStreamHandler.read_next_chunk(
            byte_iter,
            heartbeat_timeout,
            url,
            llm_stream_retry_on_heartbeat_timeout,
        )
        if exhausted:
            if not is_done and finish_reason is None:
                raise LLMTransportError(
                    kind="PREMATURE_EOF",
                    phase="in_stream",
                    url=url,
                    retryable=True,
                    partial_text="".join(content_parts),
                )
            return finish_reason, is_done, True

        payloads, is_done = parser.feed(raw_chunk)
        if stat_parse_errors_ref is not None and parser.stat_parse_errors:
            stat_parse_errors_ref[0] += parser.stat_parse_errors
            parser.stat_parse_errors = 0

        reason = LlmSseHelpers.process_sse_payloads(
            payloads, content_parts, tool_calls_map, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def _handle_status(resp: httpx.Response, url: str) -> None:
        """Raise on HTTP errors."""
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            LlmTransportErrorHandler.raise_http_status_error(e, url)

    @staticmethod
    def _build_payload(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = True,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload
