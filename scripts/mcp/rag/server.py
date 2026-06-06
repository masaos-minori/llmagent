#!/usr/bin/env python3
"""mcp/rag/server.py
RAG Pipeline MCP server (port 8014).

Exposes 2 tools for running the complete RAG pipeline:
  - rag_run_pipeline: Standard RAG pipeline execution
  - rag_debug_pipeline: Debug mode RAG pipeline execution

Provided endpoints:
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
  GET  /health        Health check
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from mcp.audit import _audit_log
from mcp.dispatch import dispatch_tool
from mcp.models import CallToolRequest, CallToolResponse
from mcp.rag.models import (
    RAGPipelineDebugRequest,
    RAGPipelineRequest,
)
from mcp.rag.service import RAGPipelineService
from mcp.server import MCPServer, ToolArgs

logger = logging.getLogger(__name__)

app = FastAPI(
    title="rag-pipeline-mcp",
    version="1.0.0",
    description="RAG Pipeline MCP server",
)

# Lazy singleton; created on first request.
_service: RAGPipelineService | None = None


def _get_service() -> RAGPipelineService:
    global _service
    if _service is None:
        _service = RAGPipelineService()
    return _service


# ──────────────────────────────────────────────────────────────────────────────
# MCP tool definitions
# ──────────────────────────────────────────────────────────────────────────────

_MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "rag_run_pipeline",
        "description": "Run the complete RAG pipeline with standard settings.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "context": {"type": "string", "description": "Context for RAG"},
                "max_results": {
                    "type": "integer",
                    "description": "Max results to return (default: 10)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "rag_debug_pipeline",
        "description": "Run the complete RAG pipeline with debug output.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "context": {"type": "string", "description": "Context for RAG"},
                "max_results": {
                    "type": "integer",
                    "description": "Max results to return (default: 10)",
                },
            },
            "required": ["query"],
        },
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Dispatch handlers
# ──────────────────────────────────────────────────────────────────────────────


async def _handle_rag_run_pipeline(args: ToolArgs) -> str:
    return await _get_service().run_pipeline(RAGPipelineRequest(**args))


async def _handle_rag_debug_pipeline(args: ToolArgs) -> str:
    return await _get_service().debug_pipeline(RAGPipelineDebugRequest(**args))


_DISPATCH_TABLE = {
    "rag_run_pipeline": _handle_rag_run_pipeline,
    "rag_debug_pipeline": _handle_rag_debug_pipeline,
}


async def _dispatch_rag_tool(name: str, args: ToolArgs) -> tuple[str, bool]:
    return await dispatch_tool(_DISPATCH_TABLE, name, args)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in _MCP_TOOLS
        ],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    session_id = request.headers.get("x-session-id", "")
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    result, is_error = await _dispatch_rag_tool(req.name, req.args)
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=str(req.args.get("query", ""))[:80],
        outcome="error" if is_error else "ok",
    )
    return CallToolResponse(result=result, is_error=is_error)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "rag-pipeline-mcp"}


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class RAGPipelineMCPServer(MCPServer):
    """MCPServer subclass for rag-pipeline-mcp."""

    server_name = "rag-pipeline-mcp"
    server_version = "1.0.0"
    http_port = 8014
    app_module = "mcp.rag.server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        return await _dispatch_rag_tool(name, args)


if __name__ == "__main__":
    import sys

    server = RAGPipelineMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
