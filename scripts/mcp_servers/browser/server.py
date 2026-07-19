#!/usr/bin/env python3
"""mcp_servers/browser/server.py

Read-only Browser MCP server: page fetch + render-to-text (port 8016).

Provides an HTTP API via FastAPI for fetching a URL and returning its
extracted visible text content.

Security:
  - Fail-closed domain allowlist (allowed_domains in browser_mcp_server.toml)
  - IP-literal/loopback/private/reserved/multicast targets rejected unconditionally
  - Optional Bearer-token auth via auth_token in browser_mcp_server.toml
  - Read-only: no JavaScript execution, no interactive actions

Provided endpoints:
  GET  /health        Health check
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog

from mcp_servers.audit import _audit_log
from mcp_servers.browser.models import (
    BrowserAuthorizationError,
    BrowserConfig,
    BrowserValidationError,
)
from mcp_servers.browser.service import BrowserService, build_service
from mcp_servers.browser.tools import TOOL_LIST
from mcp_servers.dispatch import DispatchResult, _to_call_tool_response, dispatch_tool
from mcp_servers.health_response import make_health_response
from mcp_servers.models import CallToolRequest, CallToolResponse
from mcp_servers.server import MCPServer, ToolArgs, attach_auth_middleware

logger = logging.getLogger(__name__)

_cfg = BrowserConfig.load()
_service: BrowserService = build_service(_cfg)

app = FastAPI(
    title="browser-mcp",
    version="1.0.0",
    description="Read-only Browser MCP server: page fetch + render-to-text",
)

attach_auth_middleware(app, _cfg.auth_token or "")


@app.exception_handler(BrowserAuthorizationError)
async def _on_browser_auth_error(
    _req: Request, exc: BrowserAuthorizationError
) -> JSONResponse:
    """Handle domain-allowlist/IP-literal authorization errors by returning a 403 response."""
    return JSONResponse({"detail": str(exc)}, status_code=403)


@app.exception_handler(BrowserValidationError)
async def _on_browser_validation_error(
    _req: Request, exc: BrowserValidationError
) -> JSONResponse:
    """Handle invalid-input errors by returning a 422 response."""
    return JSONResponse({"detail": str(exc)}, status_code=422)


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_browser_tool(name: str, args: ToolArgs) -> DispatchResult:
    """Route browser tool calls through the service's dispatch table."""
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint. No external dependency probing at check time."""
    details: dict[str, object] = {"service": "browser-mcp"}
    result: JSONResponse = make_health_response({}, details)
    return result


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    """List available browser tools with server_key="browser"."""
    return {
        "tools": [{**t, "server_key": "browser"} for t in TOOL_LIST],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Dispatch an MCP tool call through the browser service with audit logging."""
    t0 = time.perf_counter()
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    r = await _dispatch_browser_tool(req.name, req.args)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=req.args.get("url", "")[:80],
        outcome=r.outcome,
        server_key="browser",
    )
    return _to_call_tool_response(r)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class BrowserMCPServer(MCPServer):
    """MCPServer subclass for browser-mcp."""

    server_name = "browser-mcp"
    server_version = "1.0.0"
    http_port = 8016
    own_config_file = "browser_mcp_server.toml"
    app_module = "mcp_servers.browser.server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: ToolArgs) -> DispatchResult:
        """Dispatch a tool invocation via the browser service."""
        return await _dispatch_browser_tool(name, args)


if __name__ == "__main__":
    server = BrowserMCPServer()
    server.run_http()  # type: ignore[attr-defined]
