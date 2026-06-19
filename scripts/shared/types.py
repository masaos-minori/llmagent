#!/usr/bin/env python3
"""shared/types.py
Cross-layer type definitions shared by shared, rag, and agent packages.
"""

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


class ToolCallFunction(TypedDict):
    """Function descriptor inside a tool call."""

    name: str
    arguments: str  # JSON-encoded string


class ToolCallDict(TypedDict):
    """One tool call entry in an assistant message's tool_calls list."""

    id: str
    type: Literal["function"]
    function: ToolCallFunction


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
    rrf_k: int
    use_search: bool
    rag_service_url: str
    rag_auth_token: str
    use_refiner: bool
    refiner_max_tokens: int
    refiner_max_chars_per_chunk: int
    refiner_timeout: float
    use_semantic_cache: bool
