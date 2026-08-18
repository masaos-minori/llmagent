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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmSseStreamHandlerǁ_handle_status__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut: MutantDict = {}  # type: ignore


class LlmSseStreamHandler:
    """Handle SSE streaming for LLM connections."""

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut)
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
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_orig(
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
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_1(
        byte_iter: AsyncIterator[bytes],
        heartbeat_timeout: float,
        url: str,
        llm_stream_retry_on_heartbeat_timeout: bool,
    ) -> tuple[bytes, bool]:
        """Await the next raw chunk with heartbeat timeout; returns (chunk, exhausted); raises HEARTBEAT_TIMEOUT when no bytes arrive within heartbeat_timeout."""
        try:
            coro = None
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
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_2(
        byte_iter: AsyncIterator[bytes],
        heartbeat_timeout: float,
        url: str,
        llm_stream_retry_on_heartbeat_timeout: bool,
    ) -> tuple[bytes, bool]:
        """Await the next raw chunk with heartbeat timeout; returns (chunk, exhausted); raises HEARTBEAT_TIMEOUT when no bytes arrive within heartbeat_timeout."""
        try:
            coro = _anext_or_done(None)
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
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_3(
        byte_iter: AsyncIterator[bytes],
        heartbeat_timeout: float,
        url: str,
        llm_stream_retry_on_heartbeat_timeout: bool,
    ) -> tuple[bytes, bool]:
        """Await the next raw chunk with heartbeat timeout; returns (chunk, exhausted); raises HEARTBEAT_TIMEOUT when no bytes arrive within heartbeat_timeout."""
        try:
            coro = _anext_or_done(byte_iter)
            if heartbeat_timeout >= 0:
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
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_4(
        byte_iter: AsyncIterator[bytes],
        heartbeat_timeout: float,
        url: str,
        llm_stream_retry_on_heartbeat_timeout: bool,
    ) -> tuple[bytes, bool]:
        """Await the next raw chunk with heartbeat timeout; returns (chunk, exhausted); raises HEARTBEAT_TIMEOUT when no bytes arrive within heartbeat_timeout."""
        try:
            coro = _anext_or_done(byte_iter)
            if heartbeat_timeout > 1:
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
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_5(
        byte_iter: AsyncIterator[bytes],
        heartbeat_timeout: float,
        url: str,
        llm_stream_retry_on_heartbeat_timeout: bool,
    ) -> tuple[bytes, bool]:
        """Await the next raw chunk with heartbeat timeout; returns (chunk, exhausted); raises HEARTBEAT_TIMEOUT when no bytes arrive within heartbeat_timeout."""
        try:
            coro = _anext_or_done(byte_iter)
            if heartbeat_timeout > 0:
                return await asyncio.wait_for(None, timeout=heartbeat_timeout)
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
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_6(
        byte_iter: AsyncIterator[bytes],
        heartbeat_timeout: float,
        url: str,
        llm_stream_retry_on_heartbeat_timeout: bool,
    ) -> tuple[bytes, bool]:
        """Await the next raw chunk with heartbeat timeout; returns (chunk, exhausted); raises HEARTBEAT_TIMEOUT when no bytes arrive within heartbeat_timeout."""
        try:
            coro = _anext_or_done(byte_iter)
            if heartbeat_timeout > 0:
                return await asyncio.wait_for(coro, timeout=None)
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
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_7(
        byte_iter: AsyncIterator[bytes],
        heartbeat_timeout: float,
        url: str,
        llm_stream_retry_on_heartbeat_timeout: bool,
    ) -> tuple[bytes, bool]:
        """Await the next raw chunk with heartbeat timeout; returns (chunk, exhausted); raises HEARTBEAT_TIMEOUT when no bytes arrive within heartbeat_timeout."""
        try:
            coro = _anext_or_done(byte_iter)
            if heartbeat_timeout > 0:
                return await asyncio.wait_for(timeout=heartbeat_timeout)
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
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_8(
        byte_iter: AsyncIterator[bytes],
        heartbeat_timeout: float,
        url: str,
        llm_stream_retry_on_heartbeat_timeout: bool,
    ) -> tuple[bytes, bool]:
        """Await the next raw chunk with heartbeat timeout; returns (chunk, exhausted); raises HEARTBEAT_TIMEOUT when no bytes arrive within heartbeat_timeout."""
        try:
            coro = _anext_or_done(byte_iter)
            if heartbeat_timeout > 0:
                return await asyncio.wait_for(coro, )
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
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_9(
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
                kind=None,
                phase="in_stream",
                url=url,
                retryable=llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_10(
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
                phase=None,
                url=url,
                retryable=llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_11(
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
                url=None,
                retryable=llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_12(
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
                retryable=None,
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_13(
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
                detail=None,
            )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_14(
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
                phase="in_stream",
                url=url,
                retryable=llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_15(
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
                url=url,
                retryable=llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_16(
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
                retryable=llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_17(
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
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_18(
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
                )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_19(
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
                kind="XXHEARTBEAT_TIMEOUTXX",
                phase="in_stream",
                url=url,
                retryable=llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_20(
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
                kind="heartbeat_timeout",
                phase="in_stream",
                url=url,
                retryable=llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_21(
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
                phase="XXin_streamXX",
                url=url,
                retryable=llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    async def xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_22(
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
                phase="IN_STREAM",
                url=url,
                retryable=llm_stream_retry_on_heartbeat_timeout,
                detail=f"no bytes for {heartbeat_timeout:.1f}s",
            )

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut)
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_orig(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_1(
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
        parser = None
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_2(
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
            malformed_retry=None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_3(
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
            heartbeat_timeout=None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_4(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_5(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_6(
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
        content_parts: list[str] = None
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_7(
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
        tool_calls_map: dict[int, AccumulatedToolCall] = None
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_8(
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
        finish_reason: str | None = ""

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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_9(
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
                None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_10(
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
                None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_11(
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
                json=None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_12(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_13(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_14(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_15(
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
                "XXPOSTXX",
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_16(
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
                "post",
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_17(
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
                    None, tool_defs, temperature, max_tokens, stream=True
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_18(
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
                    history, None, temperature, max_tokens, stream=True
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_19(
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
                    history, tool_defs, None, max_tokens, stream=True
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_20(
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
                    history, tool_defs, temperature, None, stream=True
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_21(
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
                    history, tool_defs, temperature, max_tokens, stream=None
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_22(
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
                    tool_defs, temperature, max_tokens, stream=True
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_23(
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
                    history, temperature, max_tokens, stream=True
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_24(
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
                    history, tool_defs, max_tokens, stream=True
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_25(
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
                    history, tool_defs, temperature, stream=True
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_26(
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
                    history, tool_defs, temperature, max_tokens, ),
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_27(
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
                    history, tool_defs, temperature, max_tokens, stream=False
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_28(
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
                await LlmSseStreamHandler._handle_status(None, url)

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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_29(
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
                await LlmSseStreamHandler._handle_status(resp, None)

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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_30(
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
                await LlmSseStreamHandler._handle_status(url)

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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_31(
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
                await LlmSseStreamHandler._handle_status(resp, )

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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_32(
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

                byte_iter = None
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_33(
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
                is_done = None
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_34(
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
                is_done = True
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_35(
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
                while False:
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_36(
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
                    ) = None
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_37(
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
                        None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_38(
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
                        None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_39(
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
                        None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_40(
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
                        None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_41(
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
                        None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_42(
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
                        None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_43(
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
                        None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_44(
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
                        None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_45(
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
                        None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_46(
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
                        None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_47(
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
                        None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_48(
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
                        None,
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_49(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_50(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_51(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_52(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_53(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_54(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_55(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_56(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_57(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_58(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_59(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_60(
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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_61(
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
                        return

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
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_62(
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
            err = None
            if content_parts:
                err.partial_text = "".join(content_parts)
            raise err from e

        parse_errors = parser.stat_parse_errors
        parser.stat_parse_errors = 0
        return finish_reason, content_parts, tool_calls_map, parse_errors

    @staticmethod
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_63(
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
            err = LlmTransportErrorHandler.translate_stream_error(None, url)
            if content_parts:
                err.partial_text = "".join(content_parts)
            raise err from e

        parse_errors = parser.stat_parse_errors
        parser.stat_parse_errors = 0
        return finish_reason, content_parts, tool_calls_map, parse_errors

    @staticmethod
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_64(
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
            err = LlmTransportErrorHandler.translate_stream_error(e, None)
            if content_parts:
                err.partial_text = "".join(content_parts)
            raise err from e

        parse_errors = parser.stat_parse_errors
        parser.stat_parse_errors = 0
        return finish_reason, content_parts, tool_calls_map, parse_errors

    @staticmethod
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_65(
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
            err = LlmTransportErrorHandler.translate_stream_error(url)
            if content_parts:
                err.partial_text = "".join(content_parts)
            raise err from e

        parse_errors = parser.stat_parse_errors
        parser.stat_parse_errors = 0
        return finish_reason, content_parts, tool_calls_map, parse_errors

    @staticmethod
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_66(
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
            err = LlmTransportErrorHandler.translate_stream_error(e, )
            if content_parts:
                err.partial_text = "".join(content_parts)
            raise err from e

        parse_errors = parser.stat_parse_errors
        parser.stat_parse_errors = 0
        return finish_reason, content_parts, tool_calls_map, parse_errors

    @staticmethod
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_67(
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
                err.partial_text = None
            raise err from e

        parse_errors = parser.stat_parse_errors
        parser.stat_parse_errors = 0
        return finish_reason, content_parts, tool_calls_map, parse_errors

    @staticmethod
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_68(
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
                err.partial_text = "".join(None)
            raise err from e

        parse_errors = parser.stat_parse_errors
        parser.stat_parse_errors = 0
        return finish_reason, content_parts, tool_calls_map, parse_errors

    @staticmethod
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_69(
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
                err.partial_text = "XXXX".join(content_parts)
            raise err from e

        parse_errors = parser.stat_parse_errors
        parser.stat_parse_errors = 0
        return finish_reason, content_parts, tool_calls_map, parse_errors

    @staticmethod
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_70(
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

        parse_errors = None
        parser.stat_parse_errors = 0
        return finish_reason, content_parts, tool_calls_map, parse_errors

    @staticmethod
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_71(
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
        parser.stat_parse_errors = None
        return finish_reason, content_parts, tool_calls_map, parse_errors

    @staticmethod
    async def xǁLlmSseStreamHandlerǁstream_once__mutmut_72(
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
        parser.stat_parse_errors = 1
        return finish_reason, content_parts, tool_calls_map, parse_errors

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut)
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_orig(
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_1(
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
        raw_chunk, exhausted = None
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_2(
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
            None,
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_3(
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
            None,
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_4(
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
            None,
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_5(
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
            None,
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_6(
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_7(
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_8(
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_9(
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_10(
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
            if not is_done or finish_reason is None:
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_11(
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
            if is_done and finish_reason is None:
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_12(
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
            if not is_done and finish_reason is not None:
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_13(
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
                    kind=None,
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_14(
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
                    phase=None,
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_15(
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
                    url=None,
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_16(
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
                    retryable=None,
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_17(
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
                    partial_text=None,
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_18(
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_19(
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_20(
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_21(
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_22(
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_23(
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
                    kind="XXPREMATURE_EOFXX",
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_24(
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
                    kind="premature_eof",
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_25(
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
                    phase="XXin_streamXX",
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_26(
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
                    phase="IN_STREAM",
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_27(
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
                    retryable=False,
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_28(
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
                    partial_text="".join(None),
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_29(
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
                    partial_text="XXXX".join(content_parts),
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_30(
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
            return finish_reason, is_done, False

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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_31(
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

        payloads, is_done = None
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_32(
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

        payloads, is_done = parser.feed(None)
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
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_33(
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
        if stat_parse_errors_ref is not None or parser.stat_parse_errors:
            stat_parse_errors_ref[0] += parser.stat_parse_errors
            parser.stat_parse_errors = 0

        reason = LlmSseHelpers.process_sse_payloads(
            payloads, content_parts, tool_calls_map, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_34(
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
        if stat_parse_errors_ref is None and parser.stat_parse_errors:
            stat_parse_errors_ref[0] += parser.stat_parse_errors
            parser.stat_parse_errors = 0

        reason = LlmSseHelpers.process_sse_payloads(
            payloads, content_parts, tool_calls_map, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_35(
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
            stat_parse_errors_ref[0] = parser.stat_parse_errors
            parser.stat_parse_errors = 0

        reason = LlmSseHelpers.process_sse_payloads(
            payloads, content_parts, tool_calls_map, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_36(
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
            stat_parse_errors_ref[0] -= parser.stat_parse_errors
            parser.stat_parse_errors = 0

        reason = LlmSseHelpers.process_sse_payloads(
            payloads, content_parts, tool_calls_map, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_37(
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
            stat_parse_errors_ref[1] += parser.stat_parse_errors
            parser.stat_parse_errors = 0

        reason = LlmSseHelpers.process_sse_payloads(
            payloads, content_parts, tool_calls_map, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_38(
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
            parser.stat_parse_errors = None

        reason = LlmSseHelpers.process_sse_payloads(
            payloads, content_parts, tool_calls_map, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_39(
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
            parser.stat_parse_errors = 1

        reason = LlmSseHelpers.process_sse_payloads(
            payloads, content_parts, tool_calls_map, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_40(
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

        reason = None
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_41(
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
            None, content_parts, tool_calls_map, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_42(
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
            payloads, None, tool_calls_map, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_43(
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
            payloads, content_parts, None, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_44(
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
            payloads, content_parts, tool_calls_map, None, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_45(
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
            payloads, content_parts, tool_calls_map, on_token, None
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_46(
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
            content_parts, tool_calls_map, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_47(
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
            payloads, tool_calls_map, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_48(
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
            payloads, content_parts, on_token, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_49(
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
            payloads, content_parts, tool_calls_map, on_usage
        )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_50(
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
            payloads, content_parts, tool_calls_map, on_token, )
        if reason:
            finish_reason = reason

        return finish_reason, is_done, is_done

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_51(
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
            finish_reason = None

        return finish_reason, is_done, is_done

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmSseStreamHandlerǁ_handle_status__mutmut)
    async def _handle_status(resp: httpx.Response, url: str) -> None:
        """Raise on HTTP errors."""
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            LlmTransportErrorHandler.raise_http_status_error(e, url)

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_handle_status__mutmut_orig(resp: httpx.Response, url: str) -> None:
        """Raise on HTTP errors."""
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            LlmTransportErrorHandler.raise_http_status_error(e, url)

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_handle_status__mutmut_1(resp: httpx.Response, url: str) -> None:
        """Raise on HTTP errors."""
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            LlmTransportErrorHandler.raise_http_status_error(None, url)

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_handle_status__mutmut_2(resp: httpx.Response, url: str) -> None:
        """Raise on HTTP errors."""
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            LlmTransportErrorHandler.raise_http_status_error(e, None)

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_handle_status__mutmut_3(resp: httpx.Response, url: str) -> None:
        """Raise on HTTP errors."""
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            LlmTransportErrorHandler.raise_http_status_error(url)

    @staticmethod
    async def xǁLlmSseStreamHandlerǁ_handle_status__mutmut_4(resp: httpx.Response, url: str) -> None:
        """Raise on HTTP errors."""
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            LlmTransportErrorHandler.raise_http_status_error(e, )

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut)
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

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_orig(
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

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_1(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
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

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_2(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = True,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = None
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_3(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = True,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "XXmessagesXX": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_4(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = True,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "MESSAGES": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_5(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = True,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "XXtoolsXX": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_6(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = True,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "TOOLS": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_7(
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
            "XXtool_choiceXX": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_8(
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
            "TOOL_CHOICE": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_9(
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
            "tool_choice": "XXautoXX",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_10(
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
            "tool_choice": "AUTO",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_11(
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
            "XXtemperatureXX": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_12(
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
            "TEMPERATURE": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_13(
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
            "XXmax_tokensXX": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_14(
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
            "MAX_TOKENS": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_15(
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
            payload["stream"] = None
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_16(
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
            payload["XXstreamXX"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_17(
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
            payload["STREAM"] = True
        return payload

    @staticmethod
    def xǁLlmSseStreamHandlerǁ_build_payload__mutmut_18(
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
            payload["stream"] = False
        return payload

mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['_mutmut_orig'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_1'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_2'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_3'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_4'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_5'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_6'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_7'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_8'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_9'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_10'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_11'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_12'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_13'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_14'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_15'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_16'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_17'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_18'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_19'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_20'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_21'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁread_next_chunk__mutmut['xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_22'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁread_next_chunk__mutmut_22 # type: ignore # mutmut generated

mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['_mutmut_orig'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_1'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_2'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_3'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_4'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_5'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_6'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_7'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_8'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_9'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_10'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_11'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_12'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_13'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_14'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_15'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_16'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_17'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_18'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_19'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_20'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_21'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_22'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_23'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_24'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_25'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_26'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_27'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_28'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_29'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_29 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_30'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_31'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_31 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_32'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_32 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_33'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_33 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_34'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_34 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_35'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_35 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_36'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_36 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_37'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_37 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_38'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_38 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_39'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_39 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_40'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_40 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_41'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_41 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_42'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_42 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_43'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_43 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_44'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_44 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_45'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_45 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_46'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_46 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_47'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_47 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_48'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_48 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_49'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_49 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_50'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_50 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_51'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_51 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_52'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_52 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_53'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_53 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_54'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_54 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_55'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_55 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_56'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_56 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_57'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_57 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_58'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_58 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_59'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_59 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_60'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_60 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_61'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_61 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_62'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_62 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_63'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_63 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_64'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_64 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_65'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_65 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_66'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_66 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_67'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_67 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_68'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_68 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_69'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_69 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_70'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_70 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_71'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_71 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁstream_once__mutmut['xǁLlmSseStreamHandlerǁstream_once__mutmut_72'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁstream_once__mutmut_72 # type: ignore # mutmut generated

mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['_mutmut_orig'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_1'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_2'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_3'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_4'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_5'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_6'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_7'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_8'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_9'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_10'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_11'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_12'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_13'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_14'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_15'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_16'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_17'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_18'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_19'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_20'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_21'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_22'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_23'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_24'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_25'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_26'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_27'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_28'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_29'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_29 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_30'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_31'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_31 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_32'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_32 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_33'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_33 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_34'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_34 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_35'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_35 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_36'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_36 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_37'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_37 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_38'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_38 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_39'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_39 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_40'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_40 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_41'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_41 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_42'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_42 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_43'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_43 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_44'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_44 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_45'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_45 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_46'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_46 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_47'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_47 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_48'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_48 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_49'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_49 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_50'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_50 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut['xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_51'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_process_next_chunk__mutmut_51 # type: ignore # mutmut generated

mutants_xǁLlmSseStreamHandlerǁ_handle_status__mutmut['_mutmut_orig'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_handle_status__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_handle_status__mutmut['xǁLlmSseStreamHandlerǁ_handle_status__mutmut_1'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_handle_status__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_handle_status__mutmut['xǁLlmSseStreamHandlerǁ_handle_status__mutmut_2'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_handle_status__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_handle_status__mutmut['xǁLlmSseStreamHandlerǁ_handle_status__mutmut_3'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_handle_status__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_handle_status__mutmut['xǁLlmSseStreamHandlerǁ_handle_status__mutmut_4'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_handle_status__mutmut_4 # type: ignore # mutmut generated

mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['_mutmut_orig'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_1'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_2'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_3'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_4'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_5'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_6'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_7'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_8'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_9'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_10'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_11'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_12'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_13'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_14'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_15'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_16'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_17'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmSseStreamHandlerǁ_build_payload__mutmut['xǁLlmSseStreamHandlerǁ_build_payload__mutmut_18'] = LlmSseStreamHandler.xǁLlmSseStreamHandlerǁ_build_payload__mutmut_18 # type: ignore # mutmut generated
