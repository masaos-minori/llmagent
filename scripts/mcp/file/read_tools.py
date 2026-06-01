#!/usr/bin/env python3
"""mcp/file/read_tools.py
MCP tool schema definitions for file-read-mcp server (inputSchema format).

Imported by mcp/file/read_server.py to keep the server module under 400 lines.
"""

from __future__ import annotations

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
        "description": "Return directory entries with sizes including stat size for directories",
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
        "description": "Read file contents as UTF-8 text. head/tail options limit the number of lines returned",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the file to read",
                },
                "head": {
                    "type": "integer",
                    "description": "Return only the first N lines (mutually exclusive with tail)",
                },
                "tail": {
                    "type": "integer",
                    "description": "Return only the last N lines (mutually exclusive with head)",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "read_media_file",
        "description": "Return a media file (image/audio etc.) base64-encoded with its MIME type",
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
        "name": "read_multiple_files",
        "description": "Retrieve multiple files in a single request. Continues even if individual errors occur",
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
        "name": "search_files",
        "description": "Recursively search for files matching a glob pattern within a directory",
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
        "name": "get_file_info",
        "description": "Return metadata (size, timestamps, permissions) for a file or directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the file or directory to inspect",
                },
            },
            "required": ["path"],
        },
    },
]
