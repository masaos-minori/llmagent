#!/usr/bin/env python3
"""mcp_servers/github/tools_issues.py

MCP tool schema definitions for GitHub issues operations.
"""

from __future__ import annotations

TOOL_LIST: list[dict] = [
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
        "status": "production",
        "requires_config": True,
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
        "status": "production",
        "requires_config": True,
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
        "status": "production",
        "requires_config": True,
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
        "status": "production",
        "requires_config": True,
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
        "status": "production",
        "requires_config": True,
    },
]
