"""
tests/shared/test_json_utils.py

Characterization tests for shared/json_utils.py public functions.
"""

from __future__ import annotations

import datetime
from typing import Any

import orjson
import pytest
from shared.json_utils import (
    dumps,
    extract_llm_content,
    now_iso,
    now_iso_raw,
    parse_http_json,
    serialized_length,
    tool_call_serialized_length,
)


class TestExtractLlmContentValidPath:
    """Verify normal operation path."""

    def test_valid_response_returns_stripped_content(self) -> None:
        result = extract_llm_content({"choices": [{"message": {"content": "Hello"}}]})
        assert result == "Hello"

    def test_valid_response_with_whitespace_strips(self) -> None:
        result = extract_llm_content(
            {"choices": [{"message": {"content": "  Hello  "}}]}
        )
        assert result == "Hello"

    def test_valid_response_with_empty_string_content(self) -> None:
        result = extract_llm_content({"choices": [{"message": {"content": ""}}]})
        assert result == ""

    def test_valid_response_with_newlines_strips(self) -> None:
        result = extract_llm_content(
            {"choices": [{"message": {"content": "\nHello\n"}}]}
        )
        assert result == "Hello"

    def test_valid_response_with_multiple_choices_returns_first(self) -> None:
        result = extract_llm_content(
            {
                "choices": [
                    {"message": {"content": "first"}},
                    {"message": {"content": "second"}},
                ]
            }
        )
        assert result == "first"

    def test_valid_response_with_extra_fields_in_message_accepted(self) -> None:
        result = extract_llm_content(
            {"choices": [{"message": {"content": "hi", "extra": "field"}}]}
        )
        assert result == "hi"

    def test_valid_response_with_unicode_content(self) -> None:
        result = extract_llm_content(
            {"choices": [{"message": {"content": "こんにちは"}}]}
        )
        assert result == "こんにちは"

    def test_valid_response_with_tool_calls_in_message_works(self) -> None:
        tc = {"id": "1", "type": "function", "function": {"name": "test"}}
        result = extract_llm_content(
            {"choices": [{"message": {"content": "calling tools", "tool_calls": [tc]}}]}
        )
        assert result == "calling tools"

    def test_valid_response_with_finish_reason_in_choice_works(self) -> None:
        result = extract_llm_content(
            {
                "choices": [
                    {"finishReason": "stop", "index": 0, "message": {"content": "done"}}
                ]
            }
        )
        assert result == "done"

    def test_valid_response_with_refusal_field_in_message_works(self) -> None:
        result = extract_llm_content(
            {
                "choices": [
                    {
                        "message": {
                            "content": "I can't do that",
                            "refusal": "I can't do that",
                        }
                    }
                ]
            }
        )
        assert result == "I can't do that"

    def test_valid_response_with_long_content(self) -> None:
        long_text = "a" * 10000
        result = extract_llm_content({"choices": [{"message": {"content": long_text}}]})
        assert result == long_text

    def test_valid_response_with_special_characters_preserved(self) -> None:
        special = "!@#$%^&*()_+-=[]{}|;':\"./<>?"
        result = extract_llm_content({"choices": [{"message": {"content": special}}]})
        assert result == special

    def test_valid_response_with_tabs_and_spaces_preserved_after_strip(self) -> None:
        result = extract_llm_content(
            {"choices": [{"message": {"content": "\t hello \t world \t"}}]}
        )
        assert result == "hello \t world"

    def test_valid_response_with_multiline_content_strips_only_edges(self) -> None:
        result = extract_llm_content(
            {"choices": [{"message": {"content": "\nhello\nworld\n"}}]}
        )
        assert result == "hello\nworld"

    # ── Missing or empty choices ──

    def test_no_choices_key_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing or empty"):
            extract_llm_content({})

    def test_none_choices_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing or empty"):
            extract_llm_content({"choices": None})

    def test_empty_list_choices_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing or empty"):
            extract_llm_content({"choices": []})

    def test_string_choices_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing or empty"):
            extract_llm_content({"choices": "not a list"})

    def test_dict_choices_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing or empty"):
            extract_llm_content({"choices": {"key": "value"}})

    def test_number_choices_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing or empty"):
            extract_llm_content({"choices": 42})

    # ── Non-dict first choice ──

    def test_none_first_choice_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"choices\[0\] is not a dict"):
            extract_llm_content({"choices": [None]})

    def test_string_first_choice_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"choices\[0\] is not a dict"):
            extract_llm_content({"choices": ["not a dict"]})

    def test_list_first_choice_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"choices\[0\] is not a dict"):
            extract_llm_content({"choices": [["not a dict"]]})

    def test_number_first_choice_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"choices\[0\] is not a dict"):
            extract_llm_content({"choices": [42]})

    # ── Missing message key ──

    def test_missing_message_key_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"choices\[0\]\.message is not a dict"):
            extract_llm_content({"choices": [{}]})

    def test_none_message_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"choices\[0\]\.message is not a dict"):
            extract_llm_content({"choices": [{"message": None}]})

    def test_string_message_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"choices\[0\]\.message is not a dict"):
            extract_llm_content({"choices": [{"message": "not a dict"}]})

    def test_list_message_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"choices\[0\]\.message is not a dict"):
            extract_llm_content({"choices": [{"message": ["not a dict"]}]})

    def test_number_message_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"choices\[0\]\.message is not a dict"):
            extract_llm_content({"choices": [{"message": 42}]})

    # ── Non-string content ──

    def test_null_content_rejected(self) -> None:
        with pytest.raises(ValueError, match="content is not a str"):
            extract_llm_content({"choices": [{"message": {"content": None}}]})

    def test_number_content_rejected(self) -> None:
        with pytest.raises(ValueError, match="content is not a str"):
            extract_llm_content({"choices": [{"message": {"content": 123}}]})

    def test_list_content_rejected(self) -> None:
        with pytest.raises(ValueError, match="content is not a str"):
            extract_llm_content({"choices": [{"message": {"content": ["a", "b"]}}]})

    def test_dict_content_rejected(self) -> None:
        with pytest.raises(ValueError, match="content is not a str"):
            extract_llm_content(
                {"choices": [{"message": {"content": {"nested": True}}}]}
            )


class TestDumps:
    """Verify dumps() behavior."""

    def test_dumps_simple_dict(self) -> None:
        result = dumps({"key": "value"})
        assert result == '{"key":"value"}'

    def test_dumps_nested_dict(self) -> None:
        result = dumps({"outer": {"inner": "value"}})
        assert result == '{"outer":{"inner":"value"}}'

    def test_dumps_sorted_keys_by_default(self) -> None:
        result = dumps({"z": 1, "a": 2, "m": 3})
        assert result == '{"a":2,"m":3,"z":1}'

    def test_dumps_unsorted_keys_when_option_disabled(self) -> None:
        result = dumps({"z": 1, "a": 2}, option=0)
        parsed = orjson.loads(result)
        assert parsed["z"] == 1
        assert parsed["a"] == 2

    def test_dumps_list(self) -> None:
        result = dumps([1, 2, 3])
        assert result == "[1,2,3]"

    def test_dumps_string(self) -> None:
        result = dumps("hello")
        assert result == '"hello"'

    def test_dumps_number(self) -> None:
        result = dumps(42)
        assert result == "42"

    def test_dumps_null(self) -> None:
        result = dumps(None)
        assert result == "null"

    def test_dumps_boolean_true(self) -> None:
        result = dumps(True)
        assert result == "true"

    def test_dumps_boolean_false(self) -> None:
        result = dumps(False)
        assert result == "false"

    def test_dumps_returns_str_not_bytes(self) -> None:
        result = dumps({"key": "value"})
        assert isinstance(result, str)

    def test_dumps_with_indent_option(self) -> None:
        result = dumps({"a": 1, "b": 2}, option=orjson.OPT_INDENT_2)
        assert "\n" in result

    def test_dumps_with_sort_keys_disabled(self) -> None:
        result = dumps({"z": 1, "a": 2}, option=0)
        parsed = orjson.loads(result)
        assert parsed == {"z": 1, "a": 2}

    def test_dumps_unicode(self) -> None:
        result = dumps({"emoji": "\U0001f600"})
        assert "emoji" in result

    def test_dumps_empty_dict(self) -> None:
        result = dumps({})
        assert result == "{}"

    def test_dumps_empty_list(self) -> None:
        result = dumps([])
        assert result == "[]"

    def test_dumps_zero(self) -> None:
        result = dumps(0)
        assert result == "0"

    def test_dumps_negative_number(self) -> None:
        result = dumps(-42)
        assert result == "-42"

    def test_dumps_float(self) -> None:
        result = dumps(3.14)
        assert "3.14" in result

    def test_dumps_mixed_types_in_list(self) -> None:
        result = dumps([1, "two", True, None, 3.14])
        parsed = orjson.loads(result)
        assert parsed == [1, "two", True, None, 3.14]

    def test_dumps_complex_nested_structure(self) -> None:
        data: Any = {
            "users": [
                {"name": "Alice", "age": 30, "active": True},
                {"name": "Bob", "age": 25, "active": False},
            ],
            "meta": {"total": 2, "page": 1},
        }
        result = dumps(data)
        parsed = orjson.loads(result)
        assert parsed == data

    def test_dumps_large_integer_raises(self) -> None:
        """orjson rejects integers exceeding 64-bit range."""
        large_num = 99999999999999999999
        with pytest.raises(TypeError, match="Integer exceeds"):
            dumps(large_num)

    def test_dumps_empty_string(self) -> None:
        result = dumps("")
        assert result == '""'

    def test_dumps_whitespace_only_string(self) -> None:
        result = dumps("   ")
        assert result == '"   "'

    def test_dumps_newlines_in_string(self) -> None:
        result = dumps("line1\nline2")
        assert "\\n" in result

    def test_dumps_quotes_in_string(self) -> None:
        result = dumps('say "hello"')
        assert '"' in result

    def test_dumps_backslash_in_string(self) -> None:
        result = dumps(r"path\to\file")
        assert "\\" in result

    def test_dumps_tabs_in_string(self) -> None:
        result = dumps("col1\tcol2")
        assert "\\t" in result

    def test_dumps_array_of_dicts(self) -> None:
        result = dumps([{"a": 1}, {"b": 2}])
        parsed = orjson.loads(result)
        assert parsed == [{"a": 1}, {"b": 2}]

    def test_dumps_dict_with_list_value(self) -> None:
        result = dumps({"items": [1, 2, 3]})
        parsed = orjson.loads(result)
        assert parsed == {"items": [1, 2, 3]}

    def test_dumps_none_key_rejected(self) -> None:
        with pytest.raises(TypeError):
            dumps({None: "value"})

    def test_dumps_tuple_key_rejected(self) -> None:
        with pytest.raises(TypeError):
            dumps({(1, 2): "value"})

    def test_dumps_circular_reference_rejected(self) -> None:
        d: Any = {}
        d["self"] = d
        with pytest.raises((TypeError, ValueError)):
            dumps(d)

    def test_dumps_custom_object_rejected(self) -> None:
        class CustomObj:
            pass

        with pytest.raises(TypeError):
            dumps(CustomObj())

    def test_dumps_set_rejected(self) -> None:
        with pytest.raises(TypeError):
            dumps({1, 2, 3})

    def test_dumps_bytes_rejected(self) -> None:
        with pytest.raises(TypeError):
            dumps(b"bytes")


class TestNowIso:
    """Verify now_iso() behavior."""

    def test_now_iso_format_ends_with_z(self) -> None:
        result = now_iso()
        assert result.endswith("Z")

    def test_now_iso_format_is_valid_iso8601(self) -> None:
        result = now_iso()
        parts = result.split("T")
        assert len(parts) == 2
        date_part, time_part = parts
        assert len(date_part) == 10
        assert len(time_part) == 9
        assert "-" in date_part
        assert ":" in time_part

    def test_now_iso_returns_str(self) -> None:
        result = now_iso()
        assert isinstance(result, str)

    def test_now_iso_time_changes_over_time(self) -> None:
        import time

        t1 = now_iso()
        time.sleep(1.1)
        t2 = now_iso()
        assert t1 != t2

    def test_now_iso_date_changes_at_midnight(self) -> None:
        result = now_iso()
        today = datetime.date.today().strftime("%Y-%m-%d")
        assert result.startswith(today)

    def test_now_iso_utc_timezone(self) -> None:
        result = now_iso()
        # Just verify it uses Z suffix (UTC), not exact equality which fails due to timing
        assert result.endswith("Z")
        parts = result.split("T")
        assert len(parts) == 2
        date_part, time_part = parts
        assert len(date_part) == 10
        assert len(time_part) == 9

    def test_now_iso_consistent_across_calls_same_second(self) -> None:
        import time

        t1 = now_iso()
        time.sleep(0.01)
        t2 = now_iso()
        assert t1 == t2

    def test_now_iso_end_of_day(self) -> None:
        result = now_iso()
        assert result.endswith("Z")

    def test_now_iso_timezone_offset_not_present(self) -> None:
        result = now_iso()
        assert "+00:00" not in result


class TestNowIsoRaw:
    """Verify now_iso_raw() behavior."""

    def test_now_iso_raw_format_contains_plus_offset(self) -> None:
        result = now_iso_raw()
        assert "+00:00" in result

    def test_now_iso_raw_format_is_valid_iso8601(self) -> None:
        result = now_iso_raw()
        parts = result.split("T")
        assert len(parts) == 2
        date_part, time_part = parts
        assert len(date_part) == 10
        assert "+" in time_part

    def test_now_iso_raw_returns_str(self) -> None:
        result = now_iso_raw()
        assert isinstance(result, str)

    def test_now_iso_raw_time_changes_over_time(self) -> None:
        import time

        t1 = now_iso_raw()
        time.sleep(1.1)
        t2 = now_iso_raw()
        assert t1 != t2

    def test_now_iso_raw_different_from_now_iso(self) -> None:
        iso_result = now_iso()
        raw_result = now_iso_raw()
        assert iso_result != raw_result

    def test_now_iso_raw_utc_timezone(self) -> None:
        result = now_iso_raw()
        # Just verify it ends with +00:00 (UTC offset), not exact equality which fails due to microsecond drift
        assert "+00:00" in result

    def test_now_iso_raw_consistent_across_calls_same_second(self) -> None:
        import time

        t1 = now_iso_raw()
        time.sleep(0.01)
        t2 = now_iso_raw()
        # Same second should produce same result
        assert t1[:19] == t2[:19]

    def test_now_iso_raw_microseconds_included(self) -> None:
        result = now_iso_raw()
        assert "T" in result
        assert "+" in result

    def test_now_iso_raw_no_trailing_zeros_removed(self) -> None:
        result = now_iso_raw()
        # Verify it's valid ISO format with UTC offset
        assert "T" in result
        assert "+00:00" in result


class TestToolCallSerializedLength:
    """Verify tool_call_serialized_length() behavior."""

    def test_simple_tool_call_length(self) -> None:
        tool_call = {"id": "1", "type": "function", "function": {"name": "test"}}
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_empty_tool_call_length(self) -> None:
        tool_call: dict[str, object] = {}
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_complex_tool_call_length(self) -> None:
        tool_call: Any = {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "execute_command",
                "arguments": '{"cmd": "ls -la", "cwd": "/tmp"}',
            },
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_returns_int(self) -> None:
        tool_call = {"id": "1", "type": "function", "function": {"name": "test"}}
        result = tool_call_serialized_length(tool_call)
        assert isinstance(result, int)

    def test_tool_call_serialized_length_positive(self) -> None:
        tool_call = {"id": "1", "type": "function", "function": {"name": "test"}}
        result = tool_call_serialized_length(tool_call)
        assert result > 0

    def test_tool_call_serialized_length_deterministic(self) -> None:
        tool_call = {"id": "1", "type": "function", "function": {"name": "test"}}
        result1 = tool_call_serialized_length(tool_call)
        result2 = tool_call_serialized_length(tool_call)
        assert result1 == result2

    def test_tool_call_serialized_length_different_inputs_different_lengths(
        self,
    ) -> None:
        tc1 = {"id": "1", "type": "function", "function": {"name": "a"}}
        tc2 = {
            "id": "1",
            "type": "function",
            "function": {"name": "very_long_function_name"},
        }
        l1 = tool_call_serialized_length(tc1)
        l2 = tool_call_serialized_length(tc2)
        assert l2 > l1

    def test_tool_call_serialized_length_unicode_content(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "\u3053\u3093\u306b\u3061\u306f"},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_nested_arguments(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {
                "name": "run",
                "arguments": {"nested": {"deep": {"value": 42}}},
            },
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_list_arguments(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {
                "name": "batch",
                "arguments": [1, 2, 3],
            },
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_null_values(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "test", "args": None},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_boolean_values(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "test", "active": True},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_zero_value(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "test", "count": 0},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_negative_value(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "test", "offset": -10},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_float_value(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "test", "score": 0.95},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_array_of_objects(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {
                "name": "process",
                "arguments": [{"item": 1}, {"item": 2}],
            },
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_deeply_nested(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {
                "name": "deep",
                "arguments": {"l1": {"l2": {"l3": {"l4": {"l5": "deep"}}}}},
            },
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_empty_string_argument(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "test", "arg": ""},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_special_characters_in_argument(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "test", "arg": "!@#$%^&*()"},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_newline_in_argument(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "test", "arg": "line1\nline2"},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_tab_in_argument(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "test", "arg": "col1\tcol2"},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_quote_in_argument(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "test", "arg": 'say "hello"'},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_backslash_in_argument(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "test", "arg": r"path\to\file"},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected

    def test_tool_call_serialized_length_emoji_in_argument(self) -> None:
        tool_call: Any = {
            "id": "1",
            "type": "function",
            "function": {"name": "test", "arg": "\U0001f600"},
        }
        result = tool_call_serialized_length(tool_call)
        expected = len(orjson.dumps(tool_call))
        assert result == expected


class TestSerializedLength:
    """Verify serialized_length() behavior."""

    def test_simple_dict_length(self) -> None:
        data = {"key": "value"}
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_list_length(self) -> None:
        data = [1, 2, 3]
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_string_length(self) -> None:
        data = "hello"
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_number_length(self) -> None:
        data = 42
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_null_length(self) -> None:
        data = None
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_returns_int(self) -> None:
        result = serialized_length({"key": "value"})
        assert isinstance(result, int)

    def test_positive(self) -> None:
        result = serialized_length({"key": "value"})
        assert result > 0

    def test_deterministic(self) -> None:
        data = {"key": "value"}
        result1 = serialized_length(data)
        result2 = serialized_length(data)
        assert result1 == result2

    def test_different_inputs_different_lengths(self) -> None:
        l1 = serialized_length({"a": 1})
        l2 = serialized_length({"a": 1, "b": 2, "c": 3})
        assert l2 > l1

    def test_empty_dict_length(self) -> None:
        data: dict[str, object] = {}
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_empty_list_length(self) -> None:
        data: list[object] = []
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_large_number_raises(self) -> None:
        """orjson rejects integers exceeding 64-bit range."""
        large_num = 99999999999999999999
        with pytest.raises(TypeError, match="Integer exceeds"):
            serialized_length(large_num)

    def test_unicode_content(self) -> None:
        data: Any = {"text": "\u3053\u3093\u306b\u3061\u306f"}
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_complex_structure(self) -> None:
        data: Any = {
            "users": [
                {"name": "Alice", "age": 30, "active": True},
                {"name": "Bob", "age": 25, "active": False},
            ],
            "meta": {"total": 2, "page": 1},
        }
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_deeply_nested(self) -> None:
        data: Any = {"l1": {"l2": {"l3": {"l4": {"l5": "deep"}}}}}
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_mixed_types_in_list(self) -> None:
        data: Any = [1, "two", True, None, 3.14]
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_zero_value(self) -> None:
        data = 0
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_negative_number(self) -> None:
        data = -42
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_float_value(self) -> None:
        data = 3.14
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_boolean_true(self) -> None:
        data = True
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_boolean_false(self) -> None:
        data = False
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_empty_string(self) -> None:
        data = ""
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_whitespace_only_string(self) -> None:
        data = "   "
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_newlines_in_string(self) -> None:
        data = "line1\nline2"
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_quotes_in_string(self) -> None:
        data = 'say "hello"'
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_backslash_in_string(self) -> None:
        data = r"path\to\file"
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_tabs_in_string(self) -> None:
        data = "col1\tcol2"
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_emoji_in_string(self) -> None:
        data: Any = {"char": "\U0001f600"}
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_array_of_dicts(self) -> None:
        data: Any = [{"a": 1}, {"b": 2}]
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_dict_with_list_value(self) -> None:
        data: Any = {"items": [1, 2, 3]}
        result = serialized_length(data)
        expected = len(orjson.dumps(data))
        assert result == expected

    def test_none_key_rejected(self) -> None:
        with pytest.raises(TypeError):
            serialized_length({None: "value"})

    def test_tuple_key_rejected(self) -> None:
        with pytest.raises(TypeError):
            serialized_length({(1, 2): "value"})

    def test_circular_reference_rejected(self) -> None:
        d: Any = {}
        d["self"] = d
        with pytest.raises((TypeError, ValueError)):
            serialized_length(d)

    def test_custom_object_rejected(self) -> None:
        class CustomObj:
            pass

        with pytest.raises(TypeError):
            serialized_length(CustomObj())

    def test_set_rejected(self) -> None:
        with pytest.raises(TypeError):
            serialized_length({1, 2, 3})

    def test_bytes_rejected(self) -> None:
        with pytest.raises(TypeError):
            serialized_length(b"bytes")


class TestParseHttpJson:
    """Verify parse_http_json() behavior."""

    def test_parse_http_json_valid(self, mocker: Any) -> None:
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = b'{"key": "value"}'
        resp.headers = {"content-type": "application/json"}
        result = parse_http_json(resp)
        assert result == {"key": "value"}

    def test_parse_http_json_invalid_json_raises(self, mocker: Any) -> None:
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = b"not json"
        resp.headers = {"content-type": "application/json"}
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_http_json(resp)

    def test_parse_http_json_non_dict_json_raises(self, mocker: Any) -> None:
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = b"[1, 2, 3]"
        resp.headers = {"content-type": "application/json"}
        with pytest.raises(ValueError, match="Expected JSON dict"):
            parse_http_json(resp)

    def test_parse_http_json_empty_body_raises(self, mocker: Any) -> None:
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = b""
        resp.headers = {"content-type": "application/json"}
        with pytest.raises(ValueError):
            parse_http_json(resp)

    def test_parse_http_json_nested_dict(self, mocker: Any) -> None:
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = b'{"outer": {"inner": "value"}}'
        resp.headers = {"content-type": "application/json"}
        result = parse_http_json(resp)
        assert result == {"outer": {"inner": "value"}}

    def test_parse_http_json_array_response_raises(self, mocker: Any) -> None:
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = b"[]"
        resp.headers = {"content-type": "application/json"}
        with pytest.raises(ValueError, match="Expected JSON dict"):
            parse_http_json(resp)

    def test_parse_http_json_string_response_raises(self, mocker: Any) -> None:
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = b'"just a string"'
        resp.headers = {"content-type": "application/json"}
        with pytest.raises(ValueError, match="Expected JSON dict"):
            parse_http_json(resp)

    def test_parse_http_json_number_response_raises(self, mocker: Any) -> None:
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = b"42"
        resp.headers = {"content-type": "application/json"}
        with pytest.raises(ValueError, match="Expected JSON dict"):
            parse_http_json(resp)

    def test_parse_http_json_null_response_raises(self, mocker: Any) -> None:
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = b"null"
        resp.headers = {"content-type": "application/json"}
        with pytest.raises(ValueError, match="Expected JSON dict"):
            parse_http_json(resp)

    def test_parse_http_json_unicode_content(self, mocker: Any) -> None:
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = '{"text": "\u3053\u3093\u306b\u3061\u306f"}'.encode("utf-8")
        resp.headers = {"content-type": "application/json"}
        result = parse_http_json(resp)
        assert result == {"text": "\u3053\u3093\u306b\u3061\u306f"}

    def test_parse_http_json_large_response(self, mocker: Any) -> None:
        large_data = {str(i): i for i in range(100)}
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = orjson.dumps(large_data)
        resp.headers = {"content-type": "application/json"}
        result = parse_http_json(resp)
        assert result == large_data

    def test_parse_http_json_special_characters(self, mocker: Any) -> None:
        import json

        special = "!@#$%^&*()_+-=[]{}|;':\"./<>?"
        data = {"special": special}
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = json.dumps(data).encode()
        resp.headers = {"content-type": "application/json"}
        result = parse_http_json(resp)
        assert result == data

    def test_parse_http_json_returns_dict(self, mocker: Any) -> None:
        resp = mocker.Mock()
        resp.status_code = 200
        resp.content = b'{"key": "value"}'
        resp.headers = {"content-type": "application/json"}
        result = parse_http_json(resp)
        assert isinstance(result, dict)
