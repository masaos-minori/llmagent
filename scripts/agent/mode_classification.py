"""scripts/agent/mode_classification.py — MDQ/RAG mode classification and system prompt injection."""

from __future__ import annotations

import logging

from agent.context import AgentContext
from agent.mdq_rag_classifier import MdqRagMode, resolve_mode

logger = logging.getLogger(__name__)

_MDQ_KEYWORDS: frozenset[str] = frozenset(
    {"structure", "outline", "schema", "definition", "reference"}
)
_RAG_KEYWORDS: frozenset[str] = frozenset(
    {"explain", "summarize", "compare", "general", "overview"}
)


def _validate_classification(query: str, mode: MdqRagMode) -> bool:
    """Heuristic check: verify classification makes sense for the query."""
    query_lower = query.lower()
    if mode == MdqRagMode.MDQ:
        if not any(kw in query_lower for kw in _MDQ_KEYWORDS):
            logger.warning(
                "MDQ classification may be incorrect: no structural keywords found"
            )
            return False
    elif mode == MdqRagMode.RAG:
        if not any(kw in query_lower for kw in _RAG_KEYWORDS):
            logger.warning(
                "RAG classification may be incorrect: no semantic keywords found"
            )
            return False
    return True


def _mode_hint(mode: MdqRagMode) -> str:
    """Return a human-readable hint explaining which tool category to prefer for the given mode."""
    if mode == MdqRagMode.MDQ:
        return "For this query, prefer MDQ tools (search_docs, outline, get_chunk) for Markdown-structural retrieval."
    if mode == MdqRagMode.RAG:
        return "For this query, prefer RAG tools (rag_run_pipeline) for semantic/general retrieval."
    return ""


async def classify_and_inject_mode(query: str, ctx: AgentContext) -> None:
    """Inject MDQ/RAG routing hint into system prompt based on query classification."""
    config_mode = getattr(ctx.cfg, "mdq_rag_mode", None)
    mode = resolve_mode(query, config_mode)
    if mode == MdqRagMode.MDQ:
        mdq_available = any(
            "search_docs" in (srv.tool_names or [])
            for srv in ctx.cfg.mcp.mcp_servers.values()
        )
        if not mdq_available:
            logger.warning(
                "MDQ mode selected but mdq-mcp tools unavailable; falling back to RAG"
            )
            mode = MdqRagMode.RAG
    hint = _mode_hint(mode)
    if hint:
        if not _validate_classification(query, mode):
            logger.info("Classification validation failed; using fallback mode")
            mode = MdqRagMode.RAG
            hint = _mode_hint(mode)
        await ctx.conv.append_message(
            {"role": "system", "content": hint, "_ephemeral": True},
            source="cmd_handler",
        )
