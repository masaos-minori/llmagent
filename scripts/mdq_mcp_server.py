#!/usr/bin/env python3
"""
mcp/mdq/server.py
Markdown Context Compression Engine MCP Server.

This server provides tools for searching, retrieving, and outlining Markdown
documents with heading-level granularity.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
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
from mcp.server import MCPServer

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# MCP Server Implementation
# ──────────────────────────────────────────────────────────────────────────────


class MdqMCPServer(MCPServer):
    """Markdown Context Compression Engine MCP Server."""

    server_name = "mdq-mcp"
    server_version = "0.1.0"
    http_port = 8013
    app_module = "mcp.mdq.server:app"

    def __init__(self) -> None:
        self._service = MdqService()
        # Define the tools this server provides
        self.mcp_tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_docs",
                    "description": "Search indexed Markdown sections before reading full files.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer"},
                            "mode": {"type": "string"},
                            "path_prefix": {"type": "string"},
                            "tag_filter": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "heading_prefix": {"type": "string"},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_chunk",
                    "description": "Get a Markdown chunk by chunk_id.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chunk_id": {"type": "integer"},
                            "with_neighbors": {"type": "boolean"},
                        },
                        "required": ["chunk_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "outline",
                    "description": "Get Markdown heading outline for a file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "index_paths",
                    "description": "Index a target directory or file set.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "paths": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["paths"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "refresh_index",
                    "description": "Re-index only incremental updates.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "paths": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["paths"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "stats",
                    "description": "Return index statistics.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "grep_docs",
                    "description": "Search Markdown chunks with regex priority.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string"},
                            "paths": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["pattern"],
                    },
                },
            },
        ]

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        """Dispatch tool calls to the appropriate handler."""
        try:
            if name == "search_docs":
                result = await self._service.search_docs(SearchDocsRequest(**args))
                return result, False
            elif name == "get_chunk":
                result = await self._service.get_chunk(GetChunkRequest(**args))
                return result, False
            elif name == "outline":
                result = await self._service.outline(OutlineRequest(**args))
                return result, False
            elif name == "index_paths":
                result = await self._service.index_paths(IndexPathsRequest(**args))
                return result, False
            elif name == "refresh_index":
                result = await self._service.refresh_index(RefreshIndexRequest(**args))
                return result, False
            elif name == "stats":
                result = await self._service.stats(StatsRequest(**args))
                return result, False
            elif name == "grep_docs":
                result = await self._service.grep_docs(GrepDocsRequest(**args))
                return result, False
            else:
                return f"Unknown tool: {name}", True
        except Exception as e:
            logger.error(f"Error in dispatch: {e}", exc_info=True)
            return f"Tool error: {e}", True


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI Application
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Markdown Context Compression Engine MCP Server",
    version="0.1.0",
    description="MCP server for searching and retrieving Markdown documents with heading-level granularity.",
)

server = MdqMCPServer()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return server.health()


@app.get("/v1/tools")
async def list_tools():
    """List available tools."""
    return {"tools": server.list_tools()}


@app.post("/v1/call_tool")
async def call_tool(request: CallToolRequest):
    """Call a tool by name with arguments."""
    result_text, is_error = await server.dispatch(request.name, request.args)
    return CallToolResponse(result=result_text, is_error=is_error)


if __name__ == "__main__":
    server.run()
