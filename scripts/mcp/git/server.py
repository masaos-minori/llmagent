#!/usr/bin/env python3
"""mcp/git/server.py
Local git operations MCP server (port 8014).

Provides an HTTP API via FastAPI for safe git operations against allowlisted repositories.

Security:
  - Operations are restricted to repositories in allowed_repo_paths (fail-closed)
  - read_only=true (default) prevents all write operations (add/commit/checkout/pull/push)
  - All write tools support dry_run=True for preview without side effects
  - Optional Bearer-token auth via auth_token in git_mcp_server.toml

Provided endpoints:
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
  GET  /health        Health check
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from mcp.dispatch import dispatch_tool
from mcp.git.models import load_git_config
from mcp.git.service import build_service
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs, attach_auth_middleware

_cfg = load_git_config()
_service = build_service(_cfg)

app = FastAPI(
    title="git-mcp",
    version="1.0.0",
    description="Local git operations MCP server",
)

attach_auth_middleware(app, _cfg.get("auth_token", ""))


# ──────────────────────────────────────────────────────────────────────────────
# MCP tool definitions
# ──────────────────────────────────────────────────────────────────────────────

_MCP_TOOLS = [
    {
        "name": "git_status",
        "description": "Show the working tree status of a local git repository.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
            },
            "required": ["repo_path"],
        },
    },
    {
        "name": "git_log",
        "description": "Show commit history. Results capped at max_log_entries (default: 20).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "max_entries": {
                    "type": "integer",
                    "description": "Max commits to return (1–200)",
                    "default": 20,
                },
                "branch": {
                    "type": "string",
                    "description": "Branch or ref; empty = current HEAD",
                    "default": "",
                },
            },
            "required": ["repo_path"],
        },
    },
    {
        "name": "git_diff",
        "description": "Show diff of working tree, staged changes, or against a commit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "staged": {
                    "type": "boolean",
                    "description": "When true, show staged diff (--cached)",
                    "default": False,
                },
                "commit": {
                    "type": "string",
                    "description": "Commit ref to diff against; empty = working tree",
                    "default": "",
                },
            },
            "required": ["repo_path"],
        },
    },
    {
        "name": "git_branch",
        "description": "List all local branches. Current branch is marked with *.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
            },
            "required": ["repo_path"],
        },
    },
    {
        "name": "git_show",
        "description": "Show the content of a commit (stat + patch). Output capped at 8000 chars.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "ref": {
                    "type": "string",
                    "description": "Commit ref or tag",
                    "default": "HEAD",
                },
            },
            "required": ["repo_path"],
        },
    },
    {
        "name": "git_add",
        "description": "Stage files for commit. Requires read_only=false in config.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File paths to stage",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview only without staging",
                    "default": False,
                },
            },
            "required": ["repo_path", "paths"],
        },
    },
    {
        "name": "git_commit",
        "description": "Commit staged changes. Requires read_only=false in config.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "message": {"type": "string", "description": "Commit message"},
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview staged files without committing",
                    "default": False,
                },
            },
            "required": ["repo_path", "message"],
        },
    },
    {
        "name": "git_checkout",
        "description": "Switch or create a branch. Requires read_only=false in config.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name to checkout or create",
                },
                "create": {
                    "type": "boolean",
                    "description": "When true, create a new branch (-b)",
                    "default": False,
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview only without switching",
                    "default": False,
                },
            },
            "required": ["repo_path", "branch"],
        },
    },
    {
        "name": "git_pull",
        "description": "Pull from remote. Requires read_only=false in config.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "remote": {
                    "type": "string",
                    "description": "Remote name",
                    "default": "origin",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name; empty = current tracking branch",
                    "default": "",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Perform fetch --dry-run only",
                    "default": False,
                },
            },
            "required": ["repo_path"],
        },
    },
    {
        "name": "git_push",
        "description": "Push branch to remote. Requires read_only=false in config.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository",
                },
                "remote": {
                    "type": "string",
                    "description": "Remote name",
                    "default": "origin",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name; empty = current branch",
                    "default": "",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview only without pushing",
                    "default": False,
                },
            },
            "required": ["repo_path"],
        },
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_git_tool(name: str, args: ToolArgs) -> tuple[str, bool]:
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
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    result, is_error = await _dispatch_git_tool(req.name, req.args)
    return CallToolResponse(result=result, is_error=is_error)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class GitMCPServer(MCPServer):
    """MCPServer subclass for git-mcp."""

    server_name = "git-mcp"
    server_version = "1.0.0"
    http_port = 8014
    app_module = "mcp.git.server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        return await _dispatch_git_tool(name, args)


if __name__ == "__main__":
    import sys

    server = GitMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
