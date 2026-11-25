"""tests/agent/services/test_typed_validators.py

Unit tests for typed boundary extraction helpers.

The type rules live in scripts/shared/config_field_types.py. These tests pin the
delegating layer's contract: the field path in the raised message, the bool rejection,
the values the getters keep accepting, and the *_nonempty helpers' return-None-on-empty
contract (REQ-001, REQ-011).
"""

from __future__ import annotations

import pytest
from agent.services.exceptions import ConfigReloadValidationError
from agent.services.typed_validators import (
    _apply_dict_nonempty,
    _apply_list_nonempty,
    _apply_str_nonempty,
    _get_bool,
    _get_dict,
    _get_dict_nonempty,
    _get_float,
    _get_int,
    _get_list,
    _get_list_nonempty,
    _get_str,
    _get_str_nonempty,
)

_EMPTY_CFG: dict[str, object] = {}

_REQUIRED_KEYS: dict[str, object] = {
    "int_val": 42,
    "float_val": 3.14,
    "bool_val": True,
    "str_val": "hello",
    "list_val": ["a"],
    "dict_val": {"k": "v"},
}

_MISSING_KEYS: dict[str, object] = {}

# --- _get_int ---


class TestGetInt:
    def test_present_value_returns_int(self) -> None:
        assert _get_int(_REQUIRED_KEYS, "int_val") == 42

    def test_present_value_with_required_true_returns_int(self) -> None:
        assert _get_int(_REQUIRED_KEYS, "int_val", required=True) == 42

    def test_missing_key_without_required_returns_none(self) -> None:
        assert _get_int(_MISSING_KEYS, "missing_key") is None

    def test_missing_key_with_required_false_returns_none(self) -> None:
        assert _get_int(_MISSING_KEYS, "missing_key", required=False) is None

    def test_missing_key_with_required_true_raises(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError, match="is required but missing"
        ):
            _get_int(_MISSING_KEYS, "missing_key", required=True)

    def test_bool_subclass_raises(self) -> None:
        with pytest.raises(ConfigReloadValidationError, match="must be int"):
            _get_int({"key": True}, "key")

    def test_string_raises(self) -> None:
        with pytest.raises(ConfigReloadValidationError, match="must be int"):
            _get_int({"key": "42"}, "key")

    def test_error_names_the_field_path_and_excludes_the_value(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError,
            match=r"config key 'llm_max_tokens' must be int",
        ) as excinfo:
            _get_int({"llm_max_tokens": "1024"}, "llm_max_tokens")
        assert "1024" not in str(excinfo.value)


# --- _get_float ---


class TestGetFloat:
    def test_present_value_returns_float(self) -> None:
        assert _get_float(_REQUIRED_KEYS, "float_val") == 3.14

    def test_present_value_with_required_true_returns_float(self) -> None:
        assert _get_float(_REQUIRED_KEYS, "float_val", required=True) == 3.14

    def test_missing_key_without_required_returns_none(self) -> None:
        assert _get_float(_MISSING_KEYS, "missing_key") is None

    def test_missing_key_with_required_true_raises(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError, match="is required but missing"
        ):
            _get_float(_MISSING_KEYS, "missing_key", required=True)

    def test_bool_subclass_raises(self) -> None:
        with pytest.raises(ConfigReloadValidationError, match="must be float"):
            _get_float({"key": True}, "key")

    def test_int_coerces_to_float(self) -> None:
        assert _get_float({"key": 42}, "key") == 42.0

    def test_error_names_the_field_path_and_excludes_the_value(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError,
            match=r"config key 'llm_temperature' must be float",
        ) as excinfo:
            _get_float({"llm_temperature": "0.2"}, "llm_temperature")
        assert "0.2" not in str(excinfo.value)


# --- _get_bool ---


class TestGetBool:
    def test_present_value_returns_bool(self) -> None:
        assert _get_bool(_REQUIRED_KEYS, "bool_val") is True

    def test_present_value_with_required_true_returns_bool(self) -> None:
        assert _get_bool(_REQUIRED_KEYS, "bool_val", required=True) is True

    def test_missing_key_without_required_returns_none(self) -> None:
        assert _get_bool(_MISSING_KEYS, "missing_key") is None

    def test_missing_key_with_required_true_raises(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError, match="is required but missing"
        ):
            _get_bool(_MISSING_KEYS, "missing_key", required=True)

    def test_int_raises(self) -> None:
        with pytest.raises(ConfigReloadValidationError, match="must be bool"):
            _get_bool({"key": 1}, "key")

    def test_error_names_the_field_path_and_excludes_the_value(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError,
            match=r"config key 'serial_tool_calls' must be bool, got int",
        ) as excinfo:
            _get_bool({"serial_tool_calls": 1}, "serial_tool_calls")
        assert "got bool" not in str(excinfo.value)


# --- _get_str ---


class TestGetStr:
    def test_present_value_returns_str(self) -> None:
        assert _get_str(_REQUIRED_KEYS, "str_val") == "hello"

    def test_present_value_with_required_true_returns_str(self) -> None:
        assert _get_str(_REQUIRED_KEYS, "str_val", required=True) == "hello"

    def test_missing_key_without_required_returns_none(self) -> None:
        assert _get_str(_MISSING_KEYS, "missing_key") is None

    def test_missing_key_with_required_true_raises(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError, match="is required but missing"
        ):
            _get_str(_MISSING_KEYS, "missing_key", required=True)

    def test_int_raises(self) -> None:
        with pytest.raises(ConfigReloadValidationError, match="must be str"):
            _get_str({"key": 42}, "key")

    def test_error_names_the_field_path_and_excludes_the_value(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError,
            match=r"config key 'memory_embed_url' must be str, got int",
        ) as excinfo:
            _get_str({"memory_embed_url": 7}, "memory_embed_url")
        assert "7" not in str(excinfo.value)

    def test_empty_string_is_a_configured_value(self) -> None:
        # config/agent.toml carries tokenize_url = ""; _or_default applies the default.
        assert _get_str({"tokenize_url": ""}, "tokenize_url") == ""

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ConfigReloadValidationError, match="must not be empty"):
            _get_str({"tokenize_url": "   "}, "tokenize_url")


# --- _get_list ---


class TestGetList:
    def test_present_value_returns_list(self) -> None:
        assert _get_list(_REQUIRED_KEYS, "list_val") == ["a"]

    def test_present_value_with_required_true_returns_list(self) -> None:
        assert _get_list(_REQUIRED_KEYS, "list_val", required=True) == ["a"]

    def test_missing_key_without_required_returns_none(self) -> None:
        assert _get_list(_MISSING_KEYS, "missing_key") is None

    def test_missing_key_with_required_true_raises(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError, match="is required but missing"
        ):
            _get_list(_MISSING_KEYS, "missing_key", required=True)

    def test_tuple_raises(self) -> None:
        with pytest.raises(ConfigReloadValidationError, match="must be list"):
            _get_list({"key": ("a",)}, "key")

    def test_str_raises_rather_than_being_split(self) -> None:
        with pytest.raises(ConfigReloadValidationError, match="must be list, got str"):
            _get_list({"key": "abc"}, "key")

    def test_empty_list_is_accepted_at_the_getter(self) -> None:
        # config/agent.toml carries approval_github_allowed_repos = []; the registry
        # entry decides whether an empty list is valid for the field.
        assert _get_list({"allowed_tools": []}, "allowed_tools") == []

    def test_non_str_element_raises_naming_the_index(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError,
            match=r"config key 'masked_fields\[1\]' must be str",
        ) as excinfo:
            _get_list({"masked_fields": ["content", 7]}, "masked_fields")
        assert "7" not in str(excinfo.value)


# --- _get_dict ---


class TestGetDict:
    def test_present_value_returns_dict(self) -> None:
        assert _get_dict(_REQUIRED_KEYS, "dict_val") == {"k": "v"}

    def test_present_value_with_required_true_returns_dict(self) -> None:
        assert _get_dict(_REQUIRED_KEYS, "dict_val", required=True) == {"k": "v"}

    def test_missing_key_without_required_returns_none(self) -> None:
        assert _get_dict(_MISSING_KEYS, "missing_key") is None

    def test_missing_key_with_required_true_raises(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError, match="is required but missing"
        ):
            _get_dict(_MISSING_KEYS, "missing_key", required=True)

    def test_list_raises(self) -> None:
        with pytest.raises(ConfigReloadValidationError, match="must be dict"):
            _get_dict({"key": []}, "key")

    def test_mixed_value_types_are_accepted(self) -> None:
        # config/agent.toml carries tool_concurrency_limits with integer values.
        limits = {"file_read": 4, "file_write": 1}
        assert (
            _get_dict({"tool_concurrency_limits": limits}, "tool_concurrency_limits")
            == limits
        )

    def test_empty_dict_is_accepted(self) -> None:
        assert _get_dict({"diagnostics": {}}, "diagnostics") == {}

    def test_error_names_the_field_path(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError,
            match=r"config key 'diagnostics' must be dict, got str",
        ):
            _get_dict({"diagnostics": "x"}, "diagnostics")


# --- the *_nonempty helpers ---


class TestNonemptyGetters:
    """The helpers return None for an empty value instead of raising (REQ-001).

    The emptiness decision for a field belongs to the registry allow_empty flag, not to
    these helpers; the type check they inherit from the plain getter still applies.
    """

    def test_missing_key_returns_none(self) -> None:
        assert _get_list_nonempty(_MISSING_KEYS, "missing_key") is None
        assert _get_str_nonempty(_MISSING_KEYS, "missing_key") is None
        assert _get_dict_nonempty(_MISSING_KEYS, "missing_key") is None

    def test_missing_key_with_required_true_raises(self) -> None:
        for getter in (_get_list_nonempty, _get_str_nonempty, _get_dict_nonempty):
            with pytest.raises(
                ConfigReloadValidationError, match="is required but missing"
            ):
                getter(_MISSING_KEYS, "missing_key", required=True)

    def test_empty_value_returns_none(self) -> None:
        assert _get_list_nonempty({"key": []}, "key") is None
        assert _get_str_nonempty({"key": ""}, "key") is None
        assert _get_dict_nonempty({"key": {}}, "key") is None

    def test_nonempty_value_is_returned(self) -> None:
        assert _get_list_nonempty({"key": ["a"]}, "key") == ["a"]
        assert _get_str_nonempty({"key": "a"}, "key") == "a"
        assert _get_dict_nonempty({"key": {"a": 1}}, "key") == {"a": 1}

    def test_wrong_type_raises_naming_the_field(self) -> None:
        with pytest.raises(
            ConfigReloadValidationError,
            match=r"config key 'allowed_tools' must be list, got str",
        ):
            _get_list_nonempty({"allowed_tools": "a"}, "allowed_tools")
        with pytest.raises(
            ConfigReloadValidationError,
            match=r"config key 'otel_endpoint' must be str, got int",
        ):
            _get_str_nonempty({"otel_endpoint": 7}, "otel_endpoint")
        with pytest.raises(
            ConfigReloadValidationError,
            match=r"config key 'diagnostics' must be dict, got list",
        ):
            _get_dict_nonempty({"diagnostics": []}, "diagnostics")

    def test_a_whitespace_only_string_is_not_an_empty_value(self) -> None:
        # The shared rule rejects it as a value, so the helper never sees it to return None.
        with pytest.raises(ConfigReloadValidationError, match="must not be empty"):
            _get_str_nonempty({"otel_endpoint": "   "}, "otel_endpoint")


class TestNonemptyAppliers:
    """The appliers call the setter only for a present, non-empty value."""

    def test_setter_runs_for_a_nonempty_value(self) -> None:
        seen: list[object] = []
        _apply_list_nonempty({"key": ["a"]}, "key", seen.append)
        _apply_str_nonempty({"key": "b"}, "key", seen.append)
        _apply_dict_nonempty({"key": {"c": 1}}, "key", seen.append)
        assert seen == [["a"], "b", {"c": 1}]

    def test_setter_does_not_run_for_a_missing_or_empty_value(self) -> None:
        seen: list[object] = []
        _apply_list_nonempty({}, "key", seen.append)
        _apply_str_nonempty({}, "key", seen.append)
        _apply_dict_nonempty({}, "key", seen.append)
        _apply_list_nonempty({"key": []}, "key", seen.append)
        _apply_str_nonempty({"key": ""}, "key", seen.append)
        _apply_dict_nonempty({"key": {}}, "key", seen.append)
        assert seen == []

    def test_wrong_type_raises_before_the_setter_runs(self) -> None:
        seen: list[object] = []
        with pytest.raises(ConfigReloadValidationError, match="must be list"):
            _apply_list_nonempty({"key": "a"}, "key", seen.append)
        assert seen == []
