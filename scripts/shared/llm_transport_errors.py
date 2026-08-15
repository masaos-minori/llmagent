#!/usr/bin/env python3
"""scripts/shared/llm_transport_errors.py — LLM transport error handling helpers."""

import httpx

from shared.llm_exceptions import LLMTransportError

# HTTP status codes treated as transient (safe to retry): 429 Too Many Requests,
# 503 Service Unavailable.
_RETRYABLE_HTTP_STATUS_CODES = (429, 503)


class LlmTransportErrorHandler:
    """Static methods for translating HTTP/stream errors into LLMTransportError."""

    @staticmethod
    def raise_http_status_error(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
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

        HTTP status errors are handled separately in raise_http_status_error.
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
