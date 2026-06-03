#!/usr/bin/env python3
"""cmd_context.py
Context and history mixin for CommandRegistry.

Extracted from agent_commands.py.  Provides _ContextMixin with:
  _cmd_context   — /context: runtime state and budget breakdown
  _cmd_clear     — /clear: reset history and session stats
  _cmd_undo      — /undo: roll back the last turn (strips memory injection markers)
  _cmd_history   — /history: show recent messages
  _cmd_system    — /system: switch system prompt preset

Also defines _budget_breakdown (re-exported by registry.py).
DB commands (_cmd_db / _db_*) live in cmd_db.py (_DbMixin).
"""

import logging
from typing import TYPE_CHECKING

import orjson
from shared.git_helper import get_repo_info
from shared.types import LLMMessage

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


def _budget_breakdown(messages: list[LLMMessage]) -> dict[str, int]:
    """Compute per-category character counts for the given message list.

    Categories: system, history, tool_results.
    Tool results include role='tool' messages and assistant tool_calls JSON.
    """
    counts: dict[str, int] = {
        "system": 0,
        "history": 0,
        "tool_results": 0,
    }
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


def _format_memory_status(ctx: "AgentContext") -> str:
    """Return a one-line summary of the memory layer state."""
    if ctx.services.memory is None:
        return "disabled"
    mem = ctx.services.memory
    by_type = mem.stat_by_type
    return (
        f"enabled (entries={mem.stat_entries},"
        f" semantic={by_type.get('semantic', 0)},"
        f" episodic={by_type.get('episodic', 0)},"
        f" vec_entries={mem.stat_vec_entries})"
    )


def _token_source_label(token_is_exact: bool, tokenize_configured: bool) -> str:
    """Return a human-readable label for the token count source."""
    if token_is_exact:
        return "LLM usage"
    if tokenize_configured:
        return "/tokenize (next turn)"
    return "chars/4"


class _ContextMixin:
    """Context, history, and database slash-command handlers."""

    if TYPE_CHECKING:
        _ctx: "AgentContext"

    def _collect_context_state(self, ctx: "AgentContext") -> dict:
        """Collect runtime context state into a plain dict for display."""
        total_chars = (
            ctx.services.hist_mgr.count_chars(ctx.history)
            if ctx.services.hist_mgr is not None
            else sum(len(str(m.get("content") or "")) for m in ctx.history)
        )
        system_msgs = [m for m in ctx.history if m["role"] == "system"]
        sys_preview = str(system_msgs[0].get("content", ""))[:80] if system_msgs else ""
        compress_count = (
            ctx.services.hist_mgr.stat_compress_count
            if ctx.services.hist_mgr is not None
            else 0
        )
        token_is_exact = ctx.stat_input_tokens is not None
        token_estimate = (
            ctx.services.hist_mgr.count_tokens(ctx.history, ctx.stat_input_tokens)
            if ctx.services.hist_mgr is not None
            else total_chars // 4
        )
        git_info = get_repo_info()
        return {
            "total_chars": total_chars,
            "compress_limit": ctx.cfg.context_char_limit,
            "n_msgs": len(ctx.history),
            "sys_preview": sys_preview,
            "compress_count": compress_count,
            "token_is_exact": token_is_exact,
            "token_estimate": token_estimate,
            "token_limit": ctx.cfg.context_token_limit,
            "tokenize_configured": bool(getattr(ctx.cfg, "tokenize_url", "")),
            "mem_status": _format_memory_status(ctx),
            "git_str": (
                f"{git_info['branch']} @ {git_info['commit']} {git_info['message']}"
                if git_info
                else "unavailable"
            ),
            "breakdown": _budget_breakdown(ctx.history),
        }

    def _print_token_line(
        self,
        state: dict,
    ) -> None:
        """Print token count / estimate with source label and optional limit info."""
        token_estimate = state["token_estimate"]
        token_limit = state["token_limit"]
        token_limit_str = f"{token_limit:,}" if token_limit > 0 else "disabled"
        token_label = "Token count  " if state["token_is_exact"] else "Token estimate"
        src = _token_source_label(state["token_is_exact"], state["tokenize_configured"])
        if token_limit > 0:
            token_pct = int(token_estimate * 100 / token_limit)
            print(
                f"  {token_label} : {token_estimate:,}"
                f" ({src}, limit={token_limit:,} [active] {token_pct}%)",
            )
        else:
            print(f"  {token_label} : {token_estimate:,} ({src})")
        print(f"  Token limit     : {token_limit_str}")

    def _cmd_context(self) -> None:
        """Print runtime conversation context state."""
        ctx = self._ctx
        state = self._collect_context_state(ctx)
        breakdown = state["breakdown"]
        total_bd = sum(breakdown.values()) or 1  # avoid zero division
        # Token count note: exact when LLM reports usage.prompt_tokens; estimate otherwise.
        # /tokenize exact counting needs async; /context shows best synchronous value.
        print("Context state:")
        print(f"  Messages        : {state['n_msgs']}")
        print(f"  Total chars     : {state['total_chars']:,}")
        print(f"  Compress limit  : {state['compress_limit']:,}")
        print(
            f"  Remaining       : {state['compress_limit'] - state['total_chars']:,} chars until compression"
        )
        print(f"  Compress count  : {state['compress_count']}")
        print(f"  System prompt   : {ctx.system_prompt_name}")
        print(f"  System preview  : {state['sys_preview']!r}")
        self._print_token_line(state)
        print(f"  Memory layer    : {state['mem_status']}")
        print(f"  Git             : {state['git_str']}")
        print("Budget breakdown:")
        for cat, n in breakdown.items():
            pct = n * 100 // total_bd
            print(f"  {cat:<14}: {n:>8,} chars ({pct:>3}%)")

    def _cmd_clear(self, args: str = "") -> None:
        """Reset conversation history to system prompt only and clear session stats.

        /clear     — reset history in the current session
        /clear new — reset history and start a new DB session
        """
        ctx = self._ctx
        ctx.history = ctx.history[:1]
        ctx.stat_turns = 0
        ctx.stat_tool_calls = 0
        ctx.stat_tool_errors = 0
        ctx.stat_latency = {}
        ctx.stat_semantic_cache_hits = 0
        if ctx.services.llm is not None:
            ctx.services.llm.stat_retries = 0
        if "new" in args.split():
            ctx.session.start()
            print("History cleared. New session started.")
        else:
            print("History cleared. Session stats reset.")

    def _cmd_undo(self) -> None:
        """Roll back the last user+assistant turn from in-memory history and DB.

        Also removes any immediately preceding memory injection markers
        (_memory_injected=True) that were prepended before the user message.
        """
        ctx = self._ctx
        last_user_idx = next(
            (
                i
                for i in range(len(ctx.history) - 1, -1, -1)
                if ctx.history[i]["role"] == "user"
            ),
            None,
        )
        if last_user_idx is None:
            print("Nothing to undo.")
            return
        # Walk backwards from just before the user message to strip injected memory blocks.
        cut_idx = last_user_idx
        while cut_idx > 0 and ctx.history[cut_idx - 1].get("_memory_injected"):
            cut_idx -= 1
        removed = len(ctx.history) - cut_idx
        ctx.history = ctx.history[:cut_idx]
        ctx.stat_turns = max(0, ctx.stat_turns - 1)
        ctx.session.delete_last_turn()
        logger.info(f"Undo: removed {removed} messages from history")
        print("Last turn undone.")

    def _cmd_history(self, args: str) -> None:
        """Print last N user/assistant messages in compact form."""
        try:
            n = int(args.strip()) if args.strip() else 5
        except ValueError:
            print("Usage: /history [n]")
            return
        ctx = self._ctx
        turns = [m for m in ctx.history if m["role"] in ("user", "assistant")]
        recent = turns[-n:]
        if not recent:
            print("No conversation history.")
            return
        for msg in recent:
            content = msg.get("content") or ""
            preview = content[:120].replace("\n", " ")
            if len(content) > 120:
                preview += "..."
            print(f"[{msg['role']}] {preview}")

    def _cmd_system(self, args: str) -> None:
        """Switch the active system prompt to a named preset defined in agent.toml."""
        ctx = self._ctx
        name = args.strip()
        if not name:
            prompts = ctx.cfg.system_prompts
            names = ", ".join(prompts.keys()) if prompts else "(none)"
            print(f"Current: {ctx.system_prompt_name}")
            print(f"Available: {names}")
            return
        if name not in ctx.cfg.system_prompts:
            names = ", ".join(ctx.cfg.system_prompts.keys())
            print(f"Unknown preset '{name}'. Available: {names}")
            return
        ctx.system_prompt_name = name
        # Update the canonical field; Orchestrator syncs history[0] at next turn start.
        ctx.system_prompt_content = ctx.cfg.system_prompts[name]
        logger.info(f"System prompt switched to '{name}'")
        print(f"System prompt: {name}")
