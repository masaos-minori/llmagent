#!/usr/bin/env python3
"""mcp/web_search/formatters.py

MCP tool dispatch formatters for web-search-mcp.

Dependency direction: mcp.web_search.formatters → shared.formatters, mcp.web_search.models
Import from here:  from mcp.web_search.formatters import fmt_search_result, fdisp_search_web
"""

from __future__ import annotations

import time
from typing import Any, cast

from mcp.dispatch import DispatchResult, dispatch_tool
from mcp.web_search.models import (
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from mcp.web_search.search_provider import search_duckduckgo
from shared.formatters import MAX_SNIPPET_CHARS, truncate


def fmt_search_result(i: int, r: SearchResult) -> str:
    """Format one search result with title, URL, provider, and truncated snippet."""
    title = r.title or "(no title)"
    snippet = truncate(r.body or "", MAX_SNIPPET_CHARS)
    return f"[{i}] {title}\nURL: {r.url}\nProvider: {r.provider}\n{snippet}"


async def fdisp_search_web(args: dict[str, Any]) -> str:
    """Format search_web MCP tool result as plain text for LLM."""
    result = await search_web(args)
    if not result.results:
        return "No search results found."
    header = f"[Search: {len(result.results)} results via {result.provider}]\n\n"
    lines = [fmt_search_result(i, r) for i, r in enumerate(result.results, 1)]
    return header + "\n\n".join(lines)


async def search_web(args: dict[str, Any]) -> SearchResponse:
    """Execute a web search using DuckDuckGo."""
    req = SearchRequest(**args)
    t0 = time.perf_counter()
    results = cast(
        list[SearchResult],
        await search_duckduckgo(req.query, req.max_results),
    )

    if not results:
        from mcp.web_search.models import WebSearchUpstreamError

        raise WebSearchUpstreamError("No results returned from DuckDuckGo")

    ms = (time.perf_counter() - t0) * 1000
    from shared.formatters import fmt_kvlog
    from shared.logger import Logger

    logger = Logger(__name__, "/opt/llm/logs/web-search-mcp.log")
    logger.info(
        fmt_kvlog(
            "search",
            q=req.query[:80],
            provider="duckduckgo",
            n=len(results),
            ms=f"{ms:.0f}",
        ),
    )
    return SearchResponse(
        query=req.query,
        results=results,
        provider="duckduckgo",
    )


_WEB_DISPATCH: dict[str, Any] = {
    "search_web": fdisp_search_web,
}


async def dispatch_web_tool(name: str, args: dict[str, Any]) -> DispatchResult:
    """Route a tool call through the web-search dispatch table."""
    return await dispatch_tool(_WEB_DISPATCH, name, args)
