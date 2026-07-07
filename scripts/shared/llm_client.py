"""shared/llm_client.py
LLM communication layer with robust SSE streaming.

Backward-compatible re-exports (also available from sub-modules):
  shared.llm_exceptions → LLMErrorKind, LLMTransportError
  shared.sse_parser     → RobustSSEParser, _anext_or_done

Key components:
  LLMClient — HTTP retry, payload construction, reconnect-aware SSE streaming
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import httpx

from shared.llm_exceptions import LLMErrorKind, LLMTransportError
from shared.llm_hot_config import LlmHotConfigHandler
from shared.llm_payload import LlmPayloadHandler
from shared.llm_reconnect import LlmReconnectHandler
from shared.llm_retry import LlmRetryHandler
from shared.llm_types import LLMResponse
from shared.sse_parser import RobustSSEParser, _anext_or_done
from shared.types import LLMMessage

# Re-exports for backward compatibility
__all__ = [
    "LLMClient",
    "LLMTransportError",
    "LLMErrorKind",
    "RobustSSEParser",
    "_anext_or_done",
]

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM HTTP client with exponential-backoff retry and robust SSE streaming; stat_* counters accumulate for the instance lifetime."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    ) -> None:
        self._http = http
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._on_token = on_token
        # Called with (prompt_tokens, completion_tokens) when usage data is available.
        self._on_usage = on_usage
        self._sse_heartbeat_timeout = sse_heartbeat_timeout
        self._sse_malformed_retry = sse_malformed_retry
        self._sse_reconnect_max = sse_reconnect_max
        self._llm_stream_retry_on_heartbeat_timeout = (
            llm_stream_retry_on_heartbeat_timeout
        )
        self._llm_stream_retry_on_malformed_chunk = llm_stream_retry_on_malformed_chunk
        # Cumulative session statistics
        self.stat_retries: int = 0
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0
        self._heartbeat_timeout_counter: int = 0
        self.stat_partial_completions: int = 0
        self.stat_parse_errors: int = 0

    def apply_config(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        sse_heartbeat_timeout: float | None = None,
        sse_malformed_retry: int | None = None,
        sse_reconnect_max: int | None = None,
        stream_retry_on_heartbeat_timeout: bool | None = None,
        stream_retry_on_malformed_chunk: bool | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        LlmHotConfigHandler.apply_config(
            self,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

    # ── Retry logic ───────────────────────────────────────────────────────────

    async def request_with_retry(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        try:
            return await LlmRetryHandler.request_with_retry(
                self._http,
                url,
                payload,
                self._max_retries,
                self._retry_base_delay,
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            self.stat_retries += 1
            raise

    # ── Payload construction ──────────────────────────────────────────────────

    def build_payload(
        self,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        return LlmPayloadHandler.build_payload(
            history,
            tool_defs,
            self._temperature,
            self._max_tokens,
            stream,
        )

    def _parse_response(self, raw: dict[str, Any]) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        return LlmPayloadHandler.parse_response(raw, self._on_usage)

    # ── Non-streaming call ────────────────────────────────────────────────────

    async def call(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send conversation history to LLM and return a typed LLMResponse."""
        resp = await self.request_with_retry(
            url,
            self.build_payload(history, tool_defs),
        )
        return LlmPayloadHandler.parse_non_stream_response(resp.content, self._on_usage)

    # ── Streaming call with reconnect ─────────────────────────────────────────

    async def stream(
        self,
        url: str,
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
    ) -> LLMResponse:
        """Stream a chat completion via SSE; returns LLMResponse; raises LLMTransportError with partial_text on failure."""
        try:
            (
                llm_response,
                reconnect_count,
                heartbeat_timeouts,
                parse_errors,
                partial_completions,
            ) = await LlmReconnectHandler.stream(
                self._http,
                url,
                history,
                tool_defs,
                self._temperature,
                self._max_tokens,
                self._sse_malformed_retry,
                self._sse_heartbeat_timeout,
                self._sse_reconnect_max,
                self._retry_base_delay,
                self._llm_stream_retry_on_heartbeat_timeout,
                self._llm_stream_retry_on_malformed_chunk,
                self._on_token,
                self._on_usage,
            )
            self.stat_reconnects += reconnect_count
            self.stat_heartbeat_timeouts += heartbeat_timeouts
            self.stat_parse_errors += parse_errors
            self.stat_partial_completions += partial_completions
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise
