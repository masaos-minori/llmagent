#!/usr/bin/env python3
"""
mcp/sqlite/server.py
SQLite read-only query MCP server (port 8011).

Provides an HTTP API via FastAPI for executing SELECT-only queries against
allowlisted SQLite databases.

Security:
  - Only SELECT statements are permitted; all other DML/DDL is rejected
  - Accessible DBs are restricted to the db_allowlist in sqlite_mcp_server.toml
  - PRAGMA query_only=ON is applied on every connection
  - Row count is capped at max_rows to prevent large data dumps
  - Optional Bearer-token auth via auth_token in sqlite_mcp_server.toml

Provided endpoints:
  GET  /v1/tools      MCP tool list
  POST /v1/call_tool  MCP standard tool dispatch
  GET  /health        Health check
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs, attach_auth_middleware, dispatch_tool
from mcp.sqlite.models import _get_cfg
from mcp.sqlite.service import _service

_cfg = _get_cfg()

app = FastAPI(
    title="sqlite-mcp",
    version="1.0.0",
    description="SQLite read-only query MCP server",
)

attach_auth_middleware(app, _cfg.get("auth_token", ""))


# ──────────────────────────────────────────────────────────────────────────────
# MCP tool definitions
# ──────────────────────────────────────────────────────────────────────────────

_MCP_TOOLS = [
    {
        "name": "query_sqlite",
        "description": (
            "Execute a read-only SELECT query against a named SQLite database. "
            "Only SELECT statements are permitted. "
            "Results are capped at max_rows (default: 100)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "db": {
                    "type": "string",
                    "description": "Database name (e.g., 'rag' or 'session')",
                },
                "sql": {
                    "type": "string",
                    "description": "SELECT query string (non-SELECT statements are rejected)",
                },
            },
            "required": ["db", "sql"],
        },
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_sqlite_tool(name: str, args: ToolArgs) -> tuple[str, bool]:
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in _MCP_TOOLS
        ]
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    result, is_error = await _dispatch_sqlite_tool(req.name, req.args)
    return CallToolResponse(result=result, is_error=is_error)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class SqliteMCPServer(MCPServer):
    """MCPServer subclass for sqlite-mcp."""

    server_name = "sqlite-mcp"
    server_version = "1.0.0"
    http_port = 8011
    app_module = "mcp.sqlite.server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        return await _dispatch_sqlite_tool(name, args)


if __name__ == "__main__":
    import sys

    server = SqliteMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
