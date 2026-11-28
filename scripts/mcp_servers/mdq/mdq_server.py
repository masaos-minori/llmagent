#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/mdq_server.py

Markdown Context Compression Engine MCP server (port 8013).

Exposes 7 tools for indexing, searching, and inspecting Markdown documents.

Provided endpoints:
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
  GET  /health        Health check
"""

from __future__ import annotations

import contextvars
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.logger import Logger
from shared.security.posture_contract import SecurityPosture
from shared.security.result_dto import SecurityCheckStatus

from mcp_servers.audit import AuditEmission, hash_query_value
from mcp_servers.dispatch import DispatchResult, _to_call_tool_response, dispatch_tool
from mcp_servers.execution_context import ExecutionContext, ExecutionContextError
from mcp_servers.health_response import dedup_health_details
from mcp_servers.mdq.audit_target import extract_audit_target
from mcp_servers.mdq.health_check import _collect_dependencies, check_health
from mcp_servers.mdq.mdq_error_codes import TOOL_DISABLED, code_for_exception
from mcp_servers.mdq.mdq_models import (
    GetChunkRequest,
    GrepDocsRequest,
    IndexPathsRequest,
    MdqAuthorizationError,
    MdqConsistencyError,
    MdqDatabaseError,
    MdqIndexNotReadyError,
    MdqNotFoundError,
    MdqServiceError,
    MdqValidationError,
    OutlineRequest,
    RefreshIndexRequest,
    SearchDocsRequest,
    StatsRequest,
)
from mcp_servers.mdq.mdq_security_validation import build_mdq_posture
from mcp_servers.mdq.mdq_service import MdqService
from mcp_servers.mdq.mdq_tools import TOOL_LIST
from mcp_servers.mdq.startup_config import StartupConfig, load_startup_config
from mcp_servers.models import CallToolRequest, CallToolResponse, McpTool
from mcp_servers.server import (
    MCPServer,
    ToolArgs,
    _FastAPIApp,
    attach_auth_middleware,
    build_tools_response,
    extract_execution_context,
    extract_request_context,
    require_auth_token,
)

logger = Logger(__name__, "/opt/llm/logs/mdq-mcp.log")

app = FastAPI(
    title="mdq-mcp",
    version="1.0.0",
    description="Markdown Context Compression Engine MCP server (Markdown-only, structure-aware retrieval)",
)


_cfg: StartupConfig = load_startup_config()
_service: MdqService = MdqService(_cfg)

# Build the MDQ security posture once at import from the shared startup result (REQ-007).
# `_collect_dependencies()` supplies the probe facts the posture judges, so the gate and the
# /health body read the same probe result and cannot disagree. The gate fails closed at startup
# when the posture is not validated.
(
    _deps,
    _details,
    _startup,
    _db_file_present,
    _schema_error,
    _schema_checked,
    _index_stats,
) = _collect_dependencies(_cfg)
_security_posture: SecurityPosture = build_mdq_posture(
    _cfg, _db_file_present, _schema_error, _schema_checked, _index_stats
)


def _mdq_tool_availability(tool_name: str) -> tuple[bool, str]:
    """Return (enabled, disabled_reason) for one mdq tool by name (REQ-001).

    Every MDQ tool serves content under the authorized roots, so no authorized root means
    no tool runs; `grep_docs` is additionally disabled when grep is configured off. The
    rule is evaluated per tool name so one tool can be disabled while another runs.
    """
    if not _service.allowed_dirs:
        return False, "allowed_dirs is empty"
    if tool_name == "grep_docs" and not _service.enable_grep:
        return False, "enable_grep is false"
    return True, ""


def _mdq_error_handler(exc: Exception, status_code: int) -> JSONResponse:
    """Render the transport response for a domain exception (REQ-005).

    The handler does not audit: the call's single record is written by `call_tool()`'s
    emission boundary. Only the code is logged, so exception text, SQLite detail, and paths
    reach neither a persistent log nor the client (AC-4, AC-5).
    """
    code = code_for_exception(exc)
    logger.info(fmt_kvlog("mdq_error", code=code, status=str(status_code)))
    return JSONResponse({"detail": code}, status_code=status_code)


@app.exception_handler(MdqValidationError)
async def _on_mdq_validation_error(
    request: Request, exc: MdqValidationError
) -> JSONResponse:
    """Handle validation errors with HTTP 400 response."""
    return _mdq_error_handler(exc, 400)


@app.exception_handler(MdqAuthorizationError)
async def _on_mdq_authorization_error(
    request: Request, exc: MdqAuthorizationError
) -> JSONResponse:
    """Handle authorization errors with HTTP 403 response."""
    return _mdq_error_handler(exc, 403)


@app.exception_handler(MdqNotFoundError)
async def _on_mdq_not_found_error(
    request: Request, exc: MdqNotFoundError
) -> JSONResponse:
    """Handle not found errors with HTTP 404 response."""
    return _mdq_error_handler(exc, 404)


@app.exception_handler(MdqIndexNotReadyError)
async def _on_mdq_index_not_ready_error(
    request: Request, exc: MdqIndexNotReadyError
) -> JSONResponse:
    """Handle index-not-ready errors with HTTP 503 response."""
    return _mdq_error_handler(exc, 503)


@app.exception_handler(MdqDatabaseError)
async def _on_mdq_database_error(
    request: Request, exc: MdqDatabaseError
) -> JSONResponse:
    """Handle database errors with HTTP 503 response."""
    return _mdq_error_handler(exc, 503)


@app.exception_handler(MdqConsistencyError)
async def _on_mdq_consistency_error(
    request: Request, exc: MdqConsistencyError
) -> JSONResponse:
    """Handle consistency errors with HTTP 500 response."""
    return _mdq_error_handler(exc, 500)


@app.exception_handler(MdqServiceError)
async def _on_mdq_service_error(request: Request, exc: MdqServiceError) -> JSONResponse:
    """Handle generic service errors with HTTP 500 response."""
    return _mdq_error_handler(exc, 500)


# ──────────────────────────────────────────────────────────────────────────────
# Dispatch handlers
# ──────────────────────────────────────────────────────────────────────────────


_mdq_metadata_var: contextvars.ContextVar[dict[str, Any] | None] = (
    contextvars.ContextVar("mdq_metadata", default=None)
)
# Lifecycle: set() at the start of each request, get() after dispatch, reset() in
# finally. The default=None avoids a shared mutable default; callers use ``or {}``
# when reading to ensure a dict is always returned even when no value has been set.


@dataclass(frozen=True)
class MdqDispatchResult:
    """Wraps the shared DispatchResult with mdq-local per-call metadata."""

    output: str
    is_error: bool
    metadata: dict[str, Any]
    execution_mode: str = ""
    side_effect_applied: bool = False
    dedup_state: str = ""
    error_type: str = ""
    refused: bool = False

    @property
    def outcome(self) -> str:
        """Return 'rejected' for a refusal before the handler, 'error' for a failure, else 'ok'."""
        if self.refused:
            return "rejected"
        return "error" if self.is_error else "ok"


async def _handle_search_docs(args: ToolArgs) -> str:
    """Dispatch search_docs tool call to the mdq service."""
    req = SearchDocsRequest(
        query=args["query"],
        limit=args.get("limit", 10),
        mode=args.get("mode", "bm25"),
        path_prefix=args.get("path_prefix"),
        tag_filter=args.get("tag_filter"),
        heading_prefix=args.get("heading_prefix"),
        max_results_limit=args.get("max_results_limit"),
        max_total_result_chars=args.get("max_total_result_chars"),
    )
    text, metadata = await _service.search_docs(req)
    _mdq_metadata_var.set(dict(metadata))
    return text


async def _handle_get_chunk(args: ToolArgs) -> str:
    """Dispatch get_chunk tool call to the mdq service."""
    req = GetChunkRequest(
        chunk_id=args["chunk_id"],
        with_neighbors=args.get("with_neighbors", False),
        max_chars_per_chunk=args.get("max_chars_per_chunk"),
    )
    result: str = await _service.get_chunk(req)
    return result


async def _handle_outline(args: ToolArgs) -> str:
    """Dispatch outline tool call to the mdq service."""
    req = OutlineRequest(
        path=args["path"],
        max_depth=args.get("max_depth", 6),
        max_outline_items=args.get("max_outline_items", 500),
    )
    result: str = await _service.outline(req)
    return result


async def _handle_index_paths(args: ToolArgs) -> str:
    """Dispatch index_paths tool call to the mdq service."""
    req = IndexPathsRequest(paths=args["paths"])
    text, metadata = await _service.index_paths(req)
    _mdq_metadata_var.set(dict(metadata))
    return text


async def _handle_refresh_index(args: ToolArgs) -> str:
    """Dispatch refresh_index tool call to the mdq service."""
    req = RefreshIndexRequest(
        paths=args["paths"],
        force=args.get("force", False),
    )
    text, metadata = await _service.refresh_index(req)
    _mdq_metadata_var.set(dict(metadata))
    return text


async def _handle_stats(args: ToolArgs) -> str:
    """Dispatch stats tool call to the mdq service."""
    result: str = await _service.stats(StatsRequest())
    return result


async def _handle_grep_docs(args: ToolArgs) -> str:
    """Dispatch grep_docs tool call to the mdq service."""
    req = GrepDocsRequest(
        pattern=args["pattern"],
        paths=args.get("paths"),
        max_grep_matches=args.get("max_grep_matches", 200),
        max_chars_per_match=args.get("max_chars_per_match", 500),
        context_before=args.get("context_before", 2),
        context_after=args.get("context_after", 2),
    )
    text, metadata = await _service.grep_docs(req)
    _mdq_metadata_var.set(dict(metadata))
    return text


_DISPATCH_TABLE = {
    "search_docs": _handle_search_docs,
    "get_chunk": _handle_get_chunk,
    "outline": _handle_outline,
    "index_paths": _handle_index_paths,
    "refresh_index": _handle_refresh_index,
    "stats": _handle_stats,
    "grep_docs": _handle_grep_docs,
}


async def _dispatch_mdq_tool(
    name: str, args: ToolArgs, context: ExecutionContext | None = None
) -> MdqDispatchResult:
    """Route a tool call through the shared dispatch mechanism, capturing mdq-local metadata.

    Availability is re-evaluated here at call time (REQ-001), so the HTTP endpoint and this
    programmatic entry share one decision and a disabled tool is refused before any handler
    runs. A refusal carries no metadata and no execution mode, since nothing ran.

    The ContextVar lifecycle: set() at the start of each request, get() after
    dispatch, reset() in finally. A guard around set() prevents corruption if
    set() raises before the try block.
    """
    enabled, reason = _mdq_tool_availability(name)
    if not enabled:
        return MdqDispatchResult(
            output=f"Tool disabled: {reason}",
            is_error=True,
            metadata={},
            execution_mode="no_op",
            error_type=TOOL_DISABLED,
            refused=True,
        )
    try:
        token = _mdq_metadata_var.set({})
    except Exception:  # noqa: BLE001 — set() failure must not corrupt state
        raise RuntimeError("Failed to set mdq metadata ContextVar")
    try:
        result = await dispatch_tool(_DISPATCH_TABLE, name, args, context=context)
        metadata = _mdq_metadata_var.get() or {}
    finally:
        _mdq_metadata_var.reset(token)
    return MdqDispatchResult(
        output=result.output,
        is_error=result.is_error,
        metadata=metadata,
        execution_mode=result.execution_mode,
        side_effect_applied=result.side_effect_applied,
        dedup_state=result.dedup_state,
        error_type=result.error_type or "",
    )


def _root_identity(roots: Sequence[str]) -> str:
    """The authorized root as a hash, so the persisted record names the root without its path."""
    return hash_query_value(roots[0]) if roots else ""


def _build_call_tool_audit_detail(
    name: str,
    r: MdqDispatchResult,
    ms: float,
    args: dict[str, Any],
    roots: Sequence[str] = (),
) -> list[str]:
    """Build the per-tool audit detail parts for a completed (non-raising) dispatch result.

    Sourced from structured metadata returned by MdqService's methods (or,
    for get_chunk, from its own output text), never inferred from other
    tools' output text. For the indexing tools the request's own path count is persisted
    together with the hashed root identity, because the metadata carries counts only and
    the root path itself must not reach the record (REQ-006).
    """
    detail_parts: list[str] = [f"duration_ms={ms:.0f}"]
    if r.is_error:
        # A refusal names itself through `error_type`, so `detail` does not repeat it; a
        # dispatch-level error result carries the category here instead.
        if not r.refused:
            detail_parts.append("error_kind=tool_error")
    elif name == "search_docs":
        md = r.metadata
        detail_parts.append(f"result_count={md.get('result_count', 0)}")
        detail_parts.append(f"shown_count={md.get('shown_count', 0)}")
        if md.get("truncated"):
            detail_parts.append("truncated=true")
    elif name == "get_chunk":
        if r.output and "[Truncated" in r.output:
            detail_parts.append("truncated=true")
    elif name == "grep_docs":
        md = r.metadata
        detail_parts.append(f"match_count={md.get('match_count', 0)}")
        if md.get("truncated"):
            detail_parts.append("truncated=true")
    elif name == "index_paths":
        md = r.metadata
        detail_parts.append(f"paths_count={len(args.get('paths', []))}")
        detail_parts.append(f"root_identity={_root_identity(roots)}")
        detail_parts.append(f"indexed_count={md.get('indexed_count', 0)}")
        detail_parts.append(f"skipped_count={md.get('skipped_count', 0)}")
        detail_parts.append(f"failed_count={md.get('failed_count', 0)}")
    elif name == "refresh_index":
        md = r.metadata
        detail_parts.append(f"paths_count={len(args.get('paths', []))}")
        detail_parts.append(f"root_identity={_root_identity(roots)}")
        detail_parts.append(f"indexed_count={md.get('indexed_count', 0)}")
        detail_parts.append(f"skipped_count={md.get('skipped_count', 0)}")
        detail_parts.append(f"deleted_count={md.get('deleted_count', 0)}")
        detail_parts.append(f"failed_count={md.get('failed_count', 0)}")
    return detail_parts


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/v1/tools")
async def list_tools(
    include_disabled: bool = False, disabled_code: str | None = None
) -> dict[str, Any]:
    """Return the MCP tool list with schema_version and server_key appended."""
    annotated: list[dict[str, Any]] = []
    for tool in TOOL_LIST:
        enabled, reason = _mdq_tool_availability(tool["name"])
        annotated.append({**tool, "enabled": enabled, "disabled_reason": reason})
    return build_tools_response(
        cast("list[McpTool]", annotated),
        "mdq",
        include_disabled=include_disabled,
        disabled_code=disabled_code,
    )


def _elapsed_ms(t0: float) -> float:
    """Elapsed milliseconds since the start of the call."""
    return (time.perf_counter() - t0) * 1000


# The classes answered at HTTP 200 with `is_error=true` (MCP spec). The remaining MDQ classes
# keep their handler's transport status, so the boundary records them and re-raises.
_TOOL_LEVEL_ERRORS: tuple[type[MdqServiceError], ...] = (
    MdqValidationError,
    MdqAuthorizationError,
    MdqNotFoundError,
    MdqIndexNotReadyError,
)


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Handle MCP call_tool requests through one audit boundary (REQ-005).

    One record per authenticated call is written from the single `finally`, so the refusal
    path and the malformed-execution-context path are covered too. A refused call is
    `rejected`, a failure during the tool's work is `error`. Responses carry the stable code,
    never exception text, SQLite detail, or a path (AC-4, AC-5).
    """
    session_id, request_id = extract_request_context(request)[:2]
    emission = AuditEmission(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        server_key="mdq",
    )
    target = extract_audit_target(req.name, req.args, _service.allowed_dirs)
    t0 = time.perf_counter()
    outcome = "ok"
    error_type = ""
    detail = ""
    try:
        try:
            exec_ctx = extract_execution_context(request, req.name, req.args)
        except ExecutionContextError:
            # Refused before dispatch, so no durable state is created.
            outcome = "rejected"
            error_type = "validation_error"
            detail = f"duration_ms={_elapsed_ms(t0):.0f}"
            return CallToolResponse(result=error_type, is_error=True)

        r = await _dispatch_mdq_tool(req.name, req.args, context=exec_ctx)
        outcome = r.outcome
        error_type = r.error_type
        ms = _elapsed_ms(t0)
        detail = ", ".join(
            _build_call_tool_audit_detail(
                req.name, r, ms, req.args, _service.allowed_dirs
            )
        )
        logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
        return _to_call_tool_response(
            DispatchResult(
                output=r.output,
                is_error=r.is_error,
                dedup_state=r.dedup_state,
                execution_mode=r.execution_mode,
                side_effect_applied=r.side_effect_applied,
            )
        )
    except MdqServiceError as exc:
        outcome = "error"
        error_type = code_for_exception(exc)
        detail = f"duration_ms={_elapsed_ms(t0):.0f}"
        if isinstance(exc, _TOOL_LEVEL_ERRORS):
            return CallToolResponse(result=error_type, is_error=True)
        raise
    finally:
        emission.emit(
            target=target, outcome=outcome, error_type=error_type, detail=detail
        )


@app.get("/health")
async def health() -> JSONResponse:
    """Return health check status."""
    # The response is composed in `check_health()`, which reads the same startup result the rest
    # of the server does; the handler only adds the read-only dedup block to the details.
    return check_health(_cfg, extra_details=dedup_health_details())


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class MdqMCPServer(MCPServer):
    """MCPServer subclass for mdq-mcp.

    Conforms to MCPServer base class contract:
    - server_key: "mdq" (used for routing)
    - http_host: explicit "127.0.0.1" (matches other HTTP servers)
    - auth_token: non-empty Bearer token read from mdq_mcp_server.toml (the module refuses to load without it);
      allowed_dirs is a separate path authorization applied after authentication
    """

    server_name = "mdq-mcp"
    server_version = "1.0.0"
    http_host = "127.0.0.1"
    http_port = 8013
    own_config_file = "mdq_mcp_server.toml"
    app_module = "mcp_servers.mdq.mdq_server:app"
    mcp_tools = TOOL_LIST
    server_key = "mdq"

    async def dispatch(
        self,
        name: str,
        args: dict[str, Any],
        context: ExecutionContext | None = None,
    ) -> DispatchResult:
        """Route an MDQ tool call to the appropriate handler."""
        r = await _dispatch_mdq_tool(name, args, context=context)
        return DispatchResult(
            output=r.output,
            is_error=r.is_error,
            dedup_state=r.dedup_state,
            execution_mode=r.execution_mode,
            side_effect_applied=r.side_effect_applied,
        )


# Attach the common Bearer authentication middleware. allowed_dirs path authorization
# is applied afterwards, inside the service, and does not replace authentication.
require_auth_token("mdq-mcp", "MCP_MDQ_AUTH_TOKEN", _cfg.auth_token)
attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token)


def _enforce_posture_gate() -> None:
    """Refuse HTTP bind when the MDQ posture is not validated (fail-closed).

    Reads only `_security_posture.validated`; the payload `ready` is derived in
    `make_health_response()` from dependencies plus `validated`, so this module never
    invents its own Ready rule. Logs failed check ids and reason codes only (no auth
    tokens or allow-list entries) and raises SystemExit(1) when not validated. Runs in
    __main__ only, so importing this module in tests never triggers SystemExit.
    """
    if _security_posture.validated:
        return
    failed = ", ".join(
        f"{check.check_id}:{check.reason_code}"
        for check in _security_posture.checks
        if check.status is SecurityCheckStatus.FAILED
    )
    logger.error("mdq-mcp: security posture FAILED (%s) — refusing to bind", failed)
    raise SystemExit(1)


if __name__ == "__main__":
    _enforce_posture_gate()
    server = MdqMCPServer()
    server.run_http()
