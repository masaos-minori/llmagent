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
from typing import Any

from fastapi import FastAPI, Request

from mcp.audit import _audit_log
from mcp.dispatch import dispatch_tool
from mcp.mdq.models import (
    GetChunkRequest,
    GrepDocsRequest,
    IndexPathsRequest,
    OutlineRequest,
    RefreshIndexRequest,
    SearchDocsRequest,
    StatsRequest,
)
from mcp.mdq.service import MdqService
from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs

logger = logging.getLogger(__name__)

app = FastAPI(
    title="mdq-mcp",
    version="1.0.0",
    description="Markdown Context Compression Engine MCP server",
)

# Lazy singleton; created on first request.
_service: MdqService | None = None


def _get_service() -> MdqService:
    global _service
    if _service is None:
        _service = MdqService()
    return _service


# ──────────────────────────────────────────────────────────────────────────────
# MCP tool definitions
# ──────────────────────────────────────────────────────────────────────────────

_MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_docs",
        "description": "Search indexed Markdown sections by query.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 10)",
                },
                "mode": {
                    "type": "string",
                    "description": "Search mode: bm25/grep/hybrid",
                },
                "path_prefix": {
                    "type": "string",
                    "description": "Filter by path prefix",
                },
                "tag_filter": {"type": "array", "description": "Filter by tags"},
                "heading_prefix": {
                    "type": "string",
                    "description": "Filter by heading prefix",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_chunk",
        "description": "Retrieve a Markdown chunk by its ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chunk_id": {"type": "integer", "description": "Chunk ID"},
                "with_neighbors": {
                    "type": "boolean",
                    "description": "Include adjacent headings",
                },
            },
            "required": ["chunk_id"],
        },
    },
    {
        "name": "outline",
        "description": "Get the heading structure of a Markdown file.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path"}},
            "required": ["path"],
        },
    },
    {
        "name": "index_paths",
        "description": "Index a set of paths into the in-process SQLite DB.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {"type": "array", "description": "Paths to index"},
            },
            "required": ["paths"],
        },
    },
    {
        "name": "refresh_index",
        "description": "Incrementally refresh the index for a set of paths.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {"type": "array", "description": "Paths to refresh"},
            },
            "required": ["paths"],
        },
    },
    {
        "name": "stats",
        "description": "Return document/chunk count and index metadata.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "grep_docs",
        "description": "Search Markdown chunks with a regex pattern.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern"},
                "paths": {"type": "array", "description": "Optional path filter"},
            },
            "required": ["pattern"],
        },
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Dispatch handlers
# ──────────────────────────────────────────────────────────────────────────────


async def _handle_search_docs(args: ToolArgs) -> str:
    return await _get_service().search_docs(SearchDocsRequest(**args))


async def _handle_get_chunk(args: ToolArgs) -> str:
    return await _get_service().get_chunk(GetChunkRequest(**args))


async def _handle_outline(args: ToolArgs) -> str:
    return await _get_service().outline(OutlineRequest(**args))


async def _handle_index_paths(args: ToolArgs) -> str:
    return await _get_service().index_paths(IndexPathsRequest(**args))


async def _handle_refresh_index(args: ToolArgs) -> str:
    return await _get_service().refresh_index(RefreshIndexRequest(**args))


async def _handle_stats(args: ToolArgs) -> str:
    return await _get_service().stats(StatsRequest(**args))


async def _handle_grep_docs(args: ToolArgs) -> str:
    return await _get_service().grep_docs(GrepDocsRequest(**args))


_DISPATCH_TABLE = {
    "search_docs": _handle_search_docs,
    "get_chunk": _handle_get_chunk,
    "outline": _handle_outline,
    "index_paths": _handle_index_paths,
    "refresh_index": _handle_refresh_index,
    "stats": _handle_stats,
    "grep_docs": _handle_grep_docs,
}


async def _dispatch_mdq_tool(name: str, args: ToolArgs) -> tuple[str, bool]:
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
    result, is_error = await _dispatch_mdq_tool(req.name, req.args)
    _audit_log(
        logger,
        session_id=session_id,
        request_id=request_id,
        action=req.name,
        target=str(req.args.get("query", req.args.get("path", "")))[:80],
        outcome="error" if is_error else "ok",
    )
    return CallToolResponse(result=result, is_error=is_error)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mdq-mcp"}


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

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        return await _dispatch_mdq_tool(name, args)


if __name__ == "__main__":
    import sys

    server = MdqMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
