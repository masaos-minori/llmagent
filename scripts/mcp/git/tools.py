#!/usr/bin/env python3
"""mcp/git/tools.py
MCP tool schema definitions for git-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

McpToolProperty = dict[str, Any]  # noqa: ANN401 - MCP schema property with optional fields
McpInputSchema = dict[str, Any]  # noqa: ANN401 - MCP inputSchema with nested optional fields
McpTool = dict[str, Any]  # noqa: ANN401 - MCP tool definition with optional fields

TOOL_LIST: list[McpTool] = [
    {
        "name": "git_status",
        "description": "Show the working tree status of a local git repository.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
            },
            "required": ["repo_path"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "git_log",
        "description": "Show commit history. Results capped at max_log_entries (default: 20).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "max_entries": {
                    "type": "integer",
                    "description": "Max commits to return (1-200)",
                    "default": 20,
                },
                "branch": {
                    "type": "string",
                    "description": "Branch or ref; empty = current HEAD",
                    "default": "",
                },
            },
            "required": ["repo_path"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "git_diff",
        "description": "Show diff of working tree, staged changes, or against a commit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "staged": {
                    "type": "boolean",
                    "description": "When true, show staged diff (--cached)",
                    "default": False,
                },
                "commit": {
                    "type": "string",
                    "description": "Commit ref to diff against; empty = working tree",
                    "default": "",
                },
            },
            "required": ["repo_path"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "git_branch",
        "description": "List all local branches. Current branch is marked with *.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
            },
            "required": ["repo_path"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "git_show",
        "description": "Show the content of a commit (stat + patch). Output capped at 8000 chars.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "ref": {
                    "type": "string",
                    "description": "Commit ref or tag",
                    "default": "HEAD",
                },
            },
            "required": ["repo_path"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "git_add",
        "description": "Stage files for commit. Requires read_only=false in config.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File paths to stage",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview only without staging",
                    "default": False,
                },
            },
            "required": ["repo_path", "paths"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "git_commit",
        "description": "Commit staged changes. Requires read_only=false in config.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "message": {"type": "string", "description": "Commit message"},
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview staged files without committing",
                    "default": False,
                },
            },
            "required": ["repo_path", "message"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "git_checkout",
        "description": "Switch or create a branch. Requires read_only=false in config.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name to checkout or create",
                },
                "create": {
                    "type": "boolean",
                    "description": "When true, create a new branch (-b)",
                    "default": False,
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview only without switching",
                    "default": False,
                },
            },
            "required": ["repo_path", "branch"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "git_pull",
        "description": "Pull from remote. Requires read_only=false in config.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "remote": {
                    "type": "string",
                    "description": "Remote name",
                    "default": "origin",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name; empty = current tracking branch",
                    "default": "",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Perform fetch --dry-run only",
                    "default": False,
                },
            },
            "required": ["repo_path"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "git_push",
        "description": "Push branch to remote. Requires read_only=false in config.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "remote": {
                    "type": "string",
                    "description": "Remote name",
                    "default": "origin",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name; empty = current branch",
                    "default": "",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview only without pushing",
                    "default": False,
                },
            },
            "required": ["repo_path"],
        },
        "status": "production",
        "requires_config": True,
    },
]
