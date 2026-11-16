"""Tests for scripts/shared/config_utils.py::get_str() and get_typed().

Covers all three structural branches:
1. v is None → return default
2. not isinstance(v, str) → raise ValueError
3. passthrough str value unchanged

get_typed additionally pins the type matrix: bool is rejected for int/float
expected types and accepted for bool.
"""

import pytest
from shared.config_utils import get_str, get_typed


class TestGetStr:
    def test_get_str_returns_string_value(self) -> None:
        assert get_str({"k": "v"}, "k") == "v"

    def test_get_str_raises_on_non_string_value(self) -> None:
        with pytest.raises(ValueError, match=r"Config key 'k' must be str, got int"):
            get_str({"k": 1}, "k")

    def test_get_str_returns_default_on_missing_key(self) -> None:
        assert get_str({}, "k", default="x") == "x"

    def test_get_str_returns_default_on_none_value(self) -> None:
        assert get_str({"k": None}, "k", default="x") == "x"

    def test_get_str_default_is_empty_string_when_unset(self) -> None:
        assert get_str({}, "k") == ""


class TestGetTyped:
    def test_get_typed_returns_matching_value(self) -> None:
        assert get_typed({"k": 5}, "k", int, "an integer") == 5
        assert get_typed({"k": 1.5}, "k", float, "a float") == 1.5

    def test_get_typed_rejects_bool_for_int(self) -> None:
        with pytest.raises(ValueError, match=r"'k' must be an integer, got bool: True"):
            get_typed({"k": True}, "k", int, "an integer")

    def test_get_typed_rejects_bool_for_float(self) -> None:
        with pytest.raises(ValueError, match=r"'k' must be a float, got bool: False"):
            get_typed({"k": False}, "k", float, "a float")

    def test_get_typed_accepts_bool_for_bool(self) -> None:
        assert get_typed({"k": True}, "k", bool, "a bool") is True

    def test_get_typed_rejects_int_for_bool(self) -> None:
        with pytest.raises(ValueError, match=r"'k' must be a bool, got int: 1"):
            get_typed({"k": 1}, "k", bool, "a bool")

    def test_get_typed_rejects_float_for_int(self) -> None:
        with pytest.raises(ValueError, match=r"'k' must be an integer, got float: 1.5"):
            get_typed({"k": 1.5}, "k", int, "an integer")

    def test_get_typed_rejects_str_for_int(self) -> None:
        with pytest.raises(ValueError, match=r"'k' must be an integer, got str: 'x'"):
            get_typed({"k": "x"}, "k", int, "an integer")

    def test_get_typed_returns_default_on_missing_key(self) -> None:
        assert get_typed({}, "k", int, "an integer", default=7) == 7

    def test_get_typed_returns_default_on_none_value(self) -> None:
        assert get_typed({"k": None}, "k", int, "an integer", default=7) == 7
