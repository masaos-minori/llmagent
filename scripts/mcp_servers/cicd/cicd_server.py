#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_server.py

CI/CD MCP server (GitHub Actions backend, port 8012).

Provides HTTP endpoints for triggering and inspecting GitHub Actions workflows.

Security:
  - repo_allowlist: only listed 'owner/repo' slugs are accessible (fail-closed)
  - workflow_allowlist: restrict triggerable workflows (empty = deny all (fail-closed))
  - max_log_size_kb: log output is capped to prevent large data dumps
  - Bearer-token auth via a non-empty auth_token in cicd_mcp_server.toml (required)

Provided endpoints:
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
  GET  /health        Health check
"""

from __future__ import annotations

import os
import time
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.logger import Logger
from shared.security.posture_contract import SecurityPosture
from shared.security.result_dto import SecurityCheckStatus
from shared.security.startup_flow import run_startup_validation

from mcp_servers.audit import _audit_log
from mcp_servers.cicd.cicd_models import (
    CicdConfig,
)
from mcp_servers.cicd.cicd_service import CiCdService, build_service
from mcp_servers.cicd.cicd_service_guards import validate_cicd_security
from mcp_servers.cicd.cicd_tools import TOOL_LIST
from mcp_servers.cicd.exception_handlers import setup_exception_handlers
from mcp_servers.dispatch import (
    DispatchResult,
    ToolArgs,
    _to_call_tool_response,
    dispatch_tool,
)
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

logger = Logger(__name__, "/opt/llm/logs/cicd-mcp.log")

_cfg = CicdConfig.load()
_service: CiCdService = build_service(_cfg)

CICD_SERVER_KEY = "cicd"
CICD_OWN_CONFIG_FILE = "cicd_mcp_server.toml"


def _cicd_security_view(cfg: CicdConfig) -> dict[str, object]:
    """Build the non-secret view the posture fingerprint is computed from.

    Only scalars and counts are carried: `auth_token` and `github_token` are Secrets and
    every `repo_allowlist` / `workflow_allowlist` value is an allowlist entry, so none of
    them is hashed by value (REQ-002, REQ-009).
    """
    return {
        "own_config_file": CICD_OWN_CONFIG_FILE,
        "repo_allowlist_count": len(cfg.repo_allowlist),
        "workflow_allowlist_count": len(cfg.workflow_allowlist),
        "max_log_size_kb": cfg.max_log_size_kb,
    }


def _build_security_posture() -> SecurityPosture:
    """Run the shared ordering against the already loaded config and return the posture.

    The flow never raises, so a policy violation still produces a posture the Agent can
    read. Only the server-security stage is supplied: the flow's built-in common stage
    covers own-config, auth-token, and published-tool checks, and this module does not
    re-read cicd_mcp_server.toml or rebuild the service. The backend is the one the guard
    mixin already owns.
    """
    return run_startup_validation(
        CICD_SERVER_KEY,
        own_config_file=CICD_OWN_CONFIG_FILE,
        config_view=_cicd_security_view(_cfg),
        auth_token=_cfg.auth_token,
        declared_tools=tuple(tool["name"] for tool in TOOL_LIST),
        server_checks=lambda: validate_cicd_security(
            _service._backend, _cfg.repo_allowlist, _cfg.workflow_allowlist
        ),
    )


_security_posture: SecurityPosture = _build_security_posture()


def _cicd_tool_availability(cfg: CicdConfig, tool_name: str) -> tuple[bool, str]:
    """Return (enabled, disabled_reason) for a single cicd tool by name."""
    if not cfg.repo_allowlist:
        return False, "repo_allowlist is empty"
    if tool_name == "trigger_workflow" and not cfg.workflow_allowlist:
        return False, "workflow_allowlist is empty"
    return True, ""


app = FastAPI(
    title="cicd-mcp",
    version="1.0.0",
    description="CI/CD (GitHub Actions) MCP server",
)

attach_auth_middleware(
    cast(_FastAPIApp, app),
    require_auth_token("cicd-mcp", "MCP_CICD_AUTH_TOKEN", _cfg.auth_token),
)
setup_exception_handlers(app)


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_cicd_tool(
    name: str, args: ToolArgs, idempotency_key: str | None = None
) -> DispatchResult:
    """Route CI/CD tool calls through the service's dispatch table."""
    return await dispatch_tool(
        _service.get_dispatch_table(), name, args, idempotency_key=idempotency_key
    )


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/v1/tools")
async def list_tools(
    include_disabled: bool = False, disabled_code: str | None = None
) -> dict[str, Any]:
    """List available CI/CD tools with schema_version and server_key="cicd"."""
    annotated = [
        {**t, "enabled": enabled, "disabled_reason": reason}
        for t in TOOL_LIST
        for enabled, reason in [_cicd_tool_availability(_cfg, t["name"])]
    ]
    return build_tools_response(
        cast("list[McpTool]", annotated),
        "cicd",
        include_disabled=include_disabled,
        disabled_code=disabled_code,
    )


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Dispatch an MCP tool call through the CI/CD service with audit logging."""
    enabled, reason = _cicd_tool_availability(_cfg, req.name)
    if not enabled:
        return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)
    t0 = time.perf_counter()
    session_id, request_id, idempotency_key = extract_request_context(request)
    r = await _dispatch_cicd_tool(req.name, req.args, idempotency_key=idempotency_key)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=cast(str, req.args.get("repo", "")),
        outcome=r.outcome,
        server_key="cicd",
    )
    return _to_call_tool_response(r)


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint. Returns degraded when GITHUB_TOKEN is not set."""
    deps: dict[str, str] = {}
    try:
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            deps["github_token"] = "not_set"
    except (RuntimeError, OSError):
        deps["config"] = "check failed"
    details: dict[str, object] = {"service": "cicd-mcp"}
    result: JSONResponse = make_health_response(
        deps, details, security=_security_posture
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class CiCdMCPServer(MCPServer):
    """MCPServer subclass for cicd-mcp (GitHub Actions backend)."""

    server_name = "cicd-mcp"
    server_version = "1.0.0"
    http_port = 8012
    own_config_file = "cicd_mcp_server.toml"
    app_module = "mcp_servers.cicd.cicd_server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        """Dispatch a tool by name with the given arguments via the CI/CD service."""
        return await _dispatch_cicd_tool(name, args)


def _enforce_posture_gate() -> None:
    """Refuse HTTP bind when the posture is not validated (REQ-003, AC-003).

    The gate reads only `validated`: the payload `ready` is derived in
    `make_health_response()` from dependencies plus `validated`, so this module never
    invents its own Ready rule. The log line carries check ids and reason codes only;
    repository and workflow names are allowlist entries (REQ-002).
    """
    if _security_posture.validated:
        return
    failed = ", ".join(
        f"{check.check_id}:{check.reason_code}"
        for check in _security_posture.checks
        if check.status is SecurityCheckStatus.FAILED
    )
    logger.error("cicd-mcp: security posture FAILED (%s) — refusing to bind", failed)
    raise SystemExit(1)


if __name__ == "__main__":
    _enforce_posture_gate()
    server = CiCdMCPServer()
    server.run_http()
