#!/usr/bin/env python3
"""
rag_types.py
Shared TypedDict definitions for the RAG pipeline.

Extracted from agent_rag.py to allow lightweight imports of LLMMessage and RagHit
without pulling in the full pipeline (RagRepository, RagLLM, RagPipeline).
"""

from typing import TypedDict


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


class LLMMessage(TypedDict, total=False):
    """OpenAI-compatible chat message used throughout the agent pipeline.

    role is always required; other fields depend on the message type:
      user/system : content
      assistant   : content (may be None when tool_calls present), tool_calls
      tool result : role="tool", tool_call_id, name, content
    """

    role: str  # "user" | "assistant" | "tool" | "system"
    content: str | None  # text content; None for tool_calls-only assistant messages
    tool_calls: list[dict]  # tool call requests on assistant messages
    tool_call_id: str  # tool result messages: ID from the triggering tool_call
    name: str  # tool result messages: name of the called tool
