#!/usr/bin/env python3
"""web_search_mcp_server.py
FastAPI server that exposes web search as an MCP (Model Context Protocol) tool.
Listens on port 8004.

Supported search providers (priority order in config/web_search_mcp_server.toml):
  brave      : Brave Search API (requires BRAVE_API_KEY env var)
  bing       : Bing Web Search API v7 (requires BING_API_KEY env var)
  duckduckgo : DuckDuckGo (no API key required; uses synchronous library)

Providers are tried in order; on failure or zero results the next provider is used.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx
import orjson
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

# API keys read from environment variables (configured in /etc/conf.d/web-search-mcp)
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
BING_API_KEY = os.environ.get("BING_API_KEY", "")

# Warn once at module load time to avoid log noise on every request
if not BRAVE_API_KEY:
    logger.warning("BRAVE_API_KEY is not set; brave provider will always be skipped")
if not BING_API_KEY:
    logger.warning("BING_API_KEY is not set; bing provider will always be skipped")

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
# Per-provider search implementations
# ──────────────────────────────────────────────────────────────────────────────
async def _search_brave(query: str, max_results: int) -> list[SearchResult]:
    """Execute a text search using the Brave Search API.
    Returns an empty list if the API key is not set.
    """
    if not BRAVE_API_KEY:
        return []
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY,
    }
    params: dict[str, str | int] = {"q": query, "count": max_results}
    async with httpx.AsyncClient(timeout=float(_cfg.http_timeout)) as client:
        resp = await client.get(
            str(_cfg.brave_search_url),
            headers=headers,
            params=params,
        )
    resp.raise_for_status()
    raw = orjson.loads(resp.content).get("web", {}).get("results", [])
    return [
        SearchResult(
            title=r.get("title", ""),
            url=r.get("url", ""),
            body=r.get("description", ""),
            provider="brave",
        )
        for r in raw
    ]


async def _search_bing(query: str, max_results: int) -> list[SearchResult]:
    """Execute a text search using Bing Web Search API v7.
    Returns an empty list if the API key is not set.
    """
    if not BING_API_KEY:
        return []
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    # mkt is fixed for this Japanese-only deployment
    params: dict[str, str | int] = {"q": query, "count": max_results, "mkt": "ja-JP"}
    async with httpx.AsyncClient(timeout=float(_cfg.http_timeout)) as client:
        resp = await client.get(
            str(_cfg.bing_search_url),
            headers=headers,
            params=params,
        )
    resp.raise_for_status()
    raw = orjson.loads(resp.content).get("webPages", {}).get("value", [])
    return [
        SearchResult(
            title=r.get("name", ""),
            url=r.get("url", ""),
            body=r.get("snippet", ""),
            provider="bing",
        )
        for r in raw
    ]


async def _search_duckduckgo(query: str, max_results: int) -> list[SearchResult]:
    """Execute a text search using DuckDuckGo. No API key required.
    DDGS is a synchronous library, so it is run in a thread pool via asyncio.to_thread.
    """

    def _sync_search() -> list[dict]:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))

    raw = await asyncio.to_thread(_sync_search)
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
_PROVIDER_FUNCS = {
    "brave": _search_brave,
    "bing": _search_bing,
    "duckduckgo": _search_duckduckgo,
}


async def _try_provider(
    provider: str,
    query: str,
    max_results: int,
) -> list[SearchResult] | None:
    """Try one provider; returns results on success, None on failure or zero results."""
    func = _PROVIDER_FUNCS.get(provider)
    # Guard: skip unrecognised provider names in config
    if func is None:
        logger.warning(
            fmt_kvlog("search_try", provider=provider, result="unknown_provider"),
        )
        return None
    results = await func(query, max_results)
    if results:
        return results
    logger.info(
        fmt_kvlog(
            "search_try",
            provider=provider,
            q=query[:80],
            n=0,
            result="zero_results_fallback",
        ),
    )
    return None


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    """Execute a web search by trying configured providers in order.
    Falls back to the next provider when the current one fails or returns zero results.
    Returns 502 if all providers fail.
    """
    t0 = time.perf_counter()
    for provider in _cfg.search_providers:
        try:
            results = await _try_provider(provider, req.query, req.max_results)
            if results is not None:
                ms = (time.perf_counter() - t0) * 1000
                logger.info(
                    fmt_kvlog(
                        "search",
                        q=req.query[:80],
                        provider=provider,
                        n=len(results),
                        ms=f"{ms:.0f}",
                    ),
                )
                return SearchResponse(
                    query=req.query,
                    results=results,
                    provider=provider,
                )
        except (httpx.HTTPStatusError, TimeoutError):
            logger.warning(
                fmt_kvlog(
                    "search_provider_fail",
                    provider=provider,
                    error_class="network_error",
                ),
            )
    raise WebSearchUpstreamError("All search providers failed")


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health check endpoint. Returns configured providers and API key availability."""
    return {
        "status": "ok",
        "providers": _cfg.search_providers,
        "brave_key": "set" if BRAVE_API_KEY else "not_set",
        "bing_key": "set" if BING_API_KEY else "not_set",
    }


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
        "tools": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in _MCP_TOOLS
        ],
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
