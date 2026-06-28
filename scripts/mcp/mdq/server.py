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

import time
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.logger import Logger

from mcp.audit import _audit_log
from mcp.dispatch import DispatchResult, dispatch_tool
from mcp.mdq.models import (
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
from mcp.mdq.service import MdqService
from mcp.mdq.tools import _MCP_TOOLS
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs

logger = Logger(__name__, "/opt/llm/logs/mdq-mcp.log")

app = FastAPI(
    title="mdq-mcp",
    version="1.0.0",
    description="Markdown Context Compression Engine MCP server (Markdown-only, structure-aware retrieval)",
)

_service: MdqService = MdqService()


@app.exception_handler(MdqValidationError)
async def _on_mdq_validation_error(
    request: Request, exc: MdqValidationError
) -> JSONResponse:
    logger.info("MDQ validation error: %s", exc)
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
        detail="error_kind=validation_error",
    )
    return JSONResponse({"detail": str(exc)}, status_code=400)


@app.exception_handler(MdqAuthorizationError)
async def _on_mdq_authorization_error(
    request: Request, exc: MdqAuthorizationError
) -> JSONResponse:
    logger.info("MDQ authorization error: %s", exc)
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
        detail="error_kind=authorization_error",
    )
    return JSONResponse({"detail": str(exc)}, status_code=403)


@app.exception_handler(MdqNotFoundError)
async def _on_mdq_not_found_error(
    request: Request, exc: MdqNotFoundError
) -> JSONResponse:
    logger.info("MDQ not found error: %s", exc)
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
        detail="error_kind=not_found_error",
    )
    return JSONResponse({"detail": str(exc)}, status_code=404)


@app.exception_handler(MdqIndexNotReadyError)
async def _on_mdq_index_not_ready_error(
    request: Request, exc: MdqIndexNotReadyError
) -> JSONResponse:
    logger.info("MDQ index not ready error: %s", exc)
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
        detail="error_kind=index_not_ready_error",
    )
    return JSONResponse({"detail": str(exc)}, status_code=503)


@app.exception_handler(MdqDatabaseError)
async def _on_mdq_database_error(
    request: Request, exc: MdqDatabaseError
) -> JSONResponse:
    logger.info("MDQ database error: %s", exc)
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
        detail="error_kind=database_error",
    )
    return JSONResponse({"detail": str(exc)}, status_code=503)


@app.exception_handler(MdqConsistencyError)
async def _on_mdq_consistency_error(
    request: Request, exc: MdqConsistencyError
) -> JSONResponse:
    logger.info("MDQ consistency error: %s", exc)
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
        detail="error_kind=consistency_error",
    )
    return JSONResponse({"detail": str(exc)}, status_code=500)


@app.exception_handler(MdqServiceError)
async def _on_mdq_service_error(request: Request, exc: MdqServiceError) -> JSONResponse:
    logger.info("MDQ service error (fallback): %s", exc)
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
        detail="error_kind=service_error",
    )
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


def _audit_target(tool_name: str, args: dict[str, Any]) -> str:
    """Extract audit target based on tool name."""
    if tool_name == "search_docs":
        query = args.get("query", "")
        path = args.get("path_prefix", "")
        return f"{query}{' + ' + path if path else ''}"
    elif tool_name == "get_chunk":
        return args.get("chunk_id", "")[:80]
    elif tool_name == "outline":
        return args.get("path", "")[:80]
    elif tool_name in ("index_paths", "refresh_index"):
        paths = args.get("paths", [])
        return paths[0][:80] if paths else ""
    elif tool_name == "grep_docs":
        return args.get("pattern", "")[:80]
    elif tool_name == "stats":
        return "mdq-mcp"
    elif tool_name == "fts_consistency_check":
        return "mdq-mcp"
    elif tool_name == "fts_rebuild":
        return "mdq-mcp"
    return ""


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

    # Tool-aware target extraction
    target = _audit_target(req.name, req.args)
    detail_parts: list[str] = []
    if not r.is_error:
        detail_parts.append(f"duration_ms={ms:.0f}")
        if req.name == "search_docs":
            detail_parts.append(
                f"result_count={len(r.output.split(chr(10))) if r.output else 0}"
            )
        elif req.name == "grep_docs":
            detail_parts.append(
                f"match_count={r.output.count(chr(45) + chr(45) + chr(45)) if r.output else 0}"
            )
        elif req.name in ("index_paths", "refresh_index"):
            detail_parts.append("indexed")
    else:
        detail_parts.append(f"duration_ms={ms:.0f}")
        detail_parts.append("error_kind=dispatch_error")

    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=target[:80],
        outcome="error" if r.is_error else "ok",
        detail=", ".join(detail_parts),
    )
    return CallToolResponse(result=r.output, is_error=r.is_error)


@app.get("/health")
async def health() -> JSONResponse:
    deps: dict[str, str] = {}
    details: dict[str, object] = {"service": "mdq-mcp"}

    try:
        import os as _os

        from shared.config_loader import ConfigLoader

        cfg = ConfigLoader().load_all()
        mdq_cfg = (
            cfg.get("mdq_mcp_server", {})
            if isinstance(cfg.get("mdq_mcp_server"), dict)
            else {}
        )
        db_path = mdq_cfg.get("db_path") or "/opt/llm/db/mdq.sqlite"
        details["database"] = db_path

        if not _os.path.isfile(db_path):
            deps["db_file"] = f"not found: {db_path}"
            return JSONResponse({
                "status": "degraded",
                "ready": False,
                "dependencies": deps,
                "details": details,
            }, status_code=503)

        import sqlite3

        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            if "sections" not in tables:
                deps["db_schema"] = "missing sections table"
                return JSONResponse({
                    "status": "degraded",
                    "ready": False,
                    "dependencies": deps,
                    "details": details,
                }, status_code=503)

            if "sections_fts" not in tables:
                deps["db_schema"] = "missing sections_fts FTS5 table"
                return JSONResponse({
                    "status": "degraded",
                    "ready": False,
                    "dependencies": deps,
                    "details": details,
                }, status_code=503)

            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
            triggers = {row[0] for row in cursor.fetchall()}
            expected_triggers = {"sections_ai", "sections_ad", "sections_au"}
            missing_triggers = expected_triggers - triggers
            if missing_triggers:
                deps["db_schema"] = (
                    f"missing triggers: {', '.join(sorted(missing_triggers))}"
                )
                return JSONResponse({
                    "status": "degraded",
                    "ready": False,
                    "dependencies": deps,
                    "details": details,
                }, status_code=503)

            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM sections_fts WHERE sections_fts = 'delete' LIMIT 1"
                )
                cursor.fetchone()
            except sqlite3.OperationalError as e:
                deps["fts5"] = f"FTS5 query failed: {e}"
                return JSONResponse({
                    "status": "degraded",
                    "ready": False,
                    "dependencies": deps,
                    "details": details,
                }, status_code=503)

            chunk_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM sections"
            ).fetchone()["cnt"]
            doc_count = conn.execute(
                "SELECT COUNT(DISTINCT file_path) as cnt FROM sections"
            ).fetchone()["cnt"]
            fts_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM sections_fts WHERE sections_fts != 'delete'"
            ).fetchone()["cnt"]

            row = conn.execute("SELECT MAX(file_mtime) as mt FROM sections").fetchone()
            last_indexed = row["mt"] if row and row["mt"] is not None else None
            details["document_count"] = doc_count
            details["chunk_count"] = chunk_count
            details["fts_row_count"] = fts_count
            details["last_indexed"] = last_indexed

            # Check for stale documents (file_mtime mismatch)
            try:
                from pathlib import Path as _Path

                stale_count = 0
                index_paths_cfg = mdq_cfg.get("index_paths", []) or []
                if index_paths_cfg:
                    first_path = _Path(index_paths_cfg[0])
                    if first_path.is_dir():
                        ref_mtime = first_path.stat().st_mtime
                    elif first_path.is_file():
                        ref_mtime = first_path.stat().st_mtime
                    else:
                        ref_mtime = None

                    stale_count = 0
                    if ref_mtime is not None:
                        stale_count = (
                            conn.execute(
                                "SELECT COUNT(DISTINCT file_path) as cnt FROM sections WHERE file_mtime < ?",
                                (ref_mtime,),
                            ).fetchone()["cnt"]
                            or 0
                        )
            except Exception:
                # If stale count fails, don't break health check
                stale_count = None
            details["stale_document_count"] = stale_count

        finally:
            conn.close()

    except (FileNotFoundError, PermissionError, KeyError, TypeError) as e:
        deps["config"] = f"check failed: {e}"

    ready = len(deps) == 0
    return JSONResponse(
        {"status": "ok" if ready else "degraded", "ready": ready, "dependencies": deps, "details": details},
        status_code=200 if ready else 503,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class MdqMCPServer(MCPServer):
    """MCPServer subclass for mdq-mcp."""

    server_name = "mdq-mcp"
    server_version = "1.0.0"
    http_port = 8013
    app_module = "mcp.mdq.server:app"
    mcp_tools = cast(list[dict[str, Any]], _MCP_TOOLS)

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
