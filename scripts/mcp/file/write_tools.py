#!/usr/bin/env python3
"""mcp/file/write_tools.py
MCP tool schema definitions for file-write-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

_MCP_TOOLS: list[dict[str, Any]] = [
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
