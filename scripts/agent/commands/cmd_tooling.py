#!/usr/bin/env python3
"""agent/commands/cmd_tooling.py
Tool inspection and plan-mode mixin for CommandRegistry.

Provides _ToolingMixin with:
  _cmd_tool  — /tool: inspect stored tool results
  _cmd_plan  — /plan: toggle plan mode
"""

import logging
from typing import Any

import orjson

from agent.commands.mixin_base import MixinBase
from agent.commands.models import ToolResultView

logger = logging.getLogger(__name__)


def _decode_args(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        result = orjson.loads(raw)
        return result if isinstance(result, dict) else {}
    except orjson.JSONDecodeError:
        logger.warning("Failed to decode args_masked JSON; displaying empty args")
        return {}


def _to_tool_result_view(entry: dict[str, Any]) -> ToolResultView:
    return ToolResultView(
        result_id=int(entry["id"]),
        tool_name=str(entry["tool_name"]),
        summary=entry.get("summary"),
        args_masked=_decode_args(entry.get("args_masked")),
        is_error=bool(entry.get("is_error", False)),
    )


class _ToolingMixin(MixinBase):
    """Tool inspection and plan-mode slash-command handlers."""

    def _tool_list(self) -> None:
        """Print stored tool results for the current session."""
        ctx = self._ctx
        entries = ctx.tool_result_store.list_recent(ctx.session.session_id)
        if not entries:
            self._out.write("No tool results stored in this session.")
            return
        self._out.write(f"{'ID':>6}  {'Tool':<22}  {'Size':>7}  Summarized")
        self._out.write("-" * 55)
        for entry in entries:
            view = _to_tool_result_view(entry)
            flag = "yes" if view.summary else "no"
            summary_len = len(view.summary or "")
            self._out.write(
                f"{view.result_id:>6}  {view.tool_name:<22}  {summary_len:>7}  {flag}"
            )

    def _tool_show(self, arg: str) -> None:
        """Print the full text of one stored tool result by its DB id."""
        if not arg.isdigit() or int(arg) < 1:
            self._out.write("Usage: /tool show <id>  (use /tool list to see IDs)")
            return
        raw = self._ctx.tool_result_store.get(int(arg))
        if raw is None:
            self._out.write(f"Result id={arg} not found.")
            return
        view = _to_tool_result_view(raw)
        flag = " [summarized]" if view.summary else ""
        self._out.write(f"Tool: {view.tool_name}{flag}")
        self._out.write(f"Args: {orjson.dumps(view.args_masked).decode()}")
        full_text = str(raw.get("full_text", ""))
        self._out.write(f"Size: {len(full_text)} chars")
        if view.summary:
            self._out.write(f"Summary: {view.summary}")
        self._out.write("")
        self._out.write(full_text)

    def _cmd_tool(self, args: str) -> None:
        """Inspect stored tool results from the current session.

        Usage:
          /tool list        List stored tool results (id, name, size)
          /tool show <id>   Show full text of a result by its DB id
        """
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else "list"
        if sub == "list" or not parts:
            self._tool_list()
        elif sub == "show":
            self._tool_show(parts[1].strip() if len(parts) > 1 else "")
        else:
            self._out.write("Usage: /tool list | /tool show <id>")

    def _cmd_plan(self) -> None:
        """Toggle plan mode. In plan mode, plan_blocked_tools are automatically blocked.

        This prevents destructive file operations from being executed while the agent
        is drafting a plan, guarding against accidental writes before the user has
        reviewed the proposal.
        """
        ctx = self._ctx
        ctx.conv.plan_mode = not ctx.conv.plan_mode
        state = "ON" if ctx.conv.plan_mode else "OFF"
        logger.info(f"Plan mode toggled: {state}")
        self._out.write(f"Plan mode: {state}")
        if ctx.conv.plan_mode and ctx.cfg.tool.plan_blocked_tools:
            self._out.write("  Blocked tools:")
            for t in ctx.cfg.tool.plan_blocked_tools:
                self._out.write(f"    - {t}")
