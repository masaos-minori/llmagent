#!/usr/bin/env python3
"""shared/types.py
Cross-layer type definitions shared by shared, rag, and agent packages.
"""

from typing import Protocol, TypedDict, runtime_checkable


class LLMMessage(TypedDict, total=False):
    """OpenAI-compatible chat message; role always required; content for user/system/assistant; tool_calls on assistant; tool_call_id/name on tool result messages."""

    role: str  # "user" | "assistant" | "tool" | "system"
    content: str | None  # text content; None for tool_calls-only assistant messages
    tool_calls: list[dict]  # tool call requests on assistant messages
    tool_call_id: str  # tool result messages: ID from the triggering tool_call
    name: str  # tool result messages: name of the called tool
    importance: float  # message importance score for compression
    pinned: bool  # whether message should be preserved during compression


@runtime_checkable
class RagConfig(Protocol):
    """Structural protocol for config objects consumed by RagPipeline; allows AgentConfig and SimpleNamespace adapter to satisfy it without importing agent/."""

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
    use_search: bool
    rag_service_url: str
    use_refiner: bool
    refiner_max_tokens: int
    refiner_max_chars_per_chunk: int
    refiner_timeout: float
