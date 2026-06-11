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
Clear/system logic delegates to agent.services.conversation_service.
"""

from __future__ import annotations

import logging

from agent.commands.formatter import (
    print_kv_list,
    print_no_data,
    print_success,
    print_validation_error,
)
from agent.commands.mixin_base import MixinBase
from agent.commands.utils import parse_command_args
from agent.services.context_view import collect_context_state
from agent.services.conversation_service import clear_conversation, switch_system_prompt

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
            token_value = f"{token_estimate:,} ({src}, limit={token_limit:,} [active] {token_pct}%)"
        else:
            token_value = f"{token_estimate:,} ({src})"
        print_kv_list(
            [
                (token_label, token_value),
                ("Token limit     ", token_limit_str),
            ]
        )

    def _cmd_context(self) -> None:
        """Print runtime conversation context state."""
        ctx = self._ctx
        state = collect_context_state(ctx)
        breakdown = state["breakdown"]
        total_bd = sum(breakdown.values()) or 1
        print_kv_list(
            [
                ("Messages        ", str(state["n_msgs"])),
                ("Total chars     ", f"{state['total_chars']:,}"),
                ("Compress limit  ", f"{state['compress_limit']:,}"),
                (
                    "Remaining       ",
                    f"{state['compress_limit'] - state['total_chars']:,} chars until compression",
                ),
                ("Compress count  ", str(state["compress_count"])),
                ("System prompt   ", ctx.conv.system_prompt_name),
                ("System preview  ", repr(state["sys_preview"])),
            ]
        )
        self._print_token_line(state)
        print_kv_list(
            [
                ("Memory layer    ", state["mem_status"]),
                ("Git             ", state["git_str"]),
            ]
        )
        print("Budget breakdown:")
        for cat, n in breakdown.items():
            pct = n * 100 // total_bd
            print(f"  {cat:<14}: {n:>8,} chars ({pct:>3}%)")

    def _cmd_clear(self, args: str = "") -> None:
        """Reset conversation history to system prompt only and clear session stats.

        /clear     — reset history in the current session
        /clear new — reset history and start a new DB session
        """
        parsed = parse_command_args(args.split())
        new_session = parsed.subcommand == "new"
        msg = clear_conversation(self._ctx, new_session=new_session)
        print(f"  {msg}")

    def _cmd_undo(self) -> None:
        """Roll back the last user+assistant turn from in-memory history and DB."""
        from agent.services.exceptions import (
            NothingToUndoError,  # noqa: PLC0415 — lazy: avoids import at module load
        )
        from agent.services.undo_service import (
            undo_last_turn,  # noqa: PLC0415 — lazy: avoids import at module load
        )

        try:
            result = undo_last_turn(self._ctx)
            print_success(f"Last turn undone. ({result.n_removed} messages removed)")
        except NothingToUndoError as e:
            print_no_data(str(e))

    def _cmd_history(self, args: str) -> None:
        """Print last N user/assistant messages in compact form."""
        parsed = parse_command_args(args.split())
        raw = parsed.subcommand or "5"
        try:
            n = int(raw)
        except ValueError:
            print_validation_error("/history [n]")
            return
        ctx = self._ctx
        turns = [m for m in ctx.conv.history if m["role"] in ("user", "assistant")]
        recent = turns[-n:]
        if not recent:
            print_no_data("No conversation history.")
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
            print(f"  Current: {ctx.conv.system_prompt_name}")
            print(f"  Available: {names}")
            return
        try:
            msg = switch_system_prompt(ctx, name)
            print(f"  {msg}")
        except ValueError as e:
            print_validation_error(str(e))
