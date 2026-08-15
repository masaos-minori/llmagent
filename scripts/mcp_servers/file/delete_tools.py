#!/usr/bin/env python3
"""scripts/mcp_servers/file/delete_tools.py

MCP tool schema definitions for file-delete-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

# Shared metadata block: every tool in this module is a filesystem write keyed on a
# single "path" argument, so these fields are byte-for-byte identical across all
# TOOL_LIST entries. Extracted so they stay in sync (mirrors the analogous
# _REPO_PATH_PROPERTY extraction in scripts/mcp_servers/git/git_tools.py).
_FILESYSTEM_DELETE_METADATA: dict[str, Any] = {
    "status": "production",
    "config_dependent": False,
    "is_write": True,
    "requires_serial": False,
    "resource_scope_kind": "filesystem",
    "resource_scope_keys": ["path"],
}

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
        **_FILESYSTEM_DELETE_METADATA,
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
        **_FILESYSTEM_DELETE_METADATA,
    },
]
