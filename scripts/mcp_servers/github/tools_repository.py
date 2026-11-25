#!/usr/bin/env python3
"""scripts/mcp_servers/github/tools_repository.py

MCP tool schema definitions for GitHub repository operations.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

from shared.tool_metadata import TOOL_FIELD_SET_VERSION, ResourceKeyKind

from mcp_servers.github.github_models_repository import (
    CreateBranchRequest,
    GetCommitRequest,
    ListBranchesRequest,
    ListCommitsRequest,
    SearchCodeRequest,
    SearchRepositoriesRequest,
)
from mcp_servers.models import McpTool
from mcp_servers.request_contract import build_input_schema


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
class _GithubRepositoryMetadataHead(TypedDict):
    """Shared metadata fields common to github_repository TOOL_LIST entries."""

    policy_version: str
    status: str
    config_dependent: bool


class _GithubRepositoryRepoScopeTail(TypedDict):
    """Shared metadata tail for github_repo-scoped TOOL_LIST entries."""

    requires_serial: bool
    resource_scope_kind: str
    resource_scope_keys: Mapping[str, ResourceKeyKind]


class _GithubRepositoryNoScopeTail(TypedDict):
    """Shared metadata tail for unscoped TOOL_LIST entries."""

    requires_serial: bool
    resource_scope_kind: str
    resource_scope_keys: Mapping[str, ResourceKeyKind]


_GITHUB_REPOSITORY_TOOL_METADATA_HEAD: _GithubRepositoryMetadataHead = {
    "status": "production",
    "config_dependent": True,
    "policy_version": TOOL_FIELD_SET_VERSION,
}
_GITHUB_REPOSITORY_REPO_SCOPE_TAIL: _GithubRepositoryRepoScopeTail = {
    "requires_serial": False,
    "resource_scope_kind": "github_repo",
    "resource_scope_keys": {"owner": "non_escalating", "repo": "repo"},
}
_GITHUB_REPOSITORY_NO_SCOPE_TAIL: _GithubRepositoryNoScopeTail = {
    "requires_serial": False,
    "resource_scope_kind": "",
    "resource_scope_keys": {},
}

TOOL_LIST: list[McpTool] = [
    {
        "name": "github_search_repositories",
        "description": (
            "Search GitHub repositories. Use to find OSS projects, libraries, and reference implementations"
        ),
        "inputSchema": build_input_schema(SearchRepositoriesRequest),
        **_GITHUB_REPOSITORY_TOOL_METADATA_HEAD,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        **_GITHUB_REPOSITORY_NO_SCOPE_TAIL,
    },
    {
        "name": "github_list_branches",
        "description": (
            "Retrieve the list of branches for a GitHub repository. "
            "Use to check working branches and protected branches"
        ),
        "inputSchema": build_input_schema(ListBranchesRequest),
        **_GITHUB_REPOSITORY_TOOL_METADATA_HEAD,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        **_GITHUB_REPOSITORY_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_create_branch",
        "description": (
            "Create a branch in a GitHub repository. "
            "Use to set up a working branch for new feature development or bug fixes"
        ),
        "inputSchema": build_input_schema(CreateBranchRequest),
        **_GITHUB_REPOSITORY_TOOL_METADATA_HEAD,
        "is_write": True,
        "agent_safety_tier": "WRITE_SAFE",
        "side_effect_class": "external_write",
        "retry_policy": "never",
        "reconciliation_policy": "external_state",
        "idempotency_required": True,
        "preview_capability": "dry_run",
        **_GITHUB_REPOSITORY_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_list_commits",
        "description": (
            "Retrieve the commit history for a GitHub repository. Use to review change history and work progress"
        ),
        "inputSchema": build_input_schema(ListCommitsRequest),
        **_GITHUB_REPOSITORY_TOOL_METADATA_HEAD,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        **_GITHUB_REPOSITORY_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_get_commit",
        "description": (
            "Retrieve details of a specific commit in a GitHub repository. "
            "Use to check changed file count, commit message, and author"
        ),
        "inputSchema": build_input_schema(GetCommitRequest),
        **_GITHUB_REPOSITORY_TOOL_METADATA_HEAD,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        **_GITHUB_REPOSITORY_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_search_code",
        "description": (
            "Full-text search for code on GitHub. Use to find implementation examples of specific functions or patterns"
        ),
        "inputSchema": build_input_schema(SearchCodeRequest),
        **_GITHUB_REPOSITORY_TOOL_METADATA_HEAD,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        **_GITHUB_REPOSITORY_NO_SCOPE_TAIL,
    },
]
