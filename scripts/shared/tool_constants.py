#!/usr/bin/env python3
"""shared/tool_constants.py
Canonical frozenset definitions for MCP tool classification.

These sets are used in three places:
  shared/route_resolver.py  — static routing (tool_name → server_key)
  shared/tool_executor.py   — side-effect detection (is_side_effect())
  agent/repl_tool_exec.py   — risk classification and approval logic

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
    },
)

# Local git operation tools (git-mcp, port 8014)
GIT_TOOLS: frozenset[str] = frozenset(
    {
        "git_status",
        "git_log",
        "git_diff",
        "git_branch",
        "git_show",
        "git_add",
        "git_commit",
        "git_checkout",
        "git_pull",
        "git_push",
    },
)

# SQLite query tools (sqlite-mcp, port 8011)
SQLITE_TOOLS: frozenset[str] = frozenset(
    {
        "query_sqlite",
    },
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
        | SQLITE_TOOLS,
    )
