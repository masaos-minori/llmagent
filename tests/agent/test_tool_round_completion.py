"""tests/agent/test_tool_round_completion.py

Pure-function tests for the completion step's batch ordering: no fixtures, no patching.

Mutation note (T-6): restoring ``tc["id"]`` in ``complete_round()`` (or wrapping the merge
in ``try/except KeyError``) makes the id-less cases below fail, so strict indexing cannot
come back silently.
"""

from __future__ import annotations

from agent.tool_round_completion import _merge_in_declared_order


def _row(call_id: str, tag: str = "") -> tuple:
    return (call_id, "tool", {}, tag or call_id, False, "")


class TestMergeInDeclaredOrder:
    def test_entry_without_id_key_takes_the_empty_id_result(self) -> None:
        failure = _row("", "failure")

        merged = _merge_in_declared_order([{"function": {"name": "t"}}], [failure])

        assert merged == [failure]

    def test_id_less_entries_keep_distinct_batch_positions(self) -> None:
        tool_calls = [{}, {"id": "call_b"}, {"id": ""}]
        first, second = _row("", "first"), _row("", "second")
        b = _row("call_b")

        merged = _merge_in_declared_order(tool_calls, [b, first, second])

        assert merged == [first, b, second]

    def test_repeated_real_id_has_one_result_row(self) -> None:
        # Upstream collapses a repeated real id to one collected row (D-3), so only one
        # "x" result can exist for the three declared entries.
        x, y = _row("x"), _row("y")

        merged = _merge_in_declared_order(
            [{"id": "x"}, {"id": "y"}, {"id": "x"}], [x, y]
        )

        assert merged == [x, y]

    def test_unmatched_results_are_appended_last_and_kept(self) -> None:
        zz, a = _row("zz"), _row("a")

        merged = _merge_in_declared_order([{"id": "a"}], [zz, a])

        assert merged == [a, zz]

    def test_valid_unique_id_batches_follow_declared_order(self) -> None:
        a, b, c = _row("a"), _row("b"), _row("c")
        declared = [{"id": "a"}, {"id": "b"}, {"id": "c"}]

        assert _merge_in_declared_order(declared, [a, b, c]) == [a, b, c]
        assert _merge_in_declared_order(declared, [c, a, b]) == [a, b, c]
