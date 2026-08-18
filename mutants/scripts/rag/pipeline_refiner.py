#!/usr/bin/env python3
"""scripts/rag/pipeline_refiner.py — Context refiner for RAG pipeline.

Contains the chunk refinement logic (compressing reranked hits
into query-relevant key points via LLM).
Imported by rag/pipeline.py during orchestrator construction.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Callable

import httpx
from shared.types import MergedHit, RankedHit, RawHit

from rag.llm_client import RagLLM

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


@dataclasses.dataclass
class RefineResult:
    """Result of a refine_context() call."""

    text: str | None
    reason: (
        str | None
    )  # None on success; "refiner_returned_empty" or "refiner_exception: ..." on fallback
mutants_x_refine_context__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_refine_context__mutmut)
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


async def x_refine_context__mutmut_orig(
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


async def x_refine_context__mutmut_1(
    llm: RagLLM,
    on_status: Callable[[str], None],
    reranked: list[RawHit | MergedHit | RankedHit],
    query: str,
    *,
    max_tokens: int = 2049,
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


async def x_refine_context__mutmut_2(
    llm: RagLLM,
    on_status: Callable[[str], None],
    reranked: list[RawHit | MergedHit | RankedHit],
    query: str,
    *,
    max_tokens: int = 2048,
    per_chunk_chars: int = 513,
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


async def x_refine_context__mutmut_3(
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
    """
    effective_timeout: float = None
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


async def x_refine_context__mutmut_4(
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
    """
    effective_timeout: float = timeout if timeout is None else 30.0
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


async def x_refine_context__mutmut_5(
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
    """
    effective_timeout: float = timeout if timeout is not None else 31.0
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


async def x_refine_context__mutmut_6(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status(None)
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


async def x_refine_context__mutmut_7(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("XXrefining context...XX")
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


async def x_refine_context__mutmut_8(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("REFINING CONTEXT...")
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


async def x_refine_context__mutmut_9(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("refining context...")
        refined = None
        if refined:
            return RefineResult(text=refined, reason=None)
        logger.warning("Refiner returned empty output; falling back to chunks")
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_10(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("refining context...")
        refined = await llm.refine_context(
            None,
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


async def x_refine_context__mutmut_11(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("refining context...")
        refined = await llm.refine_context(
            reranked,
            None,
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


async def x_refine_context__mutmut_12(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("refining context...")
        refined = await llm.refine_context(
            reranked,
            query,
            max_tokens=None,
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


async def x_refine_context__mutmut_13(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("refining context...")
        refined = await llm.refine_context(
            reranked,
            query,
            max_tokens=max_tokens,
            per_chunk_chars=None,
            timeout=effective_timeout,
        )
        if refined:
            return RefineResult(text=refined, reason=None)
        logger.warning("Refiner returned empty output; falling back to chunks")
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_14(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("refining context...")
        refined = await llm.refine_context(
            reranked,
            query,
            max_tokens=max_tokens,
            per_chunk_chars=per_chunk_chars,
            timeout=None,
        )
        if refined:
            return RefineResult(text=refined, reason=None)
        logger.warning("Refiner returned empty output; falling back to chunks")
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_15(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("refining context...")
        refined = await llm.refine_context(
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


async def x_refine_context__mutmut_16(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("refining context...")
        refined = await llm.refine_context(
            reranked,
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


async def x_refine_context__mutmut_17(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("refining context...")
        refined = await llm.refine_context(
            reranked,
            query,
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


async def x_refine_context__mutmut_18(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("refining context...")
        refined = await llm.refine_context(
            reranked,
            query,
            max_tokens=max_tokens,
            timeout=effective_timeout,
        )
        if refined:
            return RefineResult(text=refined, reason=None)
        logger.warning("Refiner returned empty output; falling back to chunks")
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_19(
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
    """
    effective_timeout: float = timeout if timeout is not None else 30.0
    try:
        on_status("refining context...")
        refined = await llm.refine_context(
            reranked,
            query,
            max_tokens=max_tokens,
            per_chunk_chars=per_chunk_chars,
            )
        if refined:
            return RefineResult(text=refined, reason=None)
        logger.warning("Refiner returned empty output; falling back to chunks")
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_20(
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
            return RefineResult(text=None, reason=None)
        logger.warning("Refiner returned empty output; falling back to chunks")
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_21(
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
            return RefineResult(reason=None)
        logger.warning("Refiner returned empty output; falling back to chunks")
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_22(
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
            return RefineResult(text=refined, )
        logger.warning("Refiner returned empty output; falling back to chunks")
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_23(
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
        logger.warning(None)
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_24(
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
        logger.warning("XXRefiner returned empty output; falling back to chunksXX")
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_25(
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
        logger.warning("refiner returned empty output; falling back to chunks")
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_26(
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
        logger.warning("REFINER RETURNED EMPTY OUTPUT; FALLING BACK TO CHUNKS")
        return RefineResult(text=None, reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_27(
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
        return RefineResult(text=None, reason=None)
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_28(
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
        return RefineResult(reason="refiner_returned_empty")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_29(
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
        return RefineResult(text=None, )
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_30(
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
        return RefineResult(text=None, reason="XXrefiner_returned_emptyXX")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_31(
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
        return RefineResult(text=None, reason="REFINER_RETURNED_EMPTY")
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
        logger.warning("Refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_32(
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
        logger.warning(None, e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_33(
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
        logger.warning("Refiner failed, falling back to original chunks: %s", None)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_34(
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
        logger.warning(e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_35(
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
        logger.warning("Refiner failed, falling back to original chunks: %s", )
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_36(
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
        logger.warning("XXRefiner failed, falling back to original chunks: %sXX", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_37(
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
        logger.warning("refiner failed, falling back to original chunks: %s", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_38(
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
        logger.warning("REFINER FAILED, FALLING BACK TO ORIGINAL CHUNKS: %S", e)
        return RefineResult(text=None, reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_39(
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
        return RefineResult(text=None, reason=None)


async def x_refine_context__mutmut_40(
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
        return RefineResult(reason=f"refiner_exception: {e}")


async def x_refine_context__mutmut_41(
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
        return RefineResult(text=None, )

mutants_x_refine_context__mutmut['_mutmut_orig'] = x_refine_context__mutmut_orig # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_1'] = x_refine_context__mutmut_1 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_2'] = x_refine_context__mutmut_2 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_3'] = x_refine_context__mutmut_3 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_4'] = x_refine_context__mutmut_4 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_5'] = x_refine_context__mutmut_5 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_6'] = x_refine_context__mutmut_6 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_7'] = x_refine_context__mutmut_7 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_8'] = x_refine_context__mutmut_8 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_9'] = x_refine_context__mutmut_9 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_10'] = x_refine_context__mutmut_10 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_11'] = x_refine_context__mutmut_11 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_12'] = x_refine_context__mutmut_12 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_13'] = x_refine_context__mutmut_13 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_14'] = x_refine_context__mutmut_14 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_15'] = x_refine_context__mutmut_15 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_16'] = x_refine_context__mutmut_16 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_17'] = x_refine_context__mutmut_17 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_18'] = x_refine_context__mutmut_18 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_19'] = x_refine_context__mutmut_19 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_20'] = x_refine_context__mutmut_20 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_21'] = x_refine_context__mutmut_21 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_22'] = x_refine_context__mutmut_22 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_23'] = x_refine_context__mutmut_23 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_24'] = x_refine_context__mutmut_24 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_25'] = x_refine_context__mutmut_25 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_26'] = x_refine_context__mutmut_26 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_27'] = x_refine_context__mutmut_27 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_28'] = x_refine_context__mutmut_28 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_29'] = x_refine_context__mutmut_29 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_30'] = x_refine_context__mutmut_30 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_31'] = x_refine_context__mutmut_31 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_32'] = x_refine_context__mutmut_32 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_33'] = x_refine_context__mutmut_33 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_34'] = x_refine_context__mutmut_34 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_35'] = x_refine_context__mutmut_35 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_36'] = x_refine_context__mutmut_36 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_37'] = x_refine_context__mutmut_37 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_38'] = x_refine_context__mutmut_38 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_39'] = x_refine_context__mutmut_39 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_40'] = x_refine_context__mutmut_40 # type: ignore # mutmut generated
mutants_x_refine_context__mutmut['x_refine_context__mutmut_41'] = x_refine_context__mutmut_41 # type: ignore # mutmut generated
