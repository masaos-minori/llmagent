#!/usr/bin/env python3
"""mcp/github/tools_file.py

MCP tool schema definitions for GitHub file operations.
"""

from __future__ import annotations

TOOL_LIST: list[dict] = [
    {
        "name": "github_get_file_contents",
        "description": (
            "Retrieve the contents of a specific file in a GitHub repository. "
            "Use to access source code, config files, and documentation"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner name (GitHub username or org)",
                },
                "repo": {"type": "string", "description": "Repository name"},
                "path": {
                    "type": "string",
                    "description": "File path (relative to repository root)",
                },
                "ref": {
                    "type": "string",
                    "description": "Branch, tag, or SHA (default: default branch)",
                },
            },
            "required": ["owner", "repo", "path"],
        },
    },
    {
        "name": "github_create_or_update_file",
        "description": (
            "Create or update a file in a GitHub repository. "
            "Use to commit a file directly"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "path": {
                    "type": "string",
                    "description": "File path (relative to repository root)",
                },
                "content": {
                    "type": "string",
                    "description": "File content (UTF-8 text)",
                },
                "message": {"type": "string", "description": "Commit message"},
                "branch": {
                    "type": "string",
                    "description": "Target branch name (default: default branch)",
                },
                "sha": {
                    "type": "string",
                    "description": "File SHA; required when updating (empty for new)",
                },
            },
            "required": ["owner", "repo", "path", "content", "message"],
        },
    },
    {
        "name": "github_push_files",
        "description": (
            "Push multiple files as a single commit to a GitHub repository. "
            "Use to atomically commit multiple files at once"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "branch": {
                    "type": "string",
                    "description": "Branch name to push to",
                },
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path (relative to repo root)",
                            },
                            "content": {
                                "type": "string",
                                "description": "File content (UTF-8 text)",
                            },
                        },
                        "required": ["path", "content"],
                    },
                    "description": "List of files to push",
                },
                "message": {"type": "string", "description": "Commit message"},
            },
            "required": ["owner", "repo", "branch", "files", "message"],
        },
    },
    {
        "name": "github_delete_file",
        "description": (
            "Delete a file from a GitHub repository. Use to commit a file deletion"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "path": {
                    "type": "string",
                    "description": "File path to delete (relative to repository root)",
                },
                "message": {"type": "string", "description": "Commit message"},
                "sha": {
                    "type": "string",
                    "description": "Current file SHA (required to prevent conflicts)",
                },
                "branch": {
                    "type": "string",
                    "description": "Target branch name (default: default branch)",
                },
            },
            "required": ["owner", "repo", "path", "message", "sha"],
        },
    },
]
