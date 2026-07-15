"""mode_classification.py — MDQ/RAG mode classification and system prompt injection."""

from __future__ import annotations

import logging

from agent.context import AgentContext
from agent.mdq_rag_classifier import MdqRagMode, resolve_mode

logger = logging.getLogger(__name__)


def _mode_hint(mode: MdqRagMode) -> str:
    if mode == MdqRagMode.MDQ:
        return "For this query, prefer MDQ tools (search_docs, outline, get_chunk) for Markdown-structural retrieval."
    if mode == MdqRagMode.RAG:
        return "For this query, prefer RAG tools (rag_run_pipeline) for semantic/general retrieval."
    return ""


def classify_and_inject_mode(query: str, ctx: AgentContext) -> None:
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
        ctx.conv.history.append({"role": "system", "content": hint, "_ephemeral": True})
