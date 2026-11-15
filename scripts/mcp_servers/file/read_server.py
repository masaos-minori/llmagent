#!/usr/bin/env python3
"""scripts/mcp_servers/file/read_server.py

MCP server for read-only filesystem operations (port 8005).

Provides an HTTP API via FastAPI for reading files and directories.
Security: Only paths under directories listed in allowed_dirs are accessible.

Provided endpoints:
  GET  /list_allowed_directories   Diagnostic; disposition pending maintainer decision (AC-4)
  GET  /health                     Health check
  GET  /v1/tools                   List available MCP tools
  POST /v1/call_tool               Dispatch an MCP tool call through the shared path
"""

from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.logger import Logger
from shared.security.posture_contract import SecurityPosture
from shared.security.result_dto import SecurityCheckStatus
from shared.security.startup_flow import run_startup_validation

from mcp_servers.dispatch import DispatchResult, _to_call_tool_response, dispatch_tool
from mcp_servers.file.common import (
    FileAuthorizationError,
    FileValidationError,
    _health,
    _on_auth_error,
    _on_not_found,
    _on_validation_error,
    availability_flags,
)
from mcp_servers.file.read_models import FileReadConfig
from mcp_servers.file.read_security import validate_file_read_security
from mcp_servers.file.read_service import ReadFileService, build_service
from mcp_servers.file.read_tools import TOOL_LIST
from mcp_servers.models import CallToolRequest, CallToolResponse, McpTool
from mcp_servers.server import (
    MCPServer,
    ToolArgs,
    _FastAPIApp,
    attach_auth_middleware,
    build_tools_response,
    extract_request_context,
    require_auth_token,
)

logger = Logger(__name__, "/opt/llm/logs/file-read-mcp.log")

_cfg = FileReadConfig.load()
_service: ReadFileService = build_service(_cfg)

FILE_READ_SERVER_KEY = "file_read"
FILE_READ_OWN_CONFIG_FILE = "file_read_mcp_server.toml"


def _read_security_view(cfg: FileReadConfig) -> dict[str, object]:
    """Build the non-secret view the posture fingerprint is computed from.

    Only scalars and counts are carried: `auth_token` is a Secret and every
    `allowed_dirs` value is a path.
    """
    return {
        "own_config_file": FILE_READ_OWN_CONFIG_FILE,
        "allowed_dirs_count": len(cfg.allowed_dirs),
        "max_read_bytes": cfg.max_read_bytes,
    }


def _build_security_posture(cfg: FileReadConfig) -> SecurityPosture:
    """Run the shared ordering against the already loaded config and return the posture.

    The flow never raises, so a policy violation still produces a posture the Agent can
    read. Only the server-security stage is supplied: the flow's built-in common stage
    covers own-config, auth-token, and published-tool checks, and this module does not
    re-read file_read_mcp_server.toml. The config is a parameter because FileReadConfig is
    frozen, so a test rebuilds a posture with `dataclasses.replace()` instead of mutating
    the loaded singleton.
    """
    return run_startup_validation(
        FILE_READ_SERVER_KEY,
        own_config_file=FILE_READ_OWN_CONFIG_FILE,
        config_view=_read_security_view(cfg),
        auth_token=cfg.auth_token,
        declared_tools=tuple(tool["name"] for tool in TOOL_LIST),
        server_checks=lambda: validate_file_read_security(cfg),
    )


_security_posture: SecurityPosture = _build_security_posture(_cfg)

app = FastAPI(
    title="file-read-mcp",
    version="1.0.0",
    description="MCP server for read-only filesystem operations",
)

require_auth_token("file-read-mcp", "MCP_FILE_READ_AUTH_TOKEN", _cfg.auth_token)
attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token)

app.add_exception_handler(FileAuthorizationError, _on_auth_error)
app.add_exception_handler(FileNotFoundError, _on_not_found)
app.add_exception_handler(FileValidationError, _on_validation_error)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/list_allowed_directories")
async def list_allowed_directories() -> dict[str, list[str]]:
    """Return the list of allowed directories for file access.

    NEEDS CONFIRMATION (AC-4): resolves and returns allowlist paths (path-disclosure
    risk). Disposition (keep as diagnostic vs remove) is a maintainer decision, not
    recorded here; the route is retained until the maintainer decides.
    """
    return {"allowed_dirs": [str(d.resolve()) for d in _service._allowed_dirs]}


@app.get("/health")
async def health() -> JSONResponse:
    """Return health check status."""
    result: JSONResponse = await _health(_cfg.allowed_dirs, posture=_security_posture)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch and unified call endpoint
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_read_tool(
    name: str, args: ToolArgs, idempotency_key: str | None = None
) -> DispatchResult:
    """Route a tool call through the shared dispatch mechanism."""
    return await dispatch_tool(
        _service.get_dispatch_table(), name, args, idempotency_key=idempotency_key
    )


def _annotate_tool(
    tool: McpTool, enabled: bool, disabled_reason: str
) -> dict[str, Any]:
    """Return a copy of tool with server_key and availability fields attached."""
    return {
        **tool,
        "server_key": "file_read",
        "enabled": enabled,
        "disabled_reason": disabled_reason,
    }


@app.get("/v1/tools")
async def list_tools(
    include_disabled: bool = False, disabled_code: str | None = None
) -> dict[str, Any]:
    """Return the MCP tool list with schema_version and server_key appended."""
    enabled, disabled_reason = availability_flags(_cfg.allowed_dirs)
    annotated = [_annotate_tool(t, enabled, disabled_reason) for t in TOOL_LIST]
    return build_tools_response(
        cast("list[McpTool]", annotated),
        "file_read",
        include_disabled=include_disabled,
        disabled_code=disabled_code,
    )


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Handle MCP call_tool requests with validation and error handling.

    This server emits no `_audit_log()` record: reads are audited only by the
    agent-side `tool_exec` event (see `mcp_06_05_reading-audit-logs.md`).
    """
    if not _cfg.allowed_dirs:
        return CallToolResponse(
            result="Tool disabled: allowed_dirs is empty", is_error=True
        )
    try:
        req.validate_args()
    except ValueError as e:
        return CallToolResponse(result=f"Validation error: {e}", is_error=True)
    _, _, idempotency_key = extract_request_context(request)
    r = await _dispatch_read_tool(req.name, req.args, idempotency_key=idempotency_key)
    return _to_call_tool_response(r)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class FileReadMCPServer(MCPServer):
    """MCPServer subclass for file-read-mcp."""

    server_name = "file-read-mcp"
    server_version = "1.0.0"
    http_port = 8005
    own_config_file = "file_read_mcp_server.toml"
    app_module = "mcp_servers.file.read_server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        """Dispatch a tool call to the appropriate handler."""
        return await _dispatch_read_tool(name, args)


def _enforce_posture_gate() -> None:
    """Refuse HTTP bind when the posture is not validated (AC-003).

    The gate reads only `validated`: the payload `ready` is derived in
    `make_health_response()` from dependencies plus `validated`, so this module never
    invents its own Ready rule. The log line carries check ids and reason codes only;
    allowed directory paths are excluded.
    """
    if _security_posture.validated:
        return
    failed = ", ".join(
        f"{check.check_id}:{check.reason_code}"
        for check in _security_posture.checks
        if check.status is SecurityCheckStatus.FAILED
    )
    logger.error(
        "file-read-mcp: security posture FAILED (%s) — refusing to bind", failed
    )
    raise SystemExit(1)


if __name__ == "__main__":
    _enforce_posture_gate()
    server = FileReadMCPServer()
    server.run_http()
