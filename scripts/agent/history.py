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
from agent.history_selection_policy import (
    HistorySelectionPolicy,
    SelectionResult,
)
from shared.json_utils import tool_call_serialized_length
from shared.token_counter import _WarnOnce, get_token_count
from shared.token_estimation import estimate_tokens
from shared.types import LLMMessage

logger = logging.getLogger(__name__)

# Threshold: messages scoring >= this value are protected from compression (0–1 scale)
_DEFAULT_PROTECT_IMPORTANCE: float = 0.7


class HistoryCompressionError(RuntimeError):
    """Raised when LLM-based history compression fails."""


@dataclass
class CompressResult:
    """Metadata returned by compress() and force_compress()."""

    compressed_count: int
    protected_count: int
    summary_added: bool
    is_fallback: bool = False


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
        # Cumulative fallback truncation count for this session
        self.stat_fallback_truncate_count: int = 0
        # Warn-once suppressor for /tokenize unavailability (one warning per session)
        self._warn_once = _WarnOnce()
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
                total += tool_call_serialized_length(tc)
        return total

    def count_tokens(
        self,
        history: list[LLMMessage],
        last_input_tokens: int | None = None,
    ) -> int:
        """Estimate total tokens in a history list.

        Priority:

          1. ``last_input_tokens`` (from LLM ``usage.prompt_tokens``) — exact count
          2. Category-aware estimate                                  — estimated

        The category-aware estimator uses different character-to-token ratios for
        natural language text (4.0), structured JSON tool calls (2.5), and system
        messages (3.5).  This is more accurate than a simple ``chars // 4``
        heuristic, especially for multilingual text and tool payloads.

        When ``last_input_tokens`` is ``None`` the returned value is an estimate
        (``is_exact=False`` in async context).
        """
        if last_input_tokens is not None:
            return last_input_tokens
        token_count: int = estimate_tokens(history)[0]
        return token_count

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
        token_result: tuple[int, bool] = await get_token_count(
            history, self._tokenize_url, self._http, warn_once=self._warn_once
        )
        return token_result

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
                raise HistoryCompressionError(
                    "Context compression: LLM returned empty summary"
                )
            return str(raw_content).strip()
        except (httpx.HTTPError, orjson.JSONDecodeError, KeyError, TypeError) as e:
            raise HistoryCompressionError(f"Context compression failed: {e}") from e

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
        over_char = self._is_over_char_limit(history)
        token_count, over_token = await self._check_limits(history, over_char)
        if not over_char and not over_token:
            return history, _no_op
        split = self._selection_policy.select_turns_to_compress(history)
        if split is None:
            self._log_skip_warning(history, token_count)
            return history, _no_op
        summary_text = await self._get_summary_text(split.to_compress)
        if summary_text is None:
            if self._is_over_char_limit(history):
                return self._fallback_truncate(history)
            return history, _no_op
        return self._build_compressed_result(split, summary_text)

    def _is_over_char_limit(self, history: list[LLMMessage]) -> bool:
        """Return True when history exceeds the character limit."""
        return self._char_limit > 0 and self.count_chars(history) > self._char_limit

    def _fallback_truncate(
        self, history: list[LLMMessage]
    ) -> tuple[list[LLMMessage], CompressResult]:
        """Drop low-value messages to bring context under char limit.

        Drop order: lowest importance first (tool-role messages score 0.3).
        Preserves system messages and the most-recent protect_turns turn pairs.
        """
        protected_ids = self._build_protected_ids(history)
        candidates = sorted(
            (m for m in history if id(m) not in protected_ids),
            key=HistorySelectionPolicy.classify_importance,
        )
        new_history = list(history)
        for msg in candidates:
            if not self._is_over_char_limit(new_history):
                break
            new_history = [m for m in new_history if m is not msg]

        self.stat_fallback_truncate_count += 1
        dropped = len(history) - len(new_history)
        if self._is_over_char_limit(new_history):
            logger.warning(
                "Fallback truncation could not bring context under limit:"
                " chars=%d limit=%d",
                self.count_chars(new_history),
                self._char_limit,
            )
        logger.info("Fallback truncation applied: dropped %d messages", dropped)
        return new_history, CompressResult(
            compressed_count=dropped,
            protected_count=len(protected_ids),
            summary_added=False,
            is_fallback=True,
        )

    def _build_protected_ids(self, history: list[LLMMessage]) -> set[int]:
        """Return IDs of messages protected from truncation."""
        n_protect = self._protect_turns * 2
        protected_ids: set[int] = {id(m) for m in history if m["role"] == "system"}
        turn_msgs = [m for m in history if m["role"] != "system"]
        for m in turn_msgs[-n_protect:] if n_protect > 0 else []:
            protected_ids.add(id(m))
        return protected_ids

    def _reset_for_testing(self) -> None:
        """Reset cumulative counters; for use in tests only."""
        self.stat_compress_count = 0
        self.stat_fallback_truncate_count = 0

    async def _check_limits(
        self, history: list[LLMMessage], over_char: bool
    ) -> tuple[int, bool]:
        """Return (token_count, over_token). Returns (0, False) when char already exceeds."""
        if not over_char and self._token_limit > 0:
            token_count, _ = await self.count_tokens_async(history)
            return token_count, token_count > self._token_limit
        return 0, False

    def _log_skip_warning(self, history: list[LLMMessage], token_count: int) -> None:
        """Log why compression was skipped."""
        logger.warning(
            "History compression skipped: protect_turns=%s"
            " + compress_turns=%s >= available turns."
            " chars=%s limit=%s"
            " tokens=%s token_limit=%s."
            " Consider reducing protect_turns or increasing"
            " context_char_limit.",
            self._protect_turns,
            self._compress_turns,
            self.count_chars(history),
            self._char_limit,
            token_count,
            self._token_limit,
        )

    async def _get_summary_text(self, to_compress: list[LLMMessage]) -> str | None:
        """Send compressed history to LLM and return summary text, or None on failure."""
        try:
            return await self._call_compress_llm(self._build_history_text(to_compress))
        except HistoryCompressionError as e:
            logger.warning("History compression failed, returning original: %s", e)
            return None

    def _build_compressed_result(
        self, split: SelectionResult, summary_text: str
    ) -> tuple[list[LLMMessage], CompressResult]:
        """Build the compressed history list and CompressResult."""
        system_msgs = split.system_msgs
        remaining = split.remaining
        n = len(split.to_compress)
        protected = len(remaining) - len(system_msgs)
        self.stat_compress_count += 1
        logger.info("History compressed: %s messages summarized", n)
        if self._on_compress:
            self._on_compress(n)
        summary_msg = self._build_summary_msg(system_msgs, summary_text)
        result = CompressResult(
            compressed_count=n,
            protected_count=protected,
            summary_added=True,
        )
        return system_msgs + [summary_msg] + remaining, result
