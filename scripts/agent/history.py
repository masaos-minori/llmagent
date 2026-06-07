#!/usr/bin/env python3
"""agent/history.py
Conversation history compression layer extracted from REPLAgent.
Monitors total history size and summarises old turns via the chat LLM
when the character limit is exceeded.
"""

import logging
from collections.abc import Callable

import httpx
import orjson
from rag.types import LLMMessage
from shared.token_counter import get_token_count

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
        llm_url: str,
        char_limit: int,
        compress_turns: int,
        compress_temperature: float,
        compress_max_tokens: int,
        on_compress: Callable[[int], None] | None = None,
        protect_turns: int = 2,
        token_limit: int = 0,
        tokenize_url: str = "",
    ) -> None:
        self._http = http
        self._llm_url = llm_url
        self._char_limit = char_limit
        self._compress_turns = compress_turns
        self._compress_temperature = compress_temperature
        self._compress_max_tokens = compress_max_tokens
        self._on_compress = on_compress
        # Number of most-recent turn pairs (user+assistant) to protect from compression
        self._protect_turns = protect_turns
        # Token-based limit; 0 = disabled (falls back to char_limit only)
        self._token_limit = token_limit
        # llamacpp /tokenize endpoint; "" = disabled (uses chars // 4 fallback)
        self._tokenize_url = tokenize_url
        # Cumulative compression count for this session
        self.stat_compress_count: int = 0

    @property
    def compress_turns(self) -> int:
        """Number of oldest turn pairs selected for compression.

        Exposed as a public property so external callers (e.g. _cmd_compact)
        can read the value without accessing the private _compress_turns attribute.
        """
        return self._compress_turns

    def apply_config(
        self,
        *,
        char_limit: int | None = None,
        compress_turns: int | None = None,
        token_limit: int | None = None,
        tokenize_url: str | None = None,
    ) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        if char_limit is not None:
            self._char_limit = char_limit
        if compress_turns is not None:
            self._compress_turns = compress_turns
        if token_limit is not None:
            self._token_limit = token_limit
        if tokenize_url is not None:
            self._tokenize_url = tokenize_url

    async def force_compress(self, history: list[LLMMessage]) -> list[LLMMessage]:
        """Force immediate compression regardless of the current char/token limits.

        Temporarily sets char_limit=1 so compress() always proceeds, then restores the
        original limits. Callers must replace ctx.conv.history with the returned list.
        """
        orig_char = self._char_limit
        orig_token = self._token_limit
        # char_limit=1 guarantees the over_char condition triggers; token_limit=0 disables it
        self._char_limit = 1
        self._token_limit = 0
        try:
            return await self.compress(history)
        finally:
            self._char_limit = orig_char
            self._token_limit = orig_token

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

    def count_tokens(
        self,
        history: list[LLMMessage],
        last_input_tokens: int | None = None,
    ) -> int:
        """Estimate total tokens in a history list.

        When last_input_tokens is provided (from LLM usage), return it directly
        as a precise measurement. Otherwise fall back to chars // 4 (local LLMs
        may not return usage fields consistently).
        """
        if last_input_tokens is not None:
            return last_input_tokens
        return self.count_chars(history) // 4

    async def count_tokens_async(
        self,
        history: list[LLMMessage],
        last_input_tokens: int | None = None,
    ) -> tuple[int, bool]:
        """Return (token_count, is_exact) using the best available source.

        Priority:
          1. last_input_tokens (from LLM usage.prompt_tokens) — exact
          2. /tokenize endpoint (llamacpp)                    — exact
          3. chars // 4                                       — estimate

        Returns is_exact=True for sources 1 and 2.
        """
        if last_input_tokens is not None:
            return last_input_tokens, True
        return await get_token_count(history, self._tokenize_url, self._http)

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
        match role:
            case "tool":
                return "temporary"
            case "system":
                return "factual"
            case "assistant" if msg.get("tool_calls"):
                return "temporary_reasoning"
            case _:
                return "history"

    @staticmethod
    def _classify_importance(msg: LLMMessage) -> float:
        """Classify message importance for compression prioritization.

        Higher importance scores mean the message should be preserved during compression.
        """
        # If pinned, it's very important
        if msg.get("pinned", False):
            return float("inf")

        # If importance is explicitly set, use that value
        importance = msg.get("importance", 0.0)
        if importance > 0:
            return importance

        # Default importance based on role and content
        role = msg.get("role", "")
        match role:
            case "system":
                return 10.0  # High importance for system messages
            case "assistant" if msg.get("tool_calls"):
                return 8.0  # Medium-high importance for planning messages
            case "user" | "assistant":
                return 5.0  # Medium importance for conversation turns
            case "tool":
                return 3.0  # Low importance for tool results
            case _:
                return 5.0  # Default for unknown roles

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
                self._llm_url,
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

    @staticmethod
    def _partition_by_class(
        turn_msgs: list[LLMMessage],
    ) -> tuple[
        list[LLMMessage],
        list[LLMMessage],
        list[LLMMessage],
        list[LLMMessage],
    ]:
        """Partition turn messages into (temporary, temporary_reasoning, factual, history)."""
        classified = [(HistoryManager._classify(m), m) for m in turn_msgs]
        temporary = [m for cls, m in classified if cls == "temporary"]
        temporary_reasoning = [
            m for cls, m in classified if cls == "temporary_reasoning"
        ]
        factual = [m for cls, m in classified if cls == "factual"]
        history_msgs = [m for cls, m in classified if cls == "history"]
        return temporary, temporary_reasoning, factual, history_msgs

    @staticmethod
    def _sort_by_importance(msgs: list[LLMMessage]) -> list[LLMMessage]:
        """Return msgs sorted by importance score descending (high = preserve first)."""
        scored = [(HistoryManager._classify_importance(m), m) for m in msgs]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [msg for _, msg in scored]

    def _select_turns_to_compress(
        self,
        history: list[LLMMessage],
    ) -> tuple[list[LLMMessage], list[LLMMessage], list[LLMMessage]] | None:
        """Split history into (system_msgs, to_compress, remaining).

        The most-recent protect_turns * 2 non-system messages are excluded from
        compression to preserve immediate context.  Returns None when there are
        not enough turn messages left after protection to compress.

        Uses importance scoring and classification to prioritize compression:
        - Messages with pinned=True are preserved
        - Messages with high importance scores are preserved
        - 'temporary' messages (tool results) are compressed first
        - 'temporary_reasoning' messages (assistant with tool_calls) are compressed next
        - 'factual' messages (system) are preserved
        - 'history' messages (user/assistant) are compressed last
        """
        system_msgs = [m for m in history if m["role"] == "system"]
        turn_msgs = [m for m in history if m["role"] != "system"]
        n_protect = self._protect_turns * 2
        n_compress = self._compress_turns * 2
        if len(turn_msgs) <= n_compress + n_protect:
            return None

        temporary, temporary_reasoning, factual, history_msgs = (
            self._partition_by_class(turn_msgs)
        )
        compressible = self._sort_by_importance(
            temporary + temporary_reasoning + history_msgs
        )

        protected_tail = turn_msgs[-n_protect:] if n_protect > 0 else []
        compressible = [m for m in compressible if m not in protected_tail]

        to_compress = compressible[:n_compress]
        remaining = [
            m for m in compressible[n_compress:] if m not in protected_tail
        ] + protected_tail
        remaining = factual + remaining

        return system_msgs, to_compress, remaining

    def _build_history_text(self, messages: list[LLMMessage]) -> str:
        """Render messages as a plain-text transcript for LLM summarisation."""
        return "\n".join(
            f"{m['role'].upper()}: {str(m.get('content', ''))[:300]}" for m in messages
        )

    @staticmethod
    def _build_summary_msg(
        system_msgs: list[LLMMessage], summary_text: str
    ) -> LLMMessage:
        """Return a system message containing summary_text.

        Appends to an existing [Conversation summary] message when present;
        otherwise creates a new one.
        """
        existing = next(
            (
                m
                for m in system_msgs
                if isinstance(m.get("content"), str)
                and str(m["content"]).startswith("[Conversation summary]")
            ),
            None,
        )
        if existing:
            new_content = f"{existing['content']}\n\n{summary_text}"
        else:
            new_content = f"[Conversation summary]\n{summary_text}"
        return {"role": "system", "content": new_content}

    async def compress(self, history: list[LLMMessage]) -> list[LLMMessage]:
        """Summarise the oldest turn pairs when history exceeds char or token limit.

        Returns the (possibly compressed) history list.
        Leaves the system prompt and recent turns intact.
        Increments stat_compress_count on successful compression.
        """
        over_char = (
            self._char_limit > 0 and self.count_chars(history) > self._char_limit
        )
        if self._token_limit > 0:
            token_count, _ = await self.count_tokens_async(history)
            over_token = token_count > self._token_limit
        else:
            token_count = 0
            over_token = False
        if not over_char and not over_token:
            return history
        split = self._select_turns_to_compress(history)
        if split is None:
            logger.warning(
                f"History compression skipped: protect_turns={self._protect_turns}"
                f" + compress_turns={self._compress_turns} >= available turns."
                f" chars={self.count_chars(history)} limit={self._char_limit}"
                f" tokens={token_count} token_limit={self._token_limit}."
                " Consider reducing protect_turns or increasing"
                " context_char_limit.",
            )
            return history
        system_msgs, to_compress, remaining = split
        summary_text = await self._call_compress_llm(
            self._build_history_text(to_compress),
        )
        if summary_text is None:
            return history

        summary_msg = self._build_summary_msg(system_msgs, summary_text)
        n = len(to_compress)
        self.stat_compress_count += 1
        logger.info(f"History compressed: {n} messages summarized")
        if self._on_compress:
            self._on_compress(n)
        return system_msgs + [summary_msg] + remaining
