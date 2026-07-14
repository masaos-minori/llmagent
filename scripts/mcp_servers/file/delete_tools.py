#!/usr/bin/env python3
"""mcp_servers/file/delete_tools.py

MCP tool schema definitions for file-delete-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

TOOL_LIST: list[dict[str, Any]] = [
    {
        "name": "delete_file",
        "description": "Delete the specified file. When dry_run=true, return file info without deleting",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the file to delete",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "When true, return file info without deleting (default: false)",
                },
            },
            "required": ["path"],
        },
        "status": "production",
        "requires_config": False,
    },
    {
        "name": "delete_directory",
        "description": "Delete a directory. When recursive=true, delete contents recursively. When dry_run=true, return directory info without deleting",
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
                "dry_run": {
                    "type": "boolean",
                    "description": "When true, return directory info without deleting (default: false)",
                },
            },
            "required": ["path"],
        },
        "status": "production",
        "requires_config": False,
    },
]
