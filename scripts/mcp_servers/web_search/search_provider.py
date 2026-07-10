#!/usr/bin/env python3
"""mcp_servers/web_search/search_provider.py

Search provider implementations for web-search-mcp.

Dependency direction: mcp_servers.web_search.search_provider → duckduckgo_search, mcp_servers.web_search.models
Import from here:  from mcp_servers.web_search.search_provider import search_duckduckgo
"""

from __future__ import annotations

import asyncio

from duckduckgo_search import DDGS
from mcp_servers.web_search.models import (
    SearchResult,
    WebSearchUpstreamError,
)


async def search_duckduckgo(query: str, max_results: int) -> list[SearchResult]:
    """Execute a text search using DuckDuckGo. No API key required."""

    def _sync_search() -> list[dict]:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))

    try:
        raw = await asyncio.to_thread(_sync_search)
    except (RuntimeError, TimeoutError) as e:
        raise WebSearchUpstreamError(f"DuckDuckGo search failed: {e}") from e

    return [
        SearchResult(
            title=r.get("title", ""),
            url=r.get("href", ""),
            body=r.get("body", ""),
            provider="duckduckgo",
        )
        for r in raw
    ]
