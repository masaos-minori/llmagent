#!/usr/bin/env python3
"""mcp/file/delete_tools.py
MCP tool schema definitions for file-delete-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

_MCP_TOOLS: list[dict[str, Any]] = [
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
