#!/usr/bin/env python3
"""Tests for scripts/shared/llm_payload.py.

Characterization tests written ahead of a structural refactor (no behavior
change intended) to lock current parse behavior, including error paths.
"""

from __future__ import annotations

import pytest
from shared.llm_payload import LlmPayloadHandler


class TestParseResponse:
    def test_valid_response_without_usage(self) -> None:
        raw = {
            "choices": [
                {
                    "message": {"role": "assistant", "content": "hi"},
                    "finish_reason": "stop",
                }
            ]
        }
        result = LlmPayloadHandler.parse_response(raw)
        assert result.message == {"role": "assistant", "content": "hi"}
        assert result.finish_reason == "stop"
        assert result.usage is None

    def test_valid_response_with_usage_calls_callback(self) -> None:
        raw = {
            "choices": [{"message": {"role": "assistant"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 7},
        }
        seen: list[tuple[int, int]] = []
        result = LlmPayloadHandler.parse_response(
            raw, on_usage=lambda p, c: seen.append((p, c))
        )
        assert result.usage is not None
        assert result.usage.prompt_tokens == 5
        assert result.usage.completion_tokens == 7
        assert seen == [(5, 7)]

    def test_missing_choices_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="missing or empty 'choices'"):
            LlmPayloadHandler.parse_response({})

    def test_empty_choices_list_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="missing or empty 'choices'"):
            LlmPayloadHandler.parse_response({"choices": []})

    def test_choices_not_a_list_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="missing or empty 'choices'"):
            LlmPayloadHandler.parse_response({"choices": "not-a-list"})

    def test_choice_not_a_dict_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="choices\\[0\\] is not a dict"):
            LlmPayloadHandler.parse_response({"choices": ["not-a-dict"]})

    def test_message_not_a_dict_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="'message' is not a dict"):
            LlmPayloadHandler.parse_response({"choices": [{"message": "not-a-dict"}]})

    def test_missing_message_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="'message' is not a dict"):
            LlmPayloadHandler.parse_response({"choices": [{}]})

    def test_non_string_finish_reason_becomes_none(self) -> None:
        raw = {"choices": [{"message": {"role": "assistant"}, "finish_reason": 123}]}
        result = LlmPayloadHandler.parse_response(raw)
        assert result.finish_reason is None

    def test_missing_finish_reason_stays_none(self) -> None:
        raw = {"choices": [{"message": {"role": "assistant"}}]}
        result = LlmPayloadHandler.parse_response(raw)
        assert result.finish_reason is None
