#!/usr/bin/env python3
"""mcp_servers/web_search/search_provider.py

Search provider implementations for web-search-mcp.

Dependency direction: mcp_servers.web_search.search_provider → duckduckgo_search, mcp_servers.web_search.models
Import from here:  from mcp_servers.web_search.search_provider import search_duckduckgo
"""

from __future__ import annotations

import asyncio

from duckduckgo_search import DDGS

from mcp_servers.web_search.web_search_models import (
    SearchResult,
    WebSearchNetworkError,
    WebSearchParseError,
    WebSearchProviderError,
    WebSearchTimeoutError,
)


async def search_duckduckgo(
    query: str, max_results: int, search_timeout_sec: float
) -> list[SearchResult]:
    """Execute a text search using DuckDuckGo. No API key required.

    Raises:
        WebSearchTimeoutError: if the search exceeds search_timeout_sec.
        WebSearchNetworkError: on a network-level provider failure.
        WebSearchProviderError: on any other provider-side failure.
        WebSearchParseError: if a raw result item is not a dict.
    """

    def _sync_search() -> list[dict]:
        """Run the synchronous DuckDuckGo search within a thread pool."""
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))

    try:
        raw = await asyncio.wait_for(
            asyncio.to_thread(_sync_search), timeout=search_timeout_sec
        )
    except TimeoutError as e:
        raise WebSearchTimeoutError(
            f"DuckDuckGo search timed out after {search_timeout_sec}s"
        ) from e
    except (RuntimeError, OSError) as e:
        raise WebSearchNetworkError(f"DuckDuckGo search failed: {e}") from e
    except Exception as e:  # noqa: BLE001 — classification fallback, see UNK-01
        raise WebSearchProviderError(f"DuckDuckGo search failed: {e}") from e

    for item in raw:
        if not isinstance(item, dict):
            raise WebSearchParseError(
                f"unexpected result item type: {type(item).__name__}"
            )

    return [
        SearchResult(
            title=r.get("title", ""),
            url=r.get("href", ""),
            body=r.get("body", ""),
            provider="duckduckgo",
        )
        for r in raw
    ]
