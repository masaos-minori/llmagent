#!/usr/bin/env python3
"""Tests for scripts/eventbus/json_utils.py."""

import re
from datetime import UTC, datetime

from scripts.eventbus.json_utils import dumps, now_iso


class TestDumpsReturnsStr:
    def test_dumps_returns_str(self):
        result = dumps({"a": 1})
        assert isinstance(result, str)

    def test_dumps_sorts_keys_by_default(self):
        result = dumps({"z": 1, "a": 2})
        assert '"a"' in result
        z_pos = result.index('"z"')
        a_pos = result.index('"a"')
        assert a_pos < z_pos

    def test_dumps_with_option_none(self):
        result = dumps({"b": 1, "a": 2}, option=None)
        assert isinstance(result, str)

    def test_dumps_empty_dict(self):
        result = dumps({})
        assert result == "{}"

    def test_dumps_nested_object(self):
        result = dumps({"nested": {"x": 1}})
        assert '"nested"' in result
        assert '"x"' in result


class TestNowIsoFormat:
    def test_now_iso_format(self):
        result = now_iso()
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", result) is not None

    def test_now_iso_is_utc(self):
        before = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = now_iso()
        after = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        assert before <= result <= after
