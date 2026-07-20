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
    attach_auth_middleware,
    build_tools_response,
)
from mcp_servers.web_search import health, metrics
from mcp_servers.web_search.formatters import dispatch_web_tool
from mcp_servers.web_search.web_search_models import (
    BrowserAuthorizationError,
    BrowserValidationError,
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

app = FastAPI(
    title="web-search-mcp",
    version="4.0.0",
    description="web-search-mcp: web search (search_web) + read-only page fetch (browser_fetch)",
)

attach_auth_middleware(app, _cfg.browser_auth_token or "")


@app.exception_handler(WebSearchUpstreamError)
async def _handle_web_search_error(
    _req: Any, exc: WebSearchUpstreamError
) -> JSONResponse:
    """Handle upstream web search errors with a 502 Bad Gateway response."""
    return JSONResponse(
        status_code=502,
        content={"error": str(exc)},
    )


@app.exception_handler(BrowserAuthorizationError)
async def _on_browser_auth_error(
    _req: Any, exc: BrowserAuthorizationError
) -> JSONResponse:
    """Handle domain-allowlist/IP-literal authorization errors by returning a 403 response."""
    return JSONResponse({"detail": str(exc)}, status_code=403)


@app.exception_handler(BrowserValidationError)
async def _on_browser_validation_error(
    _req: Any, exc: BrowserValidationError
) -> JSONResponse:
    """Handle invalid-input errors by returning a 422 response."""
    return JSONResponse({"detail": str(exc)}, status_code=422)


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
    details["browser_provider"] = health.browser_health_details()
    details["browser_metrics"] = metrics.browser_snapshot()
    if health.is_degraded():
        deps["web_search_provider"] = "degraded: repeated provider failures"
    if health.is_browser_degraded():
        deps["browser_fetch_provider"] = "degraded: repeated fetch failures"
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
    """Execute a web-search-mcp tool (search_web or browser_fetch) by name and
    return the formatted text result.

    `outcome`/`error_type`/`latency_ms` here are for the always-fires audit
    log only — health/metrics recording is owned entirely by
    `service.search_web()`/`service.fetch_browser()` (called via
    `dispatch_web_tool` -> `fdisp_search_web`/`fdisp_browser_fetch`), so this
    function must not call `health.record_*`/`metrics.record_*` itself (that
    would double-count every query).
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
    except BrowserAuthorizationError:
        # BrowserAuthorizationError (RuntimeError-based) propagates past
        # dispatch_tool()'s `except ValueError` catch, so it is handled here
        # (unlike BrowserValidationError, a ValueError subclass that
        # dispatch_tool() always converts into an is_error=True
        # DispatchResult first — surfaced via _classify_dispatch_error's
        # "Validation error: " prefix match instead, same as search_web's
        # own ValueError handling).
        outcome = "error"
        error_type = "authorization_error"
        latency_ms = (time.perf_counter() - t0) * 1000
        raise
    except Exception:
        outcome = "error"
        error_type = "unexpected_error"
        latency_ms = (time.perf_counter() - t0) * 1000
        raise
    finally:
        if req.name == "search_web":
            query = str(req.args.get("query", ""))
            target = query
            detail = (
                f"max_results={req.args.get('max_results', '')} "
                f"latency_ms={latency_ms:.0f} "
                f"query_preview={query[:80]!r} "
                f"query_hash={hashlib.sha256(query.strip().lower().encode()).hexdigest()[:16]}"
            )
        else:
            url = str(req.args.get("url", ""))
            target = url
            detail = f"latency_ms={latency_ms:.0f} url_preview={url[:80]!r}"
        _audit_log(
            logger,
            session_id=session_id,
            request_id=request_id,
            action=req.name,
            target=target,
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
    server_version = "4.0.0"
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
