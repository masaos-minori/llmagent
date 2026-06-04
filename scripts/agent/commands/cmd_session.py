#!/usr/bin/env python3
"""cmd_session.py
Session management mixin for CommandRegistry.

Extracted from agent_commands.py.  Provides _SessionMixin with:
  _generate_session_title  — background task: LLM-generated short title
  _session_load_safe       — safe session restore by ID
  _session_delete          — session deletion with self-guard
  _cmd_session             — /session dispatcher
  _load_session            — restore messages into ctx.conv.history
"""

import logging

from agent.commands.mixin_base import MixinBase

logger = logging.getLogger(__name__)


class _SessionMixin(MixinBase):
    """Session management slash-command handlers."""

    async def _generate_session_title(self, first_input: str) -> None:
        """Call the chat LLM to produce a short session title and persist it.

        Uses cfg.llm.title_llm_temperature and cfg.llm.title_llm_max_tokens for the call.
        Called as an asyncio background task so the main REPL turn is not blocked.
        Falls back to truncating the raw input on any error.
        """
        ctx = self._ctx
        if ctx.services.http is None:
            ctx.session.set_title(first_input[:50])
            return
        prompt = (
            "Summarise the following user message in one short phrase"
            f" (8 words max, no punctuation at the end): {first_input[:200]}"
        )
        try:
            resp = await ctx.services.http.post(
                ctx.cfg.llm.llm_url,
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": ctx.cfg.llm.title_llm_temperature,
                    "max_tokens": ctx.cfg.llm.title_llm_max_tokens,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            choices = resp.json().get("choices", [])
            title = ""
            if choices:
                title = choices[0].get("message", {}).get("content", "").strip()
            if title:
                ctx.session.set_title(title)
                logger.info(f"Session title generated: {title!r}")
                return
        except Exception as e:
            logger.warning(f"Session title generation failed: {e}")
        ctx.session.set_title(first_input[:50])

    def _session_load_safe(self, arg: str) -> None:
        """Parse arg as an integer session ID and load it; print error on invalid."""
        try:
            self._load_session(int(arg))
        except ValueError:
            print(f"Invalid session ID: {arg}")

    def _session_delete(self, arg: str) -> None:
        """Parse arg as an integer session ID and delete it; guard current session."""
        try:
            sid = int(arg)
        except ValueError:
            print(f"Invalid session ID: {arg}")
            return
        if sid == self._ctx.session.session_id:
            print("Cannot delete the current session.")
            return
        ok = self._ctx.session.delete_session(sid)
        print(f"Session {sid} deleted." if ok else f"Session {sid} not found.")

    def _cmd_session(self, args: str) -> None:
        """Handle /session list [n] | load | rename | delete."""
        parts = args.strip().split()
        sub = parts[0] if parts else "list"

        if sub == "list":
            limit = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 20
            rows = self._ctx.session.list_sessions(limit)
            if not rows:
                print("No sessions found")
                return
            print(f"{'ID':>4}  {'Title':<32}  Created")
            for r in rows:
                marker = "*" if r["is_current"] else " "
                raw_title = r["title"] or ""
                title = raw_title[:29] + "..." if len(raw_title) > 32 else raw_title
                print(f"{r['session_id']:>4}{marker} {title:<32}  {r['created_at']}")
            return
        if sub == "load" and len(parts) == 2:
            self._session_load_safe(parts[1])
            return
        if sub == "rename" and len(parts) >= 2:
            title = " ".join(parts[1:])
            self._ctx.session.set_title(title)
            print(f"Session renamed: {title[:50]!r}")
            return
        if sub == "delete" and len(parts) == 2:
            self._session_delete(parts[1])
            return
        print(
            "Usage: /session list [n] | /session load <id>"
            " | /session rename <title> | /session delete <id>",
        )

    def _load_session(self, session_id: int) -> None:
        """Restore a previous session's messages into ctx.conv.history.

        Lifecycle: sets ctx.session.session_id (switches the active session),
        rebuilds ctx.conv.history (preserves system prompt at index 0),
        and resets all per-session counters via _reset_session_stats().
        """
        ctx = self._ctx
        messages = ctx.session.fetch_messages(session_id)
        if messages is None:
            print(f"Session {session_id} not found or has no messages.")
            return
        system_msgs = [m for m in ctx.conv.history if m["role"] == "system"]
        ctx.conv.history = system_msgs + messages
        ctx.session.session_id = session_id
        self._reset_session_stats(ctx)
        logger.info(f"Session {session_id} loaded: {len(messages)} messages")
        print(f"Session {session_id} loaded: {len(messages)} messages restored.")
