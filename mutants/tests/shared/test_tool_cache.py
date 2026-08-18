"""tests/test_tool_cache.py
Correctness tests for shared.tool_cache.ToolResultCache.
"""

from __future__ import annotations

import time
from unittest.mock import patch

from shared.tool_cache import ToolResultCache
from shared.transport_dto import ToolCallResult


class TestToolResultCache:
    def test_store_and_get_result(self) -> None:
        """A stored successful result is retrievable via get_result() before TTL expiry."""
        cache = ToolResultCache(ttl=60.0)
        result = ToolCallResult(
            output="hello", is_error=False, request_id="", server_key=""
        )
        key = cache.make_key("test_tool", {"x": 1})
        cache.store_if_success(key, result)
        retrieved = cache.get_result(key)
        assert retrieved is not None
        assert retrieved.output == "hello"
        assert retrieved.is_error is False

    def test_ttl_expiry_returns_none(self) -> None:
        """get_result() returns None (and evicts) once the entry's age exceeds ttl."""
        with patch.object(time, "time", side_effect=[100.0, 100.0, 200.0]):
            cache = ToolResultCache(ttl=50.0)
            result = ToolCallResult(
                output="data", is_error=False, request_id="", server_key=""
            )
            key = cache.make_key("test_tool", {"x": 1})
            cache.store_if_success(key, result)
            assert cache.get_result(key) is not None
            assert cache.get_result(key) is None
            assert key not in cache._cache

    def test_lru_eviction_at_max_size(self) -> None:
        """Storing beyond max_size evicts the least-recently-used entry, not the newest."""
        cache = ToolResultCache(ttl=60.0, max_size=2)
        r1 = ToolCallResult(output="a", is_error=False, request_id="", server_key="")
        r2 = ToolCallResult(output="b", is_error=False, request_id="", server_key="")
        r3 = ToolCallResult(output="c", is_error=False, request_id="", server_key="")
        k1 = cache.make_key("tool_a", {})
        k2 = cache.make_key("tool_b", {})
        k3 = cache.make_key("tool_c", {})
        cache.store_if_success(k1, r1)
        cache.store_if_success(k2, r2)
        cache.store_if_success(k3, r3)
        assert cache.get_result(k1) is None
        assert cache.get_result(k2) is not None
        assert cache.get_result(k3) is not None

    def test_store_if_success_skips_error_results(self) -> None:
        """store_if_success() is a no-op when result.is_error is True."""
        cache = ToolResultCache(ttl=60.0)
        result = ToolCallResult(
            output="error", is_error=True, request_id="", server_key=""
        )
        key = cache.make_key("test_tool", {"x": 1})
        cache.store_if_success(key, result)
        assert cache.get_result(key) is None

    def test_clear_removes_all_entries(self) -> None:
        """clear() empties the cache; get_result() returns None for a previously-stored key."""
        cache = ToolResultCache(ttl=60.0)
        result = ToolCallResult(
            output="data", is_error=False, request_id="", server_key=""
        )
        key = cache.make_key("test_tool", {"x": 1})
        cache.store_if_success(key, result)
        cache.clear()
        assert cache.get_result(key) is None

    def test_make_key_is_deterministic_for_same_args(self) -> None:
        """make_key() returns an identical string for two calls with equal tool_name/args."""
        cache = ToolResultCache(ttl=60.0)
        args1 = {"z": 1, "a": 2}
        args2 = {"a": 2, "z": 1}
        key1 = cache.make_key("my_tool", args1)
        key2 = cache.make_key("my_tool", args2)
        assert key1 == key2
