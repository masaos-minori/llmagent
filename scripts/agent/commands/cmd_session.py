#!/usr/bin/env python3
"""cmd_session.py
Session management mixin for CommandRegistry.

Extracted from agent_commands.py.  Provides _SessionMixin with:
  _generate_session_title  — background task: LLM-generated short title
  _session_load_safe       — safe session restore by ID
  _session_delete          — session deletion with self-guard
  _cmd_session             — /session dispatcher
  _load_session            — restore messages into ctx.history
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

# LLM parameters for session title generation.
# Very low temperature for a deterministic short phrase; 20 tokens is sufficient.
_TITLE_TEMPERATURE: float = 0.1
_TITLE_MAX_TOKENS: int = 20


class _SessionMixin:
    """Session management slash-command handlers."""

    if TYPE_CHECKING:
        _ctx: "AgentContext"

    async def _generate_session_title(self, first_input: str) -> None:
        """Call the chat LLM to produce a short session title and persist it.

        Uses max_tokens=20 and the chat model (:8002) to minimise latency.
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
                ctx.cfg.llm_url,
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": _TITLE_TEMPERATURE,
                    "max_tokens": _TITLE_MAX_TOKENS,
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
        if not parts or parts[0] == "list":
            limit = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 20
            self._ctx.session.list_sessions(limit)
        elif parts[0] == "load" and len(parts) == 2:
            self._session_load_safe(parts[1])
        elif parts[0] == "rename" and len(parts) >= 2:
            title = " ".join(parts[1:])
            self._ctx.session.set_title(title)
            print(f"Session renamed: {title[:50]!r}")
        elif parts[0] == "delete" and len(parts) == 2:
            self._session_delete(parts[1])
        else:
            print(
                "Usage: /session list [n] | /session load <id>"
                " | /session rename <title> | /session delete <id>",
            )

    def _load_session(self, session_id: int) -> None:
        """Restore a previous session's messages into ctx.history."""
        ctx = self._ctx
        messages = ctx.session.fetch_messages(session_id)
        if messages is None:
            print(f"Session {session_id} not found or has no messages.")
            return
        system_msgs = [m for m in ctx.history if m["role"] == "system"]
        ctx.history = system_msgs + messages
        ctx.session.session_id = session_id
        logger.info(f"Session {session_id} loaded: {len(messages)} messages")
        print(f"Session {session_id} loaded: {len(messages)} messages restored.")
