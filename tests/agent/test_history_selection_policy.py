"""
tests/test_history_selection_policy.py
Unit tests for HistorySelectionPolicy — whole-turn-unit selection: chronological
whole-unit compression, unit atomicity across the partition boundary, pinned
protection by unit, and position-based accounting.
"""

from __future__ import annotations

from agent.history_selection_policy import HistorySelectionPolicy
from shared.types import LLMMessage


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


_TOOL_CALLS = [
    {"id": "x", "type": "function", "function": {"name": "f", "arguments": "{}"}}
]


def _index_of(history: list[LLMMessage], msg: LLMMessage) -> int:
    """Return the input index of msg by identity, not by value.

    Duplicate-content messages compare equal, so list.index() would collapse
    them; selection asserts on input position, which requires identity.
    """
    for i, m in enumerate(history):
        if m is msg:
            return i
    raise ValueError(f"{msg!r} is not in history")


# ── group_turn_messages() ──────────────────────────────────────────────────


class TestGroupTurnMessages:
    def test_units_reproduce_their_input(self) -> None:
        msgs = [
            _msg("tool", "orphan"),
            _msg("user", "q1"),
            _msg("assistant", "a1", tool_calls=_TOOL_CALLS),
            _msg("tool", "OK: done"),
            _msg("tool", "OK: done2"),
            _msg("user", "q2"),
            _msg("assistant", "a2"),
        ]
        units = HistorySelectionPolicy.group_turn_messages(msgs)
        assert [m for unit in units for m in unit] == msgs
        assert [len(u) for u in units] == [1, 4, 2]

    def test_unit_absorbs_assistant_and_tool_rows(self) -> None:
        msgs = [
            _msg("user", "q1"),
            _msg("assistant", "a1", tool_calls=_TOOL_CALLS),
            _msg("tool", "OK: done"),
            _msg("tool", "OK: done2"),
            _msg("user", "q2"),
            _msg("assistant", "a2"),
        ]
        units = HistorySelectionPolicy.group_turn_messages(msgs)
        assert [len(u) for u in units] == [4, 2]

    def test_leading_non_user_messages_form_a_leading_unit(self) -> None:
        msgs = [
            _msg("tool", "orphan"),
            _msg("user", "q1"),
            _msg("assistant", "a1"),
        ]
        units = HistorySelectionPolicy.group_turn_messages(msgs)
        assert [len(u) for u in units] == [1, 2]
        assert units[0][0] is msgs[0]

    def test_consecutive_user_messages_open_their_own_units(self) -> None:
        msgs = [
            _msg("user", "q1"),
            _msg("user", "q2"),
            _msg("assistant", "a2"),
        ]
        units = HistorySelectionPolicy.group_turn_messages(msgs)
        assert [len(u) for u in units] == [1, 2]


# ── group_importance() ─────────────────────────────────────────────────────


class TestGroupImportance:
    def test_group_score_is_the_max_member_score(self) -> None:
        unit = [
            _msg("assistant", "a1", tool_calls=_TOOL_CALLS),
            _msg("tool", "OK: done"),
        ]
        assert HistorySelectionPolicy.group_importance(unit) == 0.6

    def test_plain_pair_scores_half(self) -> None:
        unit = [_msg("user", "hello"), _msg("assistant", "hi")]
        assert HistorySelectionPolicy.group_importance(unit) == 0.5

    def test_explicit_importance_participates_in_the_max(self) -> None:
        unit = [_msg("user", "x", importance=0.95), _msg("assistant", "y")]
        assert HistorySelectionPolicy.group_importance(unit) == 0.95

    def test_pinned_member_makes_the_unit_infinite(self) -> None:
        unit = [_msg("user", "a"), _msg("user", "b", pinned=True)]
        assert HistorySelectionPolicy.group_importance(unit) == float("inf")

    def test_empty_group_scores_zero(self) -> None:
        assert HistorySelectionPolicy.group_importance([]) == 0.0


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
        result = policy.select_turns_to_compress(history)
        assert result is not None
        assert result.system_msgs == [{"role": "system", "content": "You are helpful."}]
        assert len(result.to_compress) > 0
        assert len(result.remaining) > 0

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
        result = policy.select_turns_to_compress(history)
        assert result is not None
        assert len(result.to_compress) == 2
        # The most-recent protected pair should be in remaining
        protected_msgs = [
            {"role": "user", "content": "q3"},
            {"role": "assistant", "content": "a3"},
        ]
        for pm in protected_msgs:
            assert pm in result.remaining

    def test_returns_none_with_only_system_messages(self) -> None:
        policy = HistorySelectionPolicy(compress_turns=1, protect_turns=0)
        result = policy.select_turns_to_compress([_msg("system", "You are helpful.")])
        assert result is None

    def test_ephemeral_and_memory_injected_messages_never_compressible(self) -> None:
        """_ephemeral (mode hint) and _memory_injected (memory snippet)
        messages are system-role, so they land in system_msgs -- never in
        to_compress or remaining -- before classify() is ever applied
        (requires/20260716_15_require.md)."""
        policy = HistorySelectionPolicy(compress_turns=1, protect_turns=0)
        ephemeral_msg: LLMMessage = {
            "role": "system",
            "content": "hint",
            "_ephemeral": True,
        }
        memory_msg: LLMMessage = {
            "role": "system",
            "content": "mem",
            "_memory_injected": True,
        }
        history = [
            ephemeral_msg,
            memory_msg,
            _msg("user", "q1"),
            _msg("assistant", "a1"),
            _msg("user", "q2"),
            _msg("assistant", "a2"),
        ]
        result = policy.select_turns_to_compress(history)
        assert result is not None
        assert ephemeral_msg in result.system_msgs
        assert memory_msg in result.system_msgs
        assert ephemeral_msg not in result.to_compress
        assert memory_msg not in result.to_compress
        assert ephemeral_msg not in result.remaining
        assert memory_msg not in result.remaining


# ── chronological whole-unit selection (REQ-002, REQ-004) ──────────────────

_CHRONO = [
    _msg("user", "q1"),
    _msg("assistant", "a1"),
    _msg("user", "q2"),
    _msg("assistant", "a2"),
    _msg("user", "You must always follow the rule"),
    _msg("assistant", "a3"),
    _msg("user", "q4"),
    _msg("assistant", "a4"),
]


class TestSelectionIsChronological:
    def test_oldest_units_are_compressed_first(self) -> None:
        policy = HistorySelectionPolicy(compress_turns=2, protect_turns=1)
        result = policy.select_turns_to_compress(_CHRONO)
        assert result is not None
        to_compress = [_index_of(_CHRONO, m) for m in result.to_compress]
        assert to_compress == [0, 1, 2, 3]
        remaining_idx = [_index_of(_CHRONO, m) for m in result.remaining]
        assert 4 not in to_compress
        assert 4 in remaining_idx

    def test_both_partitions_keep_input_index_order(self) -> None:
        history = [
            _msg("user", "q1"),
            _msg("assistant", "a1", tool_calls=_TOOL_CALLS),
            _msg("tool", "OK: done"),
            _msg("tool", "OK: done2"),
            _msg("user", "q2"),
            _msg("assistant", "a2"),
        ]
        policy = HistorySelectionPolicy(compress_turns=2, protect_turns=0)
        result = policy.select_turns_to_compress(history)
        assert result is not None
        to_compress = [_index_of(history, m) for m in result.to_compress]
        remaining = [_index_of(history, m) for m in result.remaining]
        assert to_compress == [0, 1, 2, 3]
        assert remaining == [4, 5]

    def test_protected_tail_is_the_newest_units(self) -> None:
        policy = HistorySelectionPolicy(compress_turns=2, protect_turns=1)
        result = policy.select_turns_to_compress(_CHRONO)
        assert result is not None
        remaining = [_index_of(_CHRONO, m) for m in result.remaining]
        assert remaining == [4, 5, 6, 7]


class TestSelectionUnitAtomicity:
    def test_tool_round_never_splits_across_partitions(self) -> None:
        history = [
            _msg("user", "q1"),
            _msg("assistant", "a1", tool_calls=_TOOL_CALLS),
            _msg("tool", "OK: done"),
            _msg("tool", "OK: done2"),
            _msg("user", "You must always follow the rule"),
            _msg("assistant", "a2"),
        ]
        policy = HistorySelectionPolicy(compress_turns=1, protect_turns=1)
        result = policy.select_turns_to_compress(history)
        assert result is not None
        to_compress = [_index_of(history, m) for m in result.to_compress]
        remaining = [_index_of(history, m) for m in result.remaining]
        assert to_compress == [0, 1, 2, 3]
        assert remaining == [4, 5]
        assert all(m["role"] != "tool" for m in result.remaining)

    def test_last_unit_may_overshoot_the_compress_target(self) -> None:
        history = [
            _msg("user", "q1"),
            _msg("assistant", "a1", tool_calls=_TOOL_CALLS),
            _msg("tool", "OK: done"),
            _msg("user", "q2"),
            _msg("assistant", "a2"),
        ]
        policy = HistorySelectionPolicy(compress_turns=1, protect_turns=0)
        result = policy.select_turns_to_compress(history)
        assert result is not None
        assert len(result.to_compress) == 3
        assert len(result.remaining) == 2


class TestPinnedUnitProtection:
    def test_pinned_unit_stays_in_remaining(self) -> None:
        history = [
            _msg("user", "q1", pinned=True),
            _msg("assistant", "a1"),
            _msg("user", "q2"),
            _msg("assistant", "a2"),
            _msg("user", "q3"),
            _msg("assistant", "a3"),
        ]
        policy = HistorySelectionPolicy(compress_turns=2, protect_turns=0)
        result = policy.select_turns_to_compress(history)
        assert result is not None
        to_compress = [_index_of(history, m) for m in result.to_compress]
        remaining = [_index_of(history, m) for m in result.remaining]
        assert to_compress == [2, 3, 4, 5]
        assert remaining == [0, 1]
        assert all(m.get("pinned") is not True for m in result.to_compress)

    def test_returns_none_when_every_candidate_unit_is_pinned(self) -> None:
        history = [_msg("user", "q1", pinned=True), _msg("assistant", "a1")]
        policy = HistorySelectionPolicy(compress_turns=1, protect_turns=0)
        result = policy.select_turns_to_compress(history)
        assert result is None


class TestPositionBasedAccounting:
    def test_every_message_is_accounted_for(self) -> None:
        history = [
            _msg("user", "q1"),
            _msg("assistant", "a1"),
            _msg("user", "q2"),
            _msg("assistant", "a2"),
            _msg("user", "same"),
            _msg("assistant", "a3"),
            _msg("user", "q4"),
            _msg("assistant", "a4"),
            _msg("user", "same"),
            _msg("assistant", "a5"),
            _msg("user", "q6"),
            _msg("assistant", "a6"),
            _msg("user", "q7"),
            _msg("assistant", "a7"),
            _msg("user", "q8"),
            _msg("assistant", "a8"),
        ]
        policy = HistorySelectionPolicy(compress_turns=2, protect_turns=2)
        result = policy.select_turns_to_compress(history)
        assert result is not None
        assert (
            len(result.system_msgs) + len(result.to_compress) + len(result.remaining)
            == 16
        )
        to_compress = [_index_of(history, m) for m in result.to_compress]
        remaining = [_index_of(history, m) for m in result.remaining]
        assert to_compress == [0, 1, 2, 3]
        assert remaining == list(range(4, 16))

    def test_identical_content_messages_are_both_retained(self) -> None:
        history = [
            _msg("user", "q1"),
            _msg("assistant", "a1"),
            _msg("user", "q2"),
            _msg("assistant", "a2"),
            _msg("user", "same"),
            _msg("assistant", "a3"),
            _msg("user", "same"),
            _msg("assistant", "a4"),
            _msg("user", "q6"),
            _msg("assistant", "a5"),
            _msg("user", "q7"),
            _msg("assistant", "a6"),
            _msg("user", "q8"),
            _msg("assistant", "a7"),
            _msg("user", "q9"),
            _msg("assistant", "a8"),
        ]
        policy = HistorySelectionPolicy(compress_turns=2, protect_turns=2)
        result = policy.select_turns_to_compress(history)
        assert result is not None
        assert result.remaining.count({"role": "user", "content": "same"}) == 2
