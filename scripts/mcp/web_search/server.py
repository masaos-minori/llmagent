#!/usr/bin/env python3
"""web_search_mcp_server.py
FastAPI server that exposes web search as an MCP (Model Context Protocol) tool.
Listens on port 8004.

Search provider: DuckDuckGo (no API key required).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from shared.logger import Logger

from mcp.dispatch import DispatchResult
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer
from mcp.web_search.formatters import dispatch_web_tool, search_web
from mcp.web_search.models import (
    SearchRequest,
    SearchResponse,
    WebSearchConfig,
    WebSearchUpstreamError,
)
from mcp.web_search.tools import TOOL_LIST

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
# Endpoint definitions
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    """Execute a web search using DuckDuckGo."""
    return await search_web({"query": req.query, "max_results": req.max_results})


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint."""
    deps: dict[str, str] = {}
    ready = len(deps) == 0
    return JSONResponse(
        {
            "status": "ok" if ready else "degraded",
            "ready": ready,
            "liveness": True,
            "restart_recommended": False,
            "operator_action_required": False,
            "dependencies": deps,
            "details": {},
        },
        status_code=200 if ready else 503,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch function
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_web_tool(name: str, args: dict[str, Any]) -> DispatchResult:
    """Route a tool call through the web-search dispatch table."""
    return await dispatch_web_tool(name, args)


# ──────────────────────────────────────────────────────────────────────────────
# Tool listing endpoint (for client-side definition validation)
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    """Return tool names and descriptions for agent.json definition validation."""
    return {
        "tools": [{**t, "server_key": "web_search"} for t in TOOL_LIST],
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
    own_config_file = "web_search_mcp_server.toml"
    app_module = "mcp.web_search.server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        return await _dispatch_web_tool(name, args)


if __name__ == "__main__":
    server = WebSearchMCPServer()
    server.run_http()
