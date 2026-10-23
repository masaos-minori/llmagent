"""tests/agent/test_tool_result_pairing.py

Pure-function tests for the round's result pairing: no fixtures, no patching.
"""

from __future__ import annotations

from agent.message_schema import validate_message
from agent.tool_enums import ToolCallStopReason
from agent.tool_result_pairing import build_denied_messages, pair_round_results

GUARD = ToolCallStopReason.GUARD_STOP
NOT_DONE = ToolCallStopReason.ROUND_NOT_COMPLETED


def _ids(rows: list) -> list[str]:
    return [row[3] for row in rows]


class TestPairingIsByDeclaredId:
    def test_unanswered_declared_ids_are_synthesized(self) -> None:
        history, rows = pair_round_results(["a", "b", "c"], set(), {}, NOT_DONE)

        assert _ids(rows) == ["a", "b", "c"]
        assert [m["tool_call_id"] for m in history] == ["a", "b", "c"]

    def test_collected_and_already_answered_ids_are_not_synthesized(self) -> None:
        _, rows = pair_round_results(
            ["a", "b", "c", "d"], {"b"}, {"c": ("c",)}, NOT_DONE
        )

        assert _ids(rows) == ["a", "d"]

    def test_a_duplicated_declared_id_yields_one_row(self) -> None:
        _, rows = pair_round_results(["a", "a"], set(), {}, GUARD)

        assert _ids(rows) == ["a"]

    def test_an_empty_declaration_yields_nothing(self) -> None:
        assert pair_round_results([], set(), {}, GUARD) == ([], [])


class TestStopReasonIsClosed:
    def test_each_reason_has_its_own_text_that_says_the_call_was_not_executed(
        self,
    ) -> None:
        texts = {
            reason: pair_round_results(["a"], set(), {}, reason)[1][0][1]
            for reason in ToolCallStopReason
        }

        assert len(set(texts.values())) == len(ToolCallStopReason) == 2
        assert all("not executed" in t for t in texts.values())

    def test_texts_differ_from_the_denial_text_and_are_not_empty(self) -> None:
        denied = build_denied_messages(["a"])[1][0][1]

        for reason in ToolCallStopReason:
            text = pair_round_results(["a"], set(), {}, reason)[1][0][1]
            assert text and text != denied


class TestOrderIsDeclaredOrder:
    def test_output_follows_declared_order_not_collection_order(self) -> None:
        collected = {"d": (), "b": ()}

        _, rows = pair_round_results(["a", "b", "c", "d", "e"], set(), collected, GUARD)

        assert _ids(rows) == ["a", "c", "e"]


class TestSynthesizedRowValidates:
    def test_message_and_row_shape(self) -> None:
        history, rows = pair_round_results(["x"], set(), {}, GUARD)

        assert validate_message(dict(history[0])).success
        assert history[0]["role"] == "tool" and history[0]["tool_call_id"] == "x"
        assert rows[0] == ("tool", history[0]["content"], None, "x")


class TestBuildDeniedMessages:
    def test_one_pair_per_denied_id_in_order(self) -> None:
        history, rows = build_denied_messages(["b", "a"])

        assert [m["tool_call_id"] for m in history] == ["b", "a"]
        assert rows == [
            ("tool", "Tool execution denied by user.", None, "b"),
            ("tool", "Tool execution denied by user.", None, "a"),
        ]
