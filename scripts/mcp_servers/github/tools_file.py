#!/usr/bin/env python3
"""scripts/mcp_servers/github/tools_file.py

MCP tool schema definitions for GitHub file operations.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

from shared.tool_metadata import TOOL_FIELD_SET_VERSION, ResourceKeyKind

from mcp_servers.github.github_models_file import (
    CreateOrUpdateFileRequest,
    DeleteRepoFileRequest,
    GetFileContentsRequest,
    PushFilesRequest,
)
from mcp_servers.models import McpTool
from mcp_servers.request_contract import build_input_schema


# Shared metadata fields: "status", "config_dependent", "requires_serial",
# "resource_scope_kind", and "resource_scope_keys" are byte-for-byte identical
# across all 4 TOOL_LIST entries. Only "is_write" varies (False for
# github_get_file_contents; True for the other 3), so it stays per-entry and
# the shared fields are split into a head (before "is_write") and tail (after
# "is_write") to preserve original key order. Extracted so they stay in sync
# (mirrors the analogous _CICD_TOOL_METADATA_TAIL split in
# scripts/mcp_servers/cicd/cicd_tools.py and the _FILESYSTEM_*_METADATA
# precedents in scripts/mcp_servers/file/read_tools.py,
# scripts/mcp_servers/file/write_tools.py, and
# scripts/mcp_servers/file/delete_tools.py).
class _GithubFileMetadataHead(TypedDict):
    """Shared metadata fields common to github_file TOOL_LIST entries."""

    policy_version: str
    status: str
    config_dependent: bool


class _GithubFileMetadataTail(TypedDict):
    """Shared metadata tail for github_repo-scoped TOOL_LIST entries."""

    requires_serial: bool
    resource_scope_kind: str
    resource_scope_keys: Mapping[str, ResourceKeyKind]


_GITHUB_FILE_TOOL_METADATA_HEAD: _GithubFileMetadataHead = {
    "status": "production",
    "config_dependent": True,
    "policy_version": TOOL_FIELD_SET_VERSION,
}
_GITHUB_FILE_TOOL_METADATA_TAIL: _GithubFileMetadataTail = {
    "requires_serial": False,
    "resource_scope_kind": "github_repo",
    "resource_scope_keys": {"owner": "non_escalating", "repo": "repo"},
}

TOOL_LIST: list[McpTool] = [
    {
        "name": "github_get_file_contents",
        "description": (
            "Retrieve the contents of a specific file in a GitHub repository. "
            "Use to access source code, config files, and documentation"
        ),
        "inputSchema": build_input_schema(GetFileContentsRequest),
        **_GITHUB_FILE_TOOL_METADATA_HEAD,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        **_GITHUB_FILE_TOOL_METADATA_TAIL,
    },
    {
        "name": "github_create_or_update_file",
        "description": (
            "Create or update a file in a GitHub repository. Use to commit a file directly"
        ),
        "inputSchema": build_input_schema(CreateOrUpdateFileRequest),
        **_GITHUB_FILE_TOOL_METADATA_HEAD,
        "is_write": True,
        "agent_safety_tier": "WRITE_DANGEROUS",
        "side_effect_class": "external_write",
        "retry_policy": "same_logical_call_only",
        "reconciliation_policy": "external_state",
        "idempotency_required": True,
        "preview_capability": "dry_run",
        **_GITHUB_FILE_TOOL_METADATA_TAIL,
    },
    {
        "name": "github_push_files",
        "description": (
            "Push multiple files as a single commit to a GitHub repository. "
            "Use to atomically commit multiple files at once"
        ),
        "inputSchema": build_input_schema(PushFilesRequest),
        **_GITHUB_FILE_TOOL_METADATA_HEAD,
        "is_write": True,
        "agent_safety_tier": "WRITE_DANGEROUS",
        "side_effect_class": "external_write",
        "retry_policy": "same_logical_call_only",
        "reconciliation_policy": "external_state",
        "idempotency_required": True,
        "preview_capability": "dry_run",
        **_GITHUB_FILE_TOOL_METADATA_TAIL,
    },
    {
        "name": "github_delete_file",
        "description": (
            "Delete a file from a GitHub repository. Use to commit a file deletion"
        ),
        "inputSchema": build_input_schema(DeleteRepoFileRequest),
        **_GITHUB_FILE_TOOL_METADATA_HEAD,
        "is_write": True,
        "agent_safety_tier": "WRITE_DANGEROUS",
        "side_effect_class": "external_write",
        "retry_policy": "same_logical_call_only",
        "reconciliation_policy": "external_state",
        "idempotency_required": True,
        "preview_capability": "dry_run",
        **_GITHUB_FILE_TOOL_METADATA_TAIL,
    },
]
