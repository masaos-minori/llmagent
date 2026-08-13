#!/usr/bin/env python3
"""Tests for scripts/shared/llm_payload.py.

Characterization tests written ahead of a structural refactor (no behavior
change intended) to lock current build/parse behavior, including error paths.
"""

from __future__ import annotations

import orjson
import pytest
from shared.llm_payload import LlmPayloadHandler
from shared.types import LLMMessage


class TestBuildPayload:
    def test_default_payload_omits_stream_key(self) -> None:
        history: list[LLMMessage] = [{"role": "user", "content": "hi"}]
        payload = LlmPayloadHandler.build_payload(
            history, [], temperature=0.5, max_tokens=100
        )
        assert payload == {
            "messages": history,
            "tools": [],
            "tool_choice": "auto",
            "temperature": 0.5,
            "max_tokens": 100,
        }
        assert "stream" not in payload

    def test_stream_true_adds_stream_key(self) -> None:
        history: list[LLMMessage] = [{"role": "user", "content": "hi"}]
        payload = LlmPayloadHandler.build_payload(
            history, [], temperature=0.2, max_tokens=50, stream=True
        )
        assert payload["stream"] is True

    def test_tool_defs_passed_through(self) -> None:
        tool_defs = [{"type": "function", "function": {"name": "search"}}]
        payload = LlmPayloadHandler.build_payload(
            [], tool_defs, temperature=1.0, max_tokens=10
        )
        assert payload["tools"] is tool_defs


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


class TestParseNonStreamResponse:
    def test_valid_bytes_parsed_into_response(self) -> None:
        content = orjson.dumps(
            {
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "ok"},
                        "finish_reason": "stop",
                    }
                ]
            }
        )
        result = LlmPayloadHandler.parse_non_stream_response(content)
        assert result.message == {"role": "assistant", "content": "ok"}
        assert result.finish_reason == "stop"

    def test_non_object_json_raises_value_error(self) -> None:
        content = orjson.dumps([1, 2, 3])
        with pytest.raises(ValueError, match="LLM response is not a JSON object: list"):
            LlmPayloadHandler.parse_non_stream_response(content)

    def test_on_usage_callback_forwarded(self) -> None:
        content = orjson.dumps(
            {
                "choices": [
                    {"message": {"role": "assistant"}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2},
            }
        )
        seen: list[tuple[int, int]] = []
        LlmPayloadHandler.parse_non_stream_response(
            content, on_usage=lambda p, c: seen.append((p, c))
        )
        assert seen == [(1, 2)]
