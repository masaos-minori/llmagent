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
    """Run the chunk refiner.

    Returns refined context string on success, or None on empty output
    or LLM failure so caller falls back to raw chunks.
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
