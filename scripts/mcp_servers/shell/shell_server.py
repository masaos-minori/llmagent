#!/usr/bin/env python3
"""scripts/mcp_servers/shell/shell_server.py

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
import shutil
import time
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.security.posture_contract import SecurityPosture
from shared.security.result_dto import SecurityCheckStatus
from shared.security.startup_flow import run_startup_validation

from mcp_servers.audit import _audit_log
from mcp_servers.dispatch import DispatchResult, _to_call_tool_response, dispatch_tool
from mcp_servers.health_response import make_health_response
from mcp_servers.models import CallToolRequest, CallToolResponse, McpTool
from mcp_servers.server import (
    MCPServer,
    ToolArgs,
    _FastAPIApp,
    attach_auth_middleware,
    build_tools_response,
    extract_request_context,
)
from mcp_servers.shell.shell_models import (
    ShellAuthorizationError,
    ShellConfig,
    ShellRunRequest,
    ShellRunResponse,
    ShellValidationError,
    load_shell_policy,
)
from mcp_servers.shell.shell_service import ShellService, build_service
from mcp_servers.shell.shell_service_static_helpers import validate_shell_security
from mcp_servers.shell.shell_tools import TOOL_LIST

logger = logging.getLogger(__name__)

SHELL_SERVER_KEY = "shell"
SHELL_OWN_CONFIG_FILE = "shell_mcp_server.toml"

_cfg: ShellConfig = ShellConfig.load()
_service: ShellService = build_service(load_shell_policy())


def _shell_security_view(cfg: ShellConfig) -> dict[str, object]:
    """Build the non-secret view the posture fingerprint is computed from.

    Only scalars and counts are carried: allowlist entries, cwd values, the audit log
    path, the execution user, the shell path, and auth_token are never hashed by value
    (REQ-002, REQ-009).
    """
    return {
        "own_config_file": SHELL_OWN_CONFIG_FILE,
        "sandbox_backend": cfg.shell_sandbox_backend,
        "command_allowlist_count": len(cfg.command_allowlist),
        "cwd_allowed_dirs_count": len(cfg.shell_cwd_allowed_dirs),
        "env_allowlist_count": len(cfg.env_allowlist),
        "max_timeout_sec": cfg.max_timeout_sec,
        "max_output_kb": cfg.max_output_kb,
        "max_memory_mb": cfg.max_memory_mb,
        "kill_policy": cfg.kill_policy,
    }


def _build_security_posture() -> SecurityPosture:
    """Run the shared ordering against the already loaded config and return the posture.

    The flow never raises, so a policy violation still produces a posture the Agent can
    read. Only the server-security stage is supplied: the flow's built-in common stage
    covers own-config, auth-token, and published-tool checks, and this module does not
    re-read shell_mcp_server.toml or the shell policy.
    """
    return run_startup_validation(
        SHELL_SERVER_KEY,
        own_config_file=SHELL_OWN_CONFIG_FILE,
        config_view=_shell_security_view(_cfg),
        auth_token=_cfg.auth_token,
        declared_tools=tuple(tool["name"] for tool in TOOL_LIST),
        server_checks=lambda: validate_shell_security(
            _cfg.shell_sandbox_backend, _cfg.command_allowlist
        ),
    )


_security_posture: SecurityPosture = _build_security_posture()


def _shell_tool_availability(cfg: ShellConfig, tool_name: str) -> tuple[bool, str]:
    """Return (enabled, disabled_reason) for a single shell tool by name."""
    if not cfg.command_allowlist:
        return False, "command_allowlist is empty"
    return True, ""


app = FastAPI(
    title="shell-mcp",
    version="1.0.0",
    description="MCP server for sandboxed shell command execution",
)

if not _cfg.auth_token:
    raise RuntimeError(
        "shell-mcp: auth_token is empty; set MCP_SHELL_AUTH_TOKEN to a non-empty "
        "value (the server does not start without Bearer authentication)"
    )
attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token)


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
    if shutil.which("sh") is None:
        deps["shell"] = "sh not found in PATH"
    details: dict[str, object] = {
        "service": "shell-mcp",
        "sandbox_backend": _service.sandbox_backend,
    }
    result: JSONResponse = make_health_response(
        deps, details, security=_security_posture
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch and unified call endpoint
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_shell_tool(
    name: str, args: ToolArgs, idempotency_key: str | None = None
) -> DispatchResult:
    """Route shell tool calls through the service's dispatch table."""
    return await dispatch_tool(
        _service.get_dispatch_table(), name, args, idempotency_key=idempotency_key
    )


@app.get("/v1/tools")
async def list_tools(
    include_disabled: bool = False, disabled_code: str | None = None
) -> dict[str, Any]:
    """List available shell tools with schema_version and server_key="shell"."""
    annotated = [
        {**t, "enabled": enabled, "disabled_reason": reason}
        for t in TOOL_LIST
        for enabled, reason in [_shell_tool_availability(_cfg, t["name"])]
    ]
    return build_tools_response(
        cast("list[McpTool]", annotated),
        "shell",
        include_disabled=include_disabled,
        disabled_code=disabled_code,
    )


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Dispatch an MCP tool call through the shell service with audit logging."""
    enabled, reason = _shell_tool_availability(_cfg, req.name)
    if not enabled:
        return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)
    session_id, request_id, idempotency_key = extract_request_context(request)
    r = await _dispatch_shell_tool(req.name, req.args, idempotency_key=idempotency_key)
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=cast(str, req.args.get("command", ""))[:80],
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
    app_module = "mcp_servers.shell.shell_server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        """Dispatch a tool by name with the given arguments via the shell service."""
        return await _dispatch_shell_tool(name, args)


def _enforce_posture_gate() -> None:
    """Refuse HTTP bind when the posture is not validated (REQ-003, AC-003).

    The gate reads only `validated`: the payload `ready` is derived in
    `make_health_response()` from dependencies plus `validated`, so this module never
    invents its own Ready rule. The log line carries check ids and reason codes only.
    """
    if _security_posture.validated:
        return
    failed = ", ".join(
        f"{check.check_id}:{check.reason_code}"
        for check in _security_posture.checks
        if check.status is SecurityCheckStatus.FAILED
    )
    logger.error("shell-mcp: security posture FAILED (%s) — refusing to bind", failed)
    raise SystemExit(1)


if __name__ == "__main__":
    _enforce_posture_gate()
    server = ShellMCPServer()
    server.run_http()
