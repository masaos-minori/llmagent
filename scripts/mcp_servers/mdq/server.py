#!/usr/bin/env python3
"""mcp_servers/mdq/server.py
Markdown Context Compression Engine MCP server (port 8013).

Exposes 7 tools for indexing, searching, and inspecting Markdown documents.

Provided endpoints:
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
  GET  /health        Health check
"""

from __future__ import annotations

import time
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp_servers.audit import _audit_log
from mcp_servers.dispatch import DispatchResult, dispatch_tool
from mcp_servers.mdq.audit_target import extract_audit_target
from mcp_servers.mdq.health_check import check_health
from mcp_servers.mdq.models import (
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
from mcp_servers.mdq.service import MdqService
from mcp_servers.mdq.tools import TOOL_LIST
from mcp_servers.models import CallToolRequest, CallToolResponse
from mcp_servers.server import MCPServer, ToolArgs, _FastAPIApp, attach_auth_middleware
from shared.formatters import fmt_kvlog
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/mdq-mcp.log")

app = FastAPI(
    title="mdq-mcp",
    version="1.0.0",
    description="Markdown Context Compression Engine MCP server (Markdown-only, structure-aware retrieval)",
)

_service: MdqService = MdqService()


def _mdq_error_handler(
    request: Request, exc: Exception, status_code: int, error_kind: str
) -> JSONResponse:
    logger.info("MDQ %s error: %s", error_kind, exc)
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action="call_tool",
        target="",
        outcome="error",
        detail=f"error_kind={error_kind}",
        server_key="mdq",
    )
    return JSONResponse({"detail": str(exc)}, status_code=status_code)


@app.exception_handler(MdqValidationError)
async def _on_mdq_validation_error(
    request: Request, exc: MdqValidationError
) -> JSONResponse:
    return _mdq_error_handler(request, exc, 400, "validation_error")


@app.exception_handler(MdqAuthorizationError)
async def _on_mdq_authorization_error(
    request: Request, exc: MdqAuthorizationError
) -> JSONResponse:
    return _mdq_error_handler(request, exc, 403, "authorization_error")


@app.exception_handler(MdqNotFoundError)
async def _on_mdq_not_found_error(
    request: Request, exc: MdqNotFoundError
) -> JSONResponse:
    return _mdq_error_handler(request, exc, 404, "not_found_error")


@app.exception_handler(MdqIndexNotReadyError)
async def _on_mdq_index_not_ready_error(
    request: Request, exc: MdqIndexNotReadyError
) -> JSONResponse:
    return _mdq_error_handler(request, exc, 503, "index_not_ready_error")


@app.exception_handler(MdqDatabaseError)
async def _on_mdq_database_error(
    request: Request, exc: MdqDatabaseError
) -> JSONResponse:
    return _mdq_error_handler(request, exc, 503, "database_error")


@app.exception_handler(MdqConsistencyError)
async def _on_mdq_consistency_error(
    request: Request, exc: MdqConsistencyError
) -> JSONResponse:
    return _mdq_error_handler(request, exc, 500, "consistency_error")


@app.exception_handler(MdqServiceError)
async def _on_mdq_service_error(request: Request, exc: MdqServiceError) -> JSONResponse:
    return _mdq_error_handler(request, exc, 500, "service_error")


# ──────────────────────────────────────────────────────────────────────────────
# Dispatch handlers
# ──────────────────────────────────────────────────────────────────────────────


async def _handle_search_docs(args: ToolArgs) -> str:
    result: str = await _service.search_docs(SearchDocsRequest(**args))
    return result


async def _handle_get_chunk(args: ToolArgs) -> str:
    result: str = await _service.get_chunk(GetChunkRequest(**args))
    return result


async def _handle_outline(args: ToolArgs) -> str:
    result: str = await _service.outline(OutlineRequest(**args))
    return result


async def _handle_index_paths(args: ToolArgs) -> str:
    result: str = await _service.index_paths(IndexPathsRequest(**args))
    return result


async def _handle_refresh_index(args: ToolArgs) -> str:
    result: str = await _service.refresh_index(RefreshIndexRequest(**args))
    return result


async def _handle_stats(args: ToolArgs) -> str:
    result: str = await _service.stats(StatsRequest(**args))
    return result


async def _handle_grep_docs(args: ToolArgs) -> str:
    result: str = await _service.grep_docs(GrepDocsRequest(**args))
    return result


_DISPATCH_TABLE = {
    "search_docs": _handle_search_docs,
    "get_chunk": _handle_get_chunk,
    "outline": _handle_outline,
    "index_paths": _handle_index_paths,
    "refresh_index": _handle_refresh_index,
    "stats": _handle_stats,
    "grep_docs": _handle_grep_docs,
}


async def _dispatch_mdq_tool(name: str, args: ToolArgs) -> DispatchResult:
    return await dispatch_tool(_DISPATCH_TABLE, name, args)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [{**t, "server_key": "mdq"} for t in TOOL_LIST],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    import re as _re

    t0 = time.perf_counter()
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
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
            detail=f"duration_ms={ms:.0f}, error_kind={error_kind}",
            server_key="mdq",
        )
        return CallToolResponse(result=str(exc), is_error=True)

    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))

    # Per-tool audit detail enrichment
    detail_parts: list[str] = [f"duration_ms={ms:.0f}"]
    if r.is_error:
        detail_parts.append("error_kind=tool_error")
    elif req.name == "search_docs":
        result_count = r.output.count("---") if r.output else 0
        detail_parts.append(f"result_count={result_count}")
    elif req.name == "get_chunk":
        if r.output and "[Truncated" in r.output:
            detail_parts.append("truncated=true")
    elif req.name == "grep_docs":
        match_count = r.output.count("---") if r.output else 0
        detail_parts.append(f"match_count={match_count}")
    elif req.name == "index_paths":
        if r.output:
            m = _re.search(r"Indexed:\s*(\d+)", r.output)
            if m:
                detail_parts.append(f"indexed_count={m.group(1)}")
    elif req.name == "refresh_index":
        if r.output:
            m_idx = _re.search(r"Indexed:\s*(\d+)", r.output)
            m_skip = _re.search(r"Skipped.*?:\s*(\d+)", r.output)
            m_del = _re.search(r"Deleted from index:\s*(\d+)", r.output)
            if m_idx:
                detail_parts.append(f"indexed_count={m_idx.group(1)}")
            if m_skip:
                detail_parts.append(f"skipped_count={m_skip.group(1)}")
            if m_del:
                detail_parts.append(f"deleted_count={m_del.group(1)}")

    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=target[:80],
        outcome="error" if r.is_error else "ok",
        detail=", ".join(detail_parts),
        server_key="mdq",
    )
    return CallToolResponse(result=r.output, is_error=r.is_error)


@app.get("/health")
async def health() -> JSONResponse:
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
    app_module = "mcp_servers.mdq.server:app"
    mcp_tools = cast(list[dict[str, Any]], TOOL_LIST)
    server_key = "mdq"

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        return await _dispatch_mdq_tool(name, args)


# Attach auth middleware — no-op when token is empty (mdq has its own authorization)
attach_auth_middleware(cast(_FastAPIApp, app), "")


if __name__ == "__main__":
    server = MdqMCPServer()
    server.run_http()
