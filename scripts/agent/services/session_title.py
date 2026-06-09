"""agent/services/session_title.py
SessionTitleService — generate and persist a session title via LLM.

Extracted from cmd_session._SessionMixin so the HTTP + prompt logic
can be tested independently of the REPL.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

_TITLE_PROMPT = (
    "Summarise the following user message in one short phrase"
    " (8 words max, no punctuation at the end): {text}"
)


class SessionTitleService:
    """Generate a short LLM-based title for a session and persist it."""

    async def generate(self, ctx: AgentContext, first_input: str) -> None:
        """Call the chat LLM to produce a short title; fall back to truncated input.

        Uses cfg.llm.title_llm_temperature and cfg.llm.title_llm_max_tokens.
        Called as an asyncio background task; failure is non-fatal.
        """
        if ctx.services.http is None:
            ctx.session.set_title(first_input[:50])
            return
        prompt = _TITLE_PROMPT.format(text=first_input[:200])
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
