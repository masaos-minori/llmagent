#!/usr/bin/env python3
"""mcp/github/tools_repository.py

MCP tool schema definitions for GitHub repository operations.
"""

from __future__ import annotations

TOOL_LIST: list[dict] = [
    {
        "name": "github_search_repositories",
        "description": (
            "Search GitHub repositories. "
            "Use to find OSS projects, libraries, and reference implementations"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Repository search query (GitHub Search syntax)",
                },
                "per_page": {
                    "type": "integer",
                    "description": "Maximum number of results (default: configured)",
                },
            },
            "required": ["query"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "github_list_branches",
        "description": (
            "Retrieve the list of branches for a GitHub repository. "
            "Use to check working branches and protected branches"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
            },
            "required": ["owner", "repo"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "github_create_branch",
        "description": (
            "Create a branch in a GitHub repository. "
            "Use to set up a working branch for new feature development or bug fixes"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "branch_name": {
                    "type": "string",
                    "description": "Name of the new branch to create",
                },
                "from_branch": {
                    "type": "string",
                    "description": "Base branch to derive from (default: repo default)",
                },
            },
            "required": ["owner", "repo", "branch_name"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "github_list_commits",
        "description": (
            "Retrieve the commit history for a GitHub repository. "
            "Use to review change history and work progress"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "branch": {
                    "type": "string",
                    "description": "Branch name (default: default branch)",
                },
            },
            "required": ["owner", "repo"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "github_get_commit",
        "description": (
            "Retrieve details of a specific commit in a GitHub repository. "
            "Use to check changed file count, commit message, and author"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "sha": {
                    "type": "string",
                    "description": "Commit SHA (full or abbreviated)",
                },
            },
            "required": ["owner", "repo", "sha"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "github_search_code",
        "description": (
            "Full-text search for code on GitHub. "
            "Use to find implementation examples of specific functions or patterns"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Code search query (e.g. 'vec0 language:C')",
                },
            },
            "required": ["query"],
        },
        "status": "production",
        "requires_config": True,
    },
]
