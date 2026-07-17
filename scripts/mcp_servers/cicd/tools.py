#!/usr/bin/env python3
"""mcp_servers/cicd/tools.py

MCP tool schema definitions for cicd-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

TOOL_LIST: list[dict[str, Any]] = [
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
                "repo": {
                    "type": "string",
                    "description": "Repository slug in 'owner/repo' format",
                },
                "workflow": {
                    "type": "string",
                    "description": "Workflow file name (e.g. ci.yml) or numeric workflow ID",
                },
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
        "requires_config": True,
    },
    {
        "name": "get_workflow_runs",
        "description": (
            "List recent workflow runs for a repository. Returns run status, conclusion, timestamps, and URLs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository slug in 'owner/repo' format",
                },
                "workflow": {
                    "type": "string",
                    "description": "Workflow file name (e.g. ci.yml) or numeric workflow ID",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of runs to return (default: 10, max: 50)",
                },
            },
            "required": ["repo", "workflow"],
        },
        "status": "production",
        "requires_config": True,
    },
    {
        "name": "get_workflow_status",
        "description": (
            "Get the current status and details of a specific workflow run by run ID."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository slug in 'owner/repo' format",
                },
                "run_id": {
                    "type": "integer",
                    "description": "Workflow run ID (from get_workflow_runs output)",
                },
            },
            "required": ["repo", "run_id"],
        },
        "status": "production",
        "requires_config": True,
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
                "repo": {
                    "type": "string",
                    "description": "Repository slug in 'owner/repo' format",
                },
                "run_id": {
                    "type": "integer",
                    "description": "Workflow run ID (from get_workflow_runs output)",
                },
            },
            "required": ["repo", "run_id"],
        },
        "status": "production",
        "requires_config": True,
    },
]
