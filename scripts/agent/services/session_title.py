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

from agent.bg_task_monitor import current_task_target
from agent.services.exceptions import SessionTitleGenerationError
from agent.services.models import SessionTitleResult

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

_TITLE_PROMPT = "Summarise the following user message in one short phrase (8 words max, no punctuation at the end): {text}"


class SessionTitleService:
    """Generate a short LLM-based title for a session and persist it."""

    @staticmethod
    def _save(ctx: AgentContext, title: str) -> None:
        """Write ``title`` to the session that created the task; never log the text.

        A stale target (the session changed since) is refused by set_title and
        nothing is written.
        """
        target = current_task_target()
        persisted = ctx.session.set_title(title, target=target)
        if target is not None and persisted is False:
            logger.info(
                "Session title discarded: session %s generation %s is not current",
                target.session_id,
                target.generation,
            )
        else:
            logger.info(
                "Session title generated: session=%s",
                ctx.session.session_id if target is None else target.session_id,
            )

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
            self._save(ctx, title)
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
