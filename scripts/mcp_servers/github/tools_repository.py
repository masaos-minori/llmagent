#!/usr/bin/env python3
"""scripts/mcp_servers/github/tools_repository.py

MCP tool schema definitions for GitHub repository operations.
"""

from __future__ import annotations

from typing import Any

# Shared metadata fields: "status" and "config_dependent" are byte-for-byte
# identical across all 6 TOOL_LIST entries, so they are split into a head
# (before "is_write"). "is_write" varies per entry and stays inline. After
# "is_write", 4 of the 6 entries also share an identical "requires_serial" +
# "resource_scope_kind" + "resource_scope_keys" tail (github_repo scope);
# github_search_repositories and github_search_code are unscoped, so they get
# their own tail with the same "requires_serial" value but an empty scope.
# Extracted so the shared parts stay in sync (mirrors the analogous
# _GITHUB_ISSUE_TOOL_METADATA_HEAD/_GITHUB_ISSUE_REPO_SCOPE_TAIL/
# _GITHUB_ISSUE_NO_SCOPE_TAIL split in
# scripts/mcp_servers/github/tools_issues.py and the analogous
# _GITHUB_PR_* split in scripts/mcp_servers/github/tools_pull_requests.py).
_GITHUB_REPOSITORY_TOOL_METADATA_HEAD: dict[str, Any] = {
    "status": "production",
    "config_dependent": True,
}
_GITHUB_REPOSITORY_REPO_SCOPE_TAIL: dict[str, Any] = {
    "requires_serial": False,
    "resource_scope_kind": "github_repo",
    "resource_scope_keys": ["owner", "repo"],
}
_GITHUB_REPOSITORY_NO_SCOPE_TAIL: dict[str, Any] = {
    "requires_serial": False,
    "resource_scope_kind": "",
    "resource_scope_keys": [],
}

TOOL_LIST: list[dict] = [
    {
        "name": "github_search_repositories",
        "description": (
            "Search GitHub repositories. Use to find OSS projects, libraries, and reference implementations"
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
        **_GITHUB_REPOSITORY_TOOL_METADATA_HEAD,
        "is_write": False,
        **_GITHUB_REPOSITORY_NO_SCOPE_TAIL,
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
        **_GITHUB_REPOSITORY_TOOL_METADATA_HEAD,
        "is_write": False,
        **_GITHUB_REPOSITORY_REPO_SCOPE_TAIL,
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
        **_GITHUB_REPOSITORY_TOOL_METADATA_HEAD,
        "is_write": True,
        **_GITHUB_REPOSITORY_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_list_commits",
        "description": (
            "Retrieve the commit history for a GitHub repository. Use to review change history and work progress"
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
        **_GITHUB_REPOSITORY_TOOL_METADATA_HEAD,
        "is_write": False,
        **_GITHUB_REPOSITORY_REPO_SCOPE_TAIL,
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
        **_GITHUB_REPOSITORY_TOOL_METADATA_HEAD,
        "is_write": False,
        **_GITHUB_REPOSITORY_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_search_code",
        "description": (
            "Full-text search for code on GitHub. Use to find implementation examples of specific functions or patterns"
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
        **_GITHUB_REPOSITORY_TOOL_METADATA_HEAD,
        "is_write": False,
        **_GITHUB_REPOSITORY_NO_SCOPE_TAIL,
    },
]
