#!/usr/bin/env python3
"""rag/types.py
Shared type definitions for the RAG pipeline.

LLMMessage is defined in shared.types and re-exported here for backward compatibility.
RawHit / MergedHit / RankedHit model the three search pipeline stages.
RagHit is a Union alias kept for backward compatibility with existing callers.
"""

from __future__ import annotations

import dataclasses
from typing import Required, TypedDict

from shared.types import LLMMessage

__all__ = [
    "LLMMessage",
    "MergedHit",
    "PipelineStageResult",
    "RagHit",
    "RagQuery",
    "RankedHit",
    "RawHit",
]


class RawHit(TypedDict, total=False):
    """Search result from vector_search or fts_search.

    chunk_id and content are always present; distance/bm25_score depend on search type.
    """

    chunk_id: Required[int]
    content: Required[str]
    url: str
    title: str
    distance: float  # vector search: L2 distance (lower = closer)
    bm25_score: float  # fts search: BM25 score (negative; more negative = better)


class MergedHit(RawHit, total=False):
    """RawHit after RRF merge; carries aggregated rrf_score."""

    rrf_score: float


class RankedHit(MergedHit, total=False):
    """MergedHit after cross-encoder rerank; carries rerank_score."""

    rerank_score: float


# Union alias — kept for backward compatibility with existing callers.
RagHit = RawHit | MergedHit | RankedHit


@dataclasses.dataclass
class RagQuery:
    """Represents a single query string with optional context."""

    query: str
    context: str = ""


@dataclasses.dataclass
class PipelineStageResult:
    """Records the outcome of a single pipeline stage execution."""

    stage: str
    success: bool
    failure_reason: str | None = None
    elapsed_s: float = 0.0
