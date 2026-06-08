"""
tests/test_history_selection_policy.py
Unit tests for HistorySelectionPolicy — pure classification/sorting logic.
"""

from __future__ import annotations

from agent.history_selection_policy import HistorySelectionPolicy
from rag.types import LLMMessage


def _msg(
    role: str,
    content: str | None = None,
    tool_calls: list | None = None,
    pinned: bool = False,
    importance: float | None = None,
) -> LLMMessage:
    m: LLMMessage = {"role": role}
    if content is not None:
        m["content"] = content
    if tool_calls is not None:
        m["tool_calls"] = tool_calls
    if pinned:
        m["pinned"] = True
    if importance is not None:
        m["importance"] = importance
    return m


# ── partition_by_class() ──────────────────────────────────────────────────────


class TestPartitionByClass:
    def test_partitions_all_categories(self) -> None:
        msgs = [
            _msg("tool", "result"),
            _msg(
                "assistant",
                content="planning",
                tool_calls=[
                    {
                        "id": "x",
                        "type": "function",
                        "function": {"name": "f", "arguments": "{}"},
                    }
                ],
            ),
            _msg("system", "You are helpful."),
            _msg("user", "hello"),
        ]
        temporary, temporary_reasoning, factual, history = (
            HistorySelectionPolicy.partition_by_class(msgs)
        )
        assert len(temporary) == 1
        assert temporary[0]["role"] == "tool"
        assert len(temporary_reasoning) == 1
        assert temporary_reasoning[0]["role"] == "assistant"
        assert len(factual) == 1
        assert factual[0]["role"] == "system"
        assert len(history) == 1
        assert history[0]["role"] == "user"

    def test_empty_list(self) -> None:
        temporary, temporary_reasoning, factual, history = (
            HistorySelectionPolicy.partition_by_class([])
        )
        assert temporary == []
        assert temporary_reasoning == []
        assert factual == []
        assert history == []

    def test_all_history(self) -> None:
        msgs = [_msg("user", "a"), _msg("assistant", "b"), _msg("user", "c")]
        temporary, temporary_reasoning, factual, history = (
            HistorySelectionPolicy.partition_by_class(msgs)
        )
        assert temporary == []
        assert temporary_reasoning == []
        assert factual == []
        assert len(history) == 3


# ── sort_by_importance() ───────────────────────────────────────────────────────


class TestSortByImportance:
    def test_returns_empty_for_empty_input(self) -> None:
        assert HistorySelectionPolicy.sort_by_importance([]) == []

    def test_sorts_descending_by_importance(self) -> None:
        msgs = [
            _msg("tool", "success result"),  # 0.3
            _msg("user", "hello"),  # 0.5
            _msg("system", "You are helpful."),  # 1.0
        ]
        sorted_msgs = HistorySelectionPolicy.sort_by_importance(msgs)
        assert sorted_msgs[0]["role"] == "system"
        assert sorted_msgs[1]["role"] == "user"
        assert sorted_msgs[2]["role"] == "tool"

    def test_pinned_is_first(self) -> None:
        msgs = [
            _msg("user", "hello"),
            _msg("user", "important", pinned=True),
        ]
        sorted_msgs = HistorySelectionPolicy.sort_by_importance(msgs)
        assert sorted_msgs[0]["role"] == "user"
        assert sorted_msgs[0].get("pinned") is True

    def test_preserves_original_messages(self) -> None:
        msgs = [_msg("user", "a"), _msg("assistant", "b")]
        sorted_msgs = HistorySelectionPolicy.sort_by_importance(msgs)
        assert len(sorted_msgs) == 2


# ── select_turns_to_compress() ─────────────────────────────────────────────────


class TestSelectTurnsToCompress:
    def test_returns_none_when_not_enough_turns(self) -> None:
        policy = HistorySelectionPolicy(compress_turns=2, protect_turns=0)
        history = [_msg("user", "q1"), _msg("assistant", "a1")]
        result = policy.select_turns_to_compress(history)
        assert result is None

    def test_returns_none_when_protect_consumes_all(self) -> None:
        policy = HistorySelectionPolicy(compress_turns=2, protect_turns=2)
        history = [
            _msg("user", "q1"),
            _msg("assistant", "a1"),
            _msg("user", "q2"),
            _msg("assistant", "a2"),
        ]
        result = policy.select_turns_to_compress(history)
        assert result is None

    def test_returns_split_with_system_msgs(self) -> None:
        policy = HistorySelectionPolicy(compress_turns=1, protect_turns=0)
        history = [
            _msg("system", "You are helpful."),
            _msg("user", "q1"),
            _msg("assistant", "a1"),
            _msg("user", "q2"),
            _msg("assistant", "a2"),
        ]
        system_msgs, to_compress, remaining = policy.select_turns_to_compress(history)
        assert system_msgs == [{"role": "system", "content": "You are helpful."}]
        assert len(to_compress) > 0
        assert len(remaining) > 0

    def test_protected_turns_excluded_from_compressible(self) -> None:
        policy = HistorySelectionPolicy(compress_turns=1, protect_turns=1)
        history = [
            _msg("user", "q1"),
            _msg("assistant", "a1"),
            _msg("user", "q2"),
            _msg("assistant", "a2"),
            _msg("user", "q3"),
            _msg("assistant", "a3"),
        ]
        _, to_compress, remaining = policy.select_turns_to_compress(history)
        assert len(to_compress) == 2
        # The most-recent protected pair should be in remaining
        protected_msgs = [
            {"role": "user", "content": "q3"},
            {"role": "assistant", "content": "a3"},
        ]
        for pm in protected_msgs:
            assert pm in remaining

    def test_returns_none_with_only_system_messages(self) -> None:
        policy = HistorySelectionPolicy(compress_turns=1, protect_turns=0)
        result = policy.select_turns_to_compress([_msg("system", "You are helpful.")])
        assert result is None
