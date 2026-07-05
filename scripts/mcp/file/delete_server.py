#!/usr/bin/env python3
"""file_delete_mcp_server.py
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
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.logger import Logger

from mcp.dispatch import DispatchResult, dispatch_tool
from mcp.file.common import (
    FileAuthorizationError,
    FileValidationError,
    _build_health_deps,
)
from mcp.file.delete_models import (
    DeleteDirectoryRequest,
    DeleteDirectoryResponse,
    DeleteFileRequest,
    DeleteFileResponse,
    FileDeleteConfig,
)
from mcp.file.delete_service import DeleteFileService, build_service
from mcp.file.delete_tools import TOOL_LIST
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs

logger = Logger(__name__, "/opt/llm/logs/file-delete-mcp.log")

_cfg = FileDeleteConfig.load()
_service: DeleteFileService = build_service(_cfg)

app = FastAPI(
    title="file-delete-mcp",
    version="1.0.0",
    description="MCP server for delete filesystem operations",
)


@app.exception_handler(FileAuthorizationError)
async def _on_auth_error(_req: Request, exc: FileAuthorizationError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=403)


@app.exception_handler(FileNotFoundError)
async def _on_not_found(_req: Request, exc: FileNotFoundError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=404)


@app.exception_handler(FileValidationError)
async def _on_validation_error(_req: Request, exc: FileValidationError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=422)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.post("/delete_file", response_model=DeleteFileResponse)
async def delete_file(req: DeleteFileRequest) -> DeleteFileResponse:
    t0 = time.perf_counter()
    result = _service.delete_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("delete_file", path=result.path, ms=f"{ms:.0f}"))
    return result


@app.post("/delete_directory", response_model=DeleteDirectoryResponse)
async def delete_directory(req: DeleteDirectoryRequest) -> DeleteDirectoryResponse:
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
    deps = _build_health_deps()
    ready = len(deps) == 0
    return JSONResponse(
        {
            "status": "ok" if ready else "degraded",
            "ready": ready,
            "liveness": True,
            "restart_recommended": False,
            "operator_action_required": not ready,
            "dependencies": deps,
            "details": {},
        },
        status_code=200 if ready else 503,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch and unified call endpoint
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_delete_tool(name: str, args: ToolArgs) -> DispatchResult:
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [{**t, "server_key": "file_delete"} for t in TOOL_LIST],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    r = await _dispatch_delete_tool(req.name, req.args)
    return CallToolResponse(result=r.output, is_error=r.is_error)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class FileDeleteMCPServer(MCPServer):
    """MCPServer subclass for file-delete-mcp."""

    server_name = "file-delete-mcp"
    server_version = "1.0.0"
    http_port = 8008
    own_config_file = "file_delete_mcp_server.toml"
    app_module = "mcp.file.delete_server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        return await _dispatch_delete_tool(name, args)


if __name__ == "__main__":
    server = FileDeleteMCPServer()
    server.run_http()
