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

from agent.commands.mixin_base import MixinBase
from agent.commands.token_display import TokenDisplay
from agent.commands.utils import parse_command_args
from agent.services.context_view import collect_context_state
from agent.services.conversation_service import clear_conversation, switch_system_prompt
from agent.services.exceptions import ContextStateBuildError, ConversationStateError

logger = logging.getLogger(__name__)

CONTEXT_PREVIEW_LENGTH = 120


class _ContextMixin(MixinBase, TokenDisplay):
    """Context, history, and database slash-command handlers."""

    def _cmd_context(self) -> None:
        """Print runtime conversation context state."""
        ctx = self._ctx
        try:
            state = collect_context_state(ctx)
        except ContextStateBuildError as e:
            self._out.write_no_data(str(e))
            return
        breakdown = state.breakdown
        total_bd = (breakdown.system + breakdown.history + breakdown.tool_messages) or 1
        git_str = (
            f"{state.git_branch} @ {state.git_commit}"
            if state.git_branch and state.git_commit
            else "unavailable"
        )
        self._out.write_kv(
            [
                ("Messages        ", str(state.n_msgs)),
                ("Total chars     ", f"{state.total_chars:,}"),
                ("Compress limit  ", f"{state.compress_limit:,}"),
                (
                    "Remaining       ",
                    f"{state.compress_limit - state.total_chars:,} chars until compression",
                ),
                ("Compress count  ", str(state.compress_count)),
                ("Fallback trunc  ", str(state.fallback_truncate_count)),
                ("System prompt   ", ctx.conv.system_prompt_name),
                ("System preview  ", repr(state.sys_preview)),
            ]
        )
        if state.partial_completions > 0:
            self._out.write_kv(
                [
                    (
                        "Partial compl   ",
                        f"{state.partial_completions} (stored in session_diagnostics)",
                    ),
                ]
            )
        self._print_token_line(state)
        approval_str = (
            "Yes -> use /approve or /reject" if state.approval_pending else "No"
        )
        self._out.write_kv(
            [
                ("Memory layer    ", state.mem_status),
                ("Git             ", git_str),
                ("Approval pending", approval_str),
            ]
        )
        self._out.write("Budget breakdown:")
        for cat, n in [
            ("system", breakdown.system),
            ("history", breakdown.history),
            ("tool_messages", breakdown.tool_messages),
        ]:
            pct = n * 100 // total_bd
            self._out.write(f"  {cat:<14}: {n:>8,} chars ({pct:>3}%)")
        if not state.token_is_exact:
            ts = breakdown.token_system
            th = breakdown.token_history
            tt = breakdown.token_tool_messages
            if ts is not None and th is not None and tt is not None:
                total_tokens = ts + th + tt
                self._out.write("Token estimate:")
                for cat, n in [
                    ("system", ts),
                    ("history", th),
                    ("tool_messages", tt),
                ]:
                    pct = n * 100 // total_tokens if total_tokens > 0 else 0
                    self._out.write(f"  {cat:<14}: {n:>8,} tokens ({pct:>3}%)")

    def _cmd_clear(self, args: str = "") -> None:
        """Reset conversation history to system prompt only and clear session stats."""
        parsed = parse_command_args(args.split())
        new_session = parsed.subcommand == "new"
        result = clear_conversation(self._ctx, new_session=new_session)
        self._out.write_success(result.message)

    def _cmd_undo(self) -> None:
        """Roll back the last user+assistant turn from in-memory history and DB."""
        from agent.services.exceptions import (  # noqa: PLC0415 — lazy import
            NothingToUndoError,
        )
        from agent.services.undo_service import (  # noqa: PLC0415 — lazy import
            undo_last_turn,
        )

        try:
            result = undo_last_turn(self._ctx)
            self._out.write_success(
                f"Last turn undone. ({result.n_removed} messages removed)"
            )
        except NothingToUndoError as e:
            self._out.write_no_data(str(e))

    def _cmd_history(self, args: str) -> None:
        """Print last N user/assistant messages in compact form."""
        parsed = parse_command_args(args.split())
        raw = parsed.subcommand or "5"
        try:
            n = int(raw)
        except ValueError:
            self._out.write_validation_error("/history [n]")
            return
        ctx = self._ctx
        turns = [m for m in ctx.conv.history if m["role"] in ("user", "assistant")]
        recent = turns[-n:]
        if not recent:
            self._out.write_no_data("No conversation history.")
            return
        for msg in recent:
            content_raw = msg.get("content")
            content = content_raw if isinstance(content_raw, str) else ""
            preview = content[:CONTEXT_PREVIEW_LENGTH].replace("\n", " ")
            if len(content) > CONTEXT_PREVIEW_LENGTH:
                preview += "..."
            self._out.write(f"[{msg['role']}] {preview}")

    def _cmd_system(self, args: str) -> None:
        """Switch the active system prompt to a named preset defined in system_prompts.toml."""
        ctx = self._ctx
        name = args.strip()
        if not name:
            prompts = ctx.cfg.tool.system_prompts
            names = ", ".join(prompts.keys()) if prompts else "(none)"
            self._out.write(f"  Current: {ctx.conv.system_prompt_name}")
            self._out.write(f"  Available: {names}")
            return
        try:
            result = switch_system_prompt(ctx, name)
            self._out.write(f"  {result.message}")
        except ConversationStateError as e:
            self._out.write_validation_error(str(e))
