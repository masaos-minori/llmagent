#!/usr/bin/env python3
"""shell_mcp_server.py
MCP server for sandboxed shell command execution (port 8009).

Provides an HTTP API via FastAPI for executing whitelisted shell commands.
Security:
  - argv[0] must be in the configured command allowlist
  - cwd must be under shell_cwd_allowed_dirs
  - Resource limits applied via setrlimit in child process
  - All executions are audit-logged to /opt/llm/logs/shell_audit.log
  - Service runs as llm-agent (non-root) OS user

Provided endpoints:
  POST /shell_run   Execute a sandboxed shell command
  GET  /health      Health check
"""

import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.logger import Logger

from mcp.audit import _audit_log
from mcp.dispatch import DispatchResult, dispatch_tool
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs
from mcp.shell.models import (
    ShellAuthorizationError,
    ShellRunRequest,
    ShellRunResponse,
    ShellValidationError,
    load_shell_policy,
)
from mcp.shell.service import ShellService, build_service
from mcp.shell.tools import _MCP_TOOLS

logger = Logger(__name__, "/opt/llm/logs/shell-mcp.log")

_service: ShellService = build_service(load_shell_policy())

app = FastAPI(
    title="shell-mcp",
    version="1.0.0",
    description="MCP server for sandboxed shell command execution",
)


@app.exception_handler(ShellAuthorizationError)
async def _on_shell_auth_error(_req: Any, exc: ShellAuthorizationError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=403)


@app.exception_handler(ShellValidationError)
async def _on_shell_validation_error(
    _req: Any, exc: ShellValidationError
) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=422)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.post("/shell_run", response_model=ShellRunResponse)
async def shell_run(req: ShellRunRequest) -> ShellRunResponse:
    t0 = time.perf_counter()
    result = await _service.run_command(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "shell_run",
            cmd=req.command[:80],
            exit=result.exit_code,
            timed_out=result.timed_out,
            truncated=result.truncated,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.get("/health")
async def health() -> dict[str, object]:
    deps: dict[str, str] = {}
    try:
        import shutil as _shutil
        if _shutil.which("sh") is None:
            deps["shell"] = "sh not found in PATH"
    except Exception:
        deps["shell"] = "check failed"
    ready = len(deps) == 0
    return {"status": "ok", "ready": ready, "dependencies": deps, "details": {}}


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch and unified call endpoint
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_shell_tool(name: str, args: ToolArgs) -> DispatchResult:
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {**t, "server_key": "shell"}
            for t in _MCP_TOOLS
        ],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    r = await _dispatch_shell_tool(req.name, req.args)
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=req.args.get("command", "")[:80],
        outcome="error" if r.is_error else "ok",
    )
    return CallToolResponse(result=r.output, is_error=r.is_error)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class ShellMCPServer(MCPServer):
    """MCPServer subclass for shell-mcp."""

    server_name = "shell-mcp"
    server_version = "1.0.0"
    http_port = 8009
    app_module = "mcp.shell.server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        return await _dispatch_shell_tool(name, args)


if __name__ == "__main__":
    import sys

    server = ShellMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
