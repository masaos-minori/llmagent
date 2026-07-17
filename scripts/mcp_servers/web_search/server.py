#!/usr/bin/env python3
"""web_search_mcp_server.py

FastAPI server that exposes web search as an MCP (Model Context Protocol) tool.
Listens on port 8004.

Search provider: DuckDuckGo (no API key required).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mcp_servers.audit import _audit_log
from mcp_servers.dispatch import DispatchResult, _to_call_tool_response
from mcp_servers.health_response import make_health_response
from mcp_servers.models import CallToolRequest, CallToolResponse
from mcp_servers.server import MCPServer
from mcp_servers.web_search.formatters import dispatch_web_tool
from mcp_servers.web_search.models import (
    WebSearchConfig,
    WebSearchUpstreamError,
)
from mcp_servers.web_search.tools import TOOL_LIST

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Typed config object (module-level singleton)
# ──────────────────────────────────────────────────────────────────────────────
_cfg: WebSearchConfig = WebSearchConfig.load()

app = FastAPI(title="web-search-mcp", version="3.0.0")


@app.exception_handler(WebSearchUpstreamError)
async def _handle_web_search_error(
    _req: Any, exc: WebSearchUpstreamError
) -> JSONResponse:
    """Handle upstream web search errors with a 502 Bad Gateway response."""
    return JSONResponse(
        status_code=502,
        content={"error": str(exc)},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint definitions
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint."""
    deps: dict[str, str] = {}
    details: dict[str, object] = {"service": "web-search-mcp"}
    result: JSONResponse = make_health_response(deps, details)
    return result


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
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Execute a web search tool by name and return the formatted text result."""
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    r = await _dispatch_web_tool(req.name, req.args)
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=req.args.get("query", ""),
        outcome=r.outcome,
        server_key="web_search",
    )
    return _to_call_tool_response(r)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
class WebSearchMCPServer(MCPServer):
    """MCPServer subclass for web-search-mcp."""

    server_name = "web-search-mcp"
    server_version = "3.0.0"
    http_port = 8004
    own_config_file = "web_search_mcp_server.toml"
    app_module = "mcp_servers.web_search.server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        """Route a web search tool call to the appropriate handler."""
        return await _dispatch_web_tool(name, args)


if __name__ == "__main__":
    server = WebSearchMCPServer()
    server.run_http()
