#!/usr/bin/env python3
"""mcp_servers/git/server.py
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

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp_servers.audit import _audit_log
from mcp_servers.dispatch import DispatchResult, _to_call_tool_response, dispatch_tool
from mcp_servers.git.models import GitConfig, GitServiceError
from mcp_servers.git.service import build_service
from mcp_servers.git.tools import TOOL_LIST
from mcp_servers.health_response import make_health_response
from mcp_servers.models import CallToolRequest, CallToolResponse
from mcp_servers.server import MCPServer, ToolArgs, attach_auth_middleware
from shared.formatters import fmt_kvlog

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
async def list_tools() -> dict[str, list[dict[str, object]]]:
    return {
        "tools": [{**t, "server_key": "git"} for t in TOOL_LIST],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    t0 = time.perf_counter()
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    r = await _dispatch_git_tool(req.name, req.args)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=req.args.get("repo", ""),
        outcome=r.outcome,
        server_key="git",
    )
    return _to_call_tool_response(r)


@app.get("/health")
async def health() -> JSONResponse:
    deps: dict[str, str] = {}
    try:
        if shutil.which("git") is None:
            deps["git"] = "git not found in PATH"
    except OSError:
        deps["git"] = "check failed"
    details: dict[str, object] = {"service": "git-mcp"}
    result: JSONResponse = make_health_response(deps, details)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class GitMCPServer(MCPServer):
    """MCPServer subclass for git-mcp."""

    server_name = "git-mcp"
    server_version = "1.0.0"
    http_port = 8014
    own_config_file = "git_mcp_server.toml"
    app_module = "mcp_servers.git.server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: ToolArgs) -> DispatchResult:
        return await _dispatch_git_tool(name, args)


if __name__ == "__main__":
    server = GitMCPServer()
    server.run_http()
