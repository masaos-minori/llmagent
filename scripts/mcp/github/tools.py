#!/usr/bin/env python3
"""mcp/github/tools.py
MCP tool schema definitions for github-mcp server (inputSchema format).

Imported by mcp/github/server.py to keep the server module under 400 lines.
"""

from __future__ import annotations

_MCP_TOOLS = [
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
    },
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
    },
    {
        "name": "github_get_issue",
        "description": (
            "Retrieve a specific issue from a GitHub repository. "
            "Use to check issue details, body, and state"
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
    },
    {
        "name": "github_create_issue",
        "description": (
            "Create an issue in a GitHub repository. "
            "Use to report bugs or request features"
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
    },
    {
        "name": "github_list_pull_requests",
        "description": (
            "Retrieve the list of pull requests for a GitHub repository. "
            "Use to check pending reviews or past PRs"
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
    },
    {
        "name": "github_get_pull_request",
        "description": (
            "Retrieve a specific pull request from a GitHub repository. "
            "Use to check PR details, branch info, and body"
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
    },
    {
        "name": "github_create_pull_request",
        "description": (
            "Create a pull request in a GitHub repository. "
            "Use to request a review of branch changes"
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
    },
    {
        "name": "github_update_pull_request",
        "description": (
            "Update the title, body, or state of a GitHub pull request. "
            "Use to reopen or close a PR"
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
    },
]
