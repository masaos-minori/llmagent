#!/usr/bin/env python3
"""web_search_mcp_server.py
FastAPI server that exposes web search as an MCP (Model Context Protocol) tool.
Listens on port 8004.

Search provider: DuckDuckGo (no API key required).
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, cast

from duckduckgo_search import DDGS
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from shared.formatters import MAX_SNIPPET_CHARS, fmt_kvlog, truncate
from shared.logger import Logger

from mcp.dispatch import DispatchResult, dispatch_tool
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer
from mcp.web_search.models import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    WebSearchConfig,
    WebSearchUpstreamError,
)
from mcp.web_search.tools import _MCP_TOOLS

# ──────────────────────────────────────────────────────────────────────────────
# Typed config object (module-level singleton)
# ──────────────────────────────────────────────────────────────────────────────
logger = Logger(__name__, "/opt/llm/logs/web-search-mcp.log")

_cfg: WebSearchConfig = WebSearchConfig.load()

app = FastAPI(title="web-search-mcp", version="3.0.0")


@app.exception_handler(WebSearchUpstreamError)
async def _handle_web_search_error(
    _req: Any, exc: WebSearchUpstreamError
) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"error": str(exc)},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Search implementation
# ──────────────────────────────────────────────────────────────────────────────
async def _search_duckduckgo(query: str, max_results: int) -> list[SearchResult]:
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


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint definitions
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    """Execute a web search using DuckDuckGo."""
    t0 = time.perf_counter()
    results = cast(
        list[SearchResult],
        await asyncio.to_thread(lambda: _search_duckduckgo(req.query, req.max_results)),
    )

    if not results:
        raise WebSearchUpstreamError("No results returned from DuckDuckGo")

    ms = (time.perf_counter() - t0) * 1000
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


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint."""
    deps: dict[str, str] = {}
    ready = len(deps) == 0
    return JSONResponse(
        {
            "status": "ok" if ready else "degraded",
            "ready": ready,
            "dependencies": deps,
            "details": {},
        },
        status_code=200 if ready else 503,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch function
# ──────────────────────────────────────────────────────────────────────────────


def _fmt_search_result(i: int, r: SearchResult) -> str:
    """Format one search result with title, URL, provider, and truncated snippet."""
    title = r.title or "(no title)"
    snippet = truncate(r.body or "", MAX_SNIPPET_CHARS)
    return f"[{i}] {title}\nURL: {r.url}\nProvider: {r.provider}\n{snippet}"


async def _fdisp_search_web(args: dict[str, Any]) -> str:
    result = await search(SearchRequest(**args))
    if not result.results:
        return "No search results found."
    header = f"[Search: {len(result.results)} results via {result.provider}]\n\n"
    lines = [_fmt_search_result(i, r) for i, r in enumerate(result.results, 1)]
    return header + "\n\n".join(lines)


_WEB_DISPATCH = {
    "search_web": _fdisp_search_web,
}


async def _dispatch_web_tool(name: str, args: dict[str, Any]) -> DispatchResult:
    """Route a tool call through the web-search dispatch table."""
    return await dispatch_tool(_WEB_DISPATCH, name, args)


# ──────────────────────────────────────────────────────────────────────────────
# Tool listing endpoint (for client-side definition validation)
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    """Return tool names and descriptions for agent.json definition validation."""
    return {
        "tools": [{**t, "server_key": "web_search"} for t in _MCP_TOOLS],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Unified tool call endpoint
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    """Execute a web search tool by name and return the formatted text result."""
    r = await _dispatch_web_tool(req.name, req.args)
    return CallToolResponse(result=r.output, is_error=r.is_error)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
class WebSearchMCPServer(MCPServer):
    """MCPServer subclass for web-search-mcp."""

    server_name = "web-search-mcp"
    server_version = "3.0.0"
    http_port = 8004
    app_module = "mcp.web_search.server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        return await _dispatch_web_tool(name, args)


if __name__ == "__main__":
    import sys

    server = WebSearchMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
