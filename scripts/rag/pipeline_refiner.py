#!/usr/bin/env python3
"""rag/pipeline_refiner.py — Context refiner for RAG pipeline.

Contains the chunk refinement logic (compressing reranked hits
into query-relevant key points via LLM).
Imported by rag/pipeline.py during orchestrator construction.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Callable

import httpx

from rag.llm import RagLLM
from rag.types import MergedHit, RankedHit, RawHit

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class RefineResult:
    """Result of a refine_context() call."""

    text: str | None
    reason: (
        str | None
    )  # None on success; "refiner_returned_empty" or "refiner_exception: ..." on fallback


async def refine_context(
    llm: RagLLM,
    on_status: Callable[[str], None],
    reranked: list[RawHit | MergedHit | RankedHit],
    query: str,
    *,
    max_tokens: int = 2048,
    per_chunk_chars: int = 512,
    timeout: float | None = None,
) -> RefineResult:
    """Run the chunk refiner.

    Return contract:
        RefineResult(text=str, reason=None)              — LLM returned a non-empty refined string
        RefineResult(text=None, reason="refiner_returned_empty")  — LLM returned empty output
        RefineResult(text=None, reason="refiner_exception: ...")  — exception during LLM call
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
            return RefineResult(text=refined, reason=None)
        logger.warning("Refiner returned empty output; falling back to chunks")
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")
