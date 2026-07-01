#!/usr/bin/env python3
"""mcp/cicd/server.py
CI/CD MCP server (GitHub Actions backend, port 8012).

Provides HTTP endpoints for triggering and inspecting GitHub Actions workflows.

Security:
  - repo_allowlist: only listed 'owner/repo' slugs are accessible (fail-closed)
  - workflow_allowlist: restrict triggerable workflows (empty = deny all (fail-closed))
  - max_log_size_kb: log output is capped to prevent large data dumps
  - Optional Bearer-token auth via auth_token in cicd_mcp_server.toml

Provided endpoints:
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
  GET  /health        Health check
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog

from mcp.audit import _audit_log
from mcp.cicd.models import (
    CicdAuthorizationError,
    CicdConfig,
    CicdNotFoundError,
    CicdUpstreamError,
    CicdValidationError,
)
from mcp.cicd.service import CiCdService, build_service
from mcp.cicd.tools import TOOL_LIST
from mcp.dispatch import DispatchResult, ToolArgs, dispatch_tool
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import (
    MCPServer,
    attach_auth_middleware,
)

logger = logging.getLogger(__name__)

_cfg = CicdConfig.load()
_service: CiCdService = build_service(_cfg)

app = FastAPI(
    title="cicd-mcp",
    version="1.0.0",
    description="CI/CD (GitHub Actions) MCP server",
)

attach_auth_middleware(app, _cfg.auth_token or "")


@app.exception_handler(CicdAuthorizationError)
async def _on_cicd_auth_error(_req: Any, exc: CicdAuthorizationError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=403)


@app.exception_handler(CicdNotFoundError)
async def _on_cicd_not_found(_req: Any, exc: CicdNotFoundError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=404)


@app.exception_handler(CicdValidationError)
async def _on_cicd_validation_error(
    _req: Any, exc: CicdValidationError
) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=422)


@app.exception_handler(CicdUpstreamError)
async def _on_cicd_upstream_error(_req: Any, exc: CicdUpstreamError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=502)


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_cicd_tool(name: str, args: ToolArgs) -> DispatchResult:
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [{**t, "server_key": "cicd"} for t in TOOL_LIST],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    t0 = time.perf_counter()
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    r = await _dispatch_cicd_tool(req.name, req.args)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=req.args.get("repo", ""),
        outcome="error" if r.is_error else "ok",
        server_key="cicd",
    )
    return CallToolResponse(result=r.output, is_error=r.is_error)


@app.get("/health")
async def health() -> JSONResponse:
    deps: dict[str, str] = {}
    try:
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            deps["github_token"] = "not_set"
    except (RuntimeError, OSError):
        deps["config"] = "check failed"
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
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class CiCdMCPServer(MCPServer):
    """MCPServer subclass for cicd-mcp (GitHub Actions backend)."""

    server_name = "cicd-mcp"
    server_version = "1.0.0"
    http_port = 8012
    app_module = "mcp.cicd.server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        return await _dispatch_cicd_tool(name, args)


if __name__ == "__main__":
    server = CiCdMCPServer()
    server.run_http()
