#!/usr/bin/env python3
"""scripts/mcp_servers/file/delete_server.py

MCP server for delete filesystem operations (port 8008).

Provides an HTTP API via FastAPI for deleting files and directories.
Security: Only paths under directories listed in allowed_dirs are accessible.
All operations are audit-logged to /opt/llm/logs/delete_audit.log.

Provided endpoints:
  POST /delete_file        Delete a file
  POST /delete_directory   Delete a directory (recursive option available)
  GET  /health             Health check
"""

import time
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.logger import Logger
from shared.security.posture_contract import SecurityPosture
from shared.security.result_dto import SecurityCheckStatus
from shared.security.startup_flow import run_startup_validation

from mcp_servers.audit import _audit_log
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
from mcp_servers.file.delete_models import (
    DeleteDirectoryRequest,
    DeleteDirectoryResponse,
    DeleteFileRequest,
    DeleteFileResponse,
    FileDeleteConfig,
)
from mcp_servers.file.delete_service import (
    AUDIT_LOG_PATH,
    DeleteFileService,
    build_service,
    validate_file_delete_security,
)
from mcp_servers.file.delete_tools import TOOL_LIST
from mcp_servers.models import CallToolRequest, CallToolResponse, McpTool
from mcp_servers.server import (
    MCPServer,
    ToolArgs,
    _FastAPIApp,
    attach_auth_middleware,
    build_tools_response,
    extract_request_context,
)

logger = Logger(__name__, "/opt/llm/logs/file-delete-mcp.log")

_cfg = FileDeleteConfig.load()
_service: DeleteFileService = build_service(_cfg)

FILE_DELETE_SERVER_KEY = "file_delete"
FILE_DELETE_OWN_CONFIG_FILE = "file_delete_mcp_server.toml"


def _delete_security_view(
    cfg: FileDeleteConfig, audit_log_path: str
) -> dict[str, object]:
    """Build the non-secret view the posture fingerprint is computed from.

    Only counts and presence flags are carried: `auth_token` is a Secret, every
    `allowed_dirs` value is a path, and the audit log path is a deployment path
    (REQ-002, REQ-004, REQ-009).
    """
    return {
        "own_config_file": FILE_DELETE_OWN_CONFIG_FILE,
        "allowed_dirs_count": len(cfg.allowed_dirs),
        "audit_log_path_configured": bool(audit_log_path),
    }


def _build_security_posture(
    cfg: FileDeleteConfig, audit_log_path: str = AUDIT_LOG_PATH
) -> SecurityPosture:
    """Run the shared ordering against the already loaded config and return the posture.

    The flow never raises, so a policy violation still produces a posture the Agent can
    read. Only the server-security stage is supplied: the flow's built-in common stage
    covers own-config, auth-token, and published-tool checks, and this module does not
    re-read file_delete_mcp_server.toml. The config is a parameter because FileDeleteConfig
    is frozen, so a test rebuilds a posture with `dataclasses.replace()` instead of mutating
    the loaded singleton.
    """
    return run_startup_validation(
        FILE_DELETE_SERVER_KEY,
        own_config_file=FILE_DELETE_OWN_CONFIG_FILE,
        config_view=_delete_security_view(cfg, audit_log_path),
        auth_token=cfg.auth_token,
        declared_tools=tuple(tool["name"] for tool in TOOL_LIST),
        server_checks=lambda: validate_file_delete_security(cfg, audit_log_path),
    )


_security_posture: SecurityPosture = _build_security_posture(_cfg)

app = FastAPI(
    title="file-delete-mcp",
    version="1.0.0",
    description="MCP server for delete filesystem operations",
)

if not _cfg.auth_token:
    raise RuntimeError(
        "file-delete-mcp: auth_token is empty; set MCP_FILE_DELETE_AUTH_TOKEN to a non-empty "
        "value (the server does not start without Bearer authentication)"
    )
attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token)

app.add_exception_handler(FileAuthorizationError, _on_auth_error)
app.add_exception_handler(FileNotFoundError, _on_not_found)
app.add_exception_handler(FileValidationError, _on_validation_error)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.post("/delete_file", response_model=DeleteFileResponse)
async def delete_file(req: DeleteFileRequest) -> DeleteFileResponse:
    """Delete a single file from disk."""
    t0 = time.perf_counter()
    result = _service.delete_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("delete_file", path=result.path, ms=f"{ms:.0f}"))
    return result


@app.post("/delete_directory", response_model=DeleteDirectoryResponse)
async def delete_directory(req: DeleteDirectoryRequest) -> DeleteDirectoryResponse:
    """Delete a directory, optionally recursively."""
    t0 = time.perf_counter()
    result = _service.delete_directory(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "delete_directory",
            path=result.path,
            recursive=req.recursive,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint returning allowed directories status."""
    result: JSONResponse = await _health(_cfg.allowed_dirs, posture=_security_posture)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch and unified call endpoint
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_delete_tool(
    name: str, args: ToolArgs, idempotency_key: str | None = None
) -> DispatchResult:
    """Dispatch a tool request to the delete-file service."""
    return await dispatch_tool(
        _service.get_dispatch_table(), name, args, idempotency_key=idempotency_key
    )


def _annotate_tool(
    tool: McpTool, enabled: bool, disabled_reason: str
) -> dict[str, Any]:
    """Return a copy of tool with server_key and availability fields attached."""
    return {
        **tool,
        "server_key": "file_delete",
        "enabled": enabled,
        "disabled_reason": disabled_reason,
    }


@app.get("/v1/tools")
async def list_tools(
    include_disabled: bool = False, disabled_code: str | None = None
) -> dict[str, Any]:
    """List available MCP tools with schema_version and server key annotation."""
    enabled, disabled_reason = availability_flags(_cfg.allowed_dirs)
    annotated = [_annotate_tool(t, enabled, disabled_reason) for t in TOOL_LIST]
    return build_tools_response(
        cast("list[McpTool]", annotated),
        "file_delete",
        include_disabled=include_disabled,
        disabled_code=disabled_code,
    )


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Handle a generic MCP call_tool request."""
    session_id, request_id, idempotency_key = extract_request_context(request)
    raw_path = cast(str, req.args.get("path", ""))
    audit_target = raw_path[:80]
    if not _cfg.allowed_dirs:
        _audit_log(
            logger,
            session_id=session_id,
            request_id=request_id,
            action=req.name,
            target=audit_target,
            requested_target=raw_path,
            outcome="rejected",
            server_key=FILE_DELETE_SERVER_KEY,
        )
        return CallToolResponse(
            result="Tool disabled: allowed_dirs is empty", is_error=True
        )
    try:
        req.validate_args()
    except ValueError as e:
        _audit_log(
            logger,
            session_id=session_id,
            request_id=request_id,
            action=req.name,
            target=audit_target,
            requested_target=raw_path,
            outcome="rejected",
            server_key=FILE_DELETE_SERVER_KEY,
        )
        return CallToolResponse(result=f"Validation error: {e}", is_error=True)
    r = await _dispatch_delete_tool(req.name, req.args, idempotency_key=idempotency_key)
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=audit_target,
        requested_target=raw_path,
        outcome=r.outcome,
        server_key=FILE_DELETE_SERVER_KEY,
    )
    return _to_call_tool_response(r)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class FileDeleteMCPServer(MCPServer):
    """MCPServer subclass for file-delete-mcp."""

    server_name = "file-delete-mcp"
    server_version = "1.0.0"
    http_port = 8008
    own_config_file = "file_delete_mcp_server.toml"
    app_module = "mcp_servers.file.delete_server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        """Dispatch a tool invocation via the delete-file service."""
        return await _dispatch_delete_tool(name, args)


def _enforce_posture_gate() -> None:
    """Refuse HTTP bind when the posture is not validated (REQ-003, AC-003).

    The gate reads only `validated`: the payload `ready` is derived in
    `make_health_response()` from dependencies plus `validated`, so this module never
    invents its own Ready rule. The log line carries check ids and reason codes only;
    allowed directory paths and the audit log path are excluded (REQ-002, REQ-004).
    """
    if _security_posture.validated:
        return
    failed = ", ".join(
        f"{check.check_id}:{check.reason_code}"
        for check in _security_posture.checks
        if check.status is SecurityCheckStatus.FAILED
    )
    logger.error(
        "file-delete-mcp: security posture FAILED (%s) — refusing to bind", failed
    )
    raise SystemExit(1)


if __name__ == "__main__":
    _enforce_posture_gate()
    server = FileDeleteMCPServer()
    server.run_http()
