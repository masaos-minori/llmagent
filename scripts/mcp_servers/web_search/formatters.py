#!/usr/bin/env python3
"""mcp_servers/web_search/formatters.py

MCP tool dispatch formatters for web-search-mcp.

Dependency direction: mcp_servers.web_search.formatters → shared.formatters, mcp_servers.web_search.service, mcp_servers.web_search.web_search_models
Import from here:  from mcp_servers.web_search.formatters import fmt_search_result, fdisp_search_web
"""

from __future__ import annotations

from typing import Any

from shared.formatters import MAX_SNIPPET_CHARS, truncate

from mcp_servers.dispatch import DispatchResult, dispatch_tool
from mcp_servers.web_search import service
from mcp_servers.web_search.web_search_models import BrowserFetchResponse, SearchResult


def fmt_search_result(i: int, r: SearchResult) -> str:
    """Format one search result with title, URL, provider, and truncated snippet."""
    title = r.title or "(no title)"
    snippet = truncate(r.body or "", MAX_SNIPPET_CHARS)
    return f"[{i}] {title}\nURL: {r.url}\nProvider: {r.provider}\n{snippet}"


async def fdisp_search_web(args: dict[str, Any]) -> str:
    """Format search_web MCP tool result as plain text for LLM."""
    result = await service.search_web(args)
    if not result.results:
        return "No search results found."
    header = f"[Search: {len(result.results)} results via {result.provider}]\n\n"
    lines = [fmt_search_result(i, r) for i, r in enumerate(result.results, 1)]
    return header + "\n\n".join(lines)


def _format_fetch_result(result: BrowserFetchResponse) -> str:
    """Format a BrowserFetchResponse as plain text for the LLM."""
    parts: list[str] = [
        f"status_code={result.status_code} elapsed={result.elapsed_sec}s"
    ]
    if result.truncated:
        parts.append("[RESPONSE TRUNCATED]")
    parts.append(result.text)
    return "\n".join(parts)


async def fdisp_browser_fetch(args: dict[str, Any]) -> str:
    """Format browser_fetch MCP tool result as plain text for LLM."""
    result = await service.fetch_browser(args)
    return _format_fetch_result(result)


_WEB_DISPATCH: dict[str, Any] = {
    "search_web": fdisp_search_web,
    "browser_fetch": fdisp_browser_fetch,
}


async def dispatch_web_tool(name: str, args: dict[str, Any]) -> DispatchResult:
    """Route a tool call through the web-search dispatch table."""
    return await dispatch_tool(_WEB_DISPATCH, name, args)
