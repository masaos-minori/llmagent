#!/usr/bin/env python3
"""mcp/git/server.py
Local git operations MCP server (port 8014).

Provides an HTTP API via FastAPI for safe git operations against allowlisted repositories.

Security:
  - Operations are restricted to repositories in allowed_repo_paths (fail-closed)
  - read_only=true (default) prevents all write operations (add/commit/checkout/pull/push)
  - All write tools support dry_run=True for preview without side effects
  - Optional Bearer-token auth via auth_token in git_mcp_server.toml

Provided endpoints:
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
  GET  /health        Health check
"""

from __future__ import annotations

import logging
import shutil
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog

from mcp.dispatch import DispatchResult, dispatch_tool
from mcp.git.models import GitConfig, GitServiceError
from mcp.git.service import build_service
from mcp.git.tools import _MCP_TOOLS
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs, attach_auth_middleware

logger = logging.getLogger(__name__)

_cfg = GitConfig.load()
_service = build_service(_cfg)

app = FastAPI(
    title="git-mcp",
    version="1.0.0",
    description="Local git operations MCP server",
)

attach_auth_middleware(app, _cfg.auth_token or "")


@app.exception_handler(GitServiceError)
async def _on_git_service_error(_req: Request, exc: GitServiceError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=500)


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_git_tool(name: str, args: ToolArgs) -> DispatchResult:
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [{**t, "server_key": "git"} for t in _MCP_TOOLS],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    t0 = time.perf_counter()
    r = await _dispatch_git_tool(req.name, req.args)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
    return CallToolResponse(result=r.output, is_error=r.is_error)


@app.get("/health")
async def health() -> dict[str, object]:
    deps: dict[str, str] = {}
    try:
        if shutil.which("git") is None:
            deps["git"] = "git not found in PATH"
    except Exception:
        deps["git"] = "check failed"
    ready = len(deps) == 0
    return {"status": "ok", "ready": ready, "dependencies": deps, "details": {}}


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class GitMCPServer(MCPServer):
    """MCPServer subclass for git-mcp."""

    server_name = "git-mcp"
    server_version = "1.0.0"
    http_port = 8014
    app_module = "mcp.git.server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        return await _dispatch_git_tool(name, args)


if __name__ == "__main__":
    import sys

    server = GitMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
