"""agent/services/session_title.py
SessionTitleService — generate and persist a session title via LLM.

Extracted from cmd_session._SessionMixin so the HTTP + prompt logic
can be tested independently of the REPL.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx
import orjson

from agent.services.exceptions import SessionTitleGenerationError
from agent.services.models import SessionTitleResult

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

_TITLE_PROMPT = (
    "Summarise the following user message in one short phrase"
    " (8 words max, no punctuation at the end): {text}"
)


class SessionTitleService:
    """Generate a short LLM-based title for a session and persist it."""

    async def generate(self, ctx: AgentContext, first_input: str) -> SessionTitleResult:
        """Call the chat LLM to produce a short title.

        Raises SessionTitleGenerationError on any failure.
        Uses cfg.llm.title_llm_temperature and cfg.llm.title_llm_max_tokens.
        """
        if ctx.services.http is None:
            raise SessionTitleGenerationError("HTTP client not configured")
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
            data = orjson.loads(resp.content)
            choices = data.get("choices")
            if not isinstance(choices, list) or not choices:
                raise SessionTitleGenerationError("LLM response has no choices")
            first = choices[0]
            if not isinstance(first, dict):
                raise SessionTitleGenerationError("LLM choices[0] is not a dict")
            message = first.get("message")
            if not isinstance(message, dict):
                raise SessionTitleGenerationError(
                    "LLM choices[0].message is not a dict"
                )
            content_raw = message.get("content")
            if not isinstance(content_raw, str):
                raise SessionTitleGenerationError(
                    f"LLM title content must be str, got {type(content_raw).__name__}"
                )
            title = content_raw.strip()
            if not title:
                raise SessionTitleGenerationError("LLM returned empty title")
            ctx.session.set_title(title)
            logger.info("Session title generated: %r", title)
            return SessionTitleResult(title=title)
        except SessionTitleGenerationError:
            raise
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            raise SessionTitleGenerationError(str(e)) from e
        except (orjson.JSONDecodeError, KeyError) as e:
            raise SessionTitleGenerationError(f"Response parse error: {e}") from e
        except Exception as e:
            raise SessionTitleGenerationError(f"Unexpected error: {e}") from e
