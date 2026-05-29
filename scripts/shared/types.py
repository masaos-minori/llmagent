#!/usr/bin/env python3
"""
shared/types.py
Cross-layer type definitions shared by shared, rag, and agent packages.
"""

from typing import Protocol, TypedDict, runtime_checkable


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


@runtime_checkable
class RagConfig(Protocol):
    """Structural protocol for config objects consumed by RagPipeline.

    Allows rag.pipeline to accept AgentConfig (from agent/) or the
    SimpleNamespace adapter from rag.mcp.models without importing agent/.
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
    use_search: bool
    rag_service_url: str
    use_refiner: bool
    refiner_max_tokens: int
    refiner_max_chars_per_chunk: int
    refiner_timeout: float
