#!/usr/bin/env python3
"""scripts/mcp_servers/file/write_tools.py

MCP tool schema definitions for file-write-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

# Shared metadata block: every tool in this module is a filesystem write, so these
# fields are byte-for-byte identical across all TOOL_LIST entries except
# resource_scope_keys (move_file scopes on "source"/"destination", not "path").
# Extracted so they stay in sync (mirrors the analogous _REPO_PATH_PROPERTY extraction
# in scripts/mcp_servers/git/git_tools.py, _FILESYSTEM_DELETE_METADATA in
# scripts/mcp_servers/file/delete_tools.py, and _FILESYSTEM_READ_METADATA in
# scripts/mcp_servers/file/read_tools.py).
_FILESYSTEM_WRITE_METADATA: dict[str, Any] = {
    "status": "production",
    "config_dependent": False,
    "is_write": True,
    "requires_serial": False,
    "resource_scope_kind": "filesystem",
}

TOOL_LIST: list[dict[str, Any]] = [
    {
        "name": "write_file",
        "description": "Create or overwrite a file. When dry_run=true, return only the diff without writing",
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
                "dry_run": {
                    "type": "boolean",
                    "description": "When true, return diff without writing (default: false)",
                },
            },
            "required": ["path", "content"],
        },
        **_FILESYSTEM_WRITE_METADATA,
        "resource_scope_keys": ["path"],
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
        **_FILESYSTEM_WRITE_METADATA,
        "resource_scope_keys": ["path"],
    },
    {
        "name": "create_directory",
        "description": "Create a directory, including parent directories recursively. When dry_run=true, return directory info without creating",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the directory to create",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "When true, return directory info without creating (default: false)",
                },
            },
            "required": ["path"],
        },
        **_FILESYSTEM_WRITE_METADATA,
        "resource_scope_keys": ["path"],
    },
    {
        "name": "move_file",
        "description": "Move or rename a file or directory. When dry_run=true, return feasibility info without moving",
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
                "dry_run": {
                    "type": "boolean",
                    "description": "When true, return feasibility info without moving (default: false)",
                },
            },
            "required": ["source", "destination"],
        },
        **_FILESYSTEM_WRITE_METADATA,
        "resource_scope_keys": ["source", "destination"],
    },
]
