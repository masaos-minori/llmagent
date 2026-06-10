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
import dataclasses
import os
import time
from typing import Any

import httpx
import orjson
from duckduckgo_search import DDGS
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader
from shared.formatters import MAX_SNIPPET_CHARS, fmt_kvlog, truncate
from shared.logger import Logger

from mcp.dispatch import dispatch_tool
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer

# ──────────────────────────────────────────────────────────────────────────────
# Domain exception
# ──────────────────────────────────────────────────────────────────────────────


class WebSearchUpstreamError(RuntimeError):
    """Raised when all search providers fail."""

    pass


# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────
logger = Logger(__name__, "/opt/llm/logs/web-search-mcp.log")


@dataclasses.dataclass
class WebSearchConfig:
    """Typed configuration for the Web Search MCP server."""

    default_max_results: int = 5
    max_results_limit: int = 20
    http_timeout: float = 30.0
    search_providers: list[str] = dataclasses.field(
        default_factory=lambda: ["duckduckgo"]
    )
    brave_search_url: str = ""
    bing_search_url: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> WebSearchConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            default_max_results=int(d.get("default_max_results", 5)),
            max_results_limit=int(d.get("max_results_limit", 20)),
            http_timeout=float(d.get("http_timeout", 30.0)),
            search_providers=list(d.get("search_providers", ["duckduckgo"])),
            brave_search_url=str(d.get("brave_search_url", "")),
            bing_search_url=str(d.get("bing_search_url", "")),
        )

    @classmethod
    def load(cls) -> WebSearchConfig:
        """Load from web_search_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("web_search_mcp_server.toml"))


# DEFAULT_MAX_RESULTS and MAX_RESULTS_LIMIT as class-level constants for Pydantic schema
DEFAULT_MAX_RESULTS: int = 5
MAX_RESULTS_LIMIT: int = 20

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
# Pydantic schema definitions
# ──────────────────────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    """Request schema for POST /search"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query string",
    )
    max_results: int = Field(
        DEFAULT_MAX_RESULTS,
        ge=1,
        le=MAX_RESULTS_LIMIT,
        description="Maximum number of results to return (max 20)",
    )


class SearchResult(BaseModel):
    """Schema for a single search result item"""

    title: str
    url: str
    body: str
    provider: str  # Name of the provider that returned this result


class SearchResponse(BaseModel):
    """Response schema for POST /search"""

    query: str
    results: list[SearchResult]
    provider: str  # Name of the provider actually used


# ──────────────────────────────────────────────────────────────────────────────
# Per-provider search implementations
# ──────────────────────────────────────────────────────────────────────────────
async def _search_brave(query: str, max_results: int) -> list[SearchResult]:
    """Execute a text search using the Brave Search API.
    Returns an empty list if the API key is not set.
    """
    if not BRAVE_API_KEY:
        return []
    cfg = WebSearchConfig.load()
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY,
    }
    params: dict[str, str | int] = {"q": query, "count": max_results}
    async with httpx.AsyncClient(timeout=float(cfg.http_timeout)) as client:
        resp = await client.get(
            str(cfg.brave_search_url),
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
    cfg = WebSearchConfig.load()
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    # mkt is fixed for this Japanese-only deployment
    params: dict[str, str | int] = {"q": query, "count": max_results, "mkt": "ja-JP"}
    async with httpx.AsyncClient(timeout=float(cfg.http_timeout)) as client:
        resp = await client.get(
            str(cfg.bing_search_url),
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
    cfg = WebSearchConfig.load()
    for provider in cfg.search_providers:
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
    cfg = WebSearchConfig.load()
    return {
        "status": "ok",
        "providers": cfg.search_providers,
        "brave_key": "set" if BRAVE_API_KEY else "not_set",
        "bing_key": "set" if BING_API_KEY else "not_set",
    }


# ──────────────────────────────────────────────────────────────────────────────
# MCP tool definitions (MCP inputSchema format, used by /v1/call_tool routing)
# ──────────────────────────────────────────────────────────────────────────────
_MCP_TOOLS = [
    {
        "name": "search_web",
        "description": (
            "Search the web for the latest information. "
            "Use when the local DB does not contain the needed information"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: configured)",
                },
            },
            "required": ["query"],
        },
    },
]


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


async def _dispatch_web_tool(name: str, args: dict[str, Any]) -> tuple[str, bool]:
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
    result, is_error = await _dispatch_web_tool(req.name, req.args)
    return CallToolResponse(result=result, is_error=is_error)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
class WebSearchMCPServer(MCPServer):
    """MCPServer subclass for web-search-mcp."""

    server_name = "web-search-mcp"
    server_version = "3.0.0"
    http_port = 8004
    app_module = "web_search_mcp_server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        return await _dispatch_web_tool(name, args)


if __name__ == "__main__":
    import sys

    server = WebSearchMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
