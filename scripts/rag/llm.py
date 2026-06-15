"""rag/llm.py -- Re-export stub for backward compatibility.

This module re-exports all public symbols from split sub-modules so that
existing imports continue to work without changes:

    from rag.llm import RagLLM, get_embedding, summarize_tool_result
    from rag.llm import RagExpansionError, RagRerankError

New code should import directly from the sub-modules:

    from rag.llm_client import RagLLM, get_embedding, summarize_tool_result
    from rag.llm_prompts import RagExpansionError, RagRerankError
"""

from __future__ import annotations

# Re-export from llm_client.py
from rag.llm_client import (  # noqa: F401
    RagHit,
    RagLLM,
    get_embedding,
    summarize_tool_result,
)

# Re-export from llm_prompts.py
from rag.llm_prompts import (  # noqa: F401
    MqeParseError,
    MqeParseResult,
    RagExpansionError,
    RagRerankError,
)

__all__ = [
    "MqeParseError",
    "MqeParseResult",
    "RagHit",
    "RagLLM",
    "RagExpansionError",
    "RagRerankError",
    "get_embedding",
    "summarize_tool_result",
]
