#!/usr/bin/env python3
"""scripts/rag/pipeline_service.py — External RAG service delegation.

Contains the HTTP delegate logic for external RAG pipeline services.
Imported by rag/pipeline.py during orchestrator construction.
"""

import asyncio
import logging
import time
from collections.abc import Callable

import httpx
from shared.json_utils import parse_http_json

from rag.models_data import TwoStageFetchResult

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__log_retry__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__log_retry__mutmut)
def _log_retry(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        rag_url,
        attempt + 1,
        _MAX_ATTEMPTS,
        error,
    )


def x__log_retry__mutmut_orig(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        rag_url,
        attempt + 1,
        _MAX_ATTEMPTS,
        error,
    )


def x__log_retry__mutmut_1(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        None,
        rag_url,
        attempt + 1,
        _MAX_ATTEMPTS,
        error,
    )


def x__log_retry__mutmut_2(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        None,
        attempt + 1,
        _MAX_ATTEMPTS,
        error,
    )


def x__log_retry__mutmut_3(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        rag_url,
        None,
        _MAX_ATTEMPTS,
        error,
    )


def x__log_retry__mutmut_4(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        rag_url,
        attempt + 1,
        None,
        error,
    )


def x__log_retry__mutmut_5(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        rag_url,
        attempt + 1,
        _MAX_ATTEMPTS,
        None,
    )


def x__log_retry__mutmut_6(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        rag_url,
        attempt + 1,
        _MAX_ATTEMPTS,
        error,
    )


def x__log_retry__mutmut_7(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        attempt + 1,
        _MAX_ATTEMPTS,
        error,
    )


def x__log_retry__mutmut_8(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        rag_url,
        _MAX_ATTEMPTS,
        error,
    )


def x__log_retry__mutmut_9(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        rag_url,
        attempt + 1,
        error,
    )


def x__log_retry__mutmut_10(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        rag_url,
        attempt + 1,
        _MAX_ATTEMPTS,
        )


def x__log_retry__mutmut_11(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "XXRAG service call failed (%s) attempt %d/%d: %sXX",
        rag_url,
        attempt + 1,
        _MAX_ATTEMPTS,
        error,
    )


def x__log_retry__mutmut_12(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "rag service call failed (%s) attempt %d/%d: %s",
        rag_url,
        attempt + 1,
        _MAX_ATTEMPTS,
        error,
    )


def x__log_retry__mutmut_13(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG SERVICE CALL FAILED (%S) ATTEMPT %D/%D: %S",
        rag_url,
        attempt + 1,
        _MAX_ATTEMPTS,
        error,
    )


def x__log_retry__mutmut_14(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        rag_url,
        attempt - 1,
        _MAX_ATTEMPTS,
        error,
    )


def x__log_retry__mutmut_15(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        rag_url,
        attempt + 2,
        _MAX_ATTEMPTS,
        error,
    )

mutants_x__log_retry__mutmut['_mutmut_orig'] = x__log_retry__mutmut_orig # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_1'] = x__log_retry__mutmut_1 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_2'] = x__log_retry__mutmut_2 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_3'] = x__log_retry__mutmut_3 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_4'] = x__log_retry__mutmut_4 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_5'] = x__log_retry__mutmut_5 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_6'] = x__log_retry__mutmut_6 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_7'] = x__log_retry__mutmut_7 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_8'] = x__log_retry__mutmut_8 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_9'] = x__log_retry__mutmut_9 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_10'] = x__log_retry__mutmut_10 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_11'] = x__log_retry__mutmut_11 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_12'] = x__log_retry__mutmut_12 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_13'] = x__log_retry__mutmut_13 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_14'] = x__log_retry__mutmut_14 # type: ignore # mutmut generated
mutants_x__log_retry__mutmut['x__log_retry__mutmut_15'] = x__log_retry__mutmut_15 # type: ignore # mutmut generated
mutants_x__set_fallback_reason__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__set_fallback_reason__mutmut)
def _set_fallback_reason(
    set_fallback_reason: Callable[[str], None] | None, reason: str
) -> None:
    """Call the fallback reason callback if provided."""
    if set_fallback_reason is not None:
        set_fallback_reason(reason)


def x__set_fallback_reason__mutmut_orig(
    set_fallback_reason: Callable[[str], None] | None, reason: str
) -> None:
    """Call the fallback reason callback if provided."""
    if set_fallback_reason is not None:
        set_fallback_reason(reason)


def x__set_fallback_reason__mutmut_1(
    set_fallback_reason: Callable[[str], None] | None, reason: str
) -> None:
    """Call the fallback reason callback if provided."""
    if set_fallback_reason is None:
        set_fallback_reason(reason)


def x__set_fallback_reason__mutmut_2(
    set_fallback_reason: Callable[[str], None] | None, reason: str
) -> None:
    """Call the fallback reason callback if provided."""
    if set_fallback_reason is not None:
        set_fallback_reason(None)

mutants_x__set_fallback_reason__mutmut['_mutmut_orig'] = x__set_fallback_reason__mutmut_orig # type: ignore # mutmut generated
mutants_x__set_fallback_reason__mutmut['x__set_fallback_reason__mutmut_1'] = x__set_fallback_reason__mutmut_1 # type: ignore # mutmut generated
mutants_x__set_fallback_reason__mutmut['x__set_fallback_reason__mutmut_2'] = x__set_fallback_reason__mutmut_2 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_call_rag_service__mutmut)
async def call_rag_service(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_orig(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_1(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "XXXX",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_2(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = None
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_3(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = None

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_4(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["XXX-RAG-TokenXX"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_5(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["x-rag-token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_6(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-TOKEN"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_7(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(None):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_8(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = None
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_9(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = None
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_10(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                None,
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_11(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json=None,
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_12(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=None,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_13(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=None,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_14(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_15(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_16(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_17(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_18(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "XXnameXX": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_19(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "NAME": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_20(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "XXrag_run_pipelineXX",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_21(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "RAG_RUN_PIPELINE",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_22(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "XXargsXX": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_23(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "ARGS": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_24(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "XXqueryXX": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_25(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "QUERY": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_26(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "XXhistory_contextXX": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_27(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "HISTORY_CONTEXT": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_28(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=11.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_29(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = None
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_30(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) / 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_31(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() + t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_32(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1001
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_33(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = None
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_34(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = None
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_35(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(None)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_36(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = None
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_37(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get(None)
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_38(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("XXresultXX")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_39(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("RESULT")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_40(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is not None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_41(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "XXXX", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_42(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_43(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    None
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_44(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(None).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_45(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code <= 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_46(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 501:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_47(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    None,
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_48(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    None,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_49(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    None,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_50(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_51(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_52(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_53(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "XXRAG service client error (%s) %s, falling back to in-processXX",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_54(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "rag service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_55(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG SERVICE CLIENT ERROR (%S) %S, FALLING BACK TO IN-PROCESS",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_56(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    None, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_57(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, None
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_58(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_59(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_60(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 1.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_61(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(None, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_62(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, None, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_63(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, None)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_64(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_65(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_66(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, )
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_67(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(None, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_68(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, None, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_69(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, None)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_70(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_71(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_72(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, )
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_73(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                None,
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_74(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                None,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_75(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                None,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_76(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_77(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_78(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_79(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "XXRAG service parse error (%s), falling back to in-process: %sXX",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_80(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "rag service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_81(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG SERVICE PARSE ERROR (%S), FALLING BACK TO IN-PROCESS: %S",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_82(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(None, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_83(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, None)
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_84(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_85(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, )
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_86(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 1.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_87(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt <= _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_88(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS + 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_89(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 2:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_90(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(None)

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_91(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(None, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_92(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, None))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_93(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_94(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, ))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_95(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2 * attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_96(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(3**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_97(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 6))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_98(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        None,
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_99(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        None,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_100(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        None,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_101(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_102(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_103(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_104(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "XXRAG service (%s) failed after %d attempts, falling back to in-processXX",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_105(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "rag service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_106(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG SERVICE (%S) FAILED AFTER %D ATTEMPTS, FALLING BACK TO IN-PROCESS",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_107(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        None, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_108(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, None
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_109(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 0.0


async def x_call_rag_service__mutmut_110(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, )
    return None, None, 0.0


async def x_call_rag_service__mutmut_111(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``{"X-RAG-Token": auth_token}`` if auth_token is non-empty
        - Timeout: _TIMEOUT seconds per attempt

    Return contract:

        +----------------+---------------------------------------------------+
        | Return value   | Condition                                         |
        +================+===================================================+
        | ``str``        | HTTP 200 + response body has a non-empty          |
        | (non-empty)    | ``"result"`` string value.                        |
        |                | Example: ``{"result": "relevant passage..."}``    |
        +----------------+---------------------------------------------------+
        | ``""``         | HTTP 200 but ``"result"`` key is absent, None,    |
        | (empty string) | or empty. Valid empty result — not a failure.     |
        |                | Example: ``{"result": null}``                     |
        +----------------+---------------------------------------------------+
        | ``None``       | One of:                                           |
        |                | - HTTP 4xx (client error, no retry)               |
        |                | - HTTP 5xx with all retries exhausted             |
        |                | - Transport error (connection refused, timeout)   |
        |                | - JSON parse error on response body               |
        |                | None triggers in-process fallback in the caller.  |
        +----------------+---------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        ``set_fetch_result`` is defined in the signature for forward compatibility
        but is not called by this function (``/v1/call_tool`` returns text only).
        If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Auth token sent as ``X-RAG-Token`` header; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        Augmented context string, empty string for valid empty results,
        or None to signal failure and trigger in-process fallback.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            t0 = time.perf_counter()
            resp = await http.post(
                f"{rag_url}/v1/call_tool",
                json={
                    "name": "rag_run_pipeline",
                    "args": {
                        "query": query,
                        "history_context": [history_context] if history_context else [],
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            return result_raw, status_code, elapsed_ms
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return None, e.response.status_code, 0.0
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            _set_fallback_reason(set_fallback_reason, f"http_parse_error: {e}")
            return None, None, 0.0
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    _set_fallback_reason(
        set_fallback_reason, f"http_max_retries: {_MAX_ATTEMPTS} attempts failed"
    )
    return None, None, 1.0

mutants_x_call_rag_service__mutmut['_mutmut_orig'] = x_call_rag_service__mutmut_orig # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_1'] = x_call_rag_service__mutmut_1 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_2'] = x_call_rag_service__mutmut_2 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_3'] = x_call_rag_service__mutmut_3 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_4'] = x_call_rag_service__mutmut_4 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_5'] = x_call_rag_service__mutmut_5 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_6'] = x_call_rag_service__mutmut_6 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_7'] = x_call_rag_service__mutmut_7 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_8'] = x_call_rag_service__mutmut_8 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_9'] = x_call_rag_service__mutmut_9 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_10'] = x_call_rag_service__mutmut_10 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_11'] = x_call_rag_service__mutmut_11 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_12'] = x_call_rag_service__mutmut_12 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_13'] = x_call_rag_service__mutmut_13 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_14'] = x_call_rag_service__mutmut_14 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_15'] = x_call_rag_service__mutmut_15 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_16'] = x_call_rag_service__mutmut_16 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_17'] = x_call_rag_service__mutmut_17 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_18'] = x_call_rag_service__mutmut_18 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_19'] = x_call_rag_service__mutmut_19 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_20'] = x_call_rag_service__mutmut_20 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_21'] = x_call_rag_service__mutmut_21 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_22'] = x_call_rag_service__mutmut_22 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_23'] = x_call_rag_service__mutmut_23 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_24'] = x_call_rag_service__mutmut_24 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_25'] = x_call_rag_service__mutmut_25 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_26'] = x_call_rag_service__mutmut_26 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_27'] = x_call_rag_service__mutmut_27 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_28'] = x_call_rag_service__mutmut_28 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_29'] = x_call_rag_service__mutmut_29 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_30'] = x_call_rag_service__mutmut_30 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_31'] = x_call_rag_service__mutmut_31 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_32'] = x_call_rag_service__mutmut_32 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_33'] = x_call_rag_service__mutmut_33 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_34'] = x_call_rag_service__mutmut_34 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_35'] = x_call_rag_service__mutmut_35 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_36'] = x_call_rag_service__mutmut_36 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_37'] = x_call_rag_service__mutmut_37 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_38'] = x_call_rag_service__mutmut_38 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_39'] = x_call_rag_service__mutmut_39 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_40'] = x_call_rag_service__mutmut_40 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_41'] = x_call_rag_service__mutmut_41 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_42'] = x_call_rag_service__mutmut_42 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_43'] = x_call_rag_service__mutmut_43 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_44'] = x_call_rag_service__mutmut_44 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_45'] = x_call_rag_service__mutmut_45 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_46'] = x_call_rag_service__mutmut_46 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_47'] = x_call_rag_service__mutmut_47 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_48'] = x_call_rag_service__mutmut_48 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_49'] = x_call_rag_service__mutmut_49 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_50'] = x_call_rag_service__mutmut_50 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_51'] = x_call_rag_service__mutmut_51 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_52'] = x_call_rag_service__mutmut_52 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_53'] = x_call_rag_service__mutmut_53 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_54'] = x_call_rag_service__mutmut_54 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_55'] = x_call_rag_service__mutmut_55 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_56'] = x_call_rag_service__mutmut_56 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_57'] = x_call_rag_service__mutmut_57 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_58'] = x_call_rag_service__mutmut_58 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_59'] = x_call_rag_service__mutmut_59 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_60'] = x_call_rag_service__mutmut_60 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_61'] = x_call_rag_service__mutmut_61 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_62'] = x_call_rag_service__mutmut_62 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_63'] = x_call_rag_service__mutmut_63 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_64'] = x_call_rag_service__mutmut_64 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_65'] = x_call_rag_service__mutmut_65 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_66'] = x_call_rag_service__mutmut_66 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_67'] = x_call_rag_service__mutmut_67 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_68'] = x_call_rag_service__mutmut_68 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_69'] = x_call_rag_service__mutmut_69 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_70'] = x_call_rag_service__mutmut_70 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_71'] = x_call_rag_service__mutmut_71 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_72'] = x_call_rag_service__mutmut_72 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_73'] = x_call_rag_service__mutmut_73 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_74'] = x_call_rag_service__mutmut_74 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_75'] = x_call_rag_service__mutmut_75 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_76'] = x_call_rag_service__mutmut_76 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_77'] = x_call_rag_service__mutmut_77 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_78'] = x_call_rag_service__mutmut_78 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_79'] = x_call_rag_service__mutmut_79 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_80'] = x_call_rag_service__mutmut_80 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_81'] = x_call_rag_service__mutmut_81 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_82'] = x_call_rag_service__mutmut_82 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_83'] = x_call_rag_service__mutmut_83 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_84'] = x_call_rag_service__mutmut_84 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_85'] = x_call_rag_service__mutmut_85 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_86'] = x_call_rag_service__mutmut_86 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_87'] = x_call_rag_service__mutmut_87 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_88'] = x_call_rag_service__mutmut_88 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_89'] = x_call_rag_service__mutmut_89 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_90'] = x_call_rag_service__mutmut_90 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_91'] = x_call_rag_service__mutmut_91 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_92'] = x_call_rag_service__mutmut_92 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_93'] = x_call_rag_service__mutmut_93 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_94'] = x_call_rag_service__mutmut_94 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_95'] = x_call_rag_service__mutmut_95 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_96'] = x_call_rag_service__mutmut_96 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_97'] = x_call_rag_service__mutmut_97 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_98'] = x_call_rag_service__mutmut_98 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_99'] = x_call_rag_service__mutmut_99 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_100'] = x_call_rag_service__mutmut_100 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_101'] = x_call_rag_service__mutmut_101 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_102'] = x_call_rag_service__mutmut_102 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_103'] = x_call_rag_service__mutmut_103 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_104'] = x_call_rag_service__mutmut_104 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_105'] = x_call_rag_service__mutmut_105 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_106'] = x_call_rag_service__mutmut_106 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_107'] = x_call_rag_service__mutmut_107 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_108'] = x_call_rag_service__mutmut_108 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_109'] = x_call_rag_service__mutmut_109 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_110'] = x_call_rag_service__mutmut_110 # type: ignore # mutmut generated
mutants_x_call_rag_service__mutmut['x_call_rag_service__mutmut_111'] = x_call_rag_service__mutmut_111 # type: ignore # mutmut generated
