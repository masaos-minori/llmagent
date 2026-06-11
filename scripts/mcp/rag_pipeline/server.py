#!/usr/bin/env python3
"""rag_mcp_server.py
RAG Pipeline MCP server (port 8010).

Wraps the six-step RagPipeline (MQE→Search→RRF→Rerank→Dedup→Augment) as an
HTTP MCP server.  Replaces the in-process augment() call when rag_service_url
is configured in agent.toml.

Provided endpoints:
  POST /rag_run_pipeline    Run full pipeline; return augmented_text + selected_hits
  POST /rag_debug_pipeline  Run pipeline returning all intermediate stage outputs
  POST /v1/search           Backward-compat for agent_rag.augment() via rag_service_url
  GET  /v1/tools            MCP tool list (minimal format)
  POST /v1/call_tool        MCP standard tool dispatch
  GET  /health              Health check
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from shared.formatters import fmt_kvlog
from shared.logger import Logger

from mcp.dispatch import dispatch_tool
from mcp.models import CallToolRequest, CallToolResponse
from mcp.rag_pipeline.models import (
    RagDebugResponse,
    RagPipelineServiceError,
    RagRunRequest,
    RagRunResponse,
    RagSearchRequest,
    RagSearchResponse,
)
from mcp.rag_pipeline.service import RagPipelineMCPService, _service
from mcp.rag_pipeline.tools import _MCP_TOOLS
from mcp.server import MCPServer, ToolArgs

logger = Logger(__name__, "/opt/llm/logs/rag-mcp.log")


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI lifespan: start / stop the shared service instance
# ──────────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    svc: RagPipelineMCPService = _service
    await svc.start()
    yield
    await svc.stop()


app = FastAPI(
    title="rag-pipeline-mcp",
    version="1.0.0",
    description="RAG Pipeline MCP server (MQE→Search→RRF→Rerank→Dedup→Augment)",
    lifespan=_lifespan,
)


@app.exception_handler(RagPipelineServiceError)
async def _handle_rag_service_error(
    _req: Any, exc: RagPipelineServiceError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"error": str(exc)},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Direct HTTP endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.post("/rag_run_pipeline", response_model=RagRunResponse)
async def rag_run_pipeline(req: RagRunRequest) -> RagRunResponse:
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


@app.post("/v1/search", response_model=RagSearchResponse)
async def v1_search(req: RagSearchRequest) -> RagSearchResponse:
    """Backward-compat endpoint for agent_rag.augment() via rag_service_url.

    Response includes selected_hits so augment() can populate self.last_reranked
    for two-stage fetch without REPL-side changes.
    """
    if _service._pipeline is None:  # noqa: SLF001 — readiness guard before dispatch
        raise RagPipelineServiceError("Service not ready")
    t0 = time.perf_counter()
    result = await _service.run_search(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "v1_search",
            hits=len(result.selected_hits),
            has_context=bool(result.context),
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# MCP standard endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in _MCP_TOOLS
        ],
    }


async def _dispatch_rag_tool(name: str, args: ToolArgs) -> tuple[str, bool]:
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    result, is_error = await _dispatch_rag_tool(req.name, req.args)
    return CallToolResponse(result=result, is_error=is_error)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class RagPipelineMCPServer(MCPServer):
    """MCPServer subclass for rag-pipeline-mcp."""

    server_name = "rag-pipeline-mcp"
    server_version = "1.0.0"
    http_port = 8010
    app_module = "mcp.rag_pipeline.server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        return await _dispatch_rag_tool(name, args)


if __name__ == "__main__":
    import sys

    server = RagPipelineMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
