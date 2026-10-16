#!/usr/bin/env python3
"""scripts/mcp_servers/file/write_server.py

MCP server for write filesystem operations (port 8007).

Provides an HTTP API via FastAPI for creating, editing, and moving files.
Security: Only paths under directories listed in allowed_dirs are accessible.
Deletions are not provided; use file-delete-mcp for that.

Provided endpoints:
  POST /write_file         Create or overwrite a file
  POST /edit_file          Diff-based editing via string replacement
  POST /create_directory   Create a directory
  POST /move_file          Move or rename a file/directory
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
from mcp_servers.file.write_models import (
    CreateDirectoryRequest,
    CreateDirectoryResponse,
    EditFileRequest,
    EditFileResponse,
    FileWriteConfig,
    MoveFileRequest,
    MoveFileResponse,
    WriteFileRequest,
    WriteFileResponse,
)
from mcp_servers.file.write_security_validation import validate_file_write_security
from mcp_servers.file.write_service import WriteFileService, build_service
from mcp_servers.file.write_tools import TOOL_LIST
from mcp_servers.models import CallToolRequest, CallToolResponse, McpTool
from mcp_servers.server import (
    MCPServer,
    ToolArgs,
    _FastAPIApp,
    attach_auth_middleware,
    build_tools_response,
    extract_request_context,
)

logger = Logger(__name__, "/opt/llm/logs/file-write-mcp.log")

_cfg = FileWriteConfig.load()
_service: WriteFileService = build_service(_cfg)

FILE_WRITE_SERVER_KEY = "file_write"
FILE_WRITE_OWN_CONFIG_FILE = "file_write_mcp_server.toml"


def _write_security_view(cfg: FileWriteConfig) -> dict[str, object]:
    """Build the non-secret view the posture fingerprint is computed from.

    Only scalars and counts are carried: `auth_token` is a Secret and every
    `allowed_dirs` value is a path (REQ-002, REQ-009).
    """
    return {
        "own_config_file": FILE_WRITE_OWN_CONFIG_FILE,
        "allowed_dirs_count": len(cfg.allowed_dirs),
        "max_write_bytes": cfg.max_write_bytes,
        "supported_extensions_count": len(cfg.supported_extensions),
    }


def _build_security_posture(cfg: FileWriteConfig) -> SecurityPosture:
    """Run the shared ordering against the already loaded config and return the posture.

    The flow never raises, so a policy violation still produces a posture the Agent can
    read. Only the server-security stage is supplied: the flow's built-in common stage
    covers own-config, auth-token, and published-tool checks, and this module does not
    re-read file_write_mcp_server.toml. The config is a parameter because FileWriteConfig
    is frozen, so a test rebuilds a posture with `dataclasses.replace()` instead of
    mutating the loaded singleton.
    """
    return run_startup_validation(
        FILE_WRITE_SERVER_KEY,
        own_config_file=FILE_WRITE_OWN_CONFIG_FILE,
        config_view=_write_security_view(cfg),
        auth_token=cfg.auth_token,
        declared_tools=tuple(tool["name"] for tool in TOOL_LIST),
        server_checks=lambda: validate_file_write_security(cfg),
    )


_security_posture: SecurityPosture = _build_security_posture(_cfg)

app = FastAPI(
    title="file-write-mcp",
    version="1.0.0",
    description="MCP server for write filesystem operations",
)

if not _cfg.auth_token:
    raise RuntimeError(
        "file-write-mcp: auth_token is empty; set MCP_FILE_WRITE_AUTH_TOKEN to a non-empty "
        "value (the server does not start without Bearer authentication)"
    )
attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token)

app.add_exception_handler(FileAuthorizationError, _on_auth_error)
app.add_exception_handler(FileNotFoundError, _on_not_found)
app.add_exception_handler(FileValidationError, _on_validation_error)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.post("/write_file", response_model=WriteFileResponse)
async def write_file(req: WriteFileRequest) -> WriteFileResponse:
    """Create or overwrite a file on disk."""
    t0 = time.perf_counter()
    result = _service.write_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog("write_file", path=result.path, bytes=result.size, ms=f"{ms:.0f}"),
    )
    return result


@app.post("/edit_file", response_model=EditFileResponse)
async def edit_file(req: EditFileRequest) -> EditFileResponse:
    """Apply diff-based edits to an existing file on disk."""
    t0 = time.perf_counter()
    result = _service.edit_file(req)
    ms = (time.perf_counter() - t0) * 1000
    action = "dry_run" if req.dry_run else "applied"
    logger.info(
        fmt_kvlog(
            "edit_file",
            path=result.path,
            action=action,
            n=len(req.edits),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/create_directory", response_model=CreateDirectoryResponse)
async def create_directory(req: CreateDirectoryRequest) -> CreateDirectoryResponse:
    """Create a directory on disk."""
    t0 = time.perf_counter()
    result = _service.create_directory(req)
    ms = (time.perf_counter() - t0) * 1000
    created = "created" if result.created else "exists"
    logger.info(
        fmt_kvlog("create_directory", path=result.path, result=created, ms=f"{ms:.0f}"),
    )
    return result


@app.post("/move_file", response_model=MoveFileResponse)
async def move_file(req: MoveFileRequest) -> MoveFileResponse:
    """Move or rename a file or directory on disk."""
    t0 = time.perf_counter()
    result = _service.move_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "move_file",
            src=result.source,
            dst=result.destination,
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


async def _dispatch_write_tool(
    name: str, args: ToolArgs, idempotency_key: str | None = None
) -> DispatchResult:
    """Dispatch a tool request to the write-file service."""
    return await dispatch_tool(
        _service.get_dispatch_table(), name, args, idempotency_key=idempotency_key
    )


def _annotate_tool(
    tool: McpTool, enabled: bool, disabled_reason: str
) -> dict[str, Any]:
    """Return a copy of tool with server_key and availability fields attached."""
    return {
        **tool,
        "server_key": "file_write",
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
        "file_write",
        include_disabled=include_disabled,
        disabled_code=disabled_code,
    )


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Handle a generic MCP call_tool request."""
    if not _cfg.allowed_dirs:
        return CallToolResponse(
            result="Tool disabled: allowed_dirs is empty", is_error=True
        )
    try:
        req.validate_args()
    except ValueError as e:
        return CallToolResponse(result=f"Validation error: {e}", is_error=True)
    _, _, idempotency_key = extract_request_context(request)
    r = await _dispatch_write_tool(req.name, req.args, idempotency_key=idempotency_key)
    return _to_call_tool_response(r)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class FileWriteMCPServer(MCPServer):
    """MCPServer subclass for file-write-mcp."""

    server_name = "file-write-mcp"
    server_version = "1.0.0"
    http_port = 8007
    own_config_file = "file_write_mcp_server.toml"
    app_module = "mcp_servers.file.write_server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        """Dispatch a tool invocation via the write-file service."""
        return await _dispatch_write_tool(name, args)


def _enforce_posture_gate() -> None:
    """Refuse HTTP bind when the posture is not validated (REQ-003, AC-003).

    The gate reads only `validated`: the payload `ready` is derived in
    `make_health_response()` from dependencies plus `validated`, so this module never
    invents its own Ready rule. The log line carries check ids and reason codes only;
    allowed directory paths are excluded (REQ-002, REQ-004).
    """
    if _security_posture.validated:
        return
    failed = ", ".join(
        f"{check.check_id}:{check.reason_code}"
        for check in _security_posture.checks
        if check.status is SecurityCheckStatus.FAILED
    )
    logger.error(
        "file-write-mcp: security posture FAILED (%s) — refusing to bind", failed
    )
    raise SystemExit(1)


if __name__ == "__main__":
    _enforce_posture_gate()
    server = FileWriteMCPServer()
    server.run_http()
