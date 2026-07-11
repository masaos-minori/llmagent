#!/usr/bin/env python3
"""shared/tool_cache.py
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
from dataclasses import dataclass
from typing import Any

from shared.json_utils import dumps as _json_dumps
from shared.transport_dto import ToolCallResult


@dataclass(frozen=True)
class CacheEntry:
    """LRU cache entry storing a successful tool call result."""

    output: str
    is_error: bool
    cached_at: float


class ToolResultCache:
    """LRU cache for tool call results with TTL expiry and optional max-size eviction."""

    def __init__(self, ttl: float, max_size: int = 0) -> None:
        self._ttl = ttl
        self._max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def make_key(self, tool_name: str, args: dict[str, Any]) -> str:
        """Return the canonical cache key for a tool call."""
        return f"{tool_name}:{_json_dumps(args)}"

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
            server_key="",
            error_type="tool" if cached.is_error else "",
        )

    def store_if_success(self, key: str, result: ToolCallResult) -> None:
        """Store a non-error result; evict the LRU entry when max_size is exceeded."""
        if result.is_error:
            return
        self._cache[key] = CacheEntry(
            output=result.output, is_error=result.is_error, cached_at=time.time()
        )
        if self._max_size > 0 and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Evict all cached results."""
        self._cache.clear()
