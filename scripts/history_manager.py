#!/usr/bin/env python3
"""
history_manager.py
Conversation history compression layer extracted from REPLAgent.
Monitors total history size and summarises old turns via the chat LLM
when the character limit is exceeded.
"""

import logging
from collections.abc import Callable

import httpx
import orjson
from rag_types import LLMMessage

logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages conversation history size via LLM-based compression.

    When the total character count of self._history exceeds char_limit,
    the oldest compress_turns * 2 messages are summarised into a single
    system message to keep the context window manageable.

    protect_turns: number of most-recent user/assistant turn pairs to exclude
    from compression candidates (prevents the latest context from being lost).
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
        protect_turns: int = 2,
        token_limit: int = 0,
    ) -> None:
        self._http = http
        self._chat_url = chat_url
        self._char_limit = char_limit
        self._compress_turns = compress_turns
        self._compress_temperature = compress_temperature
        self._compress_max_tokens = compress_max_tokens
        self._on_compress = on_compress
        # Number of most-recent turn pairs (user+assistant) to protect from compression
        self._protect_turns = protect_turns
        # Token-based limit; 0 = disabled (falls back to char_limit only)
        self._token_limit = token_limit
        # Cumulative compression count for this session
        self.stat_compress_count: int = 0

    @property
    def compress_turns(self) -> int:
        """Number of oldest turn pairs selected for compression.

        Exposed as a public property so external callers (e.g. _cmd_compact)
        can read the value without accessing the private _compress_turns attribute.
        """
        return self._compress_turns

    def count_chars(self, history: list[LLMMessage]) -> int:
        """Estimate total characters in a history list.

        Counts content string length and serialised tool_calls length.
        """
        total = 0
        for msg in history:
            total += len(str(msg.get("content") or ""))
            for tc in msg.get("tool_calls") or []:
                total += len(orjson.dumps(tc))
        return total

    def count_tokens_estimate(
        self, history: list[LLMMessage], last_input_tokens: int | None = None
    ) -> int:
        """Estimate total tokens in a history list.

        When last_input_tokens is provided (from LLM usage), return it directly
        as a precise measurement.  Otherwise fall back to chars // 4, which is a
        rough approximation suitable for budget warnings (local LLMs may not
        return usage fields consistently).

        Args:
            history: The conversation message list to measure.
            last_input_tokens: Precise token count from the last LLM usage response,
                or None when the endpoint did not return usage data.

        Returns:
            Estimated token count.
        """
        if last_input_tokens is not None:
            return last_input_tokens
        return self.count_chars(history) // 4

    @staticmethod
    def _classify(msg: LLMMessage) -> str:
        """Classify a message into a compression-priority category.

        Categories (from highest to lowest compression priority):
          'temporary'          — tool result messages (role='tool'); ephemeral context
          'temporary_reasoning'— assistant messages containing tool_calls (planning turns)
          'factual'            — system messages; structural / long-lived context
          'history'            — regular user/assistant conversation turns

        Returns:
            One of: 'temporary', 'temporary_reasoning', 'factual', 'history'.
        """
        role = msg.get("role", "")
        if role == "tool":
            return "temporary"
        if role == "system":
            return "factual"
        if role == "assistant" and msg.get("tool_calls"):
            return "temporary_reasoning"
        return "history"

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

        The most-recent protect_turns * 2 non-system messages are excluded from
        compression to preserve immediate context.  Returns None when there are
        not enough turn messages left after protection to compress.
        """
        system_msgs = [m for m in history if m["role"] == "system"]
        turn_msgs = [m for m in history if m["role"] != "system"]
        # Reserve the most-recent protect_turns pairs (2 messages per pair)
        n_protect = self._protect_turns * 2
        n_compress = self._compress_turns * 2
        # Need at least n_compress + n_protect messages to proceed
        if len(turn_msgs) <= n_compress + n_protect:
            return None
        # Compress the oldest n_compress messages; protect the trailing n_protect ones
        protected_tail = turn_msgs[-n_protect:] if n_protect > 0 else []
        compressible = turn_msgs[: len(turn_msgs) - n_protect]
        to_compress = compressible[:n_compress]
        remaining = compressible[n_compress:] + protected_tail
        return system_msgs, to_compress, remaining

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
            total_chars = self.count_chars(history)
            if total_chars > self._char_limit:
                logger.warning(
                    f"History compression skipped: protect_turns={self._protect_turns}"
                    f" + compress_turns={self._compress_turns} >= available turns."
                    f" chars={total_chars} > limit={self._char_limit}."
                    " Consider reducing protect_turns or increasing"
                    " context_char_limit."
                )
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
