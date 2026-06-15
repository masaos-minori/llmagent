#!/usr/bin/env python3
"""shared/tool_cache.py
Cache entry dataclass for ToolExecutor's LRU result cache.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class _CacheEntry:
    """Internal LRU cache entry storing a successful tool call result."""

    output: str
    is_error: bool
    cached_at: float
