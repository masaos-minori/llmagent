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
from dataclasses import dataclass
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.logger import Logger

from mcp_servers.audit import _audit_log
from mcp_servers.dispatch import DispatchResult, _to_call_tool_response, dispatch_tool
from mcp_servers.mdq.audit_target import extract_audit_target
from mcp_servers.mdq.health_check import check_health
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
from mcp_servers.mdq.mdq_service import MdqService
from mcp_servers.mdq.mdq_tools import TOOL_LIST
from mcp_servers.models import CallToolRequest, CallToolResponse, McpTool
from mcp_servers.server import (
    MCPServer,
    ToolArgs,
    _FastAPIApp,
    attach_auth_middleware,
    build_tools_response,
    extract_request_context,
)

logger = Logger(__name__, "/opt/llm/logs/mdq-mcp.log")

app = FastAPI(
    title="mdq-mcp",
    version="1.0.0",
    description="Markdown Context Compression Engine MCP server (Markdown-only, structure-aware retrieval)",
)

_service: MdqService = MdqService()


def _mdq_tool_availability(allowed_dirs: list[str], tool_name: str) -> tuple[bool, str]:
    """Return (enabled, disabled_reason) for a single mdq tool by name."""
    if not allowed_dirs:
        return False, "allowed_dirs is empty"
    return True, ""


def _mdq_error_handler(
    request: Request, exc: Exception, status_code: int, error_kind: str
) -> JSONResponse:
    """Format an MDQ error into a JSONResponse with consistent structure."""
    logger.info("MDQ %s error: %s", error_kind, exc)
    session_id, request_id = extract_request_context(request)
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action="call_tool",
        target="",
        outcome="error",
        detail="",
        server_key="mdq",
        error_type=error_kind,
    )
    return JSONResponse({"detail": str(exc)}, status_code=status_code)


@app.exception_handler(MdqValidationError)
async def _on_mdq_validation_error(
    request: Request, exc: MdqValidationError
) -> JSONResponse:
    """Handle validation errors with HTTP 400 response."""
    return _mdq_error_handler(request, exc, 400, "validation_error")


@app.exception_handler(MdqAuthorizationError)
async def _on_mdq_authorization_error(
    request: Request, exc: MdqAuthorizationError
) -> JSONResponse:
    """Handle authorization errors with HTTP 403 response."""
    return _mdq_error_handler(request, exc, 403, "authorization_error")


@app.exception_handler(MdqNotFoundError)
async def _on_mdq_not_found_error(
    request: Request, exc: MdqNotFoundError
) -> JSONResponse:
    """Handle not found errors with HTTP 404 response."""
    return _mdq_error_handler(request, exc, 404, "not_found_error")


@app.exception_handler(MdqIndexNotReadyError)
async def _on_mdq_index_not_ready_error(
    request: Request, exc: MdqIndexNotReadyError
) -> JSONResponse:
    """Handle index-not-ready errors with HTTP 503 response."""
    return _mdq_error_handler(request, exc, 503, "index_not_ready_error")


@app.exception_handler(MdqDatabaseError)
async def _on_mdq_database_error(
    request: Request, exc: MdqDatabaseError
) -> JSONResponse:
    """Handle database errors with HTTP 503 response."""
    return _mdq_error_handler(request, exc, 503, "database_error")


@app.exception_handler(MdqConsistencyError)
async def _on_mdq_consistency_error(
    request: Request, exc: MdqConsistencyError
) -> JSONResponse:
    """Handle consistency errors with HTTP 500 response."""
    return _mdq_error_handler(request, exc, 500, "consistency_error")


@app.exception_handler(MdqServiceError)
async def _on_mdq_service_error(request: Request, exc: MdqServiceError) -> JSONResponse:
    """Handle generic service errors with HTTP 500 response."""
    return _mdq_error_handler(request, exc, 500, "service_error")


# ──────────────────────────────────────────────────────────────────────────────
# Dispatch handlers
# ──────────────────────────────────────────────────────────────────────────────


_mdq_metadata_var: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "mdq_metadata", default={}
)


@dataclass(frozen=True)
class MdqDispatchResult:
    """Wraps the shared DispatchResult with mdq-local per-call metadata."""

    output: str
    is_error: bool
    metadata: dict[str, Any]

    @property
    def outcome(self) -> str:
        """Return 'error' if is_error, otherwise 'ok'."""
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


async def _dispatch_mdq_tool(name: str, args: ToolArgs) -> MdqDispatchResult:
    """Route a tool call through the shared dispatch mechanism, capturing mdq-local metadata."""
    token = _mdq_metadata_var.set({})
    try:
        result = await dispatch_tool(_DISPATCH_TABLE, name, args)
        metadata = _mdq_metadata_var.get()
    finally:
        _mdq_metadata_var.reset(token)
    return MdqDispatchResult(
        output=result.output, is_error=result.is_error, metadata=metadata
    )


def _build_call_tool_audit_detail(
    name: str, r: MdqDispatchResult, ms: float
) -> list[str]:
    """Build the per-tool audit detail parts for a completed (non-raising) dispatch result.

    Sourced from structured metadata returned by MdqService's methods (or,
    for get_chunk, from its own output text), never inferred from other
    tools' output text.
    """
    detail_parts: list[str] = [f"duration_ms={ms:.0f}"]
    if r.is_error:
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
        detail_parts.append(f"indexed_count={md.get('indexed_count', 0)}")
        detail_parts.append(f"skipped_count={md.get('skipped_count', 0)}")
        detail_parts.append(f"failed_count={md.get('failed_count', 0)}")
    elif name == "refresh_index":
        md = r.metadata
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
    enabled, reason = _mdq_tool_availability(_service.allowed_dirs, "")
    annotated = [
        {**t, "enabled": enabled, "disabled_reason": reason} for t in TOOL_LIST
    ]
    return build_tools_response(
        cast("list[McpTool]", annotated),
        "mdq",
        include_disabled=include_disabled,
        disabled_code=disabled_code,
    )


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Handle MCP call_tool requests with audit logging and error handling."""
    t0 = time.perf_counter()
    session_id, request_id = extract_request_context(request)
    target = extract_audit_target(req.name, req.args)

    try:
        r = await _dispatch_mdq_tool(req.name, req.args)
    except (
        MdqValidationError,
        MdqAuthorizationError,
        MdqNotFoundError,
        MdqIndexNotReadyError,
    ) as exc:
        # Tool-level error → is_error=True, HTTP 200 (MCP spec)
        ms = (time.perf_counter() - t0) * 1000
        error_kind = type(exc).__name__
        _audit_log(
            logger,
            session_id=session_id,
            request_id=request_id,
            action=req.name,
            target=target[:80],
            outcome="error",
            detail=f"duration_ms={ms:.0f}",
            server_key="mdq",
            error_type=error_kind,
        )
        return CallToolResponse(result=str(exc), is_error=True)

    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))

    detail_parts = _build_call_tool_audit_detail(req.name, r, ms)

    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=target[:80],
        outcome=r.outcome,
        detail=", ".join(detail_parts),
        server_key="mdq",
    )
    return _to_call_tool_response(DispatchResult(output=r.output, is_error=r.is_error))


@app.get("/health")
async def health() -> JSONResponse:
    """Return health check status."""
    result: JSONResponse = check_health()
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class MdqMCPServer(MCPServer):
    """MCPServer subclass for mdq-mcp.

    Conforms to MCPServer base class contract:
    - server_key: "mdq" (used by list_tools_with_server_key() and routing)
    - http_host: explicit "127.0.0.1" (matches other HTTP servers)
    - auth_token: empty string (no auth required — mdq has its own authorization via allowed_dirs)
    """

    server_name = "mdq-mcp"
    server_version = "1.0.0"
    http_host = "127.0.0.1"
    http_port = 8013
    own_config_file = "mdq_mcp_server.toml"
    app_module = "mcp_servers.mdq.mdq_server:app"
    mcp_tools = TOOL_LIST
    server_key = "mdq"

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        """Route an MDQ tool call to the appropriate handler."""
        r = await _dispatch_mdq_tool(name, args)
        return DispatchResult(output=r.output, is_error=r.is_error)


# Attach auth middleware — no-op when token is empty (mdq has its own authorization)
attach_auth_middleware(cast(_FastAPIApp, app), "")


if __name__ == "__main__":
    server = MdqMCPServer()
    server.run_http()
