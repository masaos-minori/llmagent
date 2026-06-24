#!/usr/bin/env python3
"""rag/types.py
Shared type definitions for the RAG pipeline.

RawHit / MergedHit / RankedHit model the three search pipeline stages.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Optional

from rag.enums import PipelineStageName

if TYPE_CHECKING:
    from rag.models_result import SearchDiagnostics
    from rag.stage import StageResult

__all__ = [
    "MergedHit",
    "PipelineRunResult",
    "PipelineStageResult",
    "RagHit",
    "RagQuery",
    "RankedHit",
    "RawHit",
]


@dataclasses.dataclass
class RawHit:
    """Search result from vector_search or fts_search."""

    chunk_id: int
    content: str
    url: str = ""
    title: str = ""
    distance: float = 0.0  # vector search: L2 distance (lower = closer)
    bm25_score: float = 0.0  # fts search: BM25 score (negative; more negative = better)


@dataclasses.dataclass
class MergedHit:
    """RawHit after RRF merge; carries aggregated rrf_score."""

    chunk_id: int
    content: str
    url: str = ""
    title: str = ""
    distance: float = 0.0
    bm25_score: float = 0.0
    rrf_score: float = 0.0


@dataclasses.dataclass
class RankedHit:
    """MergedHit after cross-encoder rerank; carries rerank_score."""

    chunk_id: int
    content: str
    url: str = ""
    title: str = ""
    distance: float = 0.0
    bm25_score: float = 0.0
    rrf_score: float = 0.0
    rerank_score: float | None = None


@dataclasses.dataclass
class RagQuery:
    """Represents a single query string with optional context."""

    query: str
    context: str = ""


@dataclasses.dataclass
class PipelineStageResult:
    """Records the outcome of a single pipeline stage execution."""

    stage: PipelineStageName | str
    success: bool
    failure_reason: str | None = None
    elapsed_s: float = 0.0


@dataclasses.dataclass
class PipelineRunResult:
    """Typed result from RagPipeline.run()."""

    queries: list[str]
    search_results: list[list[RawHit]]
    merged: list[RagHit]
    reranked: list[RagHit]
    stage_results: list[StageResult]
    diagnostics: SearchDiagnostics
    result_source: Optional[str] = None


# Union type alias for all search result hit types
RagHit = RawHit | MergedHit | RankedHit
