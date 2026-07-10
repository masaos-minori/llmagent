#!/usr/bin/env python3
"""mcp_servers/file/write_tools.py
MCP tool schema definitions for file-write-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

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
        "status": "production",
        "requires_config": False,
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
        "status": "production",
        "requires_config": False,
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
        "status": "production",
        "requires_config": False,
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
        "status": "production",
        "requires_config": False,
    },
]
