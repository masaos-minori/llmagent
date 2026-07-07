#!/usr/bin/env python3
"""rag/pipeline_service.py — External RAG service delegation.

Contains the HTTP delegate logic for external RAG pipeline services.
Imported by rag/pipeline.py during orchestrator construction.
"""

import asyncio
import logging
import time
from collections.abc import Callable

import httpx
import orjson

from rag.models_data import TwoStageFetchResult

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3


def _log_retry(rag_url: str, attempt: int, error: Exception) -> None:
    logger.warning(
        "RAG service call failed (%s) attempt %d/%d: %s",
        rag_url,
        attempt + 1,
        _MAX_ATTEMPTS,
        error,
    )


def _set_fallback_reason(
    set_fallback_reason: Callable[[str], None] | None, reason: str
) -> None:
    """Call the fallback reason callback if provided."""
    if set_fallback_reason is not None:
        set_fallback_reason(reason)


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
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8003``).
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
            body = orjson.loads(resp.content)
            result_raw = body.get("result")
            if result_raw is None:
                return "", status_code, elapsed_ms
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str,"
                    f" got {type(result_raw).__name__}"
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
        except (orjson.JSONDecodeError, ValueError) as e:
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
