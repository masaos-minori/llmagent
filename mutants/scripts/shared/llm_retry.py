#!/usr/bin/env python3
"""scripts/shared/llm_retry.py — LLM HTTP retry with exponential backoff."""

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TRANSIENT_HTTP_STATUS_CODES = frozenset({429, 503})


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__is_transient_http_error__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__is_transient_http_error__mutmut)
def _is_transient_http_error(exc: httpx.HTTPStatusError) -> bool:
    """Return True if the HTTP status error is transient and worth retrying."""
    return exc.response.status_code in _TRANSIENT_HTTP_STATUS_CODES


def x__is_transient_http_error__mutmut_orig(exc: httpx.HTTPStatusError) -> bool:
    """Return True if the HTTP status error is transient and worth retrying."""
    return exc.response.status_code in _TRANSIENT_HTTP_STATUS_CODES


def x__is_transient_http_error__mutmut_1(exc: httpx.HTTPStatusError) -> bool:
    """Return True if the HTTP status error is transient and worth retrying."""
    return exc.response.status_code not in _TRANSIENT_HTTP_STATUS_CODES

mutants_x__is_transient_http_error__mutmut['_mutmut_orig'] = x__is_transient_http_error__mutmut_orig # type: ignore # mutmut generated
mutants_x__is_transient_http_error__mutmut['x__is_transient_http_error__mutmut_1'] = x__is_transient_http_error__mutmut_1 # type: ignore # mutmut generated
mutants_x__backoff_delay__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__backoff_delay__mutmut)
def _backoff_delay(retry_base_delay: float, attempt: int) -> float:
    """Compute the exponential backoff delay for a zero-indexed attempt."""
    growth: int = 2**attempt
    return retry_base_delay * growth


def x__backoff_delay__mutmut_orig(retry_base_delay: float, attempt: int) -> float:
    """Compute the exponential backoff delay for a zero-indexed attempt."""
    growth: int = 2**attempt
    return retry_base_delay * growth


def x__backoff_delay__mutmut_1(retry_base_delay: float, attempt: int) -> float:
    """Compute the exponential backoff delay for a zero-indexed attempt."""
    growth: int = None
    return retry_base_delay * growth


def x__backoff_delay__mutmut_2(retry_base_delay: float, attempt: int) -> float:
    """Compute the exponential backoff delay for a zero-indexed attempt."""
    growth: int = 2 * attempt
    return retry_base_delay * growth


def x__backoff_delay__mutmut_3(retry_base_delay: float, attempt: int) -> float:
    """Compute the exponential backoff delay for a zero-indexed attempt."""
    growth: int = 3**attempt
    return retry_base_delay * growth


def x__backoff_delay__mutmut_4(retry_base_delay: float, attempt: int) -> float:
    """Compute the exponential backoff delay for a zero-indexed attempt."""
    growth: int = 2**attempt
    return retry_base_delay / growth

mutants_x__backoff_delay__mutmut['_mutmut_orig'] = x__backoff_delay__mutmut_orig # type: ignore # mutmut generated
mutants_x__backoff_delay__mutmut['x__backoff_delay__mutmut_1'] = x__backoff_delay__mutmut_1 # type: ignore # mutmut generated
mutants_x__backoff_delay__mutmut['x__backoff_delay__mutmut_2'] = x__backoff_delay__mutmut_2 # type: ignore # mutmut generated
mutants_x__backoff_delay__mutmut['x__backoff_delay__mutmut_3'] = x__backoff_delay__mutmut_3 # type: ignore # mutmut generated
mutants_x__backoff_delay__mutmut['x__backoff_delay__mutmut_4'] = x__backoff_delay__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut: MutantDict = {}  # type: ignore


class LlmRetryHandler:
    """Exponential-backoff retry for LLM HTTP requests."""

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut)
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_orig(
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_1(
        http: httpx.AsyncClient,
        url: str,
        payload: dict[str, Any],
        max_retries: int,
        retry_base_delay: float,
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        last_exc: Exception | None = ""
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_2(
        http: httpx.AsyncClient,
        url: str,
        payload: dict[str, Any],
        max_retries: int,
        retry_base_delay: float,
    ) -> httpx.Response:
        """POST to an LLM endpoint with exponential backoff retry; retries on 503/429 and connection errors; raises last exception when all attempts exhausted."""
        last_exc: Exception | None = None
        for attempt in range(None):
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_3(
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
                resp = None
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_4(
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
                resp = await http.post(None, json=payload)
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_5(
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
                resp = await http.post(url, json=None)
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_6(
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
                resp = await http.post(json=payload)
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_7(
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
                resp = await http.post(url, )
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_8(
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
                if _is_transient_http_error(e):
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_9(
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
                if not _is_transient_http_error(None):
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_10(
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
                last_exc = None
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_11(
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
                last_exc = None
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_12(
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
            if attempt <= max_retries - 1:
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_13(
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
            if attempt < max_retries + 1:
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_14(
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
            if attempt < max_retries - 2:
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_15(
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
                delay = None
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_16(
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
                delay = _backoff_delay(None, attempt)
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_17(
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
                delay = _backoff_delay(retry_base_delay, None)
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_18(
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
                delay = _backoff_delay(attempt)
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_19(
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
                delay = _backoff_delay(retry_base_delay, )
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_20(
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
                    None,
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_21(
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
                    None,
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_22(
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
                    None,
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_23(
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
                    None,
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_24(
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
                    None,
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_25(
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_26(
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_27(
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_28(
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_29(
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_30(
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
                    "XXLLM request failed (attempt %d/%d): %s, retrying in %.1fsXX",
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_31(
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
                    "llm request failed (attempt %d/%d): %s, retrying in %.1fs",
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_32(
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
                    "LLM REQUEST FAILED (ATTEMPT %D/%D): %S, RETRYING IN %.1FS",
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_33(
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
                    attempt - 1,
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_34(
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
                    attempt + 2,
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_35(
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
                await asyncio.sleep(None)
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

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_36(
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
                    None,
                    max_retries,
                    last_exc,
                )
        if last_exc is None:
            # Unreachable: loop always sets last_exc or returns; max_retries >= 1 required
            raise RuntimeError("request_with_retry: max_retries must be >= 1")
        raise last_exc

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_37(
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
                    None,
                    last_exc,
                )
        if last_exc is None:
            # Unreachable: loop always sets last_exc or returns; max_retries >= 1 required
            raise RuntimeError("request_with_retry: max_retries must be >= 1")
        raise last_exc

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_38(
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
                    None,
                )
        if last_exc is None:
            # Unreachable: loop always sets last_exc or returns; max_retries >= 1 required
            raise RuntimeError("request_with_retry: max_retries must be >= 1")
        raise last_exc

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_39(
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
                    max_retries,
                    last_exc,
                )
        if last_exc is None:
            # Unreachable: loop always sets last_exc or returns; max_retries >= 1 required
            raise RuntimeError("request_with_retry: max_retries must be >= 1")
        raise last_exc

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_40(
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
                    last_exc,
                )
        if last_exc is None:
            # Unreachable: loop always sets last_exc or returns; max_retries >= 1 required
            raise RuntimeError("request_with_retry: max_retries must be >= 1")
        raise last_exc

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_41(
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
                    )
        if last_exc is None:
            # Unreachable: loop always sets last_exc or returns; max_retries >= 1 required
            raise RuntimeError("request_with_retry: max_retries must be >= 1")
        raise last_exc

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_42(
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
                    "XXLLM request failed after %d attempts: %sXX",
                    max_retries,
                    last_exc,
                )
        if last_exc is None:
            # Unreachable: loop always sets last_exc or returns; max_retries >= 1 required
            raise RuntimeError("request_with_retry: max_retries must be >= 1")
        raise last_exc

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_43(
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
                    "llm request failed after %d attempts: %s",
                    max_retries,
                    last_exc,
                )
        if last_exc is None:
            # Unreachable: loop always sets last_exc or returns; max_retries >= 1 required
            raise RuntimeError("request_with_retry: max_retries must be >= 1")
        raise last_exc

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_44(
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
                    "LLM REQUEST FAILED AFTER %D ATTEMPTS: %S",
                    max_retries,
                    last_exc,
                )
        if last_exc is None:
            # Unreachable: loop always sets last_exc or returns; max_retries >= 1 required
            raise RuntimeError("request_with_retry: max_retries must be >= 1")
        raise last_exc

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_45(
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
        if last_exc is not None:
            # Unreachable: loop always sets last_exc or returns; max_retries >= 1 required
            raise RuntimeError("request_with_retry: max_retries must be >= 1")
        raise last_exc

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_46(
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
            raise RuntimeError(None)
        raise last_exc

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_47(
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
            raise RuntimeError("XXrequest_with_retry: max_retries must be >= 1XX")
        raise last_exc

    @staticmethod
    async def xǁLlmRetryHandlerǁrequest_with_retry__mutmut_48(
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
            raise RuntimeError("REQUEST_WITH_RETRY: MAX_RETRIES MUST BE >= 1")
        raise last_exc

mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['_mutmut_orig'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_1'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_2'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_3'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_4'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_5'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_6'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_7'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_8'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_9'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_10'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_11'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_12'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_13'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_14'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_15'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_16'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_17'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_18'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_19'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_20'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_21'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_22'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_23'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_24'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_25'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_26'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_27'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_28'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_29'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_29 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_30'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_31'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_31 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_32'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_32 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_33'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_33 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_34'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_34 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_35'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_35 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_36'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_36 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_37'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_37 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_38'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_38 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_39'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_39 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_40'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_40 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_41'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_41 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_42'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_42 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_43'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_43 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_44'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_44 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_45'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_45 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_46'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_46 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_47'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_47 # type: ignore # mutmut generated
mutants_xǁLlmRetryHandlerǁrequest_with_retry__mutmut['xǁLlmRetryHandlerǁrequest_with_retry__mutmut_48'] = LlmRetryHandler.xǁLlmRetryHandlerǁrequest_with_retry__mutmut_48 # type: ignore # mutmut generated
