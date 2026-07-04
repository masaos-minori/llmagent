"""tests/shared/test_tool_result_cache.py
Unit tests for ToolResultCache: key format, hit/miss, TTL, LRU, max_size, error filtering.
"""

from __future__ import annotations

import time

from shared.tool_cache import ToolResultCache
from shared.transport_dto import ToolCallResult


def _ok_result(output: str = "ok") -> ToolCallResult:
    return ToolCallResult(output=output, is_error=False, request_id="", server_key="")


def _err_result() -> ToolCallResult:
    return ToolCallResult(
        output="err", is_error=True, request_id="", server_key="", error_type="tool"
    )


class TestToolResultCache:
    def test_make_key_format(self) -> None:
        cache = ToolResultCache(ttl=60.0)
        key = cache.make_key("read_file", {"path": "a"})
        assert key.startswith("read_file:")
        assert "path" in key

    def test_cache_miss_returns_none(self) -> None:
        cache = ToolResultCache(ttl=60.0)
        assert cache.get_result("nonexistent") is None

    def test_cache_hit_returns_result(self) -> None:
        cache = ToolResultCache(ttl=60.0)
        key = cache.make_key("my_tool", {})
        result = _ok_result("cached_output")
        cache.store_if_success(key, result)
        hit = cache.get_result(key)
        assert hit is not None
        assert hit.output == "cached_output"
        assert hit.is_error is False
        assert hit.request_id == ""

    def test_ttl_expiry_returns_none(self) -> None:
        cache = ToolResultCache(ttl=0.001)
        key = cache.make_key("my_tool", {})
        cache.store_if_success(key, _ok_result())
        time.sleep(0.02)
        assert cache.get_result(key) is None

    def test_lru_move_on_hit(self) -> None:
        cache = ToolResultCache(ttl=60.0, max_size=2)
        key_a = cache.make_key("tool_a", {})
        key_b = cache.make_key("tool_b", {})
        cache.store_if_success(key_a, _ok_result("a"))
        cache.store_if_success(key_b, _ok_result("b"))
        # Hit key_a — should move it to most-recently-used
        cache.get_result(key_a)
        # Add key_c — should evict key_b (LRU) not key_a
        key_c = cache.make_key("tool_c", {})
        cache.store_if_success(key_c, _ok_result("c"))
        assert cache.get_result(key_a) is not None
        assert cache.get_result(key_b) is None
        assert cache.get_result(key_c) is not None

    def test_max_size_eviction(self) -> None:
        cache = ToolResultCache(ttl=60.0, max_size=2)
        key_a = cache.make_key("tool_a", {})
        key_b = cache.make_key("tool_b", {})
        key_c = cache.make_key("tool_c", {})
        cache.store_if_success(key_a, _ok_result("a"))
        cache.store_if_success(key_b, _ok_result("b"))
        cache.store_if_success(key_c, _ok_result("c"))
        # key_a was first inserted → evicted as LRU
        assert cache.get_result(key_a) is None
        assert cache.get_result(key_b) is not None
        assert cache.get_result(key_c) is not None

    def test_error_result_not_stored(self) -> None:
        cache = ToolResultCache(ttl=60.0)
        key = cache.make_key("failing_tool", {})
        cache.store_if_success(key, _err_result())
        assert cache.get_result(key) is None

    def test_clear_empties_cache(self) -> None:
        cache = ToolResultCache(ttl=60.0)
        key = cache.make_key("my_tool", {})
        cache.store_if_success(key, _ok_result())
        cache.clear()
        assert cache.get_result(key) is None
