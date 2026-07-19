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

import logging
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog

from mcp_servers.audit import _audit_log
from mcp_servers.dispatch import DispatchResult, _to_call_tool_response, dispatch_tool
from mcp_servers.health_response import make_health_response
from mcp_servers.models import CallToolRequest, CallToolResponse
from mcp_servers.server import (
    MCPServer,
    ToolArgs,
    build_tools_response,
)
from mcp_servers.shell.models import (
    ShellAuthorizationError,
    ShellRunRequest,
    ShellRunResponse,
    ShellValidationError,
    load_shell_policy,
)
from mcp_servers.shell.service import ShellService, build_service
from mcp_servers.shell.tools import TOOL_LIST

logger = logging.getLogger(__name__)

_service: ShellService = build_service(load_shell_policy())

app = FastAPI(
    title="shell-mcp",
    version="1.0.0",
    description="MCP server for sandboxed shell command execution",
)


@app.exception_handler(ShellAuthorizationError)
async def _on_shell_auth_error(_req: Any, exc: ShellAuthorizationError) -> JSONResponse:
    """Handle authorization errors by returning a 403 response."""
    return JSONResponse({"detail": str(exc)}, status_code=403)


@app.exception_handler(ShellValidationError)
async def _on_shell_validation_error(
    _req: Any, exc: ShellValidationError
) -> JSONResponse:
    """Handle validation errors by returning a 422 response."""
    return JSONResponse({"detail": str(exc)}, status_code=422)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.post("/shell_run", response_model=ShellRunResponse)
async def shell_run(req: ShellRunRequest) -> ShellRunResponse:
    """Execute a sandboxed shell command via the shell service."""
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
async def health() -> JSONResponse:
    """Health check endpoint. Returns degraded when 'sh' is not found in PATH."""
    deps: dict[str, str] = {}
    try:
        import shutil as _shutil

        if _shutil.which("sh") is None:
            deps["shell"] = "sh not found in PATH"
    except (ImportError, OSError):
        deps["shell"] = "check failed"
    details: dict[str, object] = {
        "service": "shell-mcp",
        "sandbox_backend": _service.sandbox_backend,
    }
    result: JSONResponse = make_health_response(deps, details)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch and unified call endpoint
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_shell_tool(name: str, args: ToolArgs) -> DispatchResult:
    """Route shell tool calls through the service's dispatch table."""
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    """List available shell tools with schema_version and server_key="shell"."""
    return build_tools_response(TOOL_LIST, "shell")


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Dispatch an MCP tool call through the shell service with audit logging."""
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
        outcome=r.outcome,
        server_key="shell",
    )
    return _to_call_tool_response(r)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class ShellMCPServer(MCPServer):
    """MCPServer subclass for shell-mcp."""

    server_name = "shell-mcp"
    server_version = "1.0.0"
    http_port = 8009
    own_config_file = "shell_mcp_server.toml"
    app_module = "mcp_servers.shell.server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        """Dispatch a tool by name with the given arguments via the shell service."""
        return await _dispatch_shell_tool(name, args)


if __name__ == "__main__":
    server = ShellMCPServer()
    server.run_http()  # type: ignore[attr-defined]
