#!/usr/bin/env python3
"""scripts/shared/tool_cache.py

Cache entry dataclass and ToolResultCache for a standalone tool-result cache.

Status: ToolResultCache is NOT currently used by ToolExecutor -- ToolExecutor
maintains its own internal OrderedDict-based cache (see _execute_with_cache(),
_store_and_evict() in shared/tool_executor.py), tightly integrated with its
stampede-protection (_inflight future sharing) mechanism, which this class has
no equivalent of. ToolResultCache remains available as a standalone, simpler
utility for a future caller that needs LRU+TTL caching without stampede
protection -- it is not deprecated, but it is also not the canonical cache.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from shared.json_utils import dumps as _json_dumps
from shared.transport_dto import ToolCallResult


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


@dataclass(frozen=True)
class CacheEntry:
    """LRU cache entry storing a successful tool call result."""

    output: str
    is_error: bool
    cached_at: float
    server_key: str = ""
mutants_xǁToolResultCacheǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolResultCacheǁmake_key__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolResultCacheǁget_result__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolResultCacheǁstore_if_success__mutmut: MutantDict = {}  # type: ignore


class ToolResultCache:
    """LRU cache for tool call results with TTL expiry and optional max-size eviction."""

    @_mutmut_mutated(mutants_xǁToolResultCacheǁ__init____mutmut)
    def __init__(self, ttl: float, max_size: int = 0) -> None:
        """Initialize with TTL duration and optional maximum cache size."""
        self._ttl = ttl
        self._max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def xǁToolResultCacheǁ__init____mutmut_orig(self, ttl: float, max_size: int = 0) -> None:
        """Initialize with TTL duration and optional maximum cache size."""
        self._ttl = ttl
        self._max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def xǁToolResultCacheǁ__init____mutmut_1(self, ttl: float, max_size: int = 1) -> None:
        """Initialize with TTL duration and optional maximum cache size."""
        self._ttl = ttl
        self._max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def xǁToolResultCacheǁ__init____mutmut_2(self, ttl: float, max_size: int = 0) -> None:
        """Initialize with TTL duration and optional maximum cache size."""
        self._ttl = None
        self._max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def xǁToolResultCacheǁ__init____mutmut_3(self, ttl: float, max_size: int = 0) -> None:
        """Initialize with TTL duration and optional maximum cache size."""
        self._ttl = ttl
        self._max_size = None
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def xǁToolResultCacheǁ__init____mutmut_4(self, ttl: float, max_size: int = 0) -> None:
        """Initialize with TTL duration and optional maximum cache size."""
        self._ttl = ttl
        self._max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = None

    @_mutmut_mutated(mutants_xǁToolResultCacheǁmake_key__mutmut)
    def make_key(self, tool_name: str, args: Mapping[str, Any]) -> str:
        """Return the canonical cache key for a tool call."""
        return f"{tool_name}:{_json_dumps(args)}"

    def xǁToolResultCacheǁmake_key__mutmut_orig(self, tool_name: str, args: Mapping[str, Any]) -> str:
        """Return the canonical cache key for a tool call."""
        return f"{tool_name}:{_json_dumps(args)}"

    def xǁToolResultCacheǁmake_key__mutmut_1(self, tool_name: str, args: Mapping[str, Any]) -> str:
        """Return the canonical cache key for a tool call."""
        return f"{tool_name}:{_json_dumps(None)}"

    @_mutmut_mutated(mutants_xǁToolResultCacheǁget_result__mutmut)
    def get_result(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_orig(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_1(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = None
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_2(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(None)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_3(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is not None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_4(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = None
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_5(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() + cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_6(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age > self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_7(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(None)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_8(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=None,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_9(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=None,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_10(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id=None,
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_11(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=None,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_12(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source=None,
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_13(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type=None,
        )

    def xǁToolResultCacheǁget_result__mutmut_14(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_15(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_16(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_17(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_18(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_19(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            )

    def xǁToolResultCacheǁget_result__mutmut_20(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="XXXX",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_21(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="XXcacheXX",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_22(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="CACHE",
            error_type="tool" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_23(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="XXtoolXX" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_24(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="TOOL" if cached.is_error else "",
        )

    def xǁToolResultCacheǁget_result__mutmut_25(self, key: str) -> ToolCallResult | None:
        """Return the cached result if present and within TTL; else return None."""
        cached = self._cache.get(key)
        if cached is None:
            return None
        age = time.time() - cached.cached_at
        if age >= self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return ToolCallResult(
            output=cached.output,
            is_error=cached.is_error,
            request_id="",
            server_key=cached.server_key,
            source="cache",
            error_type="tool" if cached.is_error else "XXXX",
        )

    @_mutmut_mutated(mutants_xǁToolResultCacheǁstore_if_success__mutmut)
    def store_if_success(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_orig(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_1(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = None
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_2(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=None,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_3(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=None,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_4(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=None,
            server_key=result.server_key,
        )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_5(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=None,
        )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_6(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_7(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_8(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            server_key=result.server_key,
        )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_9(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_10(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._max_size > 0 or len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_11(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._max_size >= 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_12(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._max_size > 1 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_13(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._max_size > 0 and len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)

    def xǁToolResultCacheǁstore_if_success__mutmut_14(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=None)

    def xǁToolResultCacheǁstore_if_success__mutmut_15(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output,
            is_error=result.is_error,
            cached_at=time.time(),
            server_key=result.server_key,
        )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=True)

    def clear(self) -> None:
        """Evict all cached results."""
        self._cache.clear()

mutants_xǁToolResultCacheǁ__init____mutmut['_mutmut_orig'] = ToolResultCache.xǁToolResultCacheǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁ__init____mutmut['xǁToolResultCacheǁ__init____mutmut_1'] = ToolResultCache.xǁToolResultCacheǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁ__init____mutmut['xǁToolResultCacheǁ__init____mutmut_2'] = ToolResultCache.xǁToolResultCacheǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁ__init____mutmut['xǁToolResultCacheǁ__init____mutmut_3'] = ToolResultCache.xǁToolResultCacheǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁ__init____mutmut['xǁToolResultCacheǁ__init____mutmut_4'] = ToolResultCache.xǁToolResultCacheǁ__init____mutmut_4 # type: ignore # mutmut generated

mutants_xǁToolResultCacheǁmake_key__mutmut['_mutmut_orig'] = ToolResultCache.xǁToolResultCacheǁmake_key__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁmake_key__mutmut['xǁToolResultCacheǁmake_key__mutmut_1'] = ToolResultCache.xǁToolResultCacheǁmake_key__mutmut_1 # type: ignore # mutmut generated

mutants_xǁToolResultCacheǁget_result__mutmut['_mutmut_orig'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_1'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_2'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_3'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_4'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_5'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_6'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_7'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_8'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_9'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_10'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_11'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_12'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_13'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_14'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_15'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_16'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_17'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_18'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_19'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_20'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_21'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_22'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_22 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_23'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_23 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_24'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_24 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁget_result__mutmut['xǁToolResultCacheǁget_result__mutmut_25'] = ToolResultCache.xǁToolResultCacheǁget_result__mutmut_25 # type: ignore # mutmut generated

mutants_xǁToolResultCacheǁstore_if_success__mutmut['_mutmut_orig'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_1'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_2'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_3'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_4'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_5'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_6'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_7'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_8'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_9'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_10'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_11'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_12'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_13'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_14'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolResultCacheǁstore_if_success__mutmut['xǁToolResultCacheǁstore_if_success__mutmut_15'] = ToolResultCache.xǁToolResultCacheǁstore_if_success__mutmut_15 # type: ignore # mutmut generated
