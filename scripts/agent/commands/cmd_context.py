#!/usr/bin/env python3
"""agent/commands/cmd_context.py
Context and history mixin for CommandRegistry.

Provides _ContextMixin with:
  _cmd_context   — /context: runtime state and budget breakdown
  _cmd_clear     — /clear: reset history and session stats
  _cmd_undo      — /undo: roll back the last turn
  _cmd_history   — /history: show recent messages
  _cmd_system    — /system: switch system prompt preset

Data collection delegates to agent.services.context_view.
Undo logic delegates to agent.services.undo_service.
"""

from __future__ import annotations

import logging

from agent.commands.mixin_base import MixinBase, reset_session_stats
from agent.services.context_view import collect_context_state

logger = logging.getLogger(__name__)


def _token_source_label(token_is_exact: bool, tokenize_configured: bool) -> str:
    """Return a human-readable label for the token count source."""
    if token_is_exact:
        return "LLM usage"
    if tokenize_configured:
        return "/tokenize (next turn)"
    return "chars/4"


class _ContextMixin(MixinBase):
    """Context, history, and database slash-command handlers."""

    def _print_token_line(self, state: dict) -> None:
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
        state = collect_context_state(ctx)
        breakdown = state["breakdown"]
        total_bd = sum(breakdown.values()) or 1  # avoid zero division
        print("Context state:")
        print(f"  Messages        : {state['n_msgs']}")
        print(f"  Total chars     : {state['total_chars']:,}")
        print(f"  Compress limit  : {state['compress_limit']:,}")
        print(
            f"  Remaining       : {state['compress_limit'] - state['total_chars']:,} chars until compression"
        )
        print(f"  Compress count  : {state['compress_count']}")
        print(f"  System prompt   : {ctx.conv.system_prompt_name}")
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
        ctx.conv.history = ctx.conv.history[:1]
        reset_session_stats(ctx)
        if "new" in args.split():
            ctx.session.start()
            print("History cleared. New session started.")
        else:
            print("History cleared. Session stats reset.")

    def _cmd_undo(self) -> None:
        """Roll back the last user+assistant turn from in-memory history and DB."""
        from agent.services.undo_service import (
            undo_last_turn,  # noqa: PLC0415 — lazy: avoids import at module load
        )

        _, message = undo_last_turn(self._ctx)
        print(message)

    def _cmd_history(self, args: str) -> None:
        """Print last N user/assistant messages in compact form."""
        try:
            n = int(args.strip()) if args.strip() else 5
        except ValueError:
            print("Usage: /history [n]")
            return
        ctx = self._ctx
        turns = [m for m in ctx.conv.history if m["role"] in ("user", "assistant")]
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
            prompts = ctx.cfg.tool.system_prompts
            names = ", ".join(prompts.keys()) if prompts else "(none)"
            print(f"Current: {ctx.conv.system_prompt_name}")
            print(f"Available: {names}")
            return
        if name not in ctx.cfg.tool.system_prompts:
            names = ", ".join(ctx.cfg.tool.system_prompts.keys())
            print(f"Unknown preset '{name}'. Available: {names}")
            return
        ctx.conv.system_prompt_name = name
        ctx.conv.system_prompt_content = ctx.cfg.tool.system_prompts[name]
        # Immediately sync history[0] so the new prompt takes effect in this turn.
        if ctx.conv.history and ctx.conv.history[0]["role"] == "system":
            ctx.conv.history[0]["content"] = ctx.conv.system_prompt_content
        elif ctx.conv.system_prompt_content:
            ctx.conv.history.insert(
                0, {"role": "system", "content": ctx.conv.system_prompt_content}
            )
        logger.info(f"System prompt switched to '{name}'")
        print(f"System prompt: {name}")
