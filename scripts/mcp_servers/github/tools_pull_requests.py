#!/usr/bin/env python3
"""mcp_servers/github/tools_pull_requests.py

MCP tool schema definitions for GitHub pull request operations.
"""

from __future__ import annotations

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
        "status": "production",
        "config_dependent": True,
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
        "status": "production",
        "config_dependent": True,
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
        "status": "production",
        "config_dependent": True,
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
        "status": "production",
        "config_dependent": True,
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
        "status": "production",
        "config_dependent": True,
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
        "status": "production",
        "config_dependent": True,
    },
]
