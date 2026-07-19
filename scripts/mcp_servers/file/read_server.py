#!/usr/bin/env python3
"""mcp_servers/file/read_server.py

MCP server for read-only filesystem operations (port 8005).

Provides an HTTP API via FastAPI for reading files and directories.
Security: Only paths under directories listed in allowed_dirs are accessible.

Provided endpoints:
  POST /list_directory             List immediate entries in a directory
  POST /list_directory_with_sizes  List directory entries with sizes
  POST /directory_tree             Recursive tree structure of a directory
  POST /read_text_file             Get file content as UTF-8 text
  POST /read_media_file            Get media files as base64
  POST /read_multiple_files        Batch retrieval of multiple files
  POST /search_files               Search files by glob pattern
  POST /grep_files                 Search file contents by regex pattern
  POST /get_file_info              Get file metadata
  GET  /list_allowed_directories   Return the list of allowed directories
  GET  /health                     Health check
"""

import time
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.logger import Logger

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
from mcp_servers.file.read_models import (
    DirectoryTreeRequest,
    DirectoryTreeResponse,
    FileReadConfig,
    GetFileInfoRequest,
    GetFileInfoResponse,
    GrepFilesRequest,
    GrepFilesResponse,
    ListDirectoryRequest,
    ListDirectoryResponse,
    ReadMediaFileRequest,
    ReadMediaFileResponse,
    ReadMultipleFilesRequest,
    ReadMultipleFilesResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    SearchFilesRequest,
    SearchFilesResponse,
)
from mcp_servers.file.read_service import ReadFileService, build_service
from mcp_servers.file.read_tools import TOOL_LIST
from mcp_servers.models import CallToolRequest, CallToolResponse
from mcp_servers.server import (
    MCP_TOOL_SCHEMA_VERSION,
    MCPServer,
    ToolArgs,
)

logger = Logger(__name__, "/opt/llm/logs/file-read-mcp.log")

_cfg = FileReadConfig.load()
_service: ReadFileService = build_service(_cfg)

app = FastAPI(
    title="file-read-mcp",
    version="1.0.0",
    description="MCP server for read-only filesystem operations",
)

app.add_exception_handler(FileAuthorizationError, _on_auth_error)
app.add_exception_handler(FileNotFoundError, _on_not_found)
app.add_exception_handler(FileValidationError, _on_validation_error)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.post("/list_directory", response_model=ListDirectoryResponse)
async def list_directory(req: ListDirectoryRequest) -> ListDirectoryResponse:
    """List immediate entries in a directory without sizes."""
    t0 = time.perf_counter()
    result = _service.list_dir_entries(req, include_dir_sizes=False)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "list_directory",
            path=result.path,
            n=len(result.entries),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/list_directory_with_sizes", response_model=ListDirectoryResponse)
async def list_directory_with_sizes(req: ListDirectoryRequest) -> ListDirectoryResponse:
    """List directory entries including their sizes."""
    t0 = time.perf_counter()
    result = _service.list_dir_entries(req, include_dir_sizes=True)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "list_directory_with_sizes",
            path=result.path,
            n=len(result.entries),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/directory_tree", response_model=DirectoryTreeResponse)
async def directory_tree(req: DirectoryTreeRequest) -> DirectoryTreeResponse:
    """Build a recursive tree structure of a directory."""
    t0 = time.perf_counter()
    result = _service.build_directory_tree(req)
    ms = (time.perf_counter() - t0) * 1000
    depth = min(req.depth, _service.max_tree_depth)
    logger.info(
        fmt_kvlog("directory_tree", path=result.root.path, depth=depth, ms=f"{ms:.0f}"),
    )
    return result


@app.post("/read_text_file", response_model=ReadTextFileResponse)
async def read_text_file(req: ReadTextFileRequest) -> ReadTextFileResponse:
    """Read a text file and return its content as UTF-8."""
    t0 = time.perf_counter()
    result = _service.read_text_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "read_text_file", path=result.path, bytes=result.size, ms=f"{ms:.0f}"
        ),
    )
    return result


@app.post("/read_media_file", response_model=ReadMediaFileResponse)
async def read_media_file(req: ReadMediaFileRequest) -> ReadMediaFileResponse:
    """Read a media file and return it as base64-encoded data."""
    t0 = time.perf_counter()
    result = _service.read_media_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "read_media_file",
            path=result.path,
            bytes=result.size,
            mime=result.mime_type,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/read_multiple_files", response_model=ReadMultipleFilesResponse)
async def read_multiple_files(
    req: ReadMultipleFilesRequest,
) -> ReadMultipleFilesResponse:
    """Batch retrieve multiple files at once."""
    t0 = time.perf_counter()
    result = _service.read_multiple_files(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("read_multiple_files", n=len(result.results), ms=f"{ms:.0f}"))
    return result


@app.post("/search_files", response_model=SearchFilesResponse)
async def search_files(req: SearchFilesRequest) -> SearchFilesResponse:
    """Search for files matching a glob pattern within a directory."""
    t0 = time.perf_counter()
    result = _service.search_files(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "search_files",
            path=req.path,
            pattern=req.pattern,
            n=len(result.matches),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/grep_files", response_model=GrepFilesResponse)
async def grep_files(req: GrepFilesRequest) -> GrepFilesResponse:
    """Search file contents by regex pattern."""
    t0 = time.perf_counter()
    result = _service.grep_files(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "grep_files",
            path=req.path,
            pattern=req.pattern,
            n=len(result.matches),
            truncated=result.truncated,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/get_file_info", response_model=GetFileInfoResponse)
async def get_file_info(req: GetFileInfoRequest) -> GetFileInfoResponse:
    """Get metadata about a single file (size, permissions, etc.)."""
    t0 = time.perf_counter()
    result = _service.get_file_info(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("get_file_info", path=result.info.path, ms=f"{ms:.0f}"))
    return result


@app.get("/list_allowed_directories")
async def list_allowed_directories() -> dict[str, list[str]]:
    """Return the list of allowed directories for file access."""
    return {"allowed_dirs": [str(d.resolve()) for d in _service._allowed_dirs]}


@app.get("/health")
async def health() -> JSONResponse:
    """Return health check status."""
    result: JSONResponse = await _health(_cfg.allowed_dirs)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch and unified call endpoint
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_read_tool(name: str, args: ToolArgs) -> DispatchResult:
    """Route a tool call through the shared dispatch mechanism."""
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    """Return the MCP tool list with schema_version and server_key appended."""
    enabled, disabled_reason = availability_flags(_cfg.allowed_dirs)
    tools_with_availability = []
    for t in TOOL_LIST:
        tool_dict = {
            **t,
            "server_key": "file_read",
            "enabled": enabled,
            "disabled_reason": disabled_reason,
        }
        tools_with_availability.append(tool_dict)
    return {
        "schema_version": MCP_TOOL_SCHEMA_VERSION,
        "tools": tools_with_availability,
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    """Handle MCP call_tool requests with audit logging and error handling."""
    if not _cfg.allowed_dirs:
        return CallToolResponse(
            result="Tool disabled: allowed_dirs is empty", is_error=True
        )
    try:
        req.validate_args()
    except ValueError as e:
        return CallToolResponse(result=f"Validation error: {e}", is_error=True)
    r = await _dispatch_read_tool(req.name, req.args)
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


if __name__ == "__main__":
    server = FileReadMCPServer()
    server.run_http()
