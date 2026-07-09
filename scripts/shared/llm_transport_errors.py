#!/usr/bin/env python3
"""shared/llm_transport_errors.py — LLM transport error handling helpers."""

import httpx
from shared.llm_exceptions import LLMTransportError


class LlmTransportErrorHandler:
    """Static methods for translating HTTP/stream errors into LLMTransportError."""

    @staticmethod
    def raise_http_status_error(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in (429, 503)
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def translate_stream_error(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in _raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def resolve_retryable(
        e: LLMTransportError,
        heartbeat_timeout_retry: bool,
        malformed_chunk_retry: bool,
        heartbeat_timeout_counter: int,
    ) -> tuple[bool, int]:
        """Return (effective_retryable, updated_heartbeat_timeout_counter).

        Increments heartbeat timeout counter when e.kind == 'HEARTBEAT_TIMEOUT'.
        """
        if e.kind == "HEARTBEAT_TIMEOUT":
            return heartbeat_timeout_retry, heartbeat_timeout_counter + 1
        if e.kind == "MALFORMED_SSE_FRAME":
            return malformed_chunk_retry, heartbeat_timeout_counter
        return e.retryable, heartbeat_timeout_counter
