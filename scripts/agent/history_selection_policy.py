#!/usr/bin/env python3
"""scripts/agent/history_selection_policy.py

HistorySelectionPolicy — whole-turn-unit compression candidate selection.

Turn units open at each user message and absorb the following assistant and
tool rows; selection compresses whole oldest units in chronological order and
never splits a unit. Importance scores only order the fallback path.

Extracted from HistoryManager so the selection logic can be tested and
configured independently of the HTTP/LLM compression pipeline.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from shared.types import LLMMessage


@dataclass(frozen=True)
class SelectionResult:
    """Typed result of select_turns_to_compress()."""

    system_msgs: list[LLMMessage]
    to_compress: list[LLMMessage]
    remaining: list[LLMMessage]


# Messages containing policy keywords get a higher importance score.
_POLICY_KEYWORDS = re.compile(
    r"\b(rule|policy|always|never|constraint|must|forbidden|required|invariant)\b",
    re.IGNORECASE,
)


class HistorySelectionPolicy:
    """Determines which messages to compress based on importance scoring."""

    def __init__(self, compress_turns: int, protect_turns: int) -> None:
        """Initialize the policy with compression and protection turn counts."""
        self._compress_turns = compress_turns
        self._protect_turns = protect_turns

    # ── Static classification helpers ────────────────────────────────────────

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
        has_policy = bool(_POLICY_KEYWORDS.search(content))
        if role == "assistant" and has_policy:
            return 0.8
        if role == "user" and has_policy:
            return 0.9
        if role == "assistant" and msg.get("tool_calls"):
            return 0.6
        return 0.5

    @staticmethod
    def group_turn_messages(turn_msgs: Sequence[LLMMessage]) -> list[list[LLMMessage]]:
        """Split turn messages into chronological turn units.

        A unit opens at a user message and absorbs every assistant and tool message
        until the next user message. Messages before the first user message form the
        leading unit, so an orphan tool row is a unit of its own. Concatenating the
        units reproduces turn_msgs exactly.
        """
        units: list[list[LLMMessage]] = []
        for msg in turn_msgs:
            if msg.get("role") == "user" or not units:
                units.append([msg])
            else:
                units[-1].append(msg)
        return units

    @staticmethod
    def group_importance(unit: Sequence[LLMMessage]) -> float:
        """Score a turn unit by its most important member."""
        return max(
            (HistorySelectionPolicy.classify_importance(m) for m in unit), default=0.0
        )

    def select_turns_to_compress(
        self,
        history: list[LLMMessage],
    ) -> SelectionResult | None:
        """Split history into (system_msgs, to_compress, remaining).

        Returns None when there are not enough turns to compress.
        """
        # All system-role messages (including _ephemeral/_memory_injected ones)
        # are pulled out here, before any scoring runs on turn_msgs below.
        # They are never part of a turn unit, so they can never be compressed;
        # do not wire them in to make ephemeral messages compressible — they
        # must never be summarized (see
        # requires/20260716_15_require.md).
        system_msgs = [m for m in history if m["role"] == "system"]
        turn_msgs = [m for m in history if m["role"] != "system"]
        n_protect = self._protect_turns * 2
        n_compress = self._compress_turns * 2
        if len(turn_msgs) < n_compress + n_protect:
            return None

        units = self.group_turn_messages(turn_msgs)
        protect_from = self._protect_tail_start(units, n_protect)
        window = self._compressible_window(units, protect_from, n_compress)
        if not window:
            return None
        to_compress, remaining = self._split_units(units, window)
        return SelectionResult(
            system_msgs=system_msgs, to_compress=to_compress, remaining=remaining
        )

    @staticmethod
    def _protect_tail_start(
        units: list[list[LLMMessage]],
        n_protect: int,
    ) -> int:
        """Index of the first unit kept in the protected tail.

        Rounds outward from the end, accumulating whole units until
        ``n_protect`` messages are covered. ``n_protect == 0`` protects nothing.
        """
        protect_from = len(units)
        tail = 0
        for i in range(len(units) - 1, -1, -1):
            if tail >= n_protect:
                break
            tail += len(units[i])
            protect_from = i
        return protect_from

    @staticmethod
    def _compressible_window(
        units: list[list[LLMMessage]],
        protect_from: int,
        n_compress: int,
    ) -> list[int]:
        """Whole-unit indices to compress, oldest first.

        Stops as soon as ``n_compress`` messages are covered (the last unit may
        overshoot); a unit holding a ``pinned`` message is skipped so it stays in
        ``remaining``.
        """
        window: list[int] = []
        taken = 0
        for i in range(protect_from):
            if taken >= n_compress:
                break
            if any(m.get("pinned") for m in units[i]):
                continue
            window.append(i)
            taken += len(units[i])
        return window

    @staticmethod
    def _split_units(
        units: list[list[LLMMessage]],
        window: list[int],
    ) -> tuple[list[LLMMessage], list[LLMMessage]]:
        """Partition units into (compressed, remaining) in chronological order."""
        wanted = set(window)
        to_compress: list[LLMMessage] = []
        remaining: list[LLMMessage] = []
        for i, unit in enumerate(units):
            if i in wanted:
                to_compress.extend(unit)
            else:
                remaining.extend(unit)
        return to_compress, remaining
