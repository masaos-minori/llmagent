#!/usr/bin/env python3
"""cmd_rag.py
Tool inspection, note, plan, and debug mixin for CommandRegistry.

Extracted from agent_commands.py.  Provides _RagMixin with:
  _cmd_tool          — /tool: inspect stored tool results
  _cmd_note          — /note: add/list/delete persistent notes
  _cmd_plan          — /plan: toggle plan mode
  _cmd_debug         — /debug: toggle debug output
  _render_history_md — render conversation history as Markdown
"""

import logging
import pathlib
from typing import TYPE_CHECKING

import orjson
from rag.types import LLMMessage

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


class _RagMixin:
    """RAG, tool, note, plan, and debug slash-command handlers."""

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

    def _note_add(self, text: str) -> None:
        """Add a new persistent note."""
        if not text:
            print("Usage: /note add <text>")
            return
        note_id = self._ctx.session.add_note(text)
        if note_id is not None:
            print(f"Note added (id={note_id}).")
        else:
            print("Failed to add note.")

    def _note_list(self) -> None:
        """List all persistent notes."""
        notes = self._ctx.session.list_notes()
        if not notes:
            print("No notes.")
            return
        print(f"{'ID':>4}  {'Created':>19}  Content")
        print("-" * 70)
        for n in notes:
            preview = n["content"]
            if len(preview) > 44:
                preview = preview[:41] + "..."
            print(f"{n['note_id']:>4}  {n['created_at'][:19]:>19}  {preview}")

    def _note_delete(self, arg: str) -> None:
        """Delete a note by id."""
        if not arg.isdigit():
            print("Usage: /note delete <id>")
            return
        ok = self._ctx.session.delete_note(int(arg))
        print(f"Note {arg} {'deleted.' if ok else 'not found.'}")

    def _cmd_note(self, args: str) -> None:
        """Manage persistent cross-session notes.

        Usage:
          /note add <text>   Add a new note
          /note list         List all notes
          /note delete <id>  Delete a note by ID
        """
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else ""
        rest = parts[1].strip() if len(parts) > 1 else ""
        if sub == "add":
            self._note_add(rest)
        elif sub == "list":
            self._note_list()
        elif sub == "delete":
            self._note_delete(rest)
        else:
            print("Usage: /note add <text> | /note list | /note delete <id>")

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
        if ctx.plan_mode and ctx.cfg.plan_blocked_tools:
            print("  Blocked tools:")
            for t in ctx.cfg.plan_blocked_tools:
                print(f"    - {t}")

    def _cmd_debug(self, args: str = "") -> None:
        """Toggle RAG debug output, or show audit log tail with '/debug audit'."""
        ctx = self._ctx
        sub = args.strip().lower()

        if sub == "audit":
            # Show the last 20 lines of audit.log for quick troubleshooting
            audit_path = pathlib.Path(ctx.cfg.audit_log_file)
            if not audit_path.exists():
                print(f"Audit log not found: {audit_path}")
                return
            try:
                lines = audit_path.read_text(encoding="utf-8").splitlines()
                for line in lines[-20:]:
                    print(line)
            except OSError as e:
                print(f"Cannot read audit log: {e}")
            return

        if sub == "verbose":
            # Switch agent logger to DEBUG level for detailed output
            logging.getLogger("agent_repl").setLevel(logging.DEBUG)
            logging.getLogger("orchestrator").setLevel(logging.DEBUG)
            print("Log level: DEBUG")
            logger.info("Log level set to DEBUG")
            return

        if sub == "normal":
            logging.getLogger("agent_repl").setLevel(logging.INFO)
            logging.getLogger("orchestrator").setLevel(logging.INFO)
            print("Log level: INFO")
            logger.info("Log level restored to INFO")
            return

        # Default: toggle RAG pipeline step debug output
        ctx.debug_mode = not ctx.debug_mode
        state = "ON" if ctx.debug_mode else "OFF"
        logger.info(f"Debug mode toggled: {state}")
        print(
            f"Debug mode: {state}  (use /debug audit | verbose | normal for more options)",
        )

    def _render_history_md(self, history: list[LLMMessage]) -> str:
        """Render conversation history as Markdown."""
        lines: list[str] = ["# Conversation Export\n"]
        for msg in history:
            role = msg.get("role", "")
            if role == "system":
                continue
            text = str(msg.get("content") or "")
            if role == "user":
                lines.append(f"## User\n\n{text}\n")
            elif role == "assistant":
                lines.append(f"## Assistant\n\n{text}\n")
            elif role == "tool":
                tc_id = msg.get("tool_call_id", "")
                lines.append(f"## Tool ({tc_id})\n\n```\n{text}\n```\n")
        return "\n".join(lines)
