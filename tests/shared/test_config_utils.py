"""Tests for scripts/shared/config_utils.py::get_str().

Covers all three structural branches:
1. v is None → return default
2. not isinstance(v, str) → raise ValueError
3. passthrough str value unchanged
"""

import pytest
from shared.config_utils import get_str


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
