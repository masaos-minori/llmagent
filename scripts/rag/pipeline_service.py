#!/usr/bin/env python3
"""rag/pipeline_service.py — External RAG service delegation.

Contains the HTTP delegate logic for external RAG pipeline services.
Imported by rag/pipeline.py during orchestrator construction.
"""

import asyncio
import logging
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


async def call_rag_service(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> str | None:
    """Delegate to external RAG service.

    Return contract:
        str (non-empty)           — HTTP 200 with body["context"] as a non-empty string
        ""                        — HTTP 200 with body["context"] missing or None
        None                      — 4xx client error, transport error, JSON parse error,
                                    all retries exhausted on 5xx

    Retries up to _MAX_ATTEMPTS times on 5xx or transport errors with
    exponential backoff.  4xx and parse errors are not retried.
    Stores hits in last_fetch_result via the callback.
    When set_fallback_reason is provided, it is called with a reason string on each failure path.
    """
    headers: dict[str, str] = {}
    if auth_token:
        headers["X-RAG-Token"] = auth_token

    for attempt in range(_MAX_ATTEMPTS):
        try:
            resp = await http.post(
                f"{rag_url}/v1/search",
                json={"query": query, "history_context": history_context},
                headers=headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            body = orjson.loads(resp.content)
            hits = body.get("selected_hits", [])
            min_score = body.get("min_score_applied", 0.0)
            max_chunks = body.get("max_chunks_per_doc", 0)
            if hits:
                set_fetch_result(
                    TwoStageFetchResult(
                        hits=hits,
                        min_score_applied=float(min_score),
                        max_chunks_per_doc=int(max_chunks),
                    )
                )
            context_raw = body.get("context")
            if context_raw is None:
                return ""
            if not isinstance(context_raw, str):
                raise ValueError(
                    f"RAG service 'context' field must be str,"
                    f" got {type(context_raw).__name__}"
                )
            return context_raw
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.warning(
                    "RAG service client error (%s) %s, falling back to in-process",
                    rag_url,
                    e,
                )
                if set_fallback_reason is not None:
                    set_fallback_reason(f"http_client_error: {e.response.status_code}")
                return None
            _log_retry(rag_url, attempt, e)
        except httpx.TransportError as e:
            _log_retry(rag_url, attempt, e)
        except (orjson.JSONDecodeError, ValueError) as e:
            logger.warning(
                "RAG service parse error (%s), falling back to in-process: %s",
                rag_url,
                e,
            )
            if set_fallback_reason is not None:
                set_fallback_reason(f"http_parse_error: {e}")
            return None
        if attempt < _MAX_ATTEMPTS - 1:
            await asyncio.sleep(min(2**attempt, 5))

    logger.warning(
        "RAG service (%s) failed after %d attempts, falling back to in-process",
        rag_url,
        _MAX_ATTEMPTS,
    )
    if set_fallback_reason is not None:
        set_fallback_reason(f"http_max_retries: {_MAX_ATTEMPTS} attempts failed")
    return None
