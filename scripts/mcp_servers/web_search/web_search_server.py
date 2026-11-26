#!/usr/bin/env python3
"""scripts/mcp_servers/web_search/web_search_server.py

FastAPI server that exposes web search as an MCP (Model Context Protocol) tool.
Listens on port 8004.

Search provider: DuckDuckGo (no API key required).
"""

from __future__ import annotations

import time
from typing import Any, cast
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from shared.logger import Logger
from shared.security.posture_contract import SecurityPosture
from shared.security.result_dto import SecurityCheckStatus
from shared.security.startup_flow import run_startup_validation

from mcp_servers.audit import AuditEmission, hash_query_value, redact_url
from mcp_servers.dispatch import DispatchResult, _to_call_tool_response
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
from mcp_servers.web_search import health, metrics
from mcp_servers.web_search.formatters import dispatch_web_tool
from mcp_servers.web_search.host_normalization import (
    HostNormalizationError,
    normalize_host,
)
from mcp_servers.web_search.web_search_models import (
    WEB_SEARCH_OWN_CONFIG_FILE,
    BrowserAuthorizationError,
    BrowserHttpStatusError,
    BrowserUnsupportedContentError,
    BrowserValidationError,
    WebSearchConfig,
    WebSearchNetworkError,
    WebSearchParseError,
    WebSearchTimeoutError,
    WebSearchUpstreamError,
)
from mcp_servers.web_search.web_search_security_checks import (
    validate_web_search_security,
)
from mcp_servers.web_search.web_search_tools import TOOL_LIST

logger = Logger(__name__, "/opt/llm/logs/web-search-mcp.log")

# ──────────────────────────────────────────────────────────────────────────────
# Typed config object (module-level singleton)
# ──────────────────────────────────────────────────────────────────────────────
_cfg: WebSearchConfig = WebSearchConfig.load()

WEB_SEARCH_SERVER_KEY = "web_search"


def _build_security_posture(cfg: WebSearchConfig) -> SecurityPosture:
    """Run the shared ordering against the already loaded config and return the posture.

    The flow never raises, so a policy violation still produces a posture the Agent can
    read. Only the server-security stage is supplied: the flow's built-in common stage
    covers own-config, auth-token, and published-tool checks, and this module does not
    re-read web_search_mcp_server.toml. The fingerprint view is the one row 51 defines on
    the config, so no second view definition exists here. Unlike Shell's module-level
    guard, this module refuses an empty token through the middleware helper: the posture
    (with its auth-token warning) is built first, then the module-scope
    attach_auth_middleware(..., require_auth_token(...)) call raises RuntimeError and the
    import fails — a failure, not a degraded-warn mode.
    """
    return run_startup_validation(
        WEB_SEARCH_SERVER_KEY,
        own_config_file=WEB_SEARCH_OWN_CONFIG_FILE,
        config_view=cfg.non_secret_view(),
        auth_token=cfg.auth_token,
        declared_tools=tuple(tool["name"] for tool in TOOL_LIST),
        server_checks=lambda: validate_web_search_security(cfg),
    )


_security_posture: SecurityPosture = _build_security_posture(_cfg)


def _web_search_tool_availability(
    cfg: WebSearchConfig, tool_name: str
) -> tuple[bool, str]:
    """Return (enabled, disabled_reason) for a single web-search tool by name."""
    if tool_name == "browser_fetch" and not cfg.browser_allowed_domains:
        return False, "browser_allowed_domains is empty"
    return True, ""


app = FastAPI(
    title="web-search-mcp",
    version="4.0.0",
    description="web-search-mcp: web search (search_web) + read-only page fetch (browser_fetch)",
)

attach_auth_middleware(
    cast(_FastAPIApp, app),
    require_auth_token("web-search-mcp", "MCP_WEB_SEARCH_AUTH_TOKEN", _cfg.auth_token),
)


@app.exception_handler(WebSearchUpstreamError)
async def _handle_web_search_error(
    _req: Any, exc: WebSearchUpstreamError
) -> JSONResponse:
    """Handle upstream web search errors with a 502 Bad Gateway response."""
    return JSONResponse(
        status_code=502,
        content={"error": str(exc)},
    )


@app.exception_handler(BrowserAuthorizationError)
async def _on_browser_auth_error(
    _req: Any, exc: BrowserAuthorizationError
) -> JSONResponse:
    """Handle domain-allowlist/IP-literal authorization errors by returning a 403 response."""
    return JSONResponse({"detail": str(exc)}, status_code=403)


@app.exception_handler(BrowserValidationError)
async def _on_browser_validation_error(
    _req: Any, exc: BrowserValidationError
) -> JSONResponse:
    """Handle invalid-input errors by returning a 422 response."""
    return JSONResponse({"detail": str(exc)}, status_code=422)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint definitions
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health_endpoint() -> JSONResponse:
    """Health check endpoint."""
    deps: dict[str, str] = {}
    details: dict[str, object] = {"service": "web-search-mcp"}
    details["provider"] = health.health_details()
    details["metrics"] = metrics.snapshot()
    details["browser_provider"] = health.browser_health_details()
    details["browser_metrics"] = metrics.browser_snapshot()
    details.update(dedup_health_details())
    if health.is_degraded():
        deps["web_search_provider"] = "degraded: repeated provider failures"
    if health.is_browser_degraded():
        deps["browser_fetch_provider"] = "degraded: repeated fetch failures"
    result: JSONResponse = make_health_response(
        deps, details, security=_security_posture
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch function
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_web_tool(
    name: str, args: dict[str, Any], context: ExecutionContext | None = None
) -> DispatchResult:
    """Route a tool call through the web-search dispatch table."""
    return await dispatch_web_tool(name, args, context=context)


def _classify_dispatch_error(output: str, error_type: str | None) -> str:
    """Classify a non-raised DispatchResult error.

    Prefer the structured ``error_type`` from DispatchResult; fall back to
    string-prefix matching for backward compatibility with callers that do not
    provide an error_type.
    """
    if error_type is not None:
        return error_type
    if output.startswith("Validation error: "):
        return "validation_error"
    if output.startswith("Unknown tool: "):
        return "unknown_tool"
    if output == "Tool name must be a non-empty string":
        return "invalid_tool_name"
    return "dispatch_error"


def _classify_upstream_error(exc: WebSearchUpstreamError) -> str:
    """Classify a raised WebSearchUpstreamError by its concrete subclass.

    web_search_models.py now defines distinct WebSearchUpstreamError
    subclasses (WebSearchTimeoutError, WebSearchNetworkError,
    WebSearchParseError, WebSearchProviderError), so classification uses
    isinstance checks rather than a substring match on str(exc). A browser_fetch
    status error is `http_<category>` and unsupported content is
    `unsupported_content`, the same strings the service records in its metrics.
    """
    if isinstance(exc, BrowserHttpStatusError):
        return f"http_{exc.category}"
    if isinstance(exc, BrowserUnsupportedContentError):
        return "unsupported_content"
    if isinstance(exc, WebSearchTimeoutError):
        return "timeout"
    if isinstance(exc, WebSearchNetworkError):
        return "network_error"
    if isinstance(exc, WebSearchParseError):
        return "parse_error"
    return "provider_error"


def _audit_host(url: str) -> str:
    """Return the normalized host of `url` for the audit detail, or `-`."""
    try:
        raw = urlsplit(url).hostname or ""
        return normalize_host(raw)
    except (ValueError, HostNormalizationError):
        return "-"


def _build_audit_target_and_detail(
    name: str, args: dict[str, Any], latency_ms: float
) -> tuple[str, str]:
    """Build the audit-log `target` and `detail` string for one tool call.

    No raw query or URL is ever recorded. `search_web` reports a normalized query
    hash as the target and the query length in the detail; `browser_fetch` reports a
    redacted URL (scheme, host, redacted path) as the target and the normalized host
    in the detail; any other tool name reports `-` and the latency only.
    """
    if name == "search_web":
        query = str(args.get("query", ""))
        detail = (
            f"max_results={args.get('max_results', '')} "
            f"latency_ms={latency_ms:.0f} "
            f"query_len={len(query)}"
        )
        return f"sha256:{hash_query_value(query)}", detail
    if name == "browser_fetch":
        url = str(args.get("url", ""))
        return redact_url(url), f"latency_ms={latency_ms:.0f} host={_audit_host(url)}"
    return "-", f"latency_ms={latency_ms:.0f}"


# ──────────────────────────────────────────────────────────────────────────────
# Tool listing endpoint (for client-side definition validation)
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/v1/tools")
async def list_tools(
    include_disabled: bool = False, disabled_code: str | None = None
) -> dict[str, Any]:
    """Return tool names and descriptions for agent.json definition validation."""
    annotated = [
        {**t, "enabled": enabled, "disabled_reason": reason}
        for t in TOOL_LIST
        for enabled, reason in [_web_search_tool_availability(_cfg, t["name"])]
    ]
    return build_tools_response(
        cast("list[McpTool]", annotated),
        "web_search",
        include_disabled=include_disabled,
        disabled_code=disabled_code,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Unified tool call endpoint
# ──────────────────────────────────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def _on_request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Audit a malformed /v1/call_tool envelope once, then answer as the framework does.

    The body never reached `call_tool`, so no tool name or argument is available; the
    record carries `-` as target. Authentication runs first, so only authenticated
    callers reach this handler. Other routes keep the default response unaudited.
    """
    if request.url.path == "/v1/call_tool":
        session_id, request_id = extract_request_context(request)[:2]
        AuditEmission(
            logger,
            session_id=session_id,
            request_id=request_id,
            action="-",
            server_key=WEB_SEARCH_SERVER_KEY,
        ).emit(target="-", outcome="rejected", error_type="validation_error")
    return await request_validation_exception_handler(request, exc)


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Execute a web-search-mcp tool (search_web or browser_fetch) by name and
    return the formatted text result.

    `outcome`/`error_type`/`latency_ms` here are for the always-fires audit
    log only — health/metrics recording is owned entirely by
    `service.search_web()`/`service.fetch_browser()` (called via
    `dispatch_web_tool` -> `fdisp_search_web`/`fdisp_browser_fetch`), so this
    function must not call `health.record_*`/`metrics.record_*` itself (that
    would double-count every query). Every outcome, including a disabled tool,
    is audited exactly once through one `AuditEmission` emitted from `finally`.
    """
    session_id, request_id = extract_request_context(request)[:2]
    emission = AuditEmission(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        server_key=WEB_SEARCH_SERVER_KEY,
    )
    t0 = time.perf_counter()
    outcome = "ok"
    error_type = ""
    latency_ms = 0.0
    try:
        enabled, reason = _web_search_tool_availability(_cfg, req.name)
        if not enabled:
            # Rejected before the service is reached, so it never touches
            # health or metrics.
            outcome = "rejected"
            error_type = "tool_disabled"
            latency_ms = (time.perf_counter() - t0) * 1000
            return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)
        exec_ctx = extract_execution_context(request, req.name, req.args)
        r = await _dispatch_web_tool(req.name, req.args, context=exec_ctx)
        outcome = r.outcome
        latency_ms = (time.perf_counter() - t0) * 1000
        if outcome == "error":
            error_type = _classify_dispatch_error(r.output, r.error_type)
        return _to_call_tool_response(r)
    except ExecutionContextError as e:
        # A malformed context (e.g. a non-boolean `dry_run`) is a validation
        # error: it is refused before dispatch, so no durable state is created.
        outcome = "error"
        error_type = "validation_error"
        latency_ms = (time.perf_counter() - t0) * 1000
        return CallToolResponse(result=f"Validation error: {e}", is_error=True)
    except WebSearchUpstreamError as e:
        outcome = "error"
        error_type = _classify_upstream_error(e)
        latency_ms = (time.perf_counter() - t0) * 1000
        raise
    except BrowserAuthorizationError:
        # BrowserAuthorizationError (RuntimeError-based) propagates past
        # dispatch_tool()'s `except ValueError` catch, so it is handled here
        # (unlike BrowserValidationError, a ValueError subclass that
        # dispatch_tool() always converts into an is_error=True
        # DispatchResult first — surfaced via _classify_dispatch_error's
        # "Validation error: " prefix match instead, same as search_web's
        # own ValueError handling).
        outcome = "error"
        error_type = "authorization_error"
        latency_ms = (time.perf_counter() - t0) * 1000
        raise
    except Exception:
        outcome = "error"
        error_type = "unexpected_error"
        latency_ms = (time.perf_counter() - t0) * 1000
        raise
    finally:
        target, detail = _build_audit_target_and_detail(req.name, req.args, latency_ms)
        emission.emit(
            target=target, outcome=outcome, error_type=error_type, detail=detail
        )


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
class WebSearchMCPServer(MCPServer):
    """MCPServer subclass for web-search-mcp."""

    server_name = "web-search-mcp"
    server_version = "4.0.0"
    http_port = 8004
    own_config_file = "web_search_mcp_server.toml"
    app_module = "mcp_servers.web_search.web_search_server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(
        self,
        name: str,
        args: dict[str, Any],
        context: ExecutionContext | None = None,
    ) -> DispatchResult:
        """Route a web search tool call to the appropriate handler."""
        return await _dispatch_web_tool(name, args, context=context)


def _enforce_posture_gate() -> None:
    """Refuse HTTP bind when the posture is not validated (AC-003).

    The gate reads only `validated`: the payload `ready` is derived in
    `make_health_response()` from dependencies plus `validated`, so this module never
    invents its own Ready rule. The log line carries check ids and reason codes only;
    auth tokens and browser_allowed_domains entries are excluded.
    """
    if _security_posture.validated:
        return
    failed = ", ".join(
        f"{check.check_id}:{check.reason_code}"
        for check in _security_posture.checks
        if check.status is SecurityCheckStatus.FAILED
    )
    logger.error(
        "web-search-mcp: security posture FAILED (%s) — refusing to bind", failed
    )
    raise SystemExit(1)


if __name__ == "__main__":
    _enforce_posture_gate()
    server = WebSearchMCPServer()
    server.run_http()
