#!/usr/bin/env python3
"""scripts/mcp_servers/github/tools_pull_requests.py

MCP tool schema definitions for GitHub pull request operations.
"""

from __future__ import annotations

from typing import Any

# Shared metadata fields: "status" and "config_dependent" are byte-for-byte
# identical across all 6 TOOL_LIST entries, so they are split into a head
# (before "is_write"). "is_write" varies per entry and stays inline. After
# "is_write", 5 of the 6 entries also share an identical "requires_serial" +
# "resource_scope_kind" + "resource_scope_keys" tail (github_repo scope);
# github_search_pull_requests is unscoped, so it gets its own tail with the
# same "requires_serial" value but an empty scope. Extracted so the shared
# parts stay in sync (mirrors the analogous
# _GITHUB_ISSUE_TOOL_METADATA_HEAD/_GITHUB_ISSUE_REPO_SCOPE_TAIL/
# _GITHUB_ISSUE_NO_SCOPE_TAIL split in
# scripts/mcp_servers/github/tools_issues.py).
_GITHUB_PR_TOOL_METADATA_HEAD: dict[str, Any] = {
    "status": "production",
    "config_dependent": True,
}
_GITHUB_PR_REPO_SCOPE_TAIL: dict[str, Any] = {
    "requires_serial": False,
    "resource_scope_kind": "github_repo",
    "resource_scope_keys": ["owner", "repo"],
}
_GITHUB_PR_NO_SCOPE_TAIL: dict[str, Any] = {
    "requires_serial": False,
    "resource_scope_kind": "",
    "resource_scope_keys": [],
}

TOOL_LIST: list[dict] = [
    {
        "name": "github_list_pull_requests",
        "description": (
            "Retrieve the list of pull requests for a GitHub repository. Use to check pending reviews or past PRs"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "state": {
                    "type": "string",
                    "description": "PR state: open / closed / all (default: open)",
                },
            },
            "required": ["owner", "repo"],
        },
        **_GITHUB_PR_TOOL_METADATA_HEAD,
        "is_write": False,
        **_GITHUB_PR_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_get_pull_request",
        "description": (
            "Retrieve a specific pull request from a GitHub repository. Use to check PR details, branch info, and body"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "pr_number": {
                    "type": "integer",
                    "description": "Pull request number",
                },
            },
            "required": ["owner", "repo", "pr_number"],
        },
        **_GITHUB_PR_TOOL_METADATA_HEAD,
        "is_write": False,
        **_GITHUB_PR_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_create_pull_request",
        "description": (
            "Create a pull request in a GitHub repository. Use to request a review of branch changes"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "title": {"type": "string", "description": "Pull request title"},
                "body": {
                    "type": "string",
                    "description": "Pull request body (Markdown, optional)",
                },
                "head": {
                    "type": "string",
                    "description": "Source branch name for the PR",
                },
                "base": {
                    "type": "string",
                    "description": "Target branch name to merge into",
                },
            },
            "required": ["owner", "repo", "title", "head", "base"],
        },
        **_GITHUB_PR_TOOL_METADATA_HEAD,
        "is_write": True,
        **_GITHUB_PR_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_search_pull_requests",
        "description": (
            "Keyword search for pull requests across all of GitHub. "
            "Use to cross-search PRs related to a specific feature"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (is:pr is appended automatically)",
                },
                "per_page": {
                    "type": "integer",
                    "description": "Maximum number of results (default: configured)",
                },
            },
            "required": ["query"],
        },
        **_GITHUB_PR_TOOL_METADATA_HEAD,
        "is_write": False,
        **_GITHUB_PR_NO_SCOPE_TAIL,
    },
    {
        "name": "github_update_pull_request",
        "description": (
            "Update the title, body, or state of a GitHub pull request. Use to reopen or close a PR"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "pr_number": {
                    "type": "integer",
                    "description": "Pull request number to update",
                },
                "title": {
                    "type": "string",
                    "description": "New title (omit to keep unchanged)",
                },
                "body": {
                    "type": "string",
                    "description": "New body (omit to keep unchanged)",
                },
                "state": {
                    "type": "string",
                    "description": "New state: open / closed (omit to keep unchanged)",
                },
            },
            "required": ["owner", "repo", "pr_number"],
        },
        **_GITHUB_PR_TOOL_METADATA_HEAD,
        "is_write": True,
        **_GITHUB_PR_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_merge_pull_request",
        "description": (
            "Merge a GitHub pull request. Use to merge a PR after review is complete"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "pr_number": {
                    "type": "integer",
                    "description": "Pull request number to merge",
                },
                "commit_title": {
                    "type": "string",
                    "description": "Merge commit title (default: GitHub default)",
                },
                "commit_message": {
                    "type": "string",
                    "description": "Merge commit body (default: GitHub default)",
                },
                "merge_method": {
                    "type": "string",
                    "description": "Merge method: merge / squash / rebase",
                },
            },
            "required": ["owner", "repo", "pr_number"],
        },
        **_GITHUB_PR_TOOL_METADATA_HEAD,
        "is_write": True,
        **_GITHUB_PR_REPO_SCOPE_TAIL,
    },
]
