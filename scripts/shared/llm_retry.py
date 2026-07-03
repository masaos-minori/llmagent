#!/usr/bin/env python3
"""shared/llm_retry.py — LLM HTTP retry with exponential backoff."""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


class LlmRetryHandler:
    """Exponential-backoff retry for LLM HTTP requests."""

    @staticmethod
    async def request_with_retry(
        http: httpx.AsyncClient,
        url: str,
        payload: dict[str, object],
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
                if e.response.status_code not in (429, 503):
                    raise
                last_exc = e
            except httpx.RequestError as e:
                # Connection resets and other network errors are transient
                last_exc = e
            if attempt < max_retries - 1:
                delay = retry_base_delay * (2**attempt)
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
