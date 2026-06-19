#!/usr/bin/env python3
"""rag/pipeline_refiner.py — Context refiner for RAG pipeline.

Contains the chunk refinement logic (compressing reranked hits
into query-relevant key points via LLM).
Imported by rag/pipeline.py during orchestrator construction.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import httpx

from rag.llm import RagLLM
from rag.types import MergedHit, RankedHit, RawHit

logger = logging.getLogger(__name__)


async def refine_context(
    llm: RagLLM,
    on_status: Callable[[str], None],
    reranked: list[RawHit | MergedHit | RankedHit],
    query: str,
    *,
    max_tokens: int = 2048,
    per_chunk_chars: int = 512,
    timeout: float | None = None,
) -> str | None:
    """Run the chunk refiner to compress reranked hits into query-relevant key points.

    The refiner sends all reranked hits to the LLM with a prompt asking it to
    extract concise, query-focused key points from the chunks. This reduces the
    context size injected into the conversation while preserving relevance.

    Return contract:

        ┌─────────────┬──────────────────────────────────────────────────┐
        │ Return value │ Condition                                       │
        ├─────────────┼──────────────────────────────────────────────────┤
        │ ``str``      │ LLM returned a non-empty refined string.         │
        │              │ The string contains compressed key points from   │
        │              │ the reranked hits, focused on the query.         │
        ├─────────────┼──────────────────────────────────────────────────┤
        │ ``None``     │ One of:                                           │
        │              │ - LLM returned empty/falsy output                │
        │              │ - HTTP error (httpx.HTTPStatusError)             │
        │              │ - Network/transport error (httpx.RequestError)   │
        │              │ - Parse error or unexpected response (ValueError)│
        │              │ None triggers raw-chunk fallback in the caller.  │
        └─────────────┴──────────────────────────────────────────────────┘

    Error handling:
        All exceptions (HTTPStatusError, RequestError, ValueError) are caught,
        logged as warnings, and converted to None. No retry is performed —
        refiner failures are non-critical; raw chunks serve as the fallback.

    Args:
        llm: The RagLLM instance used for refinement.
        on_status: Optional callback for UI status updates (e.g. "Refining...").
        reranked: List of reranked hit objects from the fusion/rerank stages.
        query: The original user query (used in the refiner prompt).
        max_tokens: Maximum tokens in the refined output (default: 2048).
        per_chunk_chars: Max characters per chunk in the prompt (default: 512).
        timeout: Request timeout in seconds (default: 30.0).

    Returns:
        Refined context string, or None to signal failure and trigger fallback.

    See Also:
        _augment_refiner: Thin wrapper that adds status tracking.
        augment: Full fallback chain including raw-chunk fallback.
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("refining context...")
        refined = await llm.refine_context(
            reranked,
            query,
            max_tokens=max_tokens,
            per_chunk_chars=per_chunk_chars,
            timeout=effective_timeout,
        )
        if refined:
            return refined
        logger.warning("Refiner returned empty output; falling back to chunks")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
    return None
