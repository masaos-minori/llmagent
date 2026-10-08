#!/usr/bin/env python3
"""scripts/rag/pipeline_service.py — External RAG service delegation.

Contains the HTTP delegate logic for external RAG pipeline services.
Imported by rag/pipeline.py during orchestrator construction.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

import httpx
from shared.json_utils import parse_http_json

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
_REQUEST_TIMEOUT_SECONDS = 10.0

CallRagKind = Literal["success", "empty", "auth_error", "transient_failure"]


@dataclass(frozen=True)
class CallRagResult:
    """Tagged outcome of one ``call_rag_service`` delegation.

    ``kind`` distinguishes a usable answer (``success``), a valid empty answer
    (``empty``), an authentication failure that must not fall back to local data
    (``auth_error``), and every other failure that may fall back
    (``transient_failure``).
    """

    kind: CallRagKind
    result: str | None
    status_code: int | None
    latency_ms: float


def _log_retry(rag_url: str, attempt: int, error: Exception) -> None:
    """Log a warning message when an RAG service call fails during retry."""
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


def _set_fetch_result(
    set_fetch_result: Callable[[list[dict[str, Any]]], None] | None,
    fetch_result: list[dict[str, Any]],
) -> None:
    """Call the fetch result callback if provided."""
    if set_fetch_result is not None:
        set_fetch_result(fetch_result)


async def call_rag_service(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[list[dict[str, Any]]], None] | None = None,
    set_fallback_reason: Callable[[str], None] | None = None,
) -> CallRagResult:
    """Delegate to external RAG service for context augmentation.

    Request details:
        - Endpoint: ``{rag_url}/v1/call_tool``
        - Body: ``{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [...]}}``
        - Headers: ``Authorization: Bearer <auth_token>`` if auth_token is non-empty
        - Timeout: ``_REQUEST_TIMEOUT_SECONDS`` per attempt

    Return contract (``CallRagResult.kind``):

        +---------------------+------------------------------------------------+
        | ``success``         | HTTP 200, body ``"result"`` is a non-empty     |
        |                     | string and ``is_error`` is not true.           |
        +---------------------+------------------------------------------------+
        | ``empty``           | HTTP 200 with ``"result"`` absent, None or     |
        |                     | empty, or a JSON parse error. Not a failure.   |
        |                     | ``result`` is ``""``.                          |
        +---------------------+------------------------------------------------+
        | ``auth_error``      | HTTP 401/403. No retry and no fallback; the    |
        |                     | caller must fail closed. ``result`` is None.   |
        +---------------------+------------------------------------------------+
        | ``transient_failure`` | Other HTTP 4xx (no retry), HTTP 5xx or       |
        |                     | transport error with retries exhausted, or     |
        |                     | ``is_error`` true. ``result`` is None; the     |
        |                     | caller may fall back in-process.               |
        +---------------------+------------------------------------------------+

    Retry behavior:
        - 5xx errors: retry up to ``_MAX_ATTEMPTS`` times with exponential backoff
        - Transport errors (connection refused, timeout): same retry policy
        - 4xx errors: no retry (client-side issue)
        - JSON parse errors: no retry (malformed response)

    Side effects:
        If ``set_fetch_result`` is provided, it is called with a ``list[dict[str, Any]]``
        on success paths when ``selected_hits`` is present. If ``set_fallback_reason`` is provided, it is called with a reason
        string on each non-success path (4xx, transport error, etc.).

    Args:
        http: An initialized httpx.AsyncClient (caller manages lifecycle).
        rag_url: Base URL of the RAG service (e.g. ``http://127.0.0.1:8081``).
        query: The user query string to search for.
        history_context: Conversation history context appended to query.
        auth_token: Token sent as ``Authorization: Bearer``; empty = no header.
        set_fetch_result: Callback to store fetch result metadata.
        set_fallback_reason: Optional callback called with a reason string on failure.

    Returns:
        A ``CallRagResult`` tagged with the outcome kind.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

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
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status_code = resp.status_code
            resp.raise_for_status()
            body = parse_http_json(resp)
            if body.get("is_error") is True:
                logger.warning(
                    "RAG service (%s) returned is_error=true, treating as failure",
                    rag_url,
                )
                _set_fallback_reason(set_fallback_reason, "http_is_error")
                return CallRagResult("transient_failure", None, status_code, elapsed_ms)
            selected_hits = body.get("selected_hits")
            result_raw = body.get("result")
            if result_raw is None:
                if selected_hits:
                    _set_fetch_result(set_fetch_result, selected_hits)
                return CallRagResult("empty", "", status_code, elapsed_ms)
            if not isinstance(result_raw, str):
                raise ValueError(
                    f"RAG service 'result' field must be str, got {type(result_raw).__name__}"
                )
            if selected_hits:
                _set_fetch_result(set_fetch_result, selected_hits)
            kind: CallRagKind = "success" if result_raw else "empty"
            return CallRagResult(kind, result_raw, status_code, elapsed_ms)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                logger.warning(
                    "RAG service authentication error (%s) %s, NOT falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_auth_error: {e.response.status_code}"
                )
                return CallRagResult("auth_error", None, e.response.status_code, 0.0)
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                _set_fallback_reason(
                    set_fallback_reason, f"http_client_error: {e.response.status_code}"
                )
                return CallRagResult(
                    "transient_failure", None, e.response.status_code, 0.0
                )
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except ValueError as e:
            logger.warning(
                "RAG service parse error (%s), returning empty result: %s",
                rag_url,
                e,
            )
            return CallRagResult("empty", "", None, 0.0)
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
    return CallRagResult("transient_failure", None, None, 0.0)
