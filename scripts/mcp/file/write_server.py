#!/usr/bin/env python3
"""file_write_mcp_server.py
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
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from mcp.dispatch import DispatchResult, dispatch_tool
from mcp.file.common import (
    FileAuthorizationError,
    FileValidationError,
    _health,
    _on_auth_error,
    _on_not_found,
    _on_validation_error,
)
from mcp.file.write_models import (
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
from mcp.file.write_service import WriteFileService, build_service
from mcp.file.write_tools import TOOL_LIST
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs
from shared.formatters import fmt_kvlog
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/file-write-mcp.log")

_cfg = FileWriteConfig.load()
_service: WriteFileService = build_service(_cfg)

app = FastAPI(
    title="file-write-mcp",
    version="1.0.0",
    description="MCP server for write filesystem operations",
)

app.add_exception_handler(FileAuthorizationError, _on_auth_error)
app.add_exception_handler(FileNotFoundError, _on_not_found)
app.add_exception_handler(FileValidationError, _on_validation_error)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.post("/write_file", response_model=WriteFileResponse)
async def write_file(req: WriteFileRequest) -> WriteFileResponse:
    t0 = time.perf_counter()
    result = _service.write_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog("write_file", path=result.path, bytes=result.size, ms=f"{ms:.0f}"),
    )
    return result


@app.post("/edit_file", response_model=EditFileResponse)
async def edit_file(req: EditFileRequest) -> EditFileResponse:
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
    return await _health()


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch and unified call endpoint
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_write_tool(name: str, args: ToolArgs) -> DispatchResult:
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [{**t, "server_key": "file_write"} for t in TOOL_LIST],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    r = await _dispatch_write_tool(req.name, req.args)
    return CallToolResponse(result=r.output, is_error=r.is_error)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class FileWriteMCPServer(MCPServer):
    """MCPServer subclass for file-write-mcp."""

    server_name = "file-write-mcp"
    server_version = "1.0.0"
    http_port = 8007
    own_config_file = "file_write_mcp_server.toml"
    app_module = "mcp.file.write_server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        return await _dispatch_write_tool(name, args)


if __name__ == "__main__":
    server = FileWriteMCPServer()
    server.run_http()
