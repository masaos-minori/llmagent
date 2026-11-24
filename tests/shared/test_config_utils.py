"""Tests for scripts/shared/config_utils.py::get_str(), get_typed(), get_non_negative_number().

Covers all three structural branches:
1. v is None → return default
2. not isinstance(v, str) → raise ValueError
3. passthrough str value unchanged

get_typed additionally pins the type matrix: bool is rejected for int/float
expected types and accepted for bool.

get_non_negative_number pins the strict range rule on top of the same type
matrix: bool, non-finite, and negative values are rejected; 0 is accepted.
"""

import math

import pytest
from shared.config_utils import get_non_negative_number, get_str, get_typed


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


class TestGetNonNegativeNumber:
    def test_accepts_positive_int_and_float(self) -> None:
        assert get_non_negative_number({"k": 5}, "k", int, "an integer") == 5
        assert get_non_negative_number({"k": 1.5}, "k", float, "a float") == 1.5

    def test_accepts_zero(self) -> None:
        assert get_non_negative_number({"k": 0}, "k", int, "an integer") == 0

    def test_rejects_negative_value(self) -> None:
        with pytest.raises(
            ValueError, match=r"'k' must be an integer, got negative value: -1"
        ):
            get_non_negative_number({"k": -1}, "k", int, "an integer")

    def test_rejects_negative_float(self) -> None:
        with pytest.raises(
            ValueError, match=r"'k' must be a float, got negative value: -0.5"
        ):
            get_non_negative_number({"k": -0.5}, "k", float, "a float")

    def test_rejects_nan(self) -> None:
        with pytest.raises(
            ValueError, match=r"'k' must be a float, got non-finite value: nan"
        ):
            get_non_negative_number({"k": math.nan}, "k", float, "a float")

    def test_rejects_positive_infinity(self) -> None:
        with pytest.raises(ValueError, match=r"non-finite value: inf"):
            get_non_negative_number({"k": math.inf}, "k", float, "a float")

    def test_rejects_negative_infinity(self) -> None:
        with pytest.raises(ValueError, match=r"non-finite value: -inf"):
            get_non_negative_number({"k": -math.inf}, "k", float, "a float")

    def test_rejects_bool_for_int(self) -> None:
        with pytest.raises(ValueError, match=r"'k' must be an integer, got bool: True"):
            get_non_negative_number({"k": True}, "k", int, "an integer")

    def test_rejects_bool_for_float(self) -> None:
        with pytest.raises(ValueError, match=r"'k' must be a float, got bool: False"):
            get_non_negative_number({"k": False}, "k", float, "a float")

    def test_rejects_str_for_int(self) -> None:
        with pytest.raises(ValueError, match=r"'k' must be an integer, got str: 'x'"):
            get_non_negative_number({"k": "x"}, "k", int, "an integer")

    def test_rejects_float_for_int(self) -> None:
        with pytest.raises(ValueError, match=r"'k' must be an integer, got float: 1.5"):
            get_non_negative_number({"k": 1.5}, "k", int, "an integer")

    def test_returns_default_on_missing_key(self) -> None:
        assert get_non_negative_number({}, "k", int, "an integer", default=0) == 0

    def test_returns_default_on_none_value(self) -> None:
        assert (
            get_non_negative_number({"k": None}, "k", int, "an integer", default=0) == 0
        )

    def test_default_is_none_when_unset(self) -> None:
        assert get_non_negative_number({}, "k", int, "an integer") is None

    def test_get_typed_behavior_is_unchanged(self) -> None:
        assert get_typed({"k": -1}, "k", int, "an integer") == -1
