#!/usr/bin/env python3
"""scripts/agent/commands/cmd_context.py

Context and history mixin for CommandRegistry.

Provides _ContextMixin with:
  _cmd_context   — /context: runtime state and budget breakdown
  _cmd_clear     — /clear: reset in-memory conversation history and session stats
  _cmd_undo      — /undo: roll back the last turn
  _cmd_history   — /history: show recent messages
  _cmd_compact   — /compact: force immediate context compression

Data collection delegates to agent.services.context_view.
Undo logic delegates to agent.services.undo_service.
Clear/system logic delegates to agent.services.conversation_service.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from agent.commands.exceptions import CommandValidationError
from agent.commands.mixin_base import MixinBase
from agent.commands.token_display import TokenDisplay
from agent.commands.utils import parse_command_args, parse_int_arg
from agent.history import HistoryCompressionError
from agent.services.context_view import collect_context_state
from agent.services.conversation_service import clear_conversation
from agent.services.exceptions import ContextStateBuildError

logger = logging.getLogger(__name__)

CONTEXT_PREVIEW_LENGTH = 120

# Matches a per-file unified-diff header: `diff --git a/<path> b/<path>`.
# Group 2 (the `b/` side) is used as the canonical path key since it reflects
# the post-change path (relevant for renames); non-greedy group 1 stops at the
# literal ` b/` separator so paths containing spaces still match correctly.
_DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$", re.MULTILINE)


class _ContextMixin(MixinBase, TokenDisplay):
    """Context, history, and database slash-command handlers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the context mixin via MixinBase and TokenDisplay constructors."""
        super().__init__(*args, **kwargs)

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
        self._out.write_kv(
            [
                ("Memory layer    ", state.mem_status),
                ("Git             ", git_str),
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

    async def _cmd_clear(self, args: str = "") -> None:
        """Reset in-memory conversation history to the system prompt; clear stats.

        Saved messages are not deleted; ``/clear new`` also starts a new session
        through the transition service (the old session is finalized first).
        """
        from agent.services.session_transition import (  # lazy import
            SessionTransitionRefusedError,
        )

        parsed = parse_command_args(args.split())
        new_session = parsed.subcommand == "new"
        try:
            result = await clear_conversation(self._ctx, new_session=new_session)
        except SessionTransitionRefusedError as e:
            self._out.write_validation_error(str(e))
            return
        self._out.write_success(result.message)

    def _cmd_undo(self) -> None:
        """Roll back the last user+assistant turn, gated by the compression boundary."""
        from agent.services.undo_service import (  # lazy import
            UndoReloadError,
            undo_last_turn,
        )

        try:
            result = undo_last_turn(self._ctx)
        except UndoReloadError as e:
            self._out.write_error(
                f"Undo removed {e.deleted_count} message(s) from the saved session, "
                "but the in-memory conversation history could not be reloaded and "
                "now differs from it. "
                f"Run /session load {e.session_id} to reload the saved messages."
            )
            return
        if result.block_reason:  # blocked by the boundary (rows 05/06)
            self._out.write_no_data(result.block_reason)
        else:
            self._out.write_success(
                f"Last turn undone. ({result.n_removed} messages removed)"
            )

    def _cmd_history(self, args: str) -> None:
        """Print last N user/assistant messages in compact form."""
        parsed = parse_command_args(args.split())
        try:
            n = parse_int_arg(
                parsed.subcommand or "5",
                usage="/history [n]",
                default=5,
                minimum=1,
                maximum=200,
            )
        except CommandValidationError:
            self._out.write_validation_error("/history [n]")
            return
        assert n is not None
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

    async def _cmd_compact(self) -> None:
        """Force immediate compression of conversation history.

        Bypasses the context_char_limit threshold and compresses the oldest
        context_compress_turns pairs unconditionally.
        """
        ctx = self._ctx
        if ctx.services_required.hist_mgr is None:
            self._out.write("History manager not available.")
            return
        turn_msgs = [m for m in ctx.conv.history if m["role"] != "system"]
        # compress_turns * 2: each "turn" = 1 user + 1 assistant message
        n_compress = ctx.services_required.hist_mgr.compress_turns * 2
        if len(turn_msgs) <= n_compress:
            self._out.write("Nothing to compact: history too short.")
            return
        try:
            (
                ctx.conv.history,
                result,
            ) = await ctx.services_required.hist_mgr.force_compress(ctx.conv.history)
            if (
                result.compressed_count > 0
                or result.summary_added
                or result.is_fallback
            ):
                ctx.session.replace_messages(ctx.conv.history)
                # establish the /undo boundary at the end of the new snapshot
                # (rows 02/04); mirrors the manager path in row 08.
                ctx.conv.undo_floor = len(ctx.conv.history)
        except HistoryCompressionError as e:
            self._out.write_error(f"Compression failed: {e}")
            return
