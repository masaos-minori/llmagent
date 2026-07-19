#!/usr/bin/env python3
"""agent/commands/cmd_context.py

Context and history mixin for CommandRegistry.

Provides _ContextMixin with:
  _cmd_context   — /context: runtime state and budget breakdown
  _cmd_clear     — /clear: reset history and session stats
  _cmd_undo      — /undo: roll back the last turn
  _cmd_history   — /history: show recent messages
  _cmd_system    — /system: switch system prompt preset
  _cmd_diff      — /diff: show diffs for files written/edited this session

Data collection delegates to agent.services.context_view.
Undo logic delegates to agent.services.undo_service.
Clear/system logic delegates to agent.services.conversation_service.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import git
import orjson

from agent.commands.mixin_base import MixinBase
from agent.commands.token_display import TokenDisplay
from agent.commands.utils import parse_command_args
from agent.services.context_view import collect_context_state
from agent.services.conversation_service import clear_conversation, switch_system_prompt
from agent.services.exceptions import ContextStateBuildError, ConversationStateError

logger = logging.getLogger(__name__)

CONTEXT_PREVIEW_LENGTH = 120

# Matches a per-file unified-diff header: `diff --git a/<path> b/<path>`.
# Group 2 (the `b/` side) is used as the canonical path key since it reflects
# the post-change path (relevant for renames); non-greedy group 1 stops at the
# literal ` b/` separator so paths containing spaces still match correctly.
_DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$", re.MULTILINE)

_DIFF_TOUCHED_TOOL_NAMES = ("write_file", "edit_file")


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
            if result.warning:
                self._out.write_no_data(f"[warn] {result.warning}")
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

    async def _cmd_diff(self) -> None:
        """Show working-tree diffs for files written/edited via tool calls this session."""
        ctx = self._ctx
        paths = self._collect_diff_touched_paths()
        if not paths:
            self._out.write("No files written or edited this session.")
            return
        if ctx.services is None or ctx.services.tools is None:
            self._out.write("MCP tool executor not available.")
            return
        by_repo, outside_repo = self._group_paths_by_repo(paths)
        for path in outside_repo:
            self._out.write(f"{path}: not inside a git repository (skipped)")
        for repo_root, repo_paths in by_repo.items():
            result = await ctx.services.tools.execute(
                "git_diff", {"repo_path": repo_root, "commit": ""}
            )
            if result.is_error or result.output.startswith("[DENIED]"):
                self._out.write(f"[{repo_root}] git diff unavailable: {result.output}")
                continue
            self._print_repo_diffs(repo_root, repo_paths, result.output)

    def _collect_diff_touched_paths(self) -> list[str]:
        """Extract distinct file paths written/edited by tool calls in this session's history.

        Scans assistant messages for write_file/edit_file tool calls, preserving
        first-seen order. Malformed entries (bad JSON, missing keys, wrong types)
        are skipped individually rather than aborting the whole scan.
        """
        ctx = self._ctx
        paths: list[str] = []
        for msg in ctx.conv.history:
            if msg["role"] != "assistant":
                continue
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                continue
            for call in tool_calls:
                try:
                    function = call["function"]
                    name = function["name"]
                    if name not in _DIFF_TOUCHED_TOOL_NAMES:
                        continue
                    args = orjson.loads(function["arguments"])
                    path = args["path"]
                except (KeyError, TypeError, orjson.JSONDecodeError):
                    continue
                if isinstance(path, str) and path:
                    paths.append(path)
        return list(dict.fromkeys(paths))

    def _group_paths_by_repo(
        self, paths: list[str]
    ) -> tuple[dict[str, list[str]], list[str]]:
        """Group touched paths by containing git repository's working-tree root.

        Paths outside any git repository (or whose containing repo has no
        working tree, e.g. a bare repo) are returned separately.
        """
        by_repo: dict[str, list[str]] = {}
        outside_repo: list[str] = []
        for path in paths:
            search_dir = str(Path(path).parent)
            try:
                repo = git.Repo(search_dir, search_parent_directories=True)
            except (git.InvalidGitRepositoryError, git.NoSuchPathError):
                outside_repo.append(path)
                continue
            repo_root = repo.working_tree_dir
            if repo_root is None:
                outside_repo.append(path)
                continue
            by_repo.setdefault(str(repo_root), []).append(path)
        return by_repo, outside_repo

    def _print_repo_diffs(
        self, repo_root: str, touched_paths: list[str], diff_text: str
    ) -> None:
        """Split a repo-wide unified diff by per-file headers and print each touched path's hunk.

        Paths with no matching hunk (clean repo, or a touched path with no
        working-tree change) get a single "no working-tree diff" notice.
        """
        matches = list(_DIFF_HEADER_RE.finditer(diff_text))
        sections: dict[str, str] = {}
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(diff_text)
            sections[match.group(2)] = diff_text[match.start() : end].rstrip("\n")
        for path in touched_paths:
            try:
                rel = Path(path).relative_to(repo_root, walk_up=True).as_posix()
            except ValueError:
                rel = path
            body = sections.get(rel)
            if body is None:
                self._out.write(f"{path}: no working-tree diff")
                continue
            self._out.write(f"--- {path} ---")
            self._out.write(body)
