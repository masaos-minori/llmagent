#!/usr/bin/env python3
"""shared/tool_constants.py

Canonical frozenset definitions for MCP tool classification.

These sets serve two purposes:
  shared/tool_registry.py   — registry seed data (auto-populates ToolRegistry at import time)
  shared/tool_executor.py   — side-effect detection (is_side_effect())
  agent/tool_policy.py      — risk classification and approval logic

Not a routing fallback source. Routing is driven by live `/v1/tools` discovery and ToolRegistry only.
Centralised here to avoid silent drift when tool lists change.
All sets are frozensets; treat them as read-only.
"""

from __future__ import annotations

READ_TOOLS: frozenset[str] = frozenset(
    {
        "list_directory",
        "list_directory_with_sizes",
        "directory_tree",
        "read_text_file",
        "read_media_file",
        "read_multiple_files",
        "search_files",
        "grep_files",
        "get_file_info",
    },
)

WRITE_TOOLS: frozenset[str] = frozenset(
    {
        "write_file",
        "edit_file",
        "create_directory",
        "move_file",
    },
)

DELETE_TOOLS: frozenset[str] = frozenset(
    {
        "delete_file",
        "delete_directory",
    },
)

RAG_TOOLS: frozenset[str] = frozenset(
    {
        "rag_run_pipeline",
        "rag_debug_pipeline",
        "rag_list_documents",
        "rag_delete_document",
    },
)

CICD_TOOLS: frozenset[str] = frozenset(
    {
        "trigger_workflow",
        "get_workflow_runs",
        "get_workflow_status",
        "get_workflow_logs",
    },
)

CICD_WRITE_TOOLS: frozenset[str] = frozenset({"trigger_workflow"})
CICD_READ_TOOLS: frozenset[str] = CICD_TOOLS - CICD_WRITE_TOOLS

RAG_WRITE_TOOLS: frozenset[str] = frozenset({"rag_delete_document"})
RAG_READ_TOOLS: frozenset[str] = RAG_TOOLS - RAG_WRITE_TOOLS

# Markdown Context Compression Engine tools
MDQ_TOOLS: frozenset[str] = frozenset(
    {
        "search_docs",
        "get_chunk",
        "outline",
        "index_paths",
        "refresh_index",
        "stats",
        "grep_docs",
        "fts_consistency_check",
        "fts_rebuild",
    },
)

MDQ_WRITE_TOOLS: frozenset[str] = frozenset(
    {"fts_rebuild", "index_paths", "refresh_index"}
)

# Local git operation tools (git-mcp, port 8014)
GIT_READ_TOOLS: frozenset[str] = frozenset(
    {
        "git_status",
        "git_log",
        "git_diff",
        "git_branch",
        "git_show",
    }
)

GIT_WRITE_TOOLS: frozenset[str] = frozenset(
    {
        "git_add",
        "git_commit",
        "git_checkout",
        "git_pull",
        "git_push",
    }
)

GIT_TOOLS: frozenset[str] = GIT_READ_TOOLS | GIT_WRITE_TOOLS

# Shell execution tools (shell-mcp)
SHELL_TOOLS: frozenset[str] = frozenset({"shell_run"})

# Web search tools (web-search-mcp)
WEB_SEARCH_TOOLS: frozenset[str] = frozenset({"search_web"})

# GitHub tools (github-mcp, port 8012)
GITHUB_READ_TOOLS: frozenset[str] = frozenset(
    {
        "github_search_repositories",
        "github_list_branches",
        "github_list_commits",
        "github_get_commit",
        "github_search_code",
        "github_get_file_contents",
        "github_list_issues",
        "github_get_issue",
        "github_search_issues",
        "github_list_pull_requests",
        "github_get_pull_request",
        "github_search_pull_requests",
    }
)

GITHUB_WRITE_TOOLS: frozenset[str] = frozenset(
    {
        "github_create_branch",
        "github_create_or_update_file",
        "github_push_files",
        "github_create_issue",
        "github_add_issue_comment",
        "github_create_pull_request",
        "github_update_pull_request",
    }
)

GITHUB_DANGEROUS_TOOLS: frozenset[str] = frozenset(
    {
        "github_delete_file",
        "github_merge_pull_request",
    }
)

GITHUB_TOOLS: frozenset[str] = (
    GITHUB_READ_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
)


def get_all_mcp_tool_names() -> frozenset[str]:
    """Return all known MCP tool names for conflict checking.

    This is the source of truth used by plugin_registry to detect
    plugin tools that shadow MCP tools.
    """
    return frozenset(
        READ_TOOLS
        | WRITE_TOOLS
        | DELETE_TOOLS
        | RAG_TOOLS
        | CICD_TOOLS
        | MDQ_TOOLS
        | GIT_TOOLS
        | SHELL_TOOLS
        | WEB_SEARCH_TOOLS
        | GITHUB_TOOLS,
    )
