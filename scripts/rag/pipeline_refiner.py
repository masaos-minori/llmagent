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

from rag.llm_client import RagLLM
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
    """Run the chunk refiner to compress reranked hits into query-relevant key points.

    The refiner sends all reranked hits to the LLM with a prompt asking it to
    extract concise, query-focused key points. This reduces context size while
    preserving relevance before injection into the conversation.

    Return contract:

        +----------------------------------------------------+-----------------------------------+
        | Return value                                       | Condition                         |
        +====================================================+===================================+
        | ``RefineResult(text=str, reason=None)``            | LLM returned a non-empty string.  |
        |                                                    | Used as final context block.      |
        +----------------------------------------------------+-----------------------------------+
        | ``RefineResult(text=None, reason=               `` | LLM returned empty/falsy output.  |
        | ``"refiner_returned_empty")``                      | Caller falls back to raw chunks.  |
        +----------------------------------------------------+-----------------------------------+
        | ``RefineResult(text=None, reason=               `` | Exception during LLM call         |
        | ``"refiner_exception: ...")``                      | (HTTP error, transport error,     |
        |                                                    | ValueError). Non-retried; caller  |
        |                                                    | falls back to raw chunks.         |
        +----------------------------------------------------+-----------------------------------+

    Note:
        ``"refiner_returned_empty"`` fires only when ``_extract_chat_content()`` returns
        ``""`` or whitespace-only after ``.strip()``.  Common causes: content-policy refusal,
        empty LLM generation, or a prompt format that extracts no key points.
        ``ValueError`` from malformed responses always reaches the
        ``"refiner_exception: ..."`` path instead.

    Error handling:
        HTTPStatusError, RequestError, and ValueError are caught, logged as
        warnings, and converted to ``RefineResult(text=None, reason=...)``.
        No retry is performed — refiner failures are non-critical.

    Args:
        llm: The RagLLM instance used for refinement.
        on_status: Callback for UI status updates (e.g. ``"refining context..."``).
        reranked: List of hit objects from the fusion/rerank stage.
        query: The original user query (used in the refiner prompt).
        max_tokens: Maximum tokens in the refined output (default: 2048).
        per_chunk_chars: Max characters per chunk in the prompt (default: 512).
        timeout: Request timeout in seconds; None uses a 30.0s default.

    Returns:
        ``RefineResult`` with text set on success, or text=None with a reason
        string on failure. The caller uses ``result.text is None`` to detect
        failure and fall back to raw-chunk formatting.

    See Also:
        augment: Complete fallback chain including raw-chunk formatting.
        augment: Complete fallback chain including raw-chunk formatting.
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
