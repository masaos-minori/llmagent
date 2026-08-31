#!/usr/bin/env python3
"""scripts/mcp_servers/git/git_server.py

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

import logging
import shutil
import time
from collections.abc import Callable
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.tool_constants import GIT_WRITE_TOOLS

from mcp_servers.audit import _audit_log
from mcp_servers.dispatch import DispatchResult, dispatch_tool
from mcp_servers.git.errors import GitServiceError
from mcp_servers.git.format_output import format_checkout, format_pull, format_push
from mcp_servers.git.git_models import (
    GitCheckoutRequest,
    GitConfig,
    GitPullRequest,
    GitPushRequest,
)
from mcp_servers.git.git_security import _resolve_repo_path
from mcp_servers.git.git_service import build_service
from mcp_servers.git.git_tools import TOOL_LIST
from mcp_servers.git.repository_state import RepositoryState, WriteProtectionPipeline
from mcp_servers.health_response import make_health_response
from mcp_servers.models import CallToolRequest, CallToolResponse, McpTool
from mcp_servers.server import (
    MCPServer,
    ToolArgs,
    _FastAPIApp,
    attach_auth_middleware,
    build_tools_response,
    extract_request_context,
)

logger = logging.getLogger(__name__)

_cfg = GitConfig.load()
_service = build_service(_cfg)


def _serialize_state(state: RepositoryState | None) -> dict[str, object] | None:
    """Serialize a RepositoryState to a JSON-safe dict."""
    if state is None:
        return None
    return {
        "path": state.path,
        "is_dirty": state.is_dirty,
        "head_type": state.head_type,
        "active_branch": state.active_branch,
        "untracked_file_count": state.untracked_file_count,
        "protected_branch": state.protected_branch,
        "ref_valid": state.ref_valid,
    }


app = FastAPI(
    title="git-mcp",
    version="1.0.0",
    description="Local git operations MCP server",
)

attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token or "")


@app.exception_handler(GitServiceError)
async def _on_git_service_error(_req: Request, exc: GitServiceError) -> JSONResponse:
    """Handle git service errors by returning a 500 response."""
    return JSONResponse({"detail": str(exc)}, status_code=500)


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch
# ──────────────────────────────────────────────────────────────────────────────


def _git_tool_availability(cfg: GitConfig, tool_name: str) -> tuple[bool, str]:
    """Return (enabled, disabled_reason) for a single git tool by name."""
    if not cfg.allowed_repo_paths:
        return False, "allowed_repo_paths is empty"
    if cfg.read_only and tool_name in GIT_WRITE_TOOLS:
        return False, "read_only=true"
    return True, ""


async def _dispatch_git_tool(name: str, args: ToolArgs) -> DispatchResult:
    """Dispatch a tool request to the git service."""
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


def _annotate_tool(tool: McpTool, cfg: GitConfig) -> dict[str, Any]:
    """Return a copy of tool with server_key and availability fields attached."""
    enabled, reason = _git_tool_availability(cfg, tool["name"])
    return {
        **tool,
        "server_key": "git",
        "enabled": enabled,
        "disabled_reason": reason,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/v1/tools")
async def list_tools(
    include_disabled: bool = False, disabled_code: str | None = None
) -> dict[str, Any]:
    """List available MCP tools with schema_version and server key annotation."""
    annotated = [_annotate_tool(t, _cfg) for t in TOOL_LIST]
    return build_tools_response(
        cast("list[McpTool]", annotated),
        "git",
        include_disabled=include_disabled,
        disabled_code=disabled_code,
    )


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Handle a generic MCP call_tool request with audit logging."""
    enabled, reason = _git_tool_availability(_cfg, req.name)
    if not enabled:
        return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)
    try:
        req.validate_args()
    except ValueError as e:
        return CallToolResponse(result=f"Validation error: {e}", is_error=True)
    t0 = time.perf_counter()
    session_id, request_id = extract_request_context(request)
    repo_path = cast(str, req.args.get("repo_path", ""))
    ok, err, resolved = _resolve_repo_path(repo_path)
    if not ok:
        logger.info(
            fmt_kvlog("call_tool", tool=req.name, ms=f"{time.perf_counter() - t0:.0f}")
        )
        _audit_log(
            logger,
            session_id=session_id,
            request_id=request_id,
            action=req.name,
            target="",
            outcome="rejected",
            server_key="git",
            pre_condition=_serialize_state(RepositoryState.snapshot(repo_path)),
            post_condition=None,
        )
        return CallToolResponse(result=f"Validation error: {err}", is_error=True)
    pre_state = RepositoryState.snapshot(resolved)
    handlers: dict[str, Callable[[], str]] = {
        "git_checkout": lambda: GitMCPServer._format_checkout(pre_state, req),
        "git_pull": lambda: GitMCPServer._format_pull(pre_state, req),
        "git_push": lambda: GitMCPServer._format_push(pre_state, req),
    }
    handler = handlers.get(req.name)
    if handler is None:
        return CallToolResponse(result=f"Unknown tool: {req.name}", is_error=True)
    pipeline = WriteProtectionPipeline(pre_state)
    result = pipeline.run(req.name, handler)
    post_state = RepositoryState.snapshot(resolved)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=resolved,
        outcome="success" if result.ok else "rejected",
        server_key="git",
        pre_condition=_serialize_state(pre_state),
        post_condition=_serialize_state(post_state),
    )
    return CallToolResponse(
        result=result.output,
        is_error=not result.ok,
    )


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint verifying git availability."""
    deps: dict[str, str] = {}
    try:
        if shutil.which("git") is None:
            deps["git"] = "git not found in PATH"
    except OSError:
        deps["git"] = "check failed"
    details: dict[str, object] = {"service": "git-mcp"}
    result: JSONResponse = make_health_response(deps, details)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class GitMCPServer(MCPServer):
    """MCPServer subclass for git-mcp."""

    server_name = "git-mcp"
    server_version = "1.0.0"
    http_port = 8014
    own_config_file = "git_mcp_server.toml"
    app_module = "mcp_servers.git.git_server:app"
    mcp_tools = TOOL_LIST

    @staticmethod
    def _format_checkout(state: RepositoryState, req: CallToolRequest) -> str:
        """Delegate to format_checkout with RepositoryState."""
        checkout_req = GitCheckoutRequest(
            repo_path=cast(str, req.args.get("repo_path", "")),
            branch=cast(str, req.args.get("branch", "")),
            create=cast(bool, req.args.get("create", False)),
            dry_run=cast(bool, req.args.get("dry_run", False)),
        )
        return format_checkout(
            state, checkout_req, allow_detached_head=_cfg.allow_detached_head
        )

    @staticmethod
    def _format_pull(state: RepositoryState, req: CallToolRequest) -> str:
        """Delegate to format_pull with RepositoryState."""
        pull_req = GitPullRequest(
            repo_path=cast(str, req.args.get("repo_path", "")),
            remote=cast(str, req.args.get("remote", "origin")),
            branch=cast(str, req.args.get("branch", "")),
            dry_run=cast(bool, req.args.get("dry_run", False)),
        )
        return format_pull(state, pull_req)

    @staticmethod
    def _format_push(state: RepositoryState, req: CallToolRequest) -> str:
        """Delegate to format_push with RepositoryState."""
        push_req = GitPushRequest(
            repo_path=cast(str, req.args.get("repo_path", "")),
            remote=cast(str, req.args.get("remote", "origin")),
            branch=cast(str, req.args.get("branch", "")),
            dry_run=cast(bool, req.args.get("dry_run", False)),
        )
        return format_push(state, push_req)

    async def dispatch(self, name: str, args: ToolArgs) -> DispatchResult:
        """Dispatch a tool invocation via the git service."""
        return await _dispatch_git_tool(name, args)


if __name__ == "__main__":
    server = GitMCPServer()
    server.run_http()
