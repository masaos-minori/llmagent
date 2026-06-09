"""agent/services/context_view.py
Context state aggregation service for /context command.

Extracted from cmd_context._ContextMixin so the data collection logic
can be tested independently of the REPL.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson
from shared.git_helper import get_repo_info
from shared.types import LLMMessage

if TYPE_CHECKING:
    from agent.context import AgentContext


def budget_breakdown(messages: list[LLMMessage]) -> dict[str, int]:
    """Compute per-category character counts (system / history / tool_results)."""
    counts: dict[str, int] = {"system": 0, "history": 0, "tool_results": 0}
    for m in messages:
        role = m.get("role", "")
        text = str(m.get("content") or "")
        tool_calls = m.get("tool_calls") or []
        if role == "system":
            counts["system"] += len(text)
        elif role == "tool":
            counts["tool_results"] += len(text)
        elif role == "assistant":
            counts["history"] += len(text)
            if tool_calls:
                counts["tool_results"] += len(orjson.dumps(tool_calls))
        else:
            counts["history"] += len(text)
    return counts


def _format_memory_status(ctx: AgentContext) -> str:
    """Return a one-line summary of the memory layer state."""
    if ctx.services.memory is None:
        return "disabled"
    store = ctx.services.memory.store
    by_type = store.count_by_type()
    return (
        f"enabled (entries={store.count_entries()},"
        f" semantic={by_type.get('semantic', 0)},"
        f" episodic={by_type.get('episodic', 0)},"
        f" vec_entries={store.count_vec()})"
    )


def collect_context_state(ctx: AgentContext) -> dict:
    """Aggregate runtime context data for /context display."""
    total_chars = (
        ctx.services.hist_mgr.count_chars(ctx.conv.history)
        if ctx.services.hist_mgr is not None
        else sum(len(str(m.get("content") or "")) for m in ctx.conv.history)
    )
    system_msgs = [m for m in ctx.conv.history if m["role"] == "system"]
    sys_preview = str(system_msgs[0].get("content", ""))[:80] if system_msgs else ""
    compress_count = (
        ctx.services.hist_mgr.stat_compress_count
        if ctx.services.hist_mgr is not None
        else 0
    )
    token_is_exact = ctx.stats.stat_input_tokens is not None
    token_estimate = (
        ctx.services.hist_mgr.count_tokens(
            ctx.conv.history, ctx.stats.stat_input_tokens
        )
        if ctx.services.hist_mgr is not None
        else total_chars // 4
    )
    git_info = get_repo_info()
    return {
        "total_chars": total_chars,
        "compress_limit": ctx.cfg.llm.context_char_limit,
        "n_msgs": len(ctx.conv.history),
        "sys_preview": sys_preview,
        "compress_count": compress_count,
        "token_is_exact": token_is_exact,
        "token_estimate": token_estimate,
        "token_limit": ctx.cfg.llm.context_token_limit,
        "tokenize_configured": bool(ctx.cfg.llm.tokenize_url),
        "mem_status": _format_memory_status(ctx),
        "git_str": (
            f"{git_info['branch']} @ {git_info['commit']} {git_info['message']}"
            if git_info
            else "unavailable"
        ),
        "breakdown": budget_breakdown(ctx.conv.history),
    }
