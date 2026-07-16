#!/usr/bin/env python3
"""mcp_servers/file/read_tools.py

MCP tool schema definitions for file-read-mcp server (inputSchema format).

Schemas are derived from the Pydantic request models in read_models.py via
model_json_schema() so that tool definitions and models stay in sync.

Imported by mcp/file/read_server.py to keep the server module under 400 lines.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from mcp_servers.file.read_models import (
    DirectoryTreeRequest,
    GetFileInfoRequest,
    GrepFilesRequest,
    ListDirectoryRequest,
    ReadMediaFileRequest,
    ReadMultipleFilesRequest,
    ReadTextFileRequest,
    SearchFilesRequest,
)


def _input_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Build an MCP inputSchema from a Pydantic model's JSON schema.

    Strips the top-level 'title' and per-property 'title' fields that Pydantic
    adds but MCP inputSchema does not require.
    """
    raw = model.model_json_schema()
    schema: dict[str, Any] = {"type": "object"}
    if "properties" in raw:
        schema["properties"] = {
            k: {ik: iv for ik, iv in v.items() if ik != "title"}
            for k, v in raw["properties"].items()
        }
    if "required" in raw:
        schema["required"] = raw["required"]
    return schema


TOOL_LIST: list[dict[str, Any]] = [
    {
        "name": "list_directory",
        "description": "Return immediate entries of the specified directory",
        "inputSchema": _input_schema(ListDirectoryRequest),
        "status": "production",
        "requires_config": False,
    },
    {
        "name": "list_directory_with_sizes",
        "description": "Return directory entries with sizes including stat size for directories",
        "inputSchema": _input_schema(ListDirectoryRequest),
        "status": "production",
        "requires_config": False,
    },
    {
        "name": "directory_tree",
        "description": "Recursively return the tree structure of a directory",
        "inputSchema": _input_schema(DirectoryTreeRequest),
        "status": "production",
        "requires_config": False,
    },
    {
        "name": "read_text_file",
        "description": "Read file contents as UTF-8 text. head/tail options limit the number of lines returned",
        "inputSchema": _input_schema(ReadTextFileRequest),
        "status": "production",
        "requires_config": False,
    },
    {
        "name": "read_media_file",
        "description": "Return a media file (image/audio etc.) base64-encoded with its MIME type",
        "inputSchema": _input_schema(ReadMediaFileRequest),
        "status": "production",
        "requires_config": False,
    },
    {
        "name": "read_multiple_files",
        "description": "Retrieve multiple files in a single request. Continues even if individual errors occur",
        "inputSchema": _input_schema(ReadMultipleFilesRequest),
        "status": "production",
        "requires_config": False,
    },
    {
        "name": "search_files",
        "description": "Recursively search for files matching a glob pattern within a directory",
        "inputSchema": _input_schema(SearchFilesRequest),
        "status": "production",
        "requires_config": False,
    },
    {
        "name": "grep_files",
        "description": "Search file contents under a directory using a regex pattern",
        "inputSchema": _input_schema(GrepFilesRequest),
        "status": "production",
        "requires_config": False,
    },
    {
        "name": "get_file_info",
        "description": "Return metadata (size, timestamps, permissions) for a file or directory",
        "inputSchema": _input_schema(GetFileInfoRequest),
        "status": "production",
        "requires_config": False,
    },
]
