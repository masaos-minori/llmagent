"""scripts/agent/services/session_title.py

SessionTitleService — generate and persist a session title via LLM.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING

import httpx
from shared.json_utils import extract_llm_content, parse_http_json
from shared.llm_client import build_llm_url

from agent.conversation_state_manager import get_captured_session_target
from agent.services.exceptions import SessionTitleGenerationError
from agent.services.models import SessionTitleResult

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

_TITLE_PROMPT = "Summarise the following user message in one short phrase (8 words max, no punctuation at the end): {text}"


class SessionTitleService:
    """Generate a short LLM-based title for a session and persist it."""

    async def generate(self, ctx: AgentContext, first_input: str) -> SessionTitleResult:
        """Call the chat LLM to produce a short title.

        Raises SessionTitleGenerationError on any failure.
        Uses cfg.llm.title_llm_temperature and cfg.llm.title_llm_max_tokens.
        """
        if ctx.services_required.http is None:
            raise SessionTitleGenerationError("HTTP client not configured")
        prompt = _TITLE_PROMPT.format(text=first_input[:200])
        try:
            resp = await ctx.services_required.http.post(
                build_llm_url(ctx.cfg.llm.llm_url),
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": ctx.cfg.llm.title_llm_temperature,
                    "max_tokens": ctx.cfg.llm.title_llm_max_tokens,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = parse_http_json(resp)
            title = extract_llm_content(data)
            if not title:
                raise SessionTitleGenerationError(
                    "LLM returned empty content — try adjusting your prompt"
                )
            # REQ-004: write only into the session generation captured at task
            # creation (context variable set by the first-turn task spawn).
            target = get_captured_session_target()
            if not ctx.session.set_title(title, target=target):
                # Stale target or no active session: refused, nothing written.
                # Redacted (AC-2): ids only, no title text.
                if target is not None:
                    logger.warning(
                        "Session title write refused for stale target "
                        "session=%s generation=%s",
                        target.session_id,
                        target.generation,
                    )
                else:
                    logger.warning("Session title write refused: no active session")
                return SessionTitleResult(title=title, stale=True)
            # REQ-005 / AC-2: no title text in logs, ids only.
            sid = target.session_id if target is not None else ctx.session.session_id
            gen = target.generation if target is not None else ctx.session.generation
            logger.info("Session title generated (session=%s generation=%s)", sid, gen)
            return SessionTitleResult(title=title)
        except SessionTitleGenerationError:
            raise
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            raise SessionTitleGenerationError(str(e)) from e
        except ValueError as e:
            raise SessionTitleGenerationError(f"Response parse error: {e}") from e
        except sqlite3.Error as e:
            raise SessionTitleGenerationError(f"DB error: {e}") from e
        except (RuntimeError, OSError) as e:
            raise SessionTitleGenerationError(f"Unexpected error: {e}") from e
