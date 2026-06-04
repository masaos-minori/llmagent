#!/usr/bin/env python3
"""agent/commands/cmd_tooling.py
Tool inspection and plan-mode mixin for CommandRegistry.

Provides _ToolingMixin with:
  _cmd_tool  — /tool: inspect stored tool results
  _cmd_plan  — /plan: toggle plan mode
"""

import logging
from typing import TYPE_CHECKING

import orjson

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


class _ToolingMixin:
    """Tool inspection and plan-mode slash-command handlers."""

    if TYPE_CHECKING:
        _ctx: "AgentContext"

    def _tool_list(self) -> None:
        """Print stored tool results for the current session."""
        ctx = self._ctx
        entries = ctx.tool_result_store.list_recent(ctx.session.session_id)
        if not entries:
            print("No tool results stored in this session.")
            return
        print(f"{'ID':>6}  {'Tool':<22}  {'Size':>7}  Summarized")
        print("-" * 55)
        for entry in entries:
            flag = "yes" if entry.get("summary") else "no"
            print(
                f"{entry['id']:>6}  {entry['tool_name']:<22}"
                f"  {len(entry['full_text']):>7}  {flag}",
            )

    def _tool_show(self, arg: str) -> None:
        """Print the full text of one stored tool result by its DB id."""
        if not arg.isdigit() or int(arg) < 1:
            print("Usage: /tool show <id>  (use /tool list to see IDs)")
            return
        result = self._ctx.tool_result_store.get(int(arg))
        if result is None:
            print(f"Result id={arg} not found.")
            return
        flag = " [summarized]" if result.get("summary") else ""
        print(f"Tool: {result['tool_name']}{flag}")
        try:
            args_obj = orjson.loads(result.get("args_json") or "{}")
        except orjson.JSONDecodeError:
            args_obj = {}
        print(f"Args: {orjson.dumps(args_obj).decode()}")
        print(f"Size: {len(result['full_text'])} chars")
        if result.get("summary"):
            print(f"Summary: {result['summary']}")
        print()
        print(result["full_text"])

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
            print("Usage: /tool list | /tool show <id>")

    def _cmd_plan(self) -> None:
        """Toggle plan mode. In plan mode, plan_blocked_tools are automatically blocked.

        This prevents destructive file operations from being executed while the agent
        is drafting a plan, guarding against accidental writes before the user has
        reviewed the proposal.
        """
        ctx = self._ctx
        ctx.plan_mode = not ctx.plan_mode
        state = "ON" if ctx.plan_mode else "OFF"
        logger.info(f"Plan mode toggled: {state}")
        print(f"Plan mode: {state}")
        if ctx.plan_mode and ctx.cfg.tool.plan_blocked_tools:
            print("  Blocked tools:")
            for t in ctx.cfg.tool.plan_blocked_tools:
                print(f"    - {t}")
