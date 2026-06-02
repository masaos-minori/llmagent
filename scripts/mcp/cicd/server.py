#!/usr/bin/env python3
"""mcp/cicd/server.py
CI/CD MCP server (GitHub Actions backend, port 8012).

Provides HTTP endpoints for triggering and inspecting GitHub Actions workflows.

Security:
  - repo_allowlist: only listed 'owner/repo' slugs are accessible (fail-closed)
  - workflow_allowlist: restrict triggerable workflows (empty = allow all)
  - max_log_size_kb: log output is capped to prevent large data dumps
  - Optional Bearer-token auth via auth_token in cicd_mcp_server.toml

Provided endpoints:
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
  GET  /health        Health check
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request

from mcp.cicd.models import _get_cfg
from mcp.cicd.service import _service
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import (
    MCPServer,
    ToolArgs,
    _audit_log,
    attach_auth_middleware,
    dispatch_tool,
)

logger = logging.getLogger(__name__)

_cfg = _get_cfg()

app = FastAPI(
    title="cicd-mcp",
    version="1.0.0",
    description="CI/CD (GitHub Actions) MCP server",
)

attach_auth_middleware(app, _cfg.get("auth_token", ""))


# ──────────────────────────────────────────────────────────────────────────────
# MCP tool definitions
# ──────────────────────────────────────────────────────────────────────────────

_MCP_TOOLS = [
    {
        "name": "trigger_workflow",
        "description": (
            "Trigger a GitHub Actions workflow dispatch event. "
            "Requires the repo to be in repo_allowlist."
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
            },
            "required": ["repo", "workflow"],
        },
    },
    {
        "name": "get_workflow_runs",
        "description": (
            "List recent workflow runs for a repository. "
            "Returns run status, conclusion, timestamps, and URLs."
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
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_cicd_tool(name: str, args: ToolArgs) -> tuple[str, bool]:
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in _MCP_TOOLS
        ],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    result, is_error = await _dispatch_cicd_tool(req.name, req.args)
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=req.args.get("repo", ""),
        outcome="error" if is_error else "ok",
    )
    return CallToolResponse(result=result, is_error=is_error)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class CiCdMCPServer(MCPServer):
    """MCPServer subclass for cicd-mcp (GitHub Actions backend)."""

    server_name = "cicd-mcp"
    server_version = "1.0.0"
    http_port = 8012
    app_module = "mcp.cicd.server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        return await _dispatch_cicd_tool(name, args)


if __name__ == "__main__":
    import sys

    server = CiCdMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
