#!/usr/bin/env python3
"""shell_mcp_server.py
MCP server for sandboxed shell command execution (port 8009).

Provides an HTTP API via FastAPI for executing whitelisted shell commands.
Security:
  - argv[0] must be in the configured command allowlist
  - cwd must be under shell_cwd_allowed_dirs
  - Resource limits applied via setrlimit in child process
  - All executions are audit-logged to /opt/llm/logs/shell_audit.log
  - Service runs as llm-agent (non-root) OS user

Provided endpoints:
  POST /shell_run   Execute a sandboxed shell command
  GET  /health      Health check
"""

import time
from typing import Any

from fastapi import FastAPI
from shared.formatters import fmt_kvlog
from shared.logger import Logger

from mcp.models import CallToolRequest, CallToolResponse
from mcp.server import MCPServer, ToolArgs, dispatch_tool
from mcp.shell.models import ShellRunRequest, ShellRunResponse
from mcp.shell.service import _service

logger = Logger(__name__, "/opt/llm/logs/shell-mcp.log")

app = FastAPI(
    title="shell-mcp",
    version="1.0.0",
    description="MCP server for sandboxed shell command execution",
)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@app.post("/shell_run", response_model=ShellRunResponse)
async def shell_run(req: ShellRunRequest) -> ShellRunResponse:
    t0 = time.perf_counter()
    result = await _service.run_command(req)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "shell_run",
            cmd=req.command[:80],
            exit=result.exit_code,
            timed_out=result.timed_out,
            truncated=result.truncated,
            ms=f"{ms:.0f}",
        ),
    )
    return result


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# MCP tool definitions
# ──────────────────────────────────────────────────────────────────────────────

_MCP_TOOLS = [
    {
        "name": "shell_run",
        "description": (
            "Execute a sandboxed shell command. "
            "argv[0] must be in the configured allowlist. "
            "cwd must be under an allowed directory."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command string (argv[0] must be in allowlist)",
                },
                "timeout_sec": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30, max: server-configured)",
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory (must be under allowed dirs)",
                },
                "env": {
                    "type": "object",
                    "description": "Additional environment variables to merge",
                },
                "max_output_kb": {
                    "type": "integer",
                    "description": "Output size limit in KB (default: 512)",
                },
            },
            "required": ["command"],
        },
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Tool dispatch and unified call endpoint
# ──────────────────────────────────────────────────────────────────────────────


async def _dispatch_shell_tool(name: str, args: ToolArgs) -> tuple[str, bool]:
    return await dispatch_tool(_service.get_dispatch_table(), name, args)


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in _MCP_TOOLS
        ],
    }


@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest) -> CallToolResponse:
    result, is_error = await _dispatch_shell_tool(req.name, req.args)
    return CallToolResponse(result=result, is_error=is_error)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


class ShellMCPServer(MCPServer):
    """MCPServer subclass for shell-mcp."""

    server_name = "shell-mcp"
    server_version = "1.0.0"
    http_port = 8009
    app_module = "shell_mcp_server:app"
    mcp_tools = _MCP_TOOLS

    async def dispatch(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        return await _dispatch_shell_tool(name, args)


if __name__ == "__main__":
    import sys

    server = ShellMCPServer()
    if "--stdio" in sys.argv:
        import asyncio

        asyncio.run(server.run_stdio())
    else:
        server.run_http()
