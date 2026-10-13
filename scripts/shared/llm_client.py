"""scripts/shared/llm_client.py

LLM communication layer with robust SSE streaming.

Key components:
  LLMClient — HTTP retry, payload construction, reconnect-aware SSE streaming
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import httpx

from shared.llm_exceptions import LLMTransportError
from shared.llm_hot_config import LlmHotConfigHandler
from shared.llm_reconnect import LlmReconnectHandler
from shared.llm_types import LLMResponse
from shared.types import LLMMessage

logger = logging.getLogger(__name__)

CHAT_COMPLETIONS_PATH = "/v1/chat/completions"
EMBEDDING_PATH = "/embedding"


def build_llm_url(base_url: str) -> str:
    """Append the chat completions endpoint path to a base URL."""
    if not base_url:
        return ""
    base = base_url.rstrip("/")
    return f"{base}{CHAT_COMPLETIONS_PATH}"


def build_embed_url(base_url: str) -> str:
    """Append the embedding endpoint path to a base URL."""
    if not base_url:
        return ""
    base = base_url.rstrip("/")
    return f"{base}{EMBEDDING_PATH}"


class LLMClient:
    """LLM HTTP client with robust SSE streaming; stat_* counters accumulate for the instance lifetime."""

    def __init__(
        self,
        http: httpx.AsyncClient,
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
        """Initialize with HTTP client, retry settings, and optional callbacks."""
        self._http = http
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
        self.stat_reconnects: int = 0
        self.stat_heartbeat_timeouts: int = 0

        self.stat_parse_errors: int = 0
        self.stat_partial_completions: int = 0

    def apply_config(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
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
            retry_base_delay=retry_base_delay,
            sse_heartbeat_timeout=sse_heartbeat_timeout,
            sse_malformed_retry=sse_malformed_retry,
            sse_reconnect_max=sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=stream_retry_on_malformed_chunk,
        )

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
            return llm_response
        except LLMTransportError as exc:
            if hasattr(exc, "stat_heartbeat_timeouts"):
                self.stat_heartbeat_timeouts += exc.stat_heartbeat_timeouts
            raise
