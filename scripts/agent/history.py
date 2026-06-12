#!/usr/bin/env python3
"""agent/history.py
Conversation history compression layer extracted from REPLAgent.
Monitors total history size and summarises old turns via the chat LLM
when the character limit is exceeded.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass

import httpx
import orjson
from shared.token_counter import get_token_count
from shared.types import LLMMessage

from agent.history_selection_policy import HistorySelectionPolicy

logger = logging.getLogger(__name__)

# Threshold: messages scoring >= this value are protected from compression (0–1 scale)
_DEFAULT_PROTECT_IMPORTANCE: float = 0.7


@dataclass
class CompressResult:
    """Metadata returned by compress() and force_compress()."""

    compressed_count: int
    protected_count: int
    summary_added: bool


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
        # Selection policy encapsulates importance scoring and candidate selection
        self._selection_policy = HistorySelectionPolicy(compress_turns, protect_turns)

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
            self._selection_policy = HistorySelectionPolicy(
                self._compress_turns, self._protect_turns
            )
        if token_limit is not None:
            self._token_limit = token_limit
        if tokenize_url is not None:
            self._tokenize_url = tokenize_url

    async def force_compress(
        self, history: list[LLMMessage]
    ) -> tuple[list[LLMMessage], CompressResult]:
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

    # Delegate classification to HistorySelectionPolicy; kept as staticmethod
    # aliases so existing callers (e.g. tests) can still reference them here.
    _classify = staticmethod(HistorySelectionPolicy.classify)
    _classify_importance = staticmethod(HistorySelectionPolicy.classify_importance)

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
        except (httpx.HTTPError, orjson.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Context compression failed: {e}")
            return None

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

    async def compress(
        self, history: list[LLMMessage]
    ) -> tuple[list[LLMMessage], CompressResult]:
        """Summarise the oldest turn pairs when history exceeds char or token limit.

        Returns (history, CompressResult). history may be unchanged when no compression
        was needed or possible. Leaves the system prompt and recent turns intact.
        Increments stat_compress_count on successful compression.
        """
        _no_op = CompressResult(
            compressed_count=0, protected_count=0, summary_added=False
        )
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
            return history, _no_op
        split = self._selection_policy.select_turns_to_compress(history)
        if split is None:
            logger.warning(
                f"History compression skipped: protect_turns={self._protect_turns}"
                f" + compress_turns={self._compress_turns} >= available turns."
                f" chars={self.count_chars(history)} limit={self._char_limit}"
                f" tokens={token_count} token_limit={self._token_limit}."
                " Consider reducing protect_turns or increasing"
                " context_char_limit.",
            )
            return history, _no_op
        system_msgs = split.system_msgs
        to_compress = split.to_compress
        remaining = split.remaining
        summary_text = await self._call_compress_llm(
            self._build_history_text(to_compress),
        )
        if summary_text is None:
            return history, _no_op

        summary_msg = self._build_summary_msg(system_msgs, summary_text)
        n = len(to_compress)
        protected = len(remaining) - len(system_msgs)
        self.stat_compress_count += 1
        logger.info(f"History compressed: {n} messages summarized")
        if self._on_compress:
            self._on_compress(n)
        result = CompressResult(
            compressed_count=n,
            protected_count=protected,
            summary_added=True,
        )
        return system_msgs + [summary_msg] + remaining, result
