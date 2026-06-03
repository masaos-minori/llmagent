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
from shared.formatters import fmt_kvlog
from shared.logger import Logger

from mcp.dispatch import dispatch_tool
from mcp.file.write_models import (
    CreateDirectoryRequest,
    CreateDirectoryResponse,
    EditFileRequest,
    EditFileResponse,
    MoveFileRequest,
    MoveFileResponse,
    WriteFileRequest,
    WriteFileResponse,
)
from mcp.file.write_service import _service
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs

logger = Logger(__name__, "/opt/llm/logs/file-write-mcp.log")

app = FastAPI(
    title="file-write-mcp",
    version="1.0.0",
    description="MCP server for write filesystem operations",
)


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
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# MCP tool definitions
# ──────────────────────────────────────────────────────────────────────────────

_MCP_TOOLS = [
    {
        "name": "write_file",
        "description": "Create or overwrite a file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (UTF-8 text)",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Apply string replacements to a file. When dry_run=true, return only the diff without writing",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the file to edit",
                },
                "edits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "old_text": {
                                "type": "string",
                                "description": "String to replace (exact match)",
                            },
                            "new_text": {
                                "type": "string",
                                "description": "Replacement string",
                            },
                        },
                        "required": ["old_text", "new_text"],
                    },
                    "description": "List of replacement operations applied in order",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "When true, return only the diff without writing (default: false)",
                },
            },
            "required": ["path", "edits"],
        },
    },
    {
        "name": "create_directory",
        "description": "Create a directory, including parent directories recursively",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the directory to create",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "move_file",
        "description": "Move or rename a file or directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Absolute path of the source",
                },
                "destination": {
                    "type": "string",
                    "description": "Absolute path of the destination",
                },
            },
            "required": ["source", "destination"],
        },
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch and unified call endpoint
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_write_tool(name: str, args: ToolArgs) -> tuple[str, bool]:
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
    result, is_error = await _dispatch_write_tool(req.name, req.args)
    return CallToolResponse(result=result, is_error=is_error)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class FileWriteMCPServer(MCPServer):
    """MCPServer subclass for file-write-mcp."""

    server_name = "file-write-mcp"
    server_version = "1.0.0"
    http_port = 8007
    app_module = "file_write_mcp_server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        return await _dispatch_write_tool(name, args)


if __name__ == "__main__":
    import sys

    server = FileWriteMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
