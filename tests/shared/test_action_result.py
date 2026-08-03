"""
tests/test_action_result.py
Unit tests for shared/action_result.py.
"""

from __future__ import annotations

import pytest
from shared.action_result import ActionResult


class TestActionResultDefaults:
    def test_action_is_required(self) -> None:
        r = ActionResult(action="continue")
        assert r.action == "continue"

    def test_defaults_are_empty(self) -> None:
        r = ActionResult(action="fail")
        assert r.reason == ""
        assert r.required_context == []
        assert r.payload == {}
        assert r.errors == []
        assert r.confidence == 1.0

    def test_frozen_immutable(self) -> None:
        import dataclasses

        r = ActionResult(action="continue")
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(r, "action", "fail")


class TestActionResultAllTypes:
    @pytest.mark.parametrize(
        "action",
        [
            "continue",
            "call_tool",
            "retrieve_more_context",
            "ask_user",
            "fail",
            "retry",
        ],
    )
    def test_valid_action_types(self, action: str) -> None:
        r = ActionResult(action=action)
        assert r.action == action


class TestActionResultFields:
    def test_reason_field(self) -> None:
        r = ActionResult(action="fail", reason="missing data")
        assert r.reason == "missing data"

    def test_required_context_field(self) -> None:
        r = ActionResult(action="retrieve_more_context", required_context=["file.py"])
        assert r.required_context == ["file.py"]

    def test_payload_field(self) -> None:
        r = ActionResult(action="call_tool", payload={"tool": "search", "query": "x"})
        assert r.payload == {"tool": "search", "query": "x"}

    def test_errors_field(self) -> None:
        r = ActionResult(action="fail", errors=["timeout", "retry exceeded"])
        assert r.errors == ["timeout", "retry exceeded"]

    def test_confidence_field(self) -> None:
        r = ActionResult(action="continue", confidence=0.85)
        assert r.confidence == pytest.approx(0.85)

    def test_all_fields_set(self) -> None:
        r = ActionResult(
            action="call_tool",
            reason="needs search",
            required_context=["query"],
            payload={"tool": "web_search"},
            errors=[],
            confidence=0.9,
        )
        assert r.action == "call_tool"
        assert r.reason == "needs search"
        assert r.required_context == ["query"]
        assert r.payload == {"tool": "web_search"}
        assert r.errors == []
        assert r.confidence == pytest.approx(0.9)
