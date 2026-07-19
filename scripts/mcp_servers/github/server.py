#!/usr/bin/env python3
"""github_mcp_server.py

GitHub operations MCP server equivalent to @modelcontextprotocol/server-github.

Dependency direction: models -> service -> server_repository/file/issues/pull_requests -> server

Split layout:
  server_repository.py        — Repository operation routes (6 endpoints)
  server_file.py              — File operation routes (4 endpoints)
  server_issues.py            — Issues operation routes (5 endpoints)
  server_pull_requests.py     — Pull request operation routes (6 endpoints)
  server.py                   — App, exception handlers, dispatch, MCP integration

Available endpoints:
  POST /search_repositories    Search repositories
  POST /get_file_contents      Retrieve file contents from a repository
  POST /push_files             Push multiple files as a single commit
  POST /delete_repo_file       Delete a file from a repository
  POST /list_branches          List branches
  POST /get_commit             Retrieve details of a specific commit
  POST /list_issues            List issues
  POST /get_issue              Retrieve a specific issue
  POST /create_issue           Create an issue
  POST /search_issues          Keyword search for issues/PRs
  POST /list_pull_requests     List pull requests
  POST /get_pull_request       Retrieve a specific pull request
  POST /search_pull_requests   Keyword search for pull requests
  POST /update_pull_request    Update pull request title/body/state
  POST /merge_pull_request     Merge a pull request
  POST /list_commits           List commits
  POST /search_code            Search code
  POST /create_pull_request    Create a pull request
  POST /create_branch          Create a branch
  POST /create_or_update_file  Create or update a file
  POST /add_issue_comment      Post a comment to an issue
  GET  /health                 Health check
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mcp_servers.audit import _audit_log
from mcp_servers.dispatch import DispatchResult, _to_call_tool_response, dispatch_tool
from mcp_servers.github.exception_handlers import setup_exception_handlers
from mcp_servers.github.models import (
    GitHubConfig,
)
from mcp_servers.github.service_dispatch import GitHubService
from mcp_servers.github.service_init import _GITHUB_TOKEN, build_service
from mcp_servers.github.tools import TOOL_LIST
from mcp_servers.health_response import make_health_response
from mcp_servers.models import CallToolRequest, CallToolResponse
from mcp_servers.server import (
    MCPServer,
    ToolArgs,
    build_tools_response,
)

# Log path is owned here; service module uses logging.getLogger(__name__)
logger = logging.getLogger(__name__)

_cfg = GitHubConfig.load()  # noqa: F821
_service: GitHubService = build_service(_cfg)

app = FastAPI(
    title="github-mcp",
    version="1.0.0",
    description="MCP server equivalent to @modelcontextprotocol/server-github",
)


# ──────────────────────────────────────────────────────────────────────────────
# Domain exception handlers + register routers
# ──────────────────────────────────────────────────────────────────────────────

setup_exception_handlers(app)


def _include_routers():
    """Register all domain routers on the FastAPI application at startup."""
    from mcp_servers.github.server_file import router as file_router
    from mcp_servers.github.server_issues import router as issues_router
    from mcp_servers.github.server_pull_requests import router as pr_router
    from mcp_servers.github.server_repository import router as repo_router

    app.include_router(repo_router)
    app.include_router(file_router)
    app.include_router(issues_router)
    app.include_router(pr_router)


_include_routers()


# ──────────────────────────────────────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint. Returns GitHub token availability."""
    deps: dict[str, str] = {}
    if not _GITHUB_TOKEN:
        deps["github_token"] = "not_set"
    details: dict[str, object] = {"service": "github-mcp"}
    result: JSONResponse = make_health_response(deps, details)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch function
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_github_tool(name: str, args: ToolArgs) -> DispatchResult:
    """Route a tool call to GitHubService via its dispatch table."""
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


# ──────────────────────────────────────────────────────────────────────────────
# Tool listing endpoint (for client-side definition validation)
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    """Return tool names and descriptions for agent.json definition validation."""
    return build_tools_response(TOOL_LIST, "github")


# ──────────────────────────────────────────────────────────────────────────────
# Unified tool call endpoint
# ──────────────────────────────────────────────────────────────────────────────


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: "Request") -> CallToolResponse:
    """Execute a GitHub tool by name and return the formatted text result."""
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    r = await _dispatch_github_tool(req.name, req.args)
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=f"repo={req.args.get('owner', '')}/{req.args.get('repo', '')}",
        outcome=r.outcome,
        server_key="github",
    )
    return _to_call_tool_response(r)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class GithubMCPServer(MCPServer):
    """MCPServer subclass for github-mcp."""

    server_name = "github-mcp"
    server_version = "1.0.0"
    http_port = 8006
    own_config_file = "github_mcp_server.toml"
    app_module = "mcp_servers.github.server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        """Route a GitHub tool call to the appropriate handler."""
        return await _dispatch_github_tool(name, args)


if __name__ == "__main__":
    server = GithubMCPServer()
    server.run_http()  # type: ignore[attr-defined]
