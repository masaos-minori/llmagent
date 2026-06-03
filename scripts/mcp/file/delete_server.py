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

from fastapi import FastAPI
from shared.formatters import fmt_kvlog
from shared.logger import Logger

from mcp.dispatch import dispatch_tool
from mcp.file.delete_models import (
    DeleteDirectoryRequest,
    DeleteDirectoryResponse,
    DeleteFileRequest,
    DeleteFileResponse,
)
from mcp.file.delete_service import _service
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs

logger = Logger(__name__, "/opt/llm/logs/file-delete-mcp.log")

app = FastAPI(
    title="file-delete-mcp",
    version="1.0.0",
    description="MCP server for delete filesystem operations",
)


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
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# MCP tool definitions
# ──────────────────────────────────────────────────────────────────────────────

_MCP_TOOLS = [
    {
        "name": "delete_file",
        "description": "Delete the specified file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the file to delete",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "delete_directory",
        "description": "Delete a directory. When recursive=true, delete contents recursively",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the directory to delete",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "When true, delete contents recursively (default: false)",
                },
            },
            "required": ["path"],
        },
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch and unified call endpoint
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_delete_tool(name: str, args: ToolArgs) -> tuple[str, bool]:
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in _MCP_TOOLS
        ],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    result, is_error = await _dispatch_delete_tool(req.name, req.args)
    return CallToolResponse(result=result, is_error=is_error)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class FileDeleteMCPServer(MCPServer):
    """MCPServer subclass for file-delete-mcp."""

    server_name = "file-delete-mcp"
    server_version = "1.0.0"
    http_port = 8008
    app_module = "file_delete_mcp_server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        return await _dispatch_delete_tool(name, args)


if __name__ == "__main__":
    import sys

    server = FileDeleteMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
