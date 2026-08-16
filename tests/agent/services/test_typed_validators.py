"""tests/agent/services/test_typed_validators.py

Unit tests for typed boundary extraction helpers.
"""

from __future__ import annotations

import pytest
from agent.services.exceptions import ConfigReloadValidationError
from agent.services.typed_validators import (
    _get_bool,
    _get_dict,
    _get_float,
    _get_int,
    _get_list,
    _get_str,
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
