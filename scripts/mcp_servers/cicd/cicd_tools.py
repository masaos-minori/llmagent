#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_tools.py

MCP tool schema definitions for cicd-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import TypedDict

from mcp_servers.models import McpTool, McpToolProperty

# Shared inputSchema properties: "repo" is identical across all 4 TOOL_LIST
# entries; "workflow" is identical across trigger_workflow/get_workflow_runs;
# "run_id" is identical across get_workflow_status/get_workflow_logs.
# Extracted so type/description stay in sync (mirrors the analogous
# _REPO_PATH_PROPERTY extraction in scripts/mcp_servers/git/git_tools.py).
_REPO_PROPERTY: McpToolProperty = {
    "type": "string",
    "description": "Repository slug in 'owner/repo' format",
}
_WORKFLOW_PROPERTY: McpToolProperty = {
    "type": "string",
    "description": "Workflow file name (e.g. ci.yml) or numeric workflow ID",
}
_RUN_ID_PROPERTY: McpToolProperty = {
    "type": "integer",
    "description": "Workflow run ID (from get_workflow_runs output)",
}


# Shared metadata fields: "requires_serial" and "resource_scope_kind" are
# byte-for-byte identical across all 4 TOOL_LIST entries. "is_write" and
# "resource_scope_keys" are kept per-entry because they vary (is_write is
# True only for trigger_workflow; resource_scope_keys differs per tool), so
# unlike the read_tools.py/write_tools.py/delete_tools.py/web_search_tools.py
# metadata-tail precedent (where the whole tail is uniform), only this
# 2-field sub-block is extracted here, positioned between the per-entry
# "is_write" and "resource_scope_keys" to preserve original key order.
class _CicdToolMetadataTail(TypedDict):
    """Shared trailing metadata fields common to cicd TOOL_LIST entries."""

    requires_serial: bool
    resource_scope_kind: str


_CICD_TOOL_METADATA_TAIL: _CicdToolMetadataTail = {
    "requires_serial": False,
    "resource_scope_kind": "cicd_workflow",
}

TOOL_LIST: list[McpTool] = [
    {
        "name": "trigger_workflow",
        "description": (
            "Trigger a GitHub Actions workflow dispatch event. "
            "Requires the repo to be in repo_allowlist. "
            "When dry_run=true, preview only without triggering dispatch."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": _REPO_PROPERTY,
                "workflow": _WORKFLOW_PROPERTY,
                "ref": {
                    "type": "string",
                    "description": "Branch, tag, or SHA to run the workflow on (default: main)",
                },
                "inputs": {
                    "type": "object",
                    "description": "Optional workflow input parameters (key-value pairs)",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview only; workflow dispatch is not triggered (default: false)",
                },
            },
            "required": ["repo", "workflow"],
        },
        "status": "production",
        "config_dependent": True,
        "is_write": True,
        **_CICD_TOOL_METADATA_TAIL,
        "resource_scope_keys": ["repo", "workflow", "ref"],
    },
    {
        "name": "get_workflow_runs",
        "description": (
            "List recent workflow runs for a repository. Returns run status, conclusion, timestamps, and URLs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": _REPO_PROPERTY,
                "workflow": _WORKFLOW_PROPERTY,
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of runs to return (default: 10, max: 50)",
                },
            },
            "required": ["repo", "workflow"],
        },
        "status": "production",
        "config_dependent": True,
        "is_write": False,
        **_CICD_TOOL_METADATA_TAIL,
        "resource_scope_keys": ["repo", "workflow"],
    },
    {
        "name": "get_workflow_status",
        "description": (
            "Get the current status and details of a specific workflow run by run ID."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": _REPO_PROPERTY,
                "run_id": _RUN_ID_PROPERTY,
            },
            "required": ["repo", "run_id"],
        },
        "status": "production",
        "config_dependent": True,
        "is_write": False,
        **_CICD_TOOL_METADATA_TAIL,
        "resource_scope_keys": ["repo", "run_id"],
    },
    {
        "name": "get_workflow_logs",
        "description": (
            "Retrieve job summaries and log text for a workflow run. "
            "Output is capped at max_log_size_kb (default: 256 KB)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": _REPO_PROPERTY,
                "run_id": _RUN_ID_PROPERTY,
            },
            "required": ["repo", "run_id"],
        },
        "status": "production",
        "config_dependent": True,
        "is_write": False,
        **_CICD_TOOL_METADATA_TAIL,
        "resource_scope_keys": ["repo", "run_id"],
    },
]
