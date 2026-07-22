#!/usr/bin/env python3
"""mcp_servers.rag_pipeline.server

RAG Pipeline MCP server (port 8010).

Wraps the six-step RagPipeline (MQE→Search→RRF→Rerank→Dedup→Augment) as an
HTTP MCP server.  Replaces the in-process augment() call when rag_service_url
is configured in rag.toml (rag_service_url).

Provided endpoints:
  POST /v1/call_tool        MCP tool dispatch
  GET  /v1/tools            List RAG tools with server_key="rag_pipeline"
  GET  /health              Health check endpoint
  POST /rag_debug_pipeline  Run pipeline returning all intermediate stage outputs
  GET  /v1/tools            MCP tool list (minimal format)
  POST /v1/call_tool        MCP standard tool dispatch
  GET  /health              Health check
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog

from mcp_servers.dispatch import DispatchResult, _to_call_tool_response, dispatch_tool
from mcp_servers.health_response import make_health_response
from mcp_servers.models import CallToolRequest, CallToolResponse
from mcp_servers.rag_pipeline.rag_pipeline_models import (
    RagDebugResponse,
    RagPipelineServiceError,
    RagRunRequest,
    RagRunResponse,
)
from mcp_servers.rag_pipeline.rag_pipeline_service import (
    RagPipelineMCPService,
    _service,
)
from mcp_servers.rag_pipeline.rag_pipeline_tools import TOOL_LIST
from mcp_servers.server import MCPServer, ToolArgs

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI lifespan: start / stop the shared service instance
# ──────────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Start and stop the shared RAG pipeline service."""
    svc: RagPipelineMCPService = _service
    await svc.start()
    yield
    await svc.stop()


app = FastAPI(
    title="rag-pipeline-mcp",
    version="1.0.0",
    description="RAG Pipeline MCP server — multi-format semantic retrieval, production-ready",
    lifespan=_lifespan,
)


@app.exception_handler(RagPipelineServiceError)
async def _handle_rag_service_error(
    _req: Any, exc: RagPipelineServiceError
) -> JSONResponse:
    """Handle RAG pipeline service errors with a 503 Service Unavailable response."""
    return JSONResponse(
        status_code=503,
        content={"error": str(exc)},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Direct HTTP endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.post("/rag_run_pipeline", response_model=RagRunResponse)
async def rag_run_pipeline(req: RagRunRequest) -> RagRunResponse:
    """Execute the full RAG pipeline with MQE→Search→RRF→Rerank→Dedup→Augment stages."""
    t0 = time.perf_counter()
    result = await _service.run_pipeline(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "rag_run_pipeline",
            hits=len(result.selected_hits),
            augmented=bool(result.augmented_text),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.post("/rag_debug_pipeline", response_model=RagDebugResponse)
async def rag_debug_pipeline(req: RagRunRequest) -> RagDebugResponse:
    """Execute the RAG pipeline returning all intermediate stage outputs for debugging."""
    t0 = time.perf_counter()
    result = await _service.run_debug_pipeline(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "rag_debug_pipeline",
            queries=len(result.queries),
            reranked=len(result.reranked_hits),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint. Returns degraded when embed_url is not configured."""
    deps: dict[str, str] = {}
    try:
        from shared.config_loader import ConfigLoader

        cfg = ConfigLoader().load("rag_pipeline_mcp_server.toml")
        embed_url = cfg.get("embed_url")
        if not embed_url or not isinstance(embed_url, str):
            deps["embed_url"] = "not configured"
    except Exception:
        deps["config"] = "check failed"  # noqa: BLE001 — health check must not fail on config errors
    details: dict[str, object] = {"service": "rag-pipeline-mcp"}
    result: JSONResponse = make_health_response(deps, details)
    return result


@app.post("/rag_invalidate_cache")
async def rag_invalidate_cache() -> JSONResponse:
    """Invalidate the semantic cache of the RAG pipeline."""
    try:
        _service.invalidate_cache()
        return JSONResponse(
            content={"status": "ok", "message": "Semantic cache invalidated"}
        )
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


# ──────────────────────────────────────────────────────────────────────────────
# MCP standard endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    """List available RAG tools with server_key="rag_pipeline"."""
    return {
        "tools": [{**t, "server_key": "rag_pipeline"} for t in TOOL_LIST],
    }


async def _dispatch_rag_tool(name: str, args: ToolArgs) -> DispatchResult:
    """Route RAG pipeline tool calls through the service's dispatch table."""
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    """Dispatch an MCP tool call through the RAG pipeline service."""
    r = await _dispatch_rag_tool(req.name, req.args)
    return _to_call_tool_response(r)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class RagPipelineMCPServer(MCPServer):
    """MCPServer subclass for rag-pipeline-mcp."""

    server_name = "rag-pipeline-mcp"
    server_version = "1.0.0"
    http_port = 8010
    own_config_file = "rag_pipeline_mcp_server.toml"
    app_module = "mcp_servers.rag_pipeline.rag_pipeline_server:app"
    mcp_tools = TOOL_LIST

    async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
        """Dispatch a tool by name with the given arguments via the RAG pipeline."""
        return await _dispatch_rag_tool(name, args)


if __name__ == "__main__":
    server = RagPipelineMCPServer()
    server.run_http()
