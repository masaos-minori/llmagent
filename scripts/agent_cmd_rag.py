#!/usr/bin/env python3
"""
agent_cmd_rag.py
RAG, tool inspection, note, plan, and debug mixin for CommandRegistry.

Extracted from agent_commands.py.  Provides _RagMixin with:
  _cmd_tool          — /tool: inspect stored tool results
  _cmd_note          — /note: add/list/delete persistent notes
  _cmd_plan          — /plan: toggle plan mode
  _cmd_debug         — /debug: toggle RAG debug output
  _print_rag_results — print dry-run RAG search results
  _cmd_rag           — /rag dispatcher (status / toggle / dry-run)
  _render_history_md — render conversation history as Markdown
"""

import json
import logging
from typing import TYPE_CHECKING

from rag_types import LLMMessage, RagHit
from sqlite_helper import SQLiteHelper

if TYPE_CHECKING:
    from agent_context import AgentContext

logger = logging.getLogger(__name__)


class _RagMixin:
    """RAG, tool, note, plan, and debug slash-command handlers."""

    if TYPE_CHECKING:
        _ctx: "AgentContext"

    def _cmd_tool(self, args: str) -> None:
        """Inspect stored tool results from the current session.

        Usage:
          /tool list        List stored tool results (id, name, size)
          /tool show <id>   Show full text of a result by its DB id
        """
        ctx = self._ctx
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else "list"
        store = ctx.tool_result_store
        if sub == "list" or not parts:
            entries = store.list_recent(ctx.session.session_id)
            if not entries:
                print("No tool results stored in this session.")
                return
            print(f"{'ID':>6}  {'Tool':<22}  {'Size':>7}  Summarized")
            print("-" * 55)
            for entry in entries:
                flag = "yes" if entry.get("summary") else "no"
                print(
                    f"{entry['id']:>6}  {entry['tool_name']:<22}"
                    f"  {len(entry['full_text']):>7}  {flag}"
                )
        elif sub == "show":
            arg = parts[1].strip() if len(parts) > 1 else ""
            if not arg.isdigit() or int(arg) < 1:
                print("Usage: /tool show <id>  (use /tool list to see IDs)")
                return
            result = store.get(int(arg))
            if result is None:
                print(f"Result id={arg} not found.")
                return
            flag = " [summarized]" if result.get("summary") else ""
            print(f"Tool: {result['tool_name']}{flag}")
            try:
                args_obj = json.loads(result.get("args_json") or "{}")
            except json.JSONDecodeError:
                args_obj = {}
            print(f"Args: {json.dumps(args_obj, ensure_ascii=False)}")
            print(f"Size: {len(result['full_text'])} chars")
            if result.get("summary"):
                print(f"Summary: {result['summary']}")
            print()
            print(result["full_text"])
        else:
            print("Usage: /tool list | /tool show <id>")

    def _cmd_note(self, args: str) -> None:
        """Manage persistent cross-session notes.

        Usage:
          /note add <text>   Add a new note
          /note list         List all notes
          /note delete <id>  Delete a note by ID
        """
        ctx = self._ctx
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else ""
        if sub == "add":
            text = parts[1].strip() if len(parts) > 1 else ""
            if not text:
                print("Usage: /note add <text>")
                return
            note_id = ctx.session.add_note(text)
            if note_id is not None:
                print(f"Note added (id={note_id}).")
            else:
                print("Failed to add note.")
        elif sub == "list":
            notes = ctx.session.list_notes()
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
        elif sub == "delete":
            arg = parts[1].strip() if len(parts) > 1 else ""
            if not arg.isdigit():
                print("Usage: /note delete <id>")
                return
            ok = ctx.session.delete_note(int(arg))
            print(f"Note {arg} {'deleted.' if ok else 'not found.'}")
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

    def _cmd_debug(self) -> None:
        """Toggle RAG pipeline step debug output."""
        ctx = self._ctx
        ctx.debug_mode = not ctx.debug_mode
        state = "ON" if ctx.debug_mode else "OFF"
        logger.info(f"Debug mode toggled: {state}")
        print(f"Debug mode: {state}")

    def _print_rag_results(
        self, query: str, queries: list[str], reranked: list[RagHit]
    ) -> None:
        """Print /rag search results: expanded queries and ranked chunks."""
        print()
        print(f"Query      : {query!r}")
        print(f"Expanded ({len(queries)}):")
        for i, q in enumerate(queries, 1):
            print(f"  {i}: {q}")
        if not reranked:
            print("No results.")
            return
        print(f"\nChunks ({len(reranked)}):")
        for i, c in enumerate(reranked, 1):
            score = c.get("rerank_score", c.get("rrf_score", 0.0))
            preview = c["content"].replace("\n", " ")[:120]
            print(f"\n[{i}] chunk_id={c['chunk_id']}  score={score:.4f}")
            print(f"     url={c['url']}")
            print(f"     {preview!r}")

    async def _cmd_rag(self, args: str) -> None:
        """Toggle RAG steps at runtime or dry-run the pipeline.

        Usage:
          /rag              Show current RAG step status
          /rag on           Enable RAG search (use_search=true)
          /rag off          Disable RAG search (use_search=false)
          /rag mqe on|off   Enable/disable Multi-Query Expansion
          /rag rerank on|off  Enable/disable Cross-Encoder reranking
          /rag search <query>  Dry-run RAG pipeline (no LLM call)
        """
        ctx = self._ctx
        parts = args.strip().split(None, 2)
        sub = parts[0] if parts else ""

        if sub == "on":
            ctx.cfg.use_search = True
            print("RAG search enabled.")
            return
        if sub == "off":
            ctx.cfg.use_search = False
            print("RAG search disabled.")
            return
        if sub == "mqe":
            val = parts[1].lower() if len(parts) > 1 else ""
            if val not in ("on", "off"):
                print("Usage: /rag mqe on|off")
                return
            ctx.cfg.use_mqe = val == "on"
            print(f"MQE {'enabled' if ctx.cfg.use_mqe else 'disabled'}.")
            return
        if sub == "rerank":
            val = parts[1].lower() if len(parts) > 1 else ""
            if val not in ("on", "off"):
                print("Usage: /rag rerank on|off")
                return
            ctx.cfg.use_rerank = val == "on"
            print(f"Reranking {'enabled' if ctx.cfg.use_rerank else 'disabled'}.")
            return
        if sub == "search":
            query = args.strip()[len("search") :].strip()
            if not query:
                print("Usage: /rag search <query>")
                return
            if not ctx.cfg.use_search:
                print("RAG is disabled (use_search=false). Enable with /rag on.")
                return
            if ctx.services.rag is None:
                print("RAG pipeline not available.")
                return
            try:
                db = SQLiteHelper().open(row_factory=True)
            except Exception as e:
                print(f"DB open failed: {e}")
                return
            try:
                with db:
                    # run() calls on_clear() in its finally block
                    queries, _, _, reranked = await ctx.services.rag.run(query, db)
            except Exception as e:
                logger.error(f"RAG pipeline failed: {e}")
                print(f"RAG pipeline error: {e}")
                return
            self._print_rag_results(query, queries, reranked)
            return
        # No subcommand: show current status
        print(
            f"RAG step status:\n"
            f"  use_search : {ctx.cfg.use_search}\n"
            f"  use_mqe    : {ctx.cfg.use_mqe}\n"
            f"  use_rrf    : {ctx.cfg.use_rrf}\n"
            f"  use_rerank : {ctx.cfg.use_rerank}\n"
            "Use /rag on|off, /rag mqe on|off, /rag rerank on|off, "
            "/rag search <query>"
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
