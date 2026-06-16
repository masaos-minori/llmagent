#!/usr/bin/env python3
"""mcp/mdq/server.py
Markdown Context Compression Engine MCP server (port 8013).

Exposes 7 tools for indexing, searching, and inspecting Markdown documents.

Provided endpoints:
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
  GET  /health        Health check
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog

from mcp.audit import _audit_log
from mcp.dispatch import DispatchResult, dispatch_tool
from mcp.mdq.models import (
    GetChunkRequest,
    GrepDocsRequest,
    IndexPathsRequest,
    MdqServiceError,
    OutlineRequest,
    RefreshIndexRequest,
    SearchDocsRequest,
    StatsRequest,
)
from mcp.mdq.service import MdqService
from mcp.mdq.tools import _MCP_TOOLS
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs

logger = logging.getLogger(__name__)

app = FastAPI(
    title="mdq-mcp",
    version="1.0.0",
    description="Markdown Context Compression Engine MCP server",
)

_service: MdqService = MdqService()


@app.exception_handler(MdqServiceError)
async def _on_mdq_service_error(_req: Any, exc: MdqServiceError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=500)


# ──────────────────────────────────────────────────────────────────────────────
# Dispatch handlers
# ──────────────────────────────────────────────────────────────────────────────


async def _handle_search_docs(args: ToolArgs) -> str:
    return await _service.search_docs(SearchDocsRequest(**args))


async def _handle_get_chunk(args: ToolArgs) -> str:
    return await _service.get_chunk(GetChunkRequest(**args))


async def _handle_outline(args: ToolArgs) -> str:
    return await _service.outline(OutlineRequest(**args))


async def _handle_index_paths(args: ToolArgs) -> str:
    return await _service.index_paths(IndexPathsRequest(**args))


async def _handle_refresh_index(args: ToolArgs) -> str:
    return await _service.refresh_index(RefreshIndexRequest(**args))


async def _handle_stats(args: ToolArgs) -> str:
    return await _service.stats(StatsRequest(**args))


async def _handle_grep_docs(args: ToolArgs) -> str:
    return await _service.grep_docs(GrepDocsRequest(**args))


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
        "tools": [{**t, "server_key": "mdq"} for t in _MCP_TOOLS],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    t0 = time.perf_counter()
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    r = await _dispatch_mdq_tool(req.name, req.args)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=str(req.args.get("query", req.args.get("path", "")))[:80],
        outcome="error" if r.is_error else "ok",
    )
    return CallToolResponse(result=r.output, is_error=r.is_error)


@app.get("/health")
async def health() -> dict[str, object]:
    deps: dict[str, str] = {}
    try:
        import os as _os

        from shared.config_loader import ConfigLoader

        cfg = ConfigLoader().load_all()
        common = cfg.get("common", {}) if isinstance(cfg.get("common"), dict) else {}
        rag_db = common.get("rag_db_path") or common.get("sqlite_rag_path")
        if isinstance(rag_db, str):
            if not _os.path.isfile(rag_db):
                deps["rag_db"] = f"not found: {rag_db}"
    except Exception:
        deps["config"] = "check failed"
    ready = len(deps) == 0
    return {
        "status": "ok",
        "ready": ready,
        "dependencies": deps,
        "details": {"service": "mdq-mcp"},
    }


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class MdqMCPServer(MCPServer):
    """MCPServer subclass for mdq-mcp."""

    server_name = "mdq-mcp"
    server_version = "1.0.0"
    http_port = 8013
    app_module = "mcp.mdq.server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        return await _dispatch_mdq_tool(name, args)


if __name__ == "__main__":
    import sys

    server = MdqMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
