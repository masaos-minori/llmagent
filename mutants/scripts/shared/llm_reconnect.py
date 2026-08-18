#!/usr/bin/env python3
"""scripts/shared/llm_reconnect.py — LLM SSE reconnect-aware streaming."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

import httpx

from shared.llm_exceptions import LLMTransportError
from shared.llm_payload import LlmPayloadHandler
from shared.llm_sse_helpers import LlmSseHelpers
from shared.llm_sse_stream import LlmSseStreamHandler
from shared.llm_types import LLMResponse
from shared.types import AccumulatedToolCall, LLMMessage

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁLlmReconnectHandlerǁresolve_retryable__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmReconnectHandlerǁstream__mutmut: MutantDict = {}  # type: ignore


class LlmReconnectHandler:
    """Handle reconnect-aware SSE streaming for LLM connections."""

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmReconnectHandlerǁresolve_retryable__mutmut)
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
    def xǁLlmReconnectHandlerǁresolve_retryable__mutmut_orig(
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
    def xǁLlmReconnectHandlerǁresolve_retryable__mutmut_1(
        e: LLMTransportError,
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
    ) -> bool:
        """Return effective retryable flag."""
        if e.kind != "HEARTBEAT_TIMEOUT":
            return heartbeat_timeout_retry
        if e.kind == "MALFORMED_SSE_FRAME":
            return malformed_chunk_retry
        return e.retryable

    @staticmethod
    def xǁLlmReconnectHandlerǁresolve_retryable__mutmut_2(
        e: LLMTransportError,
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
    ) -> bool:
        """Return effective retryable flag."""
        if e.kind == "XXHEARTBEAT_TIMEOUTXX":
            return heartbeat_timeout_retry
        if e.kind == "MALFORMED_SSE_FRAME":
            return malformed_chunk_retry
        return e.retryable

    @staticmethod
    def xǁLlmReconnectHandlerǁresolve_retryable__mutmut_3(
        e: LLMTransportError,
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
    ) -> bool:
        """Return effective retryable flag."""
        if e.kind == "heartbeat_timeout":
            return heartbeat_timeout_retry
        if e.kind == "MALFORMED_SSE_FRAME":
            return malformed_chunk_retry
        return e.retryable

    @staticmethod
    def xǁLlmReconnectHandlerǁresolve_retryable__mutmut_4(
        e: LLMTransportError,
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
    ) -> bool:
        """Return effective retryable flag."""
        if e.kind == "HEARTBEAT_TIMEOUT":
            return heartbeat_timeout_retry
        if e.kind != "MALFORMED_SSE_FRAME":
            return malformed_chunk_retry
        return e.retryable

    @staticmethod
    def xǁLlmReconnectHandlerǁresolve_retryable__mutmut_5(
        e: LLMTransportError,
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
    ) -> bool:
        """Return effective retryable flag."""
        if e.kind == "HEARTBEAT_TIMEOUT":
            return heartbeat_timeout_retry
        if e.kind == "XXMALFORMED_SSE_FRAMEXX":
            return malformed_chunk_retry
        return e.retryable

    @staticmethod
    def xǁLlmReconnectHandlerǁresolve_retryable__mutmut_6(
        e: LLMTransportError,
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
    ) -> bool:
        """Return effective retryable flag."""
        if e.kind == "HEARTBEAT_TIMEOUT":
            return heartbeat_timeout_retry
        if e.kind == "malformed_sse_frame":
            return malformed_chunk_retry
        return e.retryable

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut)
    def _evaluate_stream_error(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_orig(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_1(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = None
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_2(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) and bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_3(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) and bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_4(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(None) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_5(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(None) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_6(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(None)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_7(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = None
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_8(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            None,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_9(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            None,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_10(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            None,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_11(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_12(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_13(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_14(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind != "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_15(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "XXHEARTBEAT_TIMEOUTXX":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_16(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "heartbeat_timeout":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_17(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count = 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_18(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count -= 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_19(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 2
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_20(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = None
        should_retry = not has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_21(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = None
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_22(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = not has_partial or effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    def xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_23(
        e: LLMTransportError,
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_count: int,
    ) -> tuple[bool, int]:
        """Evaluate a stream error: update heartbeat-timeout count, decide whether to retry.

        Returns (should_retry, updated_heartbeat_timeout_count). Mutates
        `e.stat_heartbeat_timeouts` for HEARTBEAT_TIMEOUT errors so the count is visible on
        the exception if it is re-raised.
        """
        has_partial = (
            bool(content_parts) or bool(tool_calls_map) or bool(e.partial_text)
        )
        effective_retryable = LlmReconnectHandler.resolve_retryable(
            e,
            heartbeat_timeout_retry,
            malformed_chunk_retry,
        )
        if e.kind == "HEARTBEAT_TIMEOUT":
            heartbeat_timeout_count += 1
            e.stat_heartbeat_timeouts = heartbeat_timeout_count
        should_retry = has_partial and effective_retryable
        return should_retry, heartbeat_timeout_count

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmReconnectHandlerǁstream__mutmut)
    async def stream(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_orig(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_1(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
        content_parts: list[str] = None
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_2(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
        tool_calls_map: dict[int, AccumulatedToolCall] = None
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_3(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
        finish_reason: str | None = ""
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_4(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
        reconnect_count = None
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_5(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
        reconnect_count = 1
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_6(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
        heartbeat_timeout_count = None
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_7(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
        heartbeat_timeout_count = 1
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_8(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
        parse_errors = None
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_9(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
        parse_errors = 1
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_10(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
        for attempt in range(None):
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_11(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
        for attempt in range(reconnect_max - 1):
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_12(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
        for attempt in range(reconnect_max + 2):
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_13(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                ) = None
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_14(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    None,
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_15(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    None,
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_16(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    None,
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_17(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    None,
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_18(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    None,
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_19(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    None,
                    malformed_retry,
                    heartbeat_timeout,
                    llm_stream_retry_on_heartbeat_timeout,
                    on_token=on_token,
                    on_usage=on_usage,
                )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_20(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    None,
                    heartbeat_timeout,
                    llm_stream_retry_on_heartbeat_timeout,
                    on_token=on_token,
                    on_usage=on_usage,
                )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_21(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    None,
                    llm_stream_retry_on_heartbeat_timeout,
                    on_token=on_token,
                    on_usage=on_usage,
                )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_22(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    None,
                    on_token=on_token,
                    on_usage=on_usage,
                )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_23(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    on_token=None,
                    on_usage=on_usage,
                )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_24(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    on_usage=None,
                )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_25(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_26(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_27(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_28(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_29(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_30(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    malformed_retry,
                    heartbeat_timeout,
                    llm_stream_retry_on_heartbeat_timeout,
                    on_token=on_token,
                    on_usage=on_usage,
                )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_31(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    heartbeat_timeout,
                    llm_stream_retry_on_heartbeat_timeout,
                    on_token=on_token,
                    on_usage=on_usage,
                )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_32(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    llm_stream_retry_on_heartbeat_timeout,
                    on_token=on_token,
                    on_usage=on_usage,
                )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_33(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    on_token=on_token,
                    on_usage=on_usage,
                )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_34(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    on_usage=on_usage,
                )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_35(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                    )
                parse_errors += attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_36(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                parse_errors = attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_37(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                parse_errors -= attempt_parse_errors
                break  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_38(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                return  # success
            except LLMTransportError as e:
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_39(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = None
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_40(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        None,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_41(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        None,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_42(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        None,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_43(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        None,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_44(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        None,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_45(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        None,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_46(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_47(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_48(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_49(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_50(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_51(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_52(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_53(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt > reconnect_max:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_54(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count = 1
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_55(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count -= 1
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_56(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 2
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_57(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = None
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_58(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay / (2**attempt)
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_59(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2 * attempt)
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_60(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (3**attempt)
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_61(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    None,
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_62(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE error (attempt %d/%d): %s, reconnecting in %.1fs",
                    None,
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_63(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE error (attempt %d/%d): %s, reconnecting in %.1fs",
                    attempt + 1,
                    None,
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_64(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE error (attempt %d/%d): %s, reconnecting in %.1fs",
                    attempt + 1,
                    reconnect_max + 1,
                    None,
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_65(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
                    None,
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_66(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_67(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE error (attempt %d/%d): %s, reconnecting in %.1fs",
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_68(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE error (attempt %d/%d): %s, reconnecting in %.1fs",
                    attempt + 1,
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_69(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE error (attempt %d/%d): %s, reconnecting in %.1fs",
                    attempt + 1,
                    reconnect_max + 1,
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_70(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_71(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "XXSSE error (attempt %d/%d): %s, reconnecting in %.1fsXX",
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_72(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "sse error (attempt %d/%d): %s, reconnecting in %.1fs",
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_73(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE ERROR (ATTEMPT %D/%D): %S, RECONNECTING IN %.1FS",
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_74(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE error (attempt %d/%d): %s, reconnecting in %.1fs",
                    attempt - 1,
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_75(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE error (attempt %d/%d): %s, reconnecting in %.1fs",
                    attempt + 2,
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_76(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE error (attempt %d/%d): %s, reconnecting in %.1fs",
                    attempt + 1,
                    reconnect_max - 1,
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_77(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
                    raise
                if attempt >= reconnect_max:
                    raise
                reconnect_count += 1
                delay = retry_base_delay * (2**attempt)
                logger.warning(
                    "SSE error (attempt %d/%d): %s, reconnecting in %.1fs",
                    attempt + 1,
                    reconnect_max + 2,
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_78(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
                await asyncio.sleep(None)
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_79(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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

        if content_parts or on_token:
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_80(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
            on_token(None)
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_81(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
            on_token("XX\nXX")
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_82(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
        raw = None
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_83(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
            None, tool_calls_map, finish_reason
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_84(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
            content_parts, None, finish_reason
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_85(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
            content_parts, tool_calls_map, None
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_86(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
            tool_calls_map, finish_reason
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_87(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
            content_parts, finish_reason
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_88(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
            content_parts, tool_calls_map, )
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

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_89(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
        llm_response = None
        # Track partial completions when we had output but had to reconnect
        partial_completions = reconnect_count if content_parts else 0
        return (
            llm_response,
            reconnect_count,
            heartbeat_timeout_count,
            parse_errors,
            partial_completions,
        )

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_90(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
        llm_response = LlmPayloadHandler.parse_response(None, on_usage)
        # Track partial completions when we had output but had to reconnect
        partial_completions = reconnect_count if content_parts else 0
        return (
            llm_response,
            reconnect_count,
            heartbeat_timeout_count,
            parse_errors,
            partial_completions,
        )

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_91(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
        llm_response = LlmPayloadHandler.parse_response(raw, None)
        # Track partial completions when we had output but had to reconnect
        partial_completions = reconnect_count if content_parts else 0
        return (
            llm_response,
            reconnect_count,
            heartbeat_timeout_count,
            parse_errors,
            partial_completions,
        )

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_92(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
        llm_response = LlmPayloadHandler.parse_response(on_usage)
        # Track partial completions when we had output but had to reconnect
        partial_completions = reconnect_count if content_parts else 0
        return (
            llm_response,
            reconnect_count,
            heartbeat_timeout_count,
            parse_errors,
            partial_completions,
        )

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_93(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
        llm_response = LlmPayloadHandler.parse_response(raw, )
        # Track partial completions when we had output but had to reconnect
        partial_completions = reconnect_count if content_parts else 0
        return (
            llm_response,
            reconnect_count,
            heartbeat_timeout_count,
            parse_errors,
            partial_completions,
        )

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_94(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
        partial_completions = None
        return (
            llm_response,
            reconnect_count,
            heartbeat_timeout_count,
            parse_errors,
            partial_completions,
        )

    @staticmethod
    async def xǁLlmReconnectHandlerǁstream__mutmut_95(
        http: httpx.AsyncClient,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
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
                should_retry, heartbeat_timeout_count = (
                    LlmReconnectHandler._evaluate_stream_error(
                        e,
                        content_parts,
                        tool_calls_map,
                        llm_stream_retry_on_heartbeat_timeout,
                        llm_stream_retry_on_malformed_chunk,
                        heartbeat_timeout_count,
                    )
                )
                if not should_retry:
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
        partial_completions = reconnect_count if content_parts else 1
        return (
            llm_response,
            reconnect_count,
            heartbeat_timeout_count,
            parse_errors,
            partial_completions,
        )

mutants_xǁLlmReconnectHandlerǁresolve_retryable__mutmut['_mutmut_orig'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁresolve_retryable__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁresolve_retryable__mutmut['xǁLlmReconnectHandlerǁresolve_retryable__mutmut_1'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁresolve_retryable__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁresolve_retryable__mutmut['xǁLlmReconnectHandlerǁresolve_retryable__mutmut_2'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁresolve_retryable__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁresolve_retryable__mutmut['xǁLlmReconnectHandlerǁresolve_retryable__mutmut_3'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁresolve_retryable__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁresolve_retryable__mutmut['xǁLlmReconnectHandlerǁresolve_retryable__mutmut_4'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁresolve_retryable__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁresolve_retryable__mutmut['xǁLlmReconnectHandlerǁresolve_retryable__mutmut_5'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁresolve_retryable__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁresolve_retryable__mutmut['xǁLlmReconnectHandlerǁresolve_retryable__mutmut_6'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁresolve_retryable__mutmut_6 # type: ignore # mutmut generated

mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['_mutmut_orig'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_1'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_2'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_3'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_4'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_5'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_6'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_7'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_8'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_9'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_10'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_11'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_12'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_13'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_14'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_15'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_16'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_17'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_18'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_19'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_20'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_21'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_22'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut['xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_23'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁ_evaluate_stream_error__mutmut_23 # type: ignore # mutmut generated

mutants_xǁLlmReconnectHandlerǁstream__mutmut['_mutmut_orig'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_1'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_2'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_3'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_4'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_5'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_6'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_7'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_8'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_9'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_10'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_11'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_12'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_13'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_14'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_15'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_16'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_17'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_18'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_19'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_20'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_21'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_22'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_23'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_24'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_25'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_26'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_27'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_28'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_29'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_29 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_30'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_31'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_31 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_32'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_32 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_33'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_33 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_34'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_34 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_35'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_35 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_36'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_36 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_37'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_37 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_38'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_38 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_39'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_39 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_40'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_40 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_41'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_41 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_42'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_42 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_43'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_43 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_44'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_44 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_45'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_45 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_46'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_46 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_47'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_47 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_48'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_48 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_49'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_49 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_50'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_50 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_51'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_51 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_52'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_52 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_53'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_53 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_54'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_54 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_55'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_55 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_56'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_56 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_57'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_57 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_58'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_58 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_59'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_59 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_60'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_60 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_61'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_61 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_62'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_62 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_63'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_63 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_64'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_64 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_65'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_65 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_66'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_66 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_67'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_67 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_68'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_68 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_69'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_69 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_70'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_70 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_71'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_71 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_72'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_72 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_73'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_73 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_74'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_74 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_75'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_75 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_76'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_76 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_77'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_77 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_78'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_78 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_79'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_79 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_80'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_80 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_81'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_81 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_82'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_82 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_83'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_83 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_84'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_84 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_85'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_85 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_86'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_86 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_87'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_87 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_88'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_88 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_89'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_89 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_90'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_90 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_91'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_91 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_92'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_92 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_93'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_93 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_94'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_94 # type: ignore # mutmut generated
mutants_xǁLlmReconnectHandlerǁstream__mutmut['xǁLlmReconnectHandlerǁstream__mutmut_95'] = LlmReconnectHandler.xǁLlmReconnectHandlerǁstream__mutmut_95 # type: ignore # mutmut generated
