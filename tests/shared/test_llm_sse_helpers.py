"""
tests/test_llm_sse_helpers.py

Unit tests for LlmSseHelpers static methods.
No HTTP dependencies — pure unit tests.
"""

from __future__ import annotations

from shared.llm_sse_helpers import LlmSseHelpers
from shared.types import AccumulatedToolCall, ToolCallDelta


class TestMergeToolCallDelta:
    def test_first_delta_creates_entry(self) -> None:
        tool_calls_map: dict[int, object] = {}
        delta: ToolCallDelta = {"index": 0, "id": "call_1"}
        LlmSseHelpers.merge_tool_call_delta(tool_calls_map, delta)
        assert len(tool_calls_map) == 1
        assert tool_calls_map[0]["id"] == "call_1"

    def test_second_delta_appends_arguments(self) -> None:
        tool_calls_map: dict[int, AccumulatedToolCall] = {}
        delta1: ToolCallDelta = {"index": 0, "id": "call_1"}
        delta2: ToolCallDelta = {"index": 0, "function": {"arguments": '{"a"'}}
        delta3: ToolCallDelta = {"index": 0, "function": {"arguments": '":1}'}}
        LlmSseHelpers.merge_tool_call_delta(tool_calls_map, delta1)
        LlmSseHelpers.merge_tool_call_delta(tool_calls_map, delta2)
        LlmSseHelpers.merge_tool_call_delta(tool_calls_map, delta3)
        assert tool_calls_map[0]["function"]["arguments"] == '{"a"":1}'

    def test_name_accumulation(self) -> None:
        tool_calls_map: dict[int, object] = {}
        delta1: ToolCallDelta = {"index": 0, "function": {"name": "calc"}}
        delta2: ToolCallDelta = {"index": 0, "function": {"name": "_helper"}}
        LlmSseHelpers.merge_tool_call_delta(tool_calls_map, delta1)
        LlmSseHelpers.merge_tool_call_delta(tool_calls_map, delta2)
        assert tool_calls_map[0]["function"]["name"] == "calc_helper"

    def test_different_indices_are_separate_entries(self) -> None:
        tool_calls_map: dict[int, object] = {}
        delta1: ToolCallDelta = {"index": 0, "id": "call_1"}
        delta2: ToolCallDelta = {"index": 1, "id": "call_2"}
        LlmSseHelpers.merge_tool_call_delta(tool_calls_map, delta1)
        LlmSseHelpers.merge_tool_call_delta(tool_calls_map, delta2)
        assert len(tool_calls_map) == 2
        assert tool_calls_map[0]["id"] == "call_1"
        assert tool_calls_map[1]["id"] == "call_2"

    def test_empty_index_defaults_to_zero(self) -> None:
        tool_calls_map: dict[int, object] = {}
        delta: ToolCallDelta = {"id": "call_1"}
        LlmSseHelpers.merge_tool_call_delta(tool_calls_map, delta)
        assert 0 in tool_calls_map
        assert tool_calls_map[0]["id"] == "call_1"

    def test_null_function_is_noop(self) -> None:
        tool_calls_map: dict[int, object] = {}
        delta: ToolCallDelta = {"index": 0, "id": "call_1", "function": None}
        LlmSseHelpers.merge_tool_call_delta(tool_calls_map, delta)
        assert tool_calls_map[0]["id"] == "call_1"
        assert tool_calls_map[0]["function"]["name"] == ""
        assert tool_calls_map[0]["function"]["arguments"] == ""


class TestBuildStreamResponse:
    def test_text_only_response(self) -> None:
        response = LlmSseHelpers.build_stream_response(["hello"], {}, "stop")
        assert response["choices"][0]["message"]["content"] == "hello"
        assert response["choices"][0]["finish_reason"] == "stop"
        assert "tool_calls" not in response["choices"][0]["message"]

    def test_tool_call_response(self) -> None:
        tool_calls_map: dict[int, object] = {
            0: {
                "id": "call_1",
                "type": "function",
                "function": {"name": "calc", "arguments": '{"x":1}'},
            }
        }
        response = LlmSseHelpers.build_stream_response([], tool_calls_map, "tool_calls")
        assert response["choices"][0]["message"]["content"] == ""
        assert response["choices"][0]["finish_reason"] == "tool_calls"
        assert len(response["choices"][0]["message"]["tool_calls"]) == 1
        assert response["choices"][0]["message"]["tool_calls"][0]["id"] == "call_1"

    def test_multiple_tool_calls_sorted_by_index(self) -> None:
        tool_calls_map: dict[int, object] = {
            1: {
                "id": "call_2",
                "type": "function",
                "function": {"name": "b", "arguments": ""},
            },
            0: {
                "id": "call_1",
                "type": "function",
                "function": {"name": "a", "arguments": ""},
            },
        }
        response = LlmSseHelpers.build_stream_response([], tool_calls_map, "tool_calls")
        assert response["choices"][0]["message"]["tool_calls"][0]["id"] == "call_1"
        assert response["choices"][0]["message"]["tool_calls"][1]["id"] == "call_2"

    def test_none_finish_reason_preserved(self) -> None:
        response = LlmSseHelpers.build_stream_response(["text"], {}, None)
        assert response["choices"][0]["finish_reason"] is None

    def test_empty_content_parts_yields_empty_string(self) -> None:
        response = LlmSseHelpers.build_stream_response([], {}, "stop")
        assert response["choices"][0]["message"]["content"] == ""


class TestProcessSseChunk:
    def test_content_delta_appended(self) -> None:
        content_parts: list[str] = []
        finish_reason = LlmSseHelpers.process_sse_chunk(
            {"choices": [{"delta": {"content": "hi"}, "finish_reason": None}]},
            content_parts,
            {},
        )
        assert finish_reason is None
        assert content_parts == ["hi"]

    def test_finish_reason_returned(self) -> None:
        finish_reason = LlmSseHelpers.process_sse_chunk(
            {"choices": [{"delta": {}, "finish_reason": "stop"}]},
            [],
            {},
        )
        assert finish_reason == "stop"

    def test_on_token_callback_called(self) -> None:
        tokens: list[str] = []
        LlmSseHelpers.process_sse_chunk(
            {"choices": [{"delta": {"content": "x"}, "finish_reason": None}]},
            [],
            {},
            on_token=tokens.append,
        )
        assert tokens == ["x"]

    def test_on_token_not_called_when_empty_content(self) -> None:
        tokens: list[str] = []
        LlmSseHelpers.process_sse_chunk(
            {"choices": [{"delta": {}, "finish_reason": None}]},
            [],
            {},
            on_token=tokens.append,
        )
        assert tokens == []

    def test_tool_call_delta_processed(self) -> None:
        tool_calls_map: dict[int, object] = {}
        LlmSseHelpers.process_sse_chunk(
            {
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": "call_1",
                                    "function": {"name": "test"},
                                }
                            ]
                        },
                        "finish_reason": None,
                    }
                ]
            },
            [],
            tool_calls_map,
        )
        assert len(tool_calls_map) == 1
        assert tool_calls_map[0]["id"] == "call_1"
        assert tool_calls_map[0]["function"]["name"] == "test"

    def test_missing_choices_returns_none(self) -> None:
        result = LlmSseHelpers.process_sse_chunk({}, [], {})
        assert result is None

    def test_empty_choices_returns_none(self) -> None:
        result = LlmSseHelpers.process_sse_chunk({"choices": []}, [], {})
        assert result is None

    def test_null_finish_reason_becomes_none(self) -> None:
        result = LlmSseHelpers.process_sse_chunk(
            {"choices": [{"delta": {}, "finish_reason": None}]},
            [],
            {},
        )
        assert result is None


class TestProcessSsePayloads:
    def test_single_payload_processed(self) -> None:
        payloads = ['{"choices":[{"delta":{"content":"hi"},"finish_reason":null}]}']
        content_parts: list[str] = []
        finish_reason = LlmSseHelpers.process_sse_payloads(payloads, content_parts, {})
        assert content_parts == ["hi"]
        assert finish_reason is None

    def test_multiple_payloads_return_last_finish_reason(self) -> None:
        payloads = [
            '{"choices":[{"delta":{"content":"a"},"finish_reason":null}]}',
            '{"choices":[{"delta":{},"finish_reason":"stop"}]}',
        ]
        content_parts: list[str] = []
        finish_reason = LlmSseHelpers.process_sse_payloads(payloads, content_parts, {})
        assert content_parts == ["a"]
        assert finish_reason == "stop"

    def test_malformed_json_skipped(self) -> None:
        payloads = ["{bad json}", '{"choices":[{"delta":{},"finish_reason":"stop"}]}']
        content_parts: list[str] = []
        finish_reason = LlmSseHelpers.process_sse_payloads(payloads, content_parts, {})
        assert finish_reason == "stop"

    def test_usage_callback_fired(self) -> None:
        usages: list[tuple[int, int]] = []
        payloads = [
            '{"choices":[{"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":10,"completion_tokens":5}}'
        ]
        LlmSseHelpers.process_sse_payloads(
            payloads, [], {}, on_usage=lambda pt, ct: usages.append((pt, ct))
        )
        assert usages == [(10, 5)]

    def test_empty_payloads_list_returns_none(self) -> None:
        result = LlmSseHelpers.process_sse_payloads([], [], {})
        assert result is None


class TestParseUsage:
    def test_valid_usage_returned(self) -> None:
        data = {"usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        usage = LlmSseHelpers.parse_usage(data)
        assert usage is not None
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5

    def test_missing_usage_returns_none(self) -> None:
        result = LlmSseHelpers.parse_usage({})
        assert result is None

    def test_non_dict_usage_returns_none(self) -> None:
        result = LlmSseHelpers.parse_usage({"usage": "invalid"})
        assert result is None

    def test_non_int_prompt_tokens_returns_none(self) -> None:
        result = LlmSseHelpers.parse_usage(
            {"usage": {"prompt_tokens": "10", "completion_tokens": 5}}
        )
        assert result is None

    def test_usage_callback_fired(self) -> None:
        usages: list[tuple[int, int]] = []
        data = {"usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        LlmSseHelpers.parse_usage(data, on_usage=lambda pt, ct: usages.append((pt, ct)))
        assert usages == [(10, 5)]

    def test_zero_token_values_accepted(self) -> None:
        data = {"usage": {"prompt_tokens": 0, "completion_tokens": 0}}
        usage = LlmSseHelpers.parse_usage(data)
        assert usage is not None
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0


class TestAccumulateParseErrors:
    def test_accumulates_errors(self) -> None:
        from shared.sse_parser import RobustSSEParser

        parser = RobustSSEParser(malformed_retry=5, heartbeat_timeout=0.0)
        parser.stat_parse_errors = 3
        total = LlmSseHelpers.accumulate_parse_errors(parser, 5)
        assert total == 8
        assert parser.stat_parse_errors == 0

    def test_no_errors_to_accumulate(self) -> None:
        from shared.sse_parser import RobustSSEParser

        parser = RobustSSEParser(malformed_retry=5, heartbeat_timeout=0.0)
        parser.stat_parse_errors = 0
        total = LlmSseHelpers.accumulate_parse_errors(parser, 5)
        assert total == 5
        assert parser.stat_parse_errors == 0
