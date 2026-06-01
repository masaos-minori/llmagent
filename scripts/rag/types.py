#!/usr/bin/env python3
"""rag_types.py
Shared TypedDict definitions for the RAG pipeline.

LLMMessage is defined in shared.types and re-exported here for backward compatibility.
RagHit is RAG-specific and defined here directly.
"""

from typing import TypedDict

from shared.types import LLMMessage

__all__ = ["LLMMessage", "RagHit"]


class RagHit(TypedDict, total=False):
    """Typed structure for a single RAG search result.

    Fields present after each pipeline stage:
      vector_search / fts_search: chunk_id, content, url, title
      rrf_merge:     rrf_score
      rerank:        rerank_score
    """

    chunk_id: int
    content: str
    url: str
    title: str
    distance: float  # vector search: L2 distance (lower = closer)
    bm25_score: float  # fts search: BM25 score (negative; more negative = better)
    rrf_score: float  # rrf_merge: aggregated RRF score
    rerank_score: float  # cross_encoder_rerank: relevance score
