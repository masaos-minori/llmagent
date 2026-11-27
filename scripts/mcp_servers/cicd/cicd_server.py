#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_server.py

CI/CD MCP server (GitHub Actions backend, port 8012).

Provides HTTP endpoints for triggering and inspecting GitHub Actions workflows.

Security:
  - repo_allowlist: only listed 'owner/repo' slugs are accessible (fail-closed)
  - workflow_allowlist: restrict triggerable workflows (empty = deny all (fail-closed))
  - max_log_size_kb: log output is capped to prevent large data dumps
  - Bearer-token auth via a non-empty auth_token in cicd_mcp_server.toml (required)

Lifecycle:
  - The FastAPI lifespan owns the shared httpx.AsyncClient, builds the service from it, runs
    the side-effect-free read-permission probe, and closes the client on shutdown.

Provided endpoints:
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
  GET  /health        Health check
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, cast

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.logger import Logger
from shared.security.posture_contract import SecurityPosture
from shared.security.result_dto import (
    REASON_AUTH_TOKEN_MISSING,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckStatus,
)
from shared.security.startup_flow import run_startup_validation

from mcp_servers.audit import _audit_log
from mcp_servers.cicd.cicd_credential import resolve_effective_credential
from mcp_servers.cicd.cicd_models import (
    CicdConfig,
    canonical_repo_key,
)
from mcp_servers.cicd.cicd_service import CiCdService, build_service
from mcp_servers.cicd.cicd_service_defs import _GITHUB_API_BASE, build_auth_headers
from mcp_servers.cicd.cicd_service_guards import (
    ProbeOutcome,
    probe_check,
    validate_cicd_security,
)
from mcp_servers.cicd.cicd_tools import TOOL_LIST
from mcp_servers.cicd.exception_handlers import setup_exception_handlers
from mcp_servers.dispatch import (
    DispatchResult,
    ToolArgs,
    _to_call_tool_response,
    dispatch_tool,
)
from mcp_servers.execution_context import ExecutionContext, ExecutionContextError
from mcp_servers.health_response import dedup_health_details, make_health_response
from mcp_servers.models import CallToolRequest, CallToolResponse, McpTool
from mcp_servers.server import (
    MCPServer,
    _FastAPIApp,
    attach_auth_middleware,
    build_tools_response,
    extract_execution_context,
    extract_request_context,
    require_auth_token,
)

logger = Logger(__name__, "/opt/llm/logs/cicd-mcp.log")

_cfg = CicdConfig.load()
# The lifespan is the single owner of the shared client and of the service built from it,
# so nothing is constructed at import time (REQ-008). Tests inject their own client through
# the same `build_service()` parameter.
_http_client: httpx.AsyncClient | None = None
_service: CiCdService | None = None
# The outcome the lifespan probe stores for health (REQ-003).
_probe_outcome: ProbeOutcome | None = None

CICD_SERVER_KEY = "cicd"
CICD_OWN_CONFIG_FILE = "cicd_mcp_server.toml"


def _cicd_security_view(cfg: CicdConfig) -> dict[str, object]:
    """Build the non-secret view the posture fingerprint is computed from.

    Only scalars and counts are carried: `auth_token` and `github_token` are Secrets and
    every `repo_allowlist` / `workflow_allowlist` value is an allowlist entry, so none of
    them is hashed by value.
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
    re-read cicd_mcp_server.toml or rebuild the service. The gate runs before bind, so the
    service the lifespan builds does not exist yet here; the backend availability check is
    reported not_applicable for that stage and the reachability dimension is reported by the
    lifespan probe.
    """
    return run_startup_validation(
        CICD_SERVER_KEY,
        own_config_file=CICD_OWN_CONFIG_FILE,
        config_view=_cicd_security_view(_cfg),
        auth_token=_cfg.auth_token,
        declared_tools=tuple(tool["name"] for tool in TOOL_LIST),
        server_checks=lambda: validate_cicd_security(
            _service._backend if _service is not None else None,
            _cfg.repo_allowlist,
            _cfg.workflow_allowlist,
            resolve_effective_credential(_cfg),
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


def _probe_rate_limit_reason(response: httpx.Response) -> str:
    """Map the probe response's rate-limit header to a shared reason code."""
    remaining = response.headers.get("x-ratelimit-remaining")
    if remaining is None:
        return REASON_NOT_APPLICABLE
    try:
        return REASON_OK if int(remaining) > 0 else REASON_DEPENDENCY_UNREACHABLE
    except ValueError:
        return REASON_NOT_APPLICABLE


async def run_read_permission_probe(
    cfg: CicdConfig, http: httpx.AsyncClient, effective_credential: str
) -> ProbeOutcome:
    """Run the side-effect-free read-permission probe against the first allowlist entry.

    Only a read is made: dispatch permission stays `not_applicable` because no
    side-effect-free endpoint exposes a write permission (REQ-003). The credential is used in
    the request header only and never recorded or echoed. An empty allowlist has no target,
    so no probe runs.
    """
    if not cfg.repo_allowlist:
        return ProbeOutcome(
            REASON_NOT_APPLICABLE, REASON_NOT_APPLICABLE, REASON_NOT_APPLICABLE
        )
    if not effective_credential:
        return ProbeOutcome(
            REASON_AUTH_TOKEN_MISSING, REASON_NOT_APPLICABLE, REASON_NOT_APPLICABLE
        )
    target = canonical_repo_key(cfg.repo_allowlist[0])
    try:
        response = await http.get(
            f"{_GITHUB_API_BASE}/repos/{target}/actions/workflows",
            headers=build_auth_headers(effective_credential),
        )
    except httpx.HTTPError:
        return ProbeOutcome(
            REASON_DEPENDENCY_UNREACHABLE,
            REASON_DEPENDENCY_UNREACHABLE,
            REASON_NOT_APPLICABLE,
        )
    rate_limit = _probe_rate_limit_reason(response)
    if response.status_code == 200:
        return ProbeOutcome(REASON_OK, REASON_OK, rate_limit)
    read = (
        REASON_AUTH_TOKEN_MISSING
        if response.status_code in (401, 403)
        and rate_limit != REASON_DEPENDENCY_UNREACHABLE
        else REASON_DEPENDENCY_UNREACHABLE
    )
    return ProbeOutcome(read, REASON_OK, rate_limit)


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Own the shared client, build the service from it, and run the probe (REQ-008, REQ-003)."""
    global _http_client, _service, _probe_outcome
    _http_client = httpx.AsyncClient(timeout=30.0)
    _service = build_service(_cfg, _http_client)
    _probe_outcome = await run_read_permission_probe(
        _cfg, _http_client, resolve_effective_credential(_cfg)
    )
    try:
        yield
    finally:
        await _http_client.aclose()


app = FastAPI(
    title="cicd-mcp",
    version="1.0.0",
    description="CI/CD (GitHub Actions) MCP server",
    lifespan=_lifespan,
)

attach_auth_middleware(
    cast(_FastAPIApp, app),
    require_auth_token("cicd-mcp", "MCP_CICD_AUTH_TOKEN", _cfg.auth_token),
)
setup_exception_handlers(app)


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch
# ──────────────────────────────────────────────────────────────────────────────


def _require_service() -> CiCdService:
    """Return the service the lifespan built; construction is not an import-time step (REQ-008)."""
    if _service is None:
        raise RuntimeError("cicd-mcp: the service is not built; the lifespan owns it")
    return _service


async def _dispatch_cicd_tool(
    name: str, args: ToolArgs, context: ExecutionContext | None = None
) -> DispatchResult:
    """Route CI/CD tool calls through the service's dispatch table."""
    return await dispatch_tool(
        _require_service().get_dispatch_table(), name, args, context=context
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
    try:
        exec_ctx = extract_execution_context(request, req.name, req.args)
    except ExecutionContextError as exc:
        return CallToolResponse(result=f"Validation error: {exc}", is_error=True)
    session_id, request_id = extract_request_context(request)[:2]
    r = await _dispatch_cicd_tool(req.name, req.args, context=exec_ctx)
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
    """Health check: the effective credential and the lifespan probe outcome (REQ-001, REQ-003).

    Only failures become dependency entries, so an OK or not_applicable probe leaves the dict
    empty and `make_health_response()`'s ready rule is unchanged. The probe status comes from
    `probe_check()`, the same policy the posture uses, so health and the posture cannot
    disagree. The token itself is never exposed.
    """
    deps: dict[str, str] = {}
    try:
        effective = resolve_effective_credential(_cfg)
        if not effective:
            deps["github_token"] = "not_set"
        elif _probe_outcome is not None:
            probe = probe_check(_probe_outcome)
            if probe.status is SecurityCheckStatus.FAILED:
                deps["credential_probe"] = probe.reason_code
    except (RuntimeError, OSError):
        deps["config"] = "check failed"
    details: dict[str, object] = {"service": "cicd-mcp"}
    details.update(dedup_health_details())
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

    async def dispatch(
        self,
        name: str,
        args: dict[str, Any],
        context: ExecutionContext | None = None,
    ) -> DispatchResult:
        """Dispatch a tool by name with the given arguments via the CI/CD service."""
        return await _dispatch_cicd_tool(name, args, context=context)


def _enforce_posture_gate() -> None:
    """Refuse HTTP bind when the posture is not validated (AC-003).

    The gate reads only `validated`: the payload `ready` is derived in
    `make_health_response()` from dependencies plus `validated`, so this module never
    invents its own Ready rule. The log line carries check ids and reason codes only;
    repository and workflow names are allowlist entries.
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
