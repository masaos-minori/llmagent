#!/usr/bin/env python3
"""agent/history_selection_policy.py
HistorySelectionPolicy — importance-based compression candidate selection.

Extracted from HistoryManager so the selection logic can be tested and
configured independently of the HTTP/LLM compression pipeline.
"""

from __future__ import annotations

import re

from rag.types import LLMMessage

# Messages containing policy keywords get a higher importance score.
_POLICY_KEYWORDS = re.compile(
    r"\b(rule|policy|always|never|constraint|must|forbidden|required|invariant)\b",
    re.IGNORECASE,
)


class HistorySelectionPolicy:
    """Determines which messages to compress based on importance scoring."""

    def __init__(self, compress_turns: int, protect_turns: int) -> None:
        self._compress_turns = compress_turns
        self._protect_turns = protect_turns

    # ── Static classification helpers ────────────────────────────────────────

    @staticmethod
    def classify(msg: LLMMessage) -> str:
        """Classify a message into a compression-priority category.

        Categories (from highest to lowest compression priority):
          'temporary'          — tool result messages (role='tool'); ephemeral context
          'temporary_reasoning'— assistant messages containing tool_calls (planning turns)
          'factual'            — system messages; structural / long-lived context
          'history'            — regular user/assistant conversation turns
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
    def classify_importance(msg: LLMMessage) -> float:
        """Return importance score 0.0–1.0 (or inf for pinned) for compression priority.

        Higher importance = less likely to be compressed.
        """
        if msg.get("pinned", False):
            return float("inf")

        explicit = msg.get("importance")
        if explicit is not None:
            return float(explicit)

        role = msg.get("role", "")
        content = str(msg.get("content") or "")
        if role == "system":
            return 1.0
        if role == "tool":
            if "error" in content.lower() or "failed" in content.lower():
                return 0.8
            return 0.3
        if role == "assistant" and _POLICY_KEYWORDS.search(content):
            return 0.8
        if role == "user" and _POLICY_KEYWORDS.search(content):
            return 0.9
        if role == "assistant" and msg.get("tool_calls"):
            return 0.6
        return 0.5

    @staticmethod
    def partition_by_class(
        turn_msgs: list[LLMMessage],
    ) -> tuple[
        list[LLMMessage],
        list[LLMMessage],
        list[LLMMessage],
        list[LLMMessage],
    ]:
        """Partition turn messages into (temporary, temporary_reasoning, factual, history)."""
        classified = [(HistorySelectionPolicy.classify(m), m) for m in turn_msgs]
        temporary = [m for cls, m in classified if cls == "temporary"]
        temporary_reasoning = [
            m for cls, m in classified if cls == "temporary_reasoning"
        ]
        factual = [m for cls, m in classified if cls == "factual"]
        history_msgs = [m for cls, m in classified if cls == "history"]
        return temporary, temporary_reasoning, factual, history_msgs

    @staticmethod
    def sort_by_importance(msgs: list[LLMMessage]) -> list[LLMMessage]:
        """Return msgs sorted by importance score descending (high = preserve first)."""
        scored = [(HistorySelectionPolicy.classify_importance(m), m) for m in msgs]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [msg for _, msg in scored]

    def select_turns_to_compress(
        self,
        history: list[LLMMessage],
    ) -> tuple[list[LLMMessage], list[LLMMessage], list[LLMMessage]] | None:
        """Split history into (system_msgs, to_compress, remaining).

        Returns None when there are not enough turns to compress.
        """
        system_msgs = [m for m in history if m["role"] == "system"]
        turn_msgs = [m for m in history if m["role"] != "system"]
        n_protect = self._protect_turns * 2
        n_compress = self._compress_turns * 2
        if len(turn_msgs) <= n_compress + n_protect:
            return None

        temporary, temporary_reasoning, factual, history_msgs = self.partition_by_class(
            turn_msgs
        )
        compressible = self.sort_by_importance(
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
