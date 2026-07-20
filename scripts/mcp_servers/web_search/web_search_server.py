#!/usr/bin/env python3
"""web_search_mcp_server.py

FastAPI server that exposes web search as an MCP (Model Context Protocol) tool.
Listens on port 8004.

Search provider: DuckDuckGo (no API key required).
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mcp_servers.audit import _audit_log
from mcp_servers.dispatch import DispatchResult, _to_call_tool_response
from mcp_servers.health_response import make_health_response
from mcp_servers.models import CallToolRequest, CallToolResponse
from mcp_servers.server import (
    MCPServer,
    build_tools_response,
)
from mcp_servers.web_search import health, metrics
from mcp_servers.web_search.formatters import dispatch_web_tool
from mcp_servers.web_search.web_search_models import (
    WebSearchConfig,
    WebSearchNetworkError,
    WebSearchParseError,
    WebSearchTimeoutError,
    WebSearchUpstreamError,
)
from mcp_servers.web_search.web_search_tools import TOOL_LIST

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
async def health_endpoint() -> JSONResponse:
    """Health check endpoint."""
    deps: dict[str, str] = {}
    details: dict[str, object] = {"service": "web-search-mcp"}
    details["provider"] = health.health_details()
    details["metrics"] = metrics.snapshot()
    if health.is_degraded():
        deps["web_search_provider"] = "degraded: repeated provider failures"
    result: JSONResponse = make_health_response(deps, details)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch function
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_web_tool(name: str, args: dict[str, Any]) -> DispatchResult:
    """Route a tool call through the web-search dispatch table."""
    return await dispatch_web_tool(name, args)


def _classify_dispatch_error(output: str) -> str:
    """Classify a non-raised DispatchResult error by its output text prefix."""
    if output.startswith("Validation error: "):
        return "validation_error"
    if output.startswith("Unknown tool: "):
        return "unknown_tool"
    if output == "Tool name must be a non-empty string":
        return "invalid_tool_name"
    return "dispatch_error"


def _classify_upstream_error(exc: WebSearchUpstreamError) -> str:
    """Classify a raised WebSearchUpstreamError by its concrete subclass.

    web_search_models.py now defines distinct WebSearchUpstreamError
    subclasses (WebSearchTimeoutError, WebSearchNetworkError,
    WebSearchParseError, WebSearchProviderError), so classification uses
    isinstance checks rather than a substring match on str(exc).
    """
    if isinstance(exc, WebSearchTimeoutError):
        return "timeout"
    if isinstance(exc, WebSearchNetworkError):
        return "network_error"
    if isinstance(exc, WebSearchParseError):
        return "parse_error"
    return "provider_error"


# ──────────────────────────────────────────────────────────────────────────────
# Tool listing endpoint (for client-side definition validation)
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    """Return tool names and descriptions for agent.json definition validation."""
    return build_tools_response(TOOL_LIST, "web_search")


# ──────────────────────────────────────────────────────────────────────────────
# Unified tool call endpoint
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Execute a web search tool by name and return the formatted text result.

    `outcome`/`error_type`/`latency_ms` here are for the always-fires audit
    log only — health/metrics recording is owned entirely by
    `service.search_web()` (called via `dispatch_web_tool` ->
    `fdisp_search_web`), so this function must not call
    `health.record_*`/`metrics.record_query` itself (that would double-count
    every query).
    """
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    t0 = time.perf_counter()
    outcome = "ok"
    error_type = ""
    latency_ms = 0.0
    try:
        r = await _dispatch_web_tool(req.name, req.args)
        outcome = r.outcome
        latency_ms = (time.perf_counter() - t0) * 1000
        if outcome == "error":
            error_type = _classify_dispatch_error(r.output)
        return _to_call_tool_response(r)
    except WebSearchUpstreamError as e:
        outcome = "error"
        error_type = _classify_upstream_error(e)
        latency_ms = (time.perf_counter() - t0) * 1000
        raise
    except Exception:
        outcome = "error"
        error_type = "unexpected_error"
        latency_ms = (time.perf_counter() - t0) * 1000
        raise
    finally:
        query = str(req.args.get("query", ""))
        detail = (
            f"max_results={req.args.get('max_results', '')} "
            f"latency_ms={latency_ms:.0f} "
            f"query_preview={query[:80]!r} "
            f"query_hash={hashlib.sha256(query.strip().lower().encode()).hexdigest()[:16]}"
        )
        _audit_log(
            logger,
            session_id=session_id,
            request_id=request_id,
            action=req.name,
            target=query,
            outcome=outcome,
            error_type=error_type,
            server_key="web_search",
            detail=detail,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
class WebSearchMCPServer(MCPServer):
    """MCPServer subclass for web-search-mcp."""

    server_name = "web-search-mcp"
    server_version = "3.0.0"
    http_port = 8004
    own_config_file = "web_search_mcp_server.toml"
    app_module = "mcp_servers.web_search.web_search_server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        """Route a web search tool call to the appropriate handler."""
        return await _dispatch_web_tool(name, args)


if __name__ == "__main__":
    server = WebSearchMCPServer()
    server.run_http()
