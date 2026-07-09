"""agent/services/context_view.py
Context state aggregation service for /context command.

Extracted from cmd_context._ContextMixin so the data collection logic
can be tested independently of the REPL.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson
from agent.services.exceptions import ContextStateBuildError
from agent.services.models import ContextBudget, ContextStateView
from shared.git_helper import get_repo_info
from shared.types import LLMMessage

if TYPE_CHECKING:
    from agent.context import AgentContext


def budget_breakdown(messages: list[LLMMessage]) -> ContextBudget:
    """Compute per-category character counts (system / history / tool_messages)."""
    system = 0
    history = 0
    tool_messages = 0
    for m in messages:
        role = m.get("role", "")
        content_raw = m.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls = m.get("tool_calls") or []
        if role == "system":
            system += len(text)
        elif role == "tool":
            tool_messages += len(text)
        elif role == "assistant":
            history += len(text)
            if tool_calls:
                tool_messages += len(orjson.dumps(tool_calls))
        else:
            history += len(text)
    return ContextBudget(system=system, history=history, tool_messages=tool_messages)


def _build_budget(messages: list[LLMMessage], token_is_exact: bool) -> ContextBudget:
    """Build ContextBudget with optional token breakdown.

    When ``token_is_exact`` is True (LLM usage or /tokenize provided exact counts),
    only character breakdown is returned.  When False, category-aware token
    estimates are included alongside character counts.
    """
    char_budget = budget_breakdown(messages)
    if token_is_exact:
        return char_budget
    ts, th, tt = _token_breakdown(messages)
    return ContextBudget(
        system=char_budget.system,
        history=char_budget.history,
        tool_messages=char_budget.tool_messages,
        token_system=ts,
        token_history=th,
        token_tool_messages=tt,
    )


def _token_breakdown(
    messages: list[LLMMessage],
) -> tuple[int | None, int | None, int | None]:
    """Estimate per-category token counts using category-aware ratios.

    Returns ``(token_system, token_history, token_tool_messages)`` or
    ``(None, None, None)`` when there is no content to estimate.

    Maps the internal token estimator categories (text, tool_calls, system)
    to budget display categories (system, history, tool_messages):

    - system → system
    - text from user/assistant/tool → history or tool_messages by role
    - tool_calls JSON → tool_messages
    """
    _RATIO_TEXT: float = 4.0
    _RATIO_TOOL_CALL: float = 2.5
    _RATIO_SYSTEM: float = 3.5

    sys_tokens = 0
    hist_tokens = 0
    tool_tokens = 0

    for m in messages:
        role = m.get("role", "")
        content_raw = m.get("content")
        text = content_raw if isinstance(content_raw, str) else ""
        tool_calls = m.get("tool_calls") or []

        if role == "system":
            if text:
                sys_tokens += int(len(text) / _RATIO_SYSTEM)
        elif role == "assistant" and tool_calls:
            if text:
                hist_tokens += int(len(text) / _RATIO_TEXT)
            for tc in tool_calls:
                tool_tokens += int(len(orjson.dumps(tc)) / _RATIO_TOOL_CALL)
        elif role == "tool":
            if text:
                tool_tokens += int(len(text) / _RATIO_TEXT)
        else:
            # user, assistant (text-only)
            if text:
                hist_tokens += int(len(text) / _RATIO_TEXT)

    return sys_tokens or None, hist_tokens or None, tool_tokens or None


def _format_memory_status(ctx: AgentContext) -> str:
    """Return a one-line summary of the memory layer state."""
    from agent.memory.count_ops import count_by_type, count_entries

    if ctx.services_required.memory is None:
        return "disabled"
    store = ctx.services_required.memory.store
    by_type = count_by_type()
    return (
        f"enabled (entries={count_entries()},"
        f" semantic={by_type.get('semantic', 0)},"
        f" episodic={by_type.get('episodic', 0)},"
        f" vec_entries={store.count_vec()})"
    )


def _extract_sys_preview(messages: list[LLMMessage]) -> str:
    """Extract a short preview from the first system message."""
    for m in messages:
        if m["role"] == "system":
            content_raw = m.get("content")
            return content_raw[:80] if isinstance(content_raw, str) else ""
    return ""


def collect_context_state(ctx: AgentContext) -> ContextStateView:
    """Aggregate runtime context data for /context display.

    Raises ContextStateBuildError when hist_mgr is not configured.
    """
    if ctx.services_required.hist_mgr is None:
        raise ContextStateBuildError("hist_mgr is not configured")
    history = ctx.conv.history
    total_chars = ctx.services_required.hist_mgr.count_chars(history)
    compress_count = ctx.services_required.hist_mgr.stat_compress_count
    fallback_truncate_count = (
        ctx.services_required.hist_mgr.stat_fallback_truncate_count
    )
    token_is_exact = ctx.stats.stat_input_tokens is not None
    token_estimate = ctx.services_required.hist_mgr.count_tokens(
        history, ctx.stats.stat_input_tokens
    )
    repo_result = get_repo_info()
    return ContextStateView(
        total_chars=total_chars,
        compress_limit=ctx.cfg.llm.context_char_limit,
        n_msgs=len(history),
        sys_preview=_extract_sys_preview(history),
        compress_count=compress_count,
        fallback_truncate_count=fallback_truncate_count,
        partial_completions=ctx.stats.stat_partial_completions,
        token_is_exact=token_is_exact,
        token_estimate=token_estimate,
        token_limit=ctx.cfg.llm.context_token_limit,
        tokenize_configured=bool(ctx.cfg.llm.tokenize_url),
        mem_status=_format_memory_status(ctx),
        git_branch=repo_result.data["branch"]
        if (repo_result.success and repo_result.data)
        else None,
        git_commit=repo_result.data["commit"]
        if (repo_result.success and repo_result.data)
        else None,
        breakdown=_build_budget(history, token_is_exact),
        approval_pending=ctx.turn.pending_approval_id is not None,
    )
