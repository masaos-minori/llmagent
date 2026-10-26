#!/usr/bin/env python3
"""scripts/mcp_servers/git/git_server.py

Local git operations MCP server (port 8014).

Provides an HTTP API via FastAPI for safe git operations against allowlisted repositories.

Security:
  - Operations are restricted to repositories in allowed_repo_paths (fail-closed)
  - read_only=true (default) prevents all write operations (add/commit/checkout/pull/push)
  - All write tools support dry_run=True for preview without side effects
  - Bearer-token auth via a non-empty auth_token in git_mcp_server.toml (required)

Provided endpoints:
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
  GET  /health        Health check
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import threading
import time
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.logger import Logger
from shared.security.posture_contract import SecurityPosture
from shared.security.result_dto import SecurityCheckStatus
from shared.security.startup_flow import run_startup_validation
from shared.tool_constants import GIT_WRITE_TOOLS

from mcp_servers.audit import _audit_log
from mcp_servers.dispatch import DispatchResult, dispatch_tool
from mcp_servers.git.errors import GitPolicyError, GitServiceError
from mcp_servers.git.git_models import (
    GitConfig,
)
from mcp_servers.git.git_security import (
    _resolve_repo_path,
    is_within_allowed_paths,
    validate_git_security,
)
from mcp_servers.git.git_service import build_service
from mcp_servers.git.git_tools import TOOL_LIST
from mcp_servers.git.repository_state import RepositoryState
from mcp_servers.health_response import make_health_response
from mcp_servers.models import CallToolRequest, CallToolResponse, McpTool
from mcp_servers.server import (
    MCPServer,
    _FastAPIApp,
    attach_auth_middleware,
    build_tools_response,
    extract_request_context,
    require_auth_token,
)

logger = Logger(__name__, "/opt/llm/logs/git-mcp.log")

_cfg = GitConfig.load()
_service = build_service(_cfg)

GIT_SERVER_KEY = "git"
GIT_OWN_CONFIG_FILE = "git_mcp_server.toml"


def _git_security_view(cfg: GitConfig) -> dict[str, object]:
    """Build the non-secret view the posture fingerprint is computed from.

    Only scalars and counts are carried: `auth_token`, `audit_log_path`, and every
    `allowed_repo_paths` / `allowed_remote_urls` value are never hashed by value
    (REQ-002, REQ-009).
    """
    return {
        "own_config_file": GIT_OWN_CONFIG_FILE,
        "allowed_repo_paths_count": len(cfg.allowed_repo_paths),
        "read_only": cfg.read_only,
        "protected_branches_count": len(cfg.protected_branches),
        "allowed_remote_urls_count": len(cfg.allowed_remote_urls),
        "allow_detached_head": cfg.allow_detached_head,
        "max_log_entries": cfg.max_log_entries,
    }


def _build_security_posture() -> SecurityPosture:
    """Run the shared ordering against the already loaded config and return the posture.

    The flow never raises, so a policy violation still produces a posture the Agent can
    read. Only the server-security stage is supplied: the flow's built-in common stage
    covers own-config, auth-token, and published-tool checks, and this module does not
    re-read git_mcp_server.toml.
    """
    return run_startup_validation(
        GIT_SERVER_KEY,
        own_config_file=GIT_OWN_CONFIG_FILE,
        config_view=_git_security_view(_cfg),
        auth_token=_cfg.auth_token,
        declared_tools=tuple(tool["name"] for tool in TOOL_LIST),
        server_checks=lambda: validate_git_security(
            list(_cfg.allowed_repo_paths), _cfg.read_only
        ),
    )


_security_posture: SecurityPosture = _build_security_posture()


def _validate_pre_snapshot(path: str) -> tuple[bool, str]:
    """Validate that *path* is accessible and contains a Git repository before calling snapshot.

    Returns (ok, error) where ok=True means the path is safe to pass to snapshot().

    This function performs synchronous file-system operations; callers should invoke it
    via ``_validate_pre_snapshot_async`` to avoid blocking the event loop.
    """
    try:
        import os as _os

        if not _os.path.exists(path):
            return False, "[DENIED] repository path does not exist"
        if not _os.access(path, _os.R_OK):
            return False, "[DENIED] repository path is not readable"
        # Check for .git directory or bare repo indicator
        has_git = _os.path.isdir(_os.path.join(path, ".git"))
        if not has_git:
            # Bare repos have HEAD directly inside the root
            has_bare = _os.path.isfile(_os.path.join(path, "HEAD"))
            if not has_bare:
                return False, "[DENIED] path is not a Git repository"
        return True, ""
    except PermissionError:
        return False, "[DENIED] permission denied accessing repository"


async def _validate_pre_snapshot_async(path: str) -> tuple[bool, str]:
    """Async wrapper around ``_validate_pre_snapshot`` to avoid blocking the event loop."""
    return await asyncio.to_thread(_validate_pre_snapshot, path)


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


def _sanitize_for_audit(value: str) -> str:
    """Redact sensitive portions of a path for audit logging.

    Absolute paths (starting with /) always produce an empty first component after
    splitting by "/", so paths with <= 3 components are fully redacted to prevent
    sensitive system paths like /etc or /root from being logged in full.
    """
    if not value:
        return ""
    parts = value.split("/")
    if len(parts) <= 3:
        return "***"
    return "/".join(["***"] + parts[-2:])


_audit_failure_count: int = 0
_audit_failure_count_lock = threading.Lock()
# Thread-safe synchronization for _audit_failure_count: the lock protects the
# read-modify-write cycle so increments are not lost under concurrent load.
# The lock scope is intentionally narrow — only around the increment operation.
# If uvicorn runs in single-worker mode, asyncio.Lock could be used instead,
# but threading.Lock works in both modes and is the safer default.


def _audit_log_safe(logger: logging.Logger | Logger, **kwargs: Any) -> None:
    """Wrap _audit_log so its own failure cannot mask the original response."""
    global _audit_failure_count
    try:
        _audit_log(logger, **kwargs)
    except Exception:  # noqa: BLE001 — audit failure must never propagate
        with _audit_failure_count_lock:
            _audit_failure_count += 1
        logger.error("audit_log failed: %s", kwargs.get("action", "unknown"))


app = FastAPI(
    title="git-mcp",
    version="1.0.0",
    description="Local git operations MCP server",
)

attach_auth_middleware(
    cast(_FastAPIApp, app),
    require_auth_token("git-mcp", "MCP_GIT_AUTH_TOKEN", _cfg.auth_token),
)


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
    session_id, request_id, idempotency_key = extract_request_context(request)
    repo_path = cast(str, req.args.get("repo_path", ""))
    ok, err, resolved = _resolve_repo_path(repo_path)
    if not ok:
        logger.info(
            fmt_kvlog("call_tool", tool=req.name, ms=f"{time.perf_counter() - t0:.0f}")
        )
        _audit_log_safe(
            logger,
            session_id=session_id,
            request_id=request_id,
            action=req.name,
            target="",
            outcome="rejected",
            server_key="git",
            pre_condition=None,
            post_condition=None,
            requested_target=_sanitize_for_audit(repo_path),
        )
        return CallToolResponse(result=f"Validation error: {err}", is_error=True)
    # Enforce allowed_repo_paths containment using component-aware checking.
    within, deny_err = is_within_allowed_paths(resolved, _cfg.allowed_repo_paths)
    if not within:
        logger.info(
            fmt_kvlog("call_tool", tool=req.name, ms=f"{time.perf_counter() - t0:.0f}")
        )
        _audit_log_safe(
            logger,
            session_id=session_id,
            request_id=request_id,
            action=req.name,
            target="",
            outcome="rejected",
            server_key="git",
            pre_condition=None,
            post_condition=None,
        )
        return CallToolResponse(result=deny_err, is_error=True)
    # Reject missing/inaccessible/non-repository paths before snapshot (REQ-003).
    ok, err = await _validate_pre_snapshot_async(resolved)
    if not ok:
        logger.info(
            fmt_kvlog("call_tool", tool=req.name, ms=f"{time.perf_counter() - t0:.0f}")
        )
        _audit_log_safe(
            logger,
            session_id=session_id,
            request_id=request_id,
            action=req.name,
            target="",
            outcome="rejected",
            server_key="git",
            pre_condition=None,
            post_condition=None,
            requested_target=_sanitize_for_audit(repo_path),
        )
        return CallToolResponse(result=err, is_error=True)
    active_ref = cast(str, req.args.get("branch", "")) or ""
    pre_state = RepositoryState.snapshot(
        resolved, protected_branches=_cfg.protected_branches, active_ref=active_ref
    )
    result: DispatchResult | None = None
    outcome: str = ""
    policy_exc: GitPolicyError | None = None
    try:
        result = await dispatch_tool(
            _service.get_dispatch_table(),
            req.name,
            req.args,
            idempotency_key=idempotency_key,
        )
    except GitPolicyError as exc:
        policy_exc = exc
        outcome = "rejected"
    except GitServiceError:
        outcome = "error"
        raise
    else:
        outcome = "rejected" if result.is_error else "ok"
    post_state = RepositoryState.snapshot(
        resolved, protected_branches=_cfg.protected_branches, active_ref=active_ref
    )
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
    _audit_log_safe(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=resolved,
        outcome=outcome,
        server_key="git",
        pre_condition=_serialize_state(pre_state),
        post_condition=_serialize_state(post_state),
        requested_target=_sanitize_for_audit(repo_path),
        canonical_target=resolved,
    )
    if policy_exc is not None:
        return CallToolResponse(result=str(policy_exc), is_error=True)
    assert result is not None
    return CallToolResponse(
        result=result.output,
        is_error=result.is_error,
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
    details: dict[str, object] = {
        "service": "git-mcp",
        "audit_failure_count": _audit_failure_count,
    }
    result: JSONResponse = make_health_response(
        deps, details, security=_security_posture
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class GitMCPServer(MCPServer):
    """MCPServer subclass for git-mcp.

    Explicitly declares ``http_host = "127.0.0.1"`` to match other MCP server
    subclasses and prevent regressions if the base-class default changes.
    Provides a ``dispatch()`` method override to maintain consistency with other
    subclasses and prevent ``NotImplementedError`` when called programmatically.
    """

    server_name = "git-mcp"
    server_version = "1.0.0"
    http_host = "127.0.0.1"
    http_port = 8014
    own_config_file = "git_mcp_server.toml"
    app_module = "mcp_servers.git.git_server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        """Delegate a tool call to the git service's dispatch table."""
        return await dispatch_tool(_service.get_dispatch_table(), name, args)


def _enforce_posture_gate() -> None:
    """Refuse HTTP bind when the posture is not validated (REQ-003, AC-003).

    The gate reads only `validated`: the payload `ready` is derived in
    `make_health_response()` from dependencies plus `validated`, so this module never
    invents its own Ready rule. The log line carries check ids and reason codes only;
    configured repository roots are sensitive paths (REQ-002).
    """
    if _security_posture.validated:
        return
    failed = ", ".join(
        f"{check.check_id}:{check.reason_code}"
        for check in _security_posture.checks
        if check.status is SecurityCheckStatus.FAILED
    )
    logger.error("git-mcp: security posture FAILED (%s) — refusing to bind", failed)
    raise SystemExit(1)


if __name__ == "__main__":
    _enforce_posture_gate()
    server = GitMCPServer()
    server.run_http()
