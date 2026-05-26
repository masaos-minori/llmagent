#!/usr/bin/env python3
"""
history_manager.py
Conversation history compression layer extracted from REPLAgent.
Monitors total history size and summarises old turns via the chat LLM
when the character limit is exceeded.
"""

import json
import logging
from collections.abc import Callable

import httpx
from rag_types import LLMMessage

logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages conversation history size via LLM-based compression.

    When the total character count of self._history exceeds char_limit,
    the oldest compress_turns * 2 messages are summarised into a single
    system message to keep the context window manageable.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        chat_url: str,
        char_limit: int,
        compress_turns: int,
        compress_temperature: float,
        compress_max_tokens: int,
        on_compress: Callable[[int], None] | None = None,
    ) -> None:
        self._http = http
        self._chat_url = chat_url
        self._char_limit = char_limit
        self._compress_turns = compress_turns
        self._compress_temperature = compress_temperature
        self._compress_max_tokens = compress_max_tokens
        self._on_compress = on_compress
        # Cumulative compression count for this session
        self.stat_compress_count: int = 0

    def count_chars(self, history: list[LLMMessage]) -> int:
        """Estimate total characters in a history list.

        Counts content string length and serialised tool_calls length.
        """
        total = 0
        for msg in history:
            total += len(str(msg.get("content") or ""))
            for tc in msg.get("tool_calls") or []:
                total += len(json.dumps(tc))
        return total

    async def _call_compress_llm(self, history_text: str) -> str | None:
        """Send history_text to the chat LLM and return the summary string.

        Returns None when the LLM response is empty or the request fails.
        """
        prompt = (
            "Summarize the following conversation history concisely in one paragraph,"
            f" preserving key context:\n\n{history_text}"
        )
        try:
            resp = await self._http.post(
                self._chat_url,
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self._compress_temperature,
                    "max_tokens": self._compress_max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices") or []
            raw_content = (
                choices[0].get("message", {}).get("content") if choices else None
            )
            if not raw_content:
                logger.warning("Context compression: LLM returned empty summary")
                return None
            return str(raw_content).strip()
        except Exception as e:
            logger.warning(f"Context compression failed: {e}")
            return None

    def _select_turns_to_compress(
        self, history: list[LLMMessage]
    ) -> tuple[list[LLMMessage], list[LLMMessage], list[LLMMessage]] | None:
        """Split history into (system_msgs, to_compress, remaining).

        Returns None when there are not enough turn messages to compress.
        """
        system_msgs = [m for m in history if m["role"] == "system"]
        turn_msgs = [m for m in history if m["role"] != "system"]
        n_compress = self._compress_turns * 2
        if len(turn_msgs) <= n_compress:
            return None
        return system_msgs, turn_msgs[:n_compress], turn_msgs[n_compress:]

    def _build_history_text(self, messages: list[LLMMessage]) -> str:
        """Render messages as a plain-text transcript for LLM summarisation."""
        return "\n".join(
            f"{m['role'].upper()}: {str(m.get('content', ''))[:300]}" for m in messages
        )

    async def compress(self, history: list[LLMMessage]) -> list[LLMMessage]:
        """Summarise the oldest turn pairs when total history chars exceed the limit.

        Returns the (possibly compressed) history list.
        Leaves the system prompt and recent turns intact.
        Increments stat_compress_count on successful compression.
        """
        if self.count_chars(history) <= self._char_limit:
            return history
        split = self._select_turns_to_compress(history)
        if split is None:
            return history
        system_msgs, to_compress, remaining = split
        summary_text = await self._call_compress_llm(
            self._build_history_text(to_compress)
        )
        if summary_text is None:
            return history
        summary_msg: LLMMessage = {
            "role": "system",
            "content": f"[Conversation summary]\n{summary_text}",
        }
        n = len(to_compress)
        self.stat_compress_count += 1
        logger.info(f"History compressed: {n} messages summarized")
        if self._on_compress:
            self._on_compress(n)
        return system_msgs + [summary_msg] + remaining
