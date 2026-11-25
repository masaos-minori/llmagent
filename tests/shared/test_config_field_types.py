"""Tests for scripts/shared/config_field_types.py.

Pins the strict type rules both the startup builder and the reload path share
(REQ-001, AC-1), and pins that no raised message contains the configured value
(REQ-011).
"""

from __future__ import annotations

from typing import Any

import pytest
from shared.config_field_types import (
    RULE_BOOL,
    RULE_FLOAT,
    RULE_INT,
    RULE_MAPPING,
    RULE_NON_EMPTY,
    RULE_STR,
    RULE_STR_LIST,
    RULE_STR_MAPPING,
    ConfigFieldTypeError,
    FieldRule,
    apply_field_rule,
    reject_unknown_keys,
    strict_bool,
    strict_float,
    strict_int,
    strict_mapping,
    strict_str,
    strict_str_list,
    strict_str_mapping,
)

# A value that must never appear in a raised message.
SECRET = "hunter2-secret-value"


class SecretValue:
    """Wrong-typed value whose repr carries the secret, proving repr is never used."""

    def __repr__(self) -> str:
        return f"<{SECRET}>"


def _message(exc: ConfigFieldTypeError) -> str:
    return str(exc)


# --- FieldRule ---


class TestFieldRule:
    def test_rule_is_frozen(self) -> None:
        with pytest.raises(Exception):
            RULE_INT.name = "changed"

    def test_declared_type_is_exposed(self) -> None:
        assert RULE_INT.declared_type is int
        assert RULE_STR_LIST.declared_type is list


# --- strict_bool ---


class TestStrictBool:
    def test_bool_passes(self) -> None:
        assert strict_bool(True, "tool.serial_tool_calls") is True
        assert strict_bool(False, "tool.serial_tool_calls") is False

    @pytest.mark.parametrize("value", [1, 0, 1.0, "true", "false", None, [True]])
    def test_non_bool_raises(self, value: Any) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must be bool"):
            strict_bool(value, "tool.serial_tool_calls")

    def test_error_names_field_and_rule(self) -> None:
        with pytest.raises(ConfigFieldTypeError) as excinfo:
            strict_bool("true", "tool.serial_tool_calls")
        assert excinfo.value.field_path == "tool.serial_tool_calls"
        assert excinfo.value.rule == RULE_BOOL.name

    def test_message_excludes_the_value(self) -> None:
        with pytest.raises(ConfigFieldTypeError) as excinfo:
            strict_bool(SECRET, "llm.llm_url")
        assert SECRET not in _message(excinfo.value)


# --- strict_int ---


class TestStrictInt:
    def test_int_passes(self) -> None:
        assert strict_int(30, "llm.http_timeout") == 30
        assert strict_int(0, "llm.http_timeout") == 0
        assert strict_int(-1, "llm.http_timeout") == -1

    @pytest.mark.parametrize("value", [True, False, 1.5, "30", None, [30]])
    def test_bool_and_non_int_raise(self, value: Any) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must be int"):
            strict_int(value, "llm.http_timeout")

    def test_bool_is_rejected_although_it_is_an_int(self) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must be int, got bool"):
            strict_int(True, "memory.memory_max_pinned")

    def test_message_excludes_the_value(self) -> None:
        with pytest.raises(ConfigFieldTypeError) as excinfo:
            strict_int(SECRET, "llm.llm_max_tokens")
        assert SECRET not in _message(excinfo.value)


# --- strict_float ---


class TestStrictFloat:
    def test_float_passes(self) -> None:
        assert strict_float(0.7, "llm.llm_temperature") == 0.7

    def test_int_is_widened(self) -> None:
        result = strict_float(30, "llm.http_timeout")
        assert result == 30.0
        assert isinstance(result, float)

    @pytest.mark.parametrize("value", [True, False, "0.7", None, (0.7,)])
    def test_bool_and_non_number_raise(self, value: Any) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must be float"):
            strict_float(value, "llm.llm_temperature")

    def test_message_excludes_the_value(self) -> None:
        with pytest.raises(ConfigFieldTypeError) as excinfo:
            strict_float(SECRET, "llm.llm_retry_base_delay")
        assert SECRET not in _message(excinfo.value)


# --- strict_str ---


class TestStrictStr:
    def test_str_passes(self) -> None:
        assert (
            strict_str("https://example.test", "llm.llm_url") == "https://example.test"
        )

    @pytest.mark.parametrize("value", [7, 7.5, True, None, ["x"]])
    def test_non_str_raises(self, value: Any) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must be str"):
            strict_str(value, "llm.llm_url")

    @pytest.mark.parametrize("value", ["", " ", "\t", "\n"])
    def test_empty_or_whitespace_raises(self, value: str) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must not be empty"):
            strict_str(value, "memory.memory_embed_url")

    def test_allow_empty_accepts_an_empty_string(self) -> None:
        assert strict_str("", "llm.tokenize_url", allow_empty=True) == ""

    def test_allow_empty_still_rejects_whitespace_only(self) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must not be empty"):
            strict_str("   ", "llm.tokenize_url", allow_empty=True)

    def test_message_excludes_the_value(self) -> None:
        with pytest.raises(ConfigFieldTypeError) as excinfo:
            strict_str(SecretValue(), "memory.memory_embed_url")
        assert SECRET not in _message(excinfo.value)


# --- strict_str_list ---


class TestStrictStrList:
    def test_list_of_str_passes(self) -> None:
        assert strict_str_list(["a", "b"], "tool.allowed_tools") == ["a", "b"]

    def test_empty_list_raises_by_default(self) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must not be empty"):
            strict_str_list([], "tool.allowed_tools")

    def test_allow_empty_accepts_an_empty_list(self) -> None:
        assert strict_str_list([], "tool.plan_blocked_tools", allow_empty=True) == []

    @pytest.mark.parametrize("value", [("a",), "abc", 7, None, {"a": 1}])
    def test_non_list_raises_including_a_str(self, value: Any) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must be list"):
            strict_str_list(value, "tool.plan_blocked_tools")

    def test_a_str_is_not_split_into_characters(self) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must be list, got str"):
            strict_str_list("python", "mcp.server.cmd")

    def test_non_str_element_is_rejected_by_index(self) -> None:
        with pytest.raises(
            ConfigFieldTypeError, match=r"tool\.allowed_tools\[1\].*must be str"
        ):
            strict_str_list(["a", 7], "tool.allowed_tools")

    def test_empty_element_is_rejected_by_index(self) -> None:
        with pytest.raises(
            ConfigFieldTypeError, match=r"tool\.allowed_tools\[1\].*must not be empty"
        ):
            strict_str_list(["a", " "], "tool.allowed_tools")

    def test_allow_empty_leaves_element_emptiness_to_the_caller(self) -> None:
        # approval_shell_safe_prefixes skips its empty entries downstream
        # (tests/agent/test_tool_policy.py), so the primitive must not reject them.
        assert strict_str_list(
            ["", "   ", "ls"],
            "approval.approval_shell_safe_prefixes",
            allow_empty=True,
        ) == ["", "   ", "ls"]

    def test_message_excludes_the_value(self) -> None:
        with pytest.raises(ConfigFieldTypeError) as excinfo:
            strict_str_list([SecretValue()], "approval.approval_github_allowed_repos")
        assert SECRET not in _message(excinfo.value)

    def test_element_error_message_excludes_the_value(self) -> None:
        with pytest.raises(ConfigFieldTypeError) as excinfo:
            strict_str_list(["ok", SecretValue()], "approval.approval_protected_paths")
        assert SECRET not in _message(excinfo.value)


# --- strict_mapping and strict_str_mapping ---


class TestStrictMapping:
    def test_dict_of_mixed_values_passes(self) -> None:
        raw = {"retention_days": 30, "sensitive_fields": ["a"]}
        assert strict_mapping(raw, "diagnostics") == raw

    def test_empty_dict_raises_by_default(self) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must not be empty"):
            strict_mapping({}, "diagnostics")

    def test_allow_empty_accepts_an_empty_dict(self) -> None:
        assert strict_mapping({}, "diagnostics", allow_empty=True) == {}

    @pytest.mark.parametrize("value", [[], "x", 7, None])
    def test_non_dict_raises(self, value: Any) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must be dict"):
            strict_mapping(value, "diagnostics")


class TestStrictStrMapping:
    def test_str_to_str_passes(self) -> None:
        assert strict_str_mapping({"KEY": "v"}, "mcp.server.env") == {"KEY": "v"}

    def test_empty_mapping_raises_by_default(self) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must not be empty"):
            strict_str_mapping({}, "mcp.server.env")

    def test_allow_empty_accepts_an_empty_mapping(self) -> None:
        assert strict_str_mapping({}, "mcp.server.env", allow_empty=True) == {}

    @pytest.mark.parametrize("value", [[], "x", 7, None])
    def test_non_dict_raises(self, value: Any) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must be dict"):
            strict_str_mapping(value, "mcp.server.env")

    def test_non_str_value_is_rejected_naming_the_key(self) -> None:
        with pytest.raises(
            ConfigFieldTypeError, match=r"mcp\.server\.env\['KEY'\].*must be str"
        ) as excinfo:
            strict_str_mapping({"KEY": 7}, "mcp.server.env")
        assert SECRET not in _message(excinfo.value)

    def test_non_str_key_is_rejected(self) -> None:
        with pytest.raises(ConfigFieldTypeError, match="must be str"):
            strict_str_mapping({7: "v"}, "mcp.server.env")

    def test_message_excludes_the_value(self) -> None:
        with pytest.raises(ConfigFieldTypeError) as excinfo:
            strict_str_mapping({"TOKEN": SecretValue()}, "mcp.server.env")
        assert SECRET not in _message(excinfo.value)


# --- reject_unknown_keys ---


class TestRejectUnknownKeys:
    def test_declared_keys_pass(self) -> None:
        reject_unknown_keys({"cmd": ["x"], "env": {}}, ["cmd", "env"])

    def test_unknown_key_is_rejected_by_name(self) -> None:
        with pytest.raises(
            ConfigFieldTypeError, match="unknown config key 'enabled'"
        ) as excinfo:
            reject_unknown_keys({"enabled": True}, ["cmd", "env"], section="mcp.server")
        assert excinfo.value.rule == "unknown_key"
        assert excinfo.value.field_path == "mcp.server.enabled"

    def test_section_qualifies_the_message(self) -> None:
        with pytest.raises(ConfigFieldTypeError, match=r"in mcp\.server"):
            reject_unknown_keys({"auto_start": True}, ["cmd"], section="mcp.server")

    def test_message_excludes_the_value(self) -> None:
        with pytest.raises(ConfigFieldTypeError) as excinfo:
            reject_unknown_keys({"auth_token": SECRET}, ["cmd"])
        assert SECRET not in _message(excinfo.value)

    def test_error_is_a_value_error(self) -> None:
        assert issubclass(ConfigFieldTypeError, ValueError)


# --- message shape shared with the delegating callers ---


class TestMessageShape:
    @pytest.mark.parametrize(
        ("rule", "call"),
        [
            (RULE_BOOL, lambda: strict_bool("x", "f")),
            (RULE_INT, lambda: strict_int("x", "f")),
            (RULE_FLOAT, lambda: strict_float("x", "f")),
            (RULE_STR, lambda: strict_str(7, "f")),
            (RULE_STR_LIST, lambda: strict_str_list("x", "f")),
            (RULE_MAPPING, lambda: strict_mapping("x", "f")),
            (RULE_STR_MAPPING, lambda: strict_str_mapping("x", "f")),
        ],
    )
    def test_message_names_field_rule_and_received_type(
        self, rule: FieldRule, call: Any
    ) -> None:
        with pytest.raises(ConfigFieldTypeError) as excinfo:
            call()
        message = _message(excinfo.value)
        assert "config key 'f' must be" in message
        assert rule.type_label in message
        assert "got " in message


# --- apply_field_rule ---


class TestApplyFieldRule:
    """The registry's declared FieldRule is runnable as stored, so the reload path can
    validate a value before comparing it against the live one."""

    @pytest.mark.parametrize(
        ("rule", "value", "expected"),
        [
            (RULE_BOOL, False, False),
            (RULE_INT, 7, 7),
            (RULE_FLOAT, 1.5, 1.5),
            (RULE_STR, "read_file", "read_file"),
            (RULE_STR_LIST, ["read_file"], ["read_file"]),
            (RULE_MAPPING, {"retention_days": 30}, {"retention_days": 30}),
            (RULE_STR_MAPPING, {"a": "b"}, {"a": "b"}),
        ],
    )
    def test_returns_the_typed_value(
        self, rule: FieldRule, value: Any, expected: Any
    ) -> None:
        assert apply_field_rule(rule, value, "f") == expected

    @pytest.mark.parametrize(
        ("rule", "value"),
        [
            (RULE_BOOL, 1),
            (RULE_INT, "7"),
            (RULE_FLOAT, True),
            (RULE_STR, 7),
            (RULE_STR_LIST, "read_file"),
            (RULE_MAPPING, "x"),
            (RULE_STR_MAPPING, {"a": 1}),
        ],
    )
    def test_rejects_with_the_same_message_as_the_primitive(
        self, rule: FieldRule, value: Any
    ) -> None:
        direct_calls = {
            RULE_BOOL: lambda: strict_bool(value, "section.f"),
            RULE_INT: lambda: strict_int(value, "section.f"),
            RULE_FLOAT: lambda: strict_float(value, "section.f"),
            RULE_STR: lambda: strict_str(value, "section.f"),
            RULE_STR_LIST: lambda: strict_str_list(value, "section.f"),
            RULE_MAPPING: lambda: strict_mapping(value, "section.f"),
            RULE_STR_MAPPING: lambda: strict_str_mapping(value, "section.f"),
        }
        with pytest.raises(ConfigFieldTypeError) as excinfo:
            apply_field_rule(rule, value, "section.f")
        with pytest.raises(ConfigFieldTypeError) as direct:
            direct_calls[rule]()
        # The message, path, and rule are exactly what the primitive itself raises,
        # including the item-key path a mapping rule produces.
        assert _message(excinfo.value) == _message(direct.value)
        assert excinfo.value.field_path == direct.value.field_path
        assert excinfo.value.rule == direct.value.rule

    @pytest.mark.parametrize(
        ("rule", "empty"),
        [
            (RULE_STR, ""),
            (RULE_STR_LIST, []),
            (RULE_MAPPING, {}),
            (RULE_STR_MAPPING, {}),
        ],
    )
    def test_allow_empty_is_passed_through(self, rule: FieldRule, empty: Any) -> None:
        assert apply_field_rule(rule, empty, "f", allow_empty=True) == empty
        with pytest.raises(ConfigFieldTypeError, match="must not be empty"):
            apply_field_rule(rule, empty, "f")

    def test_rule_without_a_primitive_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match="no strict primitive registered for field rule 'non_empty'",
        ):
            apply_field_rule(RULE_NON_EMPTY, "x", "f")
