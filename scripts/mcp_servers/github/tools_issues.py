#!/usr/bin/env python3
"""scripts/mcp_servers/github/tools_issues.py

MCP tool schema definitions for GitHub issues operations.
"""

from __future__ import annotations

from typing import TypedDict

from mcp_servers.models import McpTool


# Shared metadata fields: "status" and "config_dependent" are byte-for-byte
# identical across all 5 TOOL_LIST entries, so they are split into a head
# (before "is_write"). "is_write" varies per entry and stays inline. After
# "is_write", 4 of the 5 entries also share an identical "requires_serial" +
# "resource_scope_kind" + "resource_scope_keys" tail (github_repo scope);
# github_search_issues is unscoped, so it gets its own tail with the same
# "requires_serial" value but an empty scope. Extracted so the shared parts
# stay in sync (mirrors the analogous _GITHUB_FILE_TOOL_METADATA_HEAD/_TAIL
# split in scripts/mcp_servers/github/tools_file.py).
class _GithubIssueMetadataHead(TypedDict):
    """Shared metadata fields common to github_issue TOOL_LIST entries."""

    status: str
    config_dependent: bool


class _GithubIssueRepoScopeTail(TypedDict):
    """Shared metadata tail for github_repo-scoped TOOL_LIST entries."""

    requires_serial: bool
    resource_scope_kind: str
    resource_scope_keys: list[str]


class _GithubIssueNoScopeTail(TypedDict):
    """Shared metadata tail for unscoped TOOL_LIST entries."""

    requires_serial: bool
    resource_scope_kind: str
    resource_scope_keys: list[str]


_GITHUB_ISSUE_TOOL_METADATA_HEAD: _GithubIssueMetadataHead = {
    "status": "production",
    "config_dependent": True,
}
_GITHUB_ISSUE_REPO_SCOPE_TAIL: _GithubIssueRepoScopeTail = {
    "requires_serial": False,
    "resource_scope_kind": "github_repo",
    "resource_scope_keys": ["owner", "repo"],
}
_GITHUB_ISSUE_NO_SCOPE_TAIL: _GithubIssueNoScopeTail = {
    "requires_serial": False,
    "resource_scope_kind": "",
    "resource_scope_keys": [],
}

TOOL_LIST: list[McpTool] = [
    {
        "name": "github_list_issues",
        "description": (
            "Retrieve the list of issues for a GitHub repository. "
            "Use to check bug reports, feature requests, and known issues"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "state": {
                    "type": "string",
                    "description": "Issue state: open / closed / all (default: open)",
                },
            },
            "required": ["owner", "repo"],
        },
        **_GITHUB_ISSUE_TOOL_METADATA_HEAD,
        "is_write": False,
        **_GITHUB_ISSUE_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_get_issue",
        "description": (
            "Retrieve a specific issue from a GitHub repository. Use to check issue details, body, and state"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "issue_number": {"type": "integer", "description": "Issue number"},
            },
            "required": ["owner", "repo", "issue_number"],
        },
        **_GITHUB_ISSUE_TOOL_METADATA_HEAD,
        "is_write": False,
        **_GITHUB_ISSUE_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_create_issue",
        "description": (
            "Create an issue in a GitHub repository. Use to report bugs or request features"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "title": {"type": "string", "description": "Issue title"},
                "body": {
                    "type": "string",
                    "description": "Issue body (Markdown, optional)",
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of label names (optional)",
                },
                "assignees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of assignee GitHub usernames (optional)",
                },
            },
            "required": ["owner", "repo", "title"],
        },
        **_GITHUB_ISSUE_TOOL_METADATA_HEAD,
        "is_write": True,
        **_GITHUB_ISSUE_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_search_issues",
        "description": (
            "Keyword search for issues/PRs across all of GitHub. "
            "Use to cross-search known bugs and discussions for specific projects"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g. 'repo:owner/repo is:issue')",
                },
                "per_page": {
                    "type": "integer",
                    "description": "Maximum number of results (default: configured)",
                },
            },
            "required": ["query"],
        },
        **_GITHUB_ISSUE_TOOL_METADATA_HEAD,
        "is_write": False,
        **_GITHUB_ISSUE_NO_SCOPE_TAIL,
    },
    {
        "name": "github_add_issue_comment",
        "description": (
            "Post a comment to an issue in a GitHub repository. "
            "Use to report progress, ask questions, or add information"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner name"},
                "repo": {"type": "string", "description": "Repository name"},
                "issue_number": {
                    "type": "integer",
                    "description": "Issue number to add the comment to",
                },
                "body": {"type": "string", "description": "Comment body (Markdown)"},
            },
            "required": ["owner", "repo", "issue_number", "body"],
        },
        **_GITHUB_ISSUE_TOOL_METADATA_HEAD,
        "is_write": True,
        **_GITHUB_ISSUE_REPO_SCOPE_TAIL,
    },
]
