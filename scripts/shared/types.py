#!/usr/bin/env python3
"""shared/types.py

Cross-layer type definitions shared by shared, rag, and agent packages.
"""

import dataclasses
from typing import Any, Literal, Protocol, TypedDict, runtime_checkable


class _LLMMessageRequired(TypedDict):
    """Required fields for every LLM chat message."""

    role: Literal["user", "assistant", "tool", "system"]


class LLMMessage(_LLMMessageRequired, total=False):
    """OpenAI-compatible chat message; role always required; other fields depend on message type."""

    content: str | None  # text content; None for tool_calls-only assistant messages
    tool_calls: list[dict[str, Any]]  # tool call requests on assistant messages
    tool_call_id: str  # tool result messages: ID from the triggering tool_call
    name: str  # tool result messages: name of the called tool
    importance: float  # message importance score for compression
    pinned: bool  # whether message should be preserved during compression
    _ephemeral: (
        bool  # excluded from persistence/compression; dropped before the next turn
    )
    _skill_ephemeral: bool  # like _ephemeral, but scoped to skill-injected messages
    _memory_injected: bool  # marks a message as memory-layer injected context


class ToolCallFunction(TypedDict):
    """Function descriptor inside a tool call."""

    name: str
    arguments: str  # JSON-encoded string


class ToolCallDict(TypedDict):
    """One tool call entry in an assistant message's tool_calls list."""

    id: str
    type: Literal["function"]
    function: ToolCallFunction


class ToolCallFunctionDelta(TypedDict, total=False):
    """Streaming delta for the function part of a tool call."""

    name: str
    arguments: str


class ToolCallDelta(TypedDict, total=False):
    """Streaming delta for a single tool call (may omit any field)."""

    index: int
    id: str
    function: ToolCallFunctionDelta


class AccumulatedToolCall(TypedDict):
    """Complete accumulated tool call from streaming deltas."""

    id: str
    type: Literal["function"]
    function: ToolCallFunction


@runtime_checkable
class RagConfig(Protocol):
    """Canonical runtime config contract for RagPipeline.

    Any object satisfying these fields (AgentConfig, SimpleNamespace adapter, etc.)
    can be passed to RagPipeline without importing agent-layer classes into the RAG layer.

    This is NOT a file-format DTO.  Config file DTOs live in:
      - mcp_servers.rag_pipeline.models.RagPipelineConfig (MCP TOML)
      - rag.models_config.* (ingestion TOML)

    See also: build_rag_cfg_adapter() in mcp_servers.rag_pipeline.models for the MCP adapter.
    """

    semantic_cache_max_size: int
    semantic_cache_threshold: float
    use_mqe: bool
    top_k_search: int
    use_rerank: bool
    rag_top_k: int
    max_chunks_per_doc: int
    top_k_rerank: int
    rag_min_score: float
    use_rrf: bool
    rrf_k: int
    use_search: bool
    rag_service_url: str
    rag_auth_token: str
    use_refiner: bool
    refiner_max_tokens: int
    refiner_max_chars_per_chunk: int
    refiner_timeout: float
    use_semantic_cache: bool


# ── RAG hit types ─────────────────────────────────────────────────────────────
# Defined here so shared/ can reference them without importing from rag/.


@dataclasses.dataclass
class RawHit:
    """Search result from vector_search or fts_search."""

    chunk_id: int
    content: str
    url: str = ""
    title: str = ""
    distance: float = 0.0
    bm25_score: float = 0.0


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


RagHit = RawHit | MergedHit | RankedHit
