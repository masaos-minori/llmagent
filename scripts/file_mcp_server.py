#!/usr/bin/env python3
"""
file_mcp_server.py
MCP server for filesystem operations.
Compliant with @modelcontextprotocol/server-filesystem.
Provides an HTTP API via FastAPI, listening on port 8005.

Security: Only paths under directories listed in ALLOWED_DIRS are accessible.
Boundary checks are performed after resolving symlinks and ../ via realpath.

Provided endpoints:
  POST /list_directory             List immediate entries in a directory
  POST /list_directory_with_sizes  List directory entries with sizes
  POST /directory_tree             Recursive tree structure of a directory
  POST /read_text_file             Get file content as UTF-8 text (head/tail options)
  POST /read_media_file            Get media files (images/audio etc.) as base64
  POST /read_multiple_files        Batch retrieval of multiple files
  POST /write_file                 Create or overwrite a file
  POST /edit_file                  Diff-based editing via string replacement
  POST /create_directory           Create a directory
  POST /move_file                  Move or rename a file/directory
  POST /search_files               Search files by glob pattern
  POST /grep_files                 Search file contents by regex pattern
  POST /delete_file                Delete a file
  POST /delete_directory           Delete a directory (recursive option available)
  POST /get_file_info              Get file metadata
  GET  /list_allowed_directories   Return the list of allowed directories
  GET  /health                     Health check
"""

import time
from typing import Any

from fastapi import FastAPI
from file_mcp_models import (
    CreateDirectoryRequest,
    CreateDirectoryResponse,
    DeleteDirectoryRequest,
    DeleteDirectoryResponse,
    DeleteFileRequest,
    DeleteFileResponse,
    DirectoryTreeRequest,
    DirectoryTreeResponse,
    EditFileRequest,
    EditFileResponse,
    GetFileInfoRequest,
    GetFileInfoResponse,
    GrepFilesRequest,
    GrepFilesResponse,
    ListDirectoryRequest,
    ListDirectoryResponse,
    MoveFileRequest,
    MoveFileResponse,
    ReadMediaFileRequest,
    ReadMediaFileResponse,
    ReadMultipleFilesRequest,
    ReadMultipleFilesResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    SearchFilesRequest,
    SearchFilesResponse,
    WriteFileRequest,
    WriteFileResponse,
)
from file_mcp_service import _service
from formatters import fmt_kvlog
from logger import Logger
from mcp_models import CallToolRequest, CallToolResponse
from mcp_server import MCPServer, ToolArgs, dispatch_tool

# Log path is owned here; service module uses logging.getLogger(__name__)
logger = Logger(__name__, "/opt/llm/logs/file-mcp.log")

# No module-scope config constants: all config is loaded lazily via _get_service()
# on first request. This keeps import side-effect-free for tests and partial imports.

app = FastAPI(
    title="file-mcp",
    version="2.0.0",
    description="MCP server compliant with @modelcontextprotocol/server-filesystem",
)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints: directory operations
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/list_directory", response_model=ListDirectoryResponse)
async def list_directory(req: ListDirectoryRequest) -> ListDirectoryResponse:
    """Return immediate entries of the specified directory.
    Directory sizes are reported as 0."""
    t0 = time.perf_counter()
    result = _service.list_dir_entries(req, include_dir_sizes=False)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "list_directory", path=result.path, n=len(result.entries), ms=f"{ms:.0f}"
        )
    )
    return result


@app.post("/list_directory_with_sizes", response_model=ListDirectoryResponse)
async def list_directory_with_sizes(req: ListDirectoryRequest) -> ListDirectoryResponse:
    """Return immediate entries of the specified directory with sizes.
    Includes stat st_size for directories."""
    t0 = time.perf_counter()
    result = _service.list_dir_entries(req, include_dir_sizes=True)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "list_directory_with_sizes",
            path=result.path,
            n=len(result.entries),
            ms=f"{ms:.0f}",
        )
    )
    return result


@app.post("/directory_tree", response_model=DirectoryTreeResponse)
async def directory_tree(req: DirectoryTreeRequest) -> DirectoryTreeResponse:
    """Recursively return the tree structure of a directory.
    The depth parameter limits recursion."""
    t0 = time.perf_counter()
    result = _service.build_directory_tree(req)
    ms = (time.perf_counter() - t0) * 1000
    depth = min(req.depth, _service._max_tree_depth)
    logger.info(
        fmt_kvlog("directory_tree", path=result.root.path, depth=depth, ms=f"{ms:.0f}")
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints: file read operations
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/read_text_file", response_model=ReadTextFileResponse)
async def read_text_file(req: ReadTextFileRequest) -> ReadTextFileResponse:
    """Return the contents of the specified file as UTF-8 text.
    head/tail limits the number of lines returned."""
    t0 = time.perf_counter()
    result = _service.read_text_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog("read_text_file", path=result.path, bytes=result.size, ms=f"{ms:.0f}")
    )
    return result


@app.post("/read_media_file", response_model=ReadMediaFileResponse)
async def read_media_file(req: ReadMediaFileRequest) -> ReadMediaFileResponse:
    """Read the specified file as binary and return it base64-encoded
    along with its MIME type."""
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
        )
    )
    return result


@app.post("/read_multiple_files", response_model=ReadMultipleFilesResponse)
async def read_multiple_files(
    req: ReadMultipleFilesRequest,
) -> ReadMultipleFilesResponse:
    """Retrieve multiple files in a single request.
    Continues reading other files even if individual errors occur."""
    t0 = time.perf_counter()
    result = _service.read_multiple_files(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("read_multiple_files", n=len(result.results), ms=f"{ms:.0f}"))
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints: file write / edit operations
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/write_file", response_model=WriteFileResponse)
async def write_file(req: WriteFileRequest) -> WriteFileResponse:
    """Create or overwrite a file at the specified path.
    Parent directories are created automatically."""
    t0 = time.perf_counter()
    result = _service.write_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog("write_file", path=result.path, bytes=result.size, ms=f"{ms:.0f}")
    )
    return result


@app.post("/edit_file", response_model=EditFileResponse)
async def edit_file(req: EditFileRequest) -> EditFileResponse:
    """
    Apply string replacements to a file. Edits are applied in the order listed.
    When dry_run=true, only the diff is returned without writing the file.
    The diff is returned in unified diff format.
    """
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
        )
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints: directory / move / delete operations
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/create_directory", response_model=CreateDirectoryResponse)
async def create_directory(req: CreateDirectoryRequest) -> CreateDirectoryResponse:
    """Create a directory, including parent directories recursively.
    Returns as-is if the directory already exists."""
    t0 = time.perf_counter()
    result = _service.create_directory(req)
    ms = (time.perf_counter() - t0) * 1000
    created = "created" if result.created else "exists"
    logger.info(
        fmt_kvlog("create_directory", path=result.path, result=created, ms=f"{ms:.0f}")
    )
    return result


@app.post("/move_file", response_model=MoveFileResponse)
async def move_file(req: MoveFileRequest) -> MoveFileResponse:
    """Move or rename a file or directory.
    The destination's parent directory is created automatically."""
    t0 = time.perf_counter()
    result = _service.move_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "move_file", src=result.source, dst=result.destination, ms=f"{ms:.0f}"
        )
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints: search operations
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/search_files", response_model=SearchFilesResponse)
async def search_files(req: SearchFilesRequest) -> SearchFilesResponse:
    """
    Recursively search for files matching a glob pattern within a directory.
    Returns up to MAX_SEARCH_RESULTS results.
    """
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
        )
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints: metadata / utility
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/get_file_info", response_model=GetFileInfoResponse)
async def get_file_info(req: GetFileInfoRequest) -> GetFileInfoResponse:
    """Return metadata (size, timestamps, permissions) for a file or directory."""
    t0 = time.perf_counter()
    result = _service.get_file_info(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("get_file_info", path=result.info.path, ms=f"{ms:.0f}"))
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints: delete operations
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/delete_file", response_model=DeleteFileResponse)
async def delete_file(req: DeleteFileRequest) -> DeleteFileResponse:
    """Delete the specified file."""
    t0 = time.perf_counter()
    result = _service.delete_file(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("delete_file", path=result.path, ms=f"{ms:.0f}"))
    return result


@app.post("/delete_directory", response_model=DeleteDirectoryResponse)
async def delete_directory(req: DeleteDirectoryRequest) -> DeleteDirectoryResponse:
    """Delete a directory.
    Fails if the directory is not empty when recursive=false (default)."""
    t0 = time.perf_counter()
    result = _service.delete_directory(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "delete_directory",
            path=result.path,
            recursive=req.recursive,
            ms=f"{ms:.0f}",
        )
    )
    return result


@app.post("/grep_files", response_model=GrepFilesResponse)
async def grep_files(req: GrepFilesRequest) -> GrepFilesResponse:
    """
    Search file contents under a directory using a regex pattern.
    Reads files filtered by file_pattern in order, checking each line for a match.
    Returns truncated=true when max_matches is reached.
    Binary files that cannot be decoded as UTF-8 are silently skipped.
    """
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
        )
    )
    return result


@app.get("/list_allowed_directories")
async def list_allowed_directories() -> dict[str, list[str]]:
    """Return the list of allowed directories."""
    return {"allowed_dirs": [str(d.resolve()) for d in _service._allowed_dirs]}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# MCP tool definitions (MCP inputSchema format, used by /v1/call_tool routing)
# ──────────────────────────────────────────────────────────────────────────────
_MCP_TOOLS = [
    {
        "name": "list_directory",
        "description": "Return immediate entries of the specified directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the directory to list",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_directory_with_sizes",
        "description": (
            "Return directory entries with sizes including stat size for directories"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the directory to list",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "directory_tree",
        "description": "Recursively return the tree structure of a directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the root directory",
                },
                "depth": {
                    "type": "integer",
                    "description": "Maximum recursion depth (default: 3)",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "read_text_file",
        "description": (
            "Read file contents as UTF-8 text."
            " head/tail options limit the number of lines returned"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the file to read",
                },
                "head": {
                    "type": "integer",
                    "description": (
                        "Return only the first N lines (mutually exclusive with tail)"
                    ),
                },
                "tail": {
                    "type": "integer",
                    "description": (
                        "Return only the last N lines (mutually exclusive with head)"
                    ),
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "read_media_file",
        "description": (
            "Return a media file (image/audio etc.) base64-encoded with its MIME type"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the media file to read",
                },
            },
            "required": ["path"],
        },
    },
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
        "name": "search_files",
        "description": (
            "Recursively search for files matching a glob pattern within a directory"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the base directory to search",
                },
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern (e.g. *.py, **/*.json)",
                },
            },
            "required": ["path", "pattern"],
        },
    },
    {
        "name": "grep_files",
        "description": "Search file contents under a directory using a regex pattern",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the base directory to search",
                },
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (Python regular expression)",
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Glob pattern for target files (default: all files)",
                },
                "max_matches": {
                    "type": "integer",
                    "description": "Maximum number of matches to return (default: 100)",
                },
            },
            "required": ["path", "pattern"],
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
        "description": (
            "Delete a directory. When recursive=true, delete contents recursively"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the directory to delete",
                },
                "recursive": {
                    "type": "boolean",
                    "description": (
                        "When true, delete contents recursively (default: false)"
                    ),
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "read_multiple_files",
        "description": (
            "Retrieve multiple files in a single request."
            " Continues even if individual errors occur"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of absolute file paths to read",
                },
            },
            "required": ["paths"],
        },
    },
    {
        "name": "edit_file",
        "description": (
            "Apply string replacements to a file."
            " When dry_run=true, return only the diff without writing"
        ),
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
                    "description": (
                        "When true, return only the diff without writing"
                        " (default: false)"
                    ),
                },
            },
            "required": ["path", "edits"],
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
    {
        "name": "get_file_info",
        "description": (
            "Return metadata (size, timestamps, permissions) for a file or directory"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Absolute path of the file or directory to inspect"
                    ),
                },
            },
            "required": ["path"],
        },
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch function
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_file_tool(name: str, args: ToolArgs) -> tuple[str, bool]:
    """Route a tool call to FileService via its dispatch table."""
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


# ──────────────────────────────────────────────────────────────────────────────
# Tool listing endpoint (for client-side definition validation)
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/v1/tools")
async def list_tools() -> dict:
    """Return tool names and descriptions for agent.json definition validation."""
    return {
        "tools": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in _MCP_TOOLS
        ]
    }


# ──────────────────────────────────────────────────────────────────────────────
# Unified tool call endpoint
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    """Execute a file tool by name and return the formatted text result."""
    result, is_error = await _dispatch_file_tool(req.name, req.args)
    return CallToolResponse(result=result, is_error=is_error)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
class FileopMCPServer(MCPServer):
    """MCPServer subclass for file-mcp."""

    server_name = "file-mcp"
    server_version = "2.0.0"
    http_port = 8005
    app_module = "file_mcp_server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        return await _dispatch_file_tool(name, args)


if __name__ == "__main__":
    import sys

    server = FileopMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run()
