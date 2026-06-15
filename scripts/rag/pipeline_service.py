#!/usr/bin/env python3
"""rag/pipeline_service.py — External RAG service delegation.

Contains the HTTP delegate logic for external RAG pipeline services.
Imported by rag/pipeline.py during orchestrator construction.
"""

import logging
from collections.abc import Callable

import httpx
import orjson

from rag.models_data import TwoStageFetchResult

logger = logging.getLogger(__name__)


async def call_rag_service(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    set_fetch_result: Callable[[TwoStageFetchResult], None],
) -> str | None:
    """Delegate to external RAG service.

    Returns context string on success, empty string on empty results,
    or None on failure (triggering in-process fallback).
    Stores hits in last_fetch_result via the callback.
    """
    try:
        resp = await http.post(
            f"{rag_url}/v1/search",
            json={"query": query, "history_context": history_context},
        )
        resp.raise_for_status()
        body = orjson.loads(resp.content)
        hits = body.get("selected_hits", [])
        if hits:
            set_fetch_result(
                TwoStageFetchResult(
                    hits=hits,
                    min_score_applied=0.0,
                    max_chunks_per_doc=0,
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
    except (
        httpx.HTTPStatusError,
        httpx.RequestError,
        orjson.JSONDecodeError,
        ValueError,
    ) as e:
        logger.warning(
            "RAG service call failed (%s), falling back to in-process: %s",
            rag_url,
            e,
        )
        return None
