#!/usr/bin/env python3
"""scripts/shared/llm_retry.py — LLM HTTP retry with exponential backoff."""

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TRANSIENT_HTTP_STATUS_CODES = frozenset({429, 503})


def _is_transient_http_error(exc: httpx.HTTPStatusError) -> bool:
    """Return True if the HTTP status error is transient and worth retrying."""
    return exc.response.status_code in _TRANSIENT_HTTP_STATUS_CODES


def _backoff_delay(retry_base_delay: float, attempt: int) -> float:
    """Compute the exponential backoff delay for a zero-indexed attempt."""
    growth: int = 2**attempt
    return retry_base_delay * growth


class LlmRetryHandler:
    """Exponential-backoff retry for LLM HTTP requests."""

    @staticmethod
    async def request_with_retry(
        http: httpx.AsyncClient,
        url: str,
        payload: dict[str, Any],
        max_retries: int,
        retry_base_delay: float,
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                resp = await http.post(url, json=payload)
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as e:
                # Re-raise immediately for non-transient HTTP errors
                if not _is_transient_http_error(e):
                    raise
                last_exc = e
            except httpx.RequestError as e:
                # Connection resets and other network errors are transient
                last_exc = e
            if attempt < max_retries - 1:
                delay = _backoff_delay(retry_base_delay, attempt)
                logger.warning(
                    "LLM request failed (attempt %d/%d): %s, retrying in %.1fs",
                    attempt + 1,
                    max_retries,
                    last_exc,
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "LLM request failed after %d attempts: %s",
                    max_retries,
                    last_exc,
                )
        if last_exc is None:
            # Unreachable: loop always sets last_exc or returns; max_retries >= 1 required
            raise RuntimeError("request_with_retry: max_retries must be >= 1")
        raise last_exc
