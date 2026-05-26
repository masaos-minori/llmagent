#!/usr/bin/env python3
"""
mcp_server.py
Base class for MCP (Model Context Protocol) servers.
Provides HTTP launch logic shared by all MCP server scripts.
"""

import asyncio
import json
import logging
import sys
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

# Library module: use standard getLogger without a dedicated log file.
logger = logging.getLogger(__name__)

# Type alias for MCP tool argument dictionaries.
# Pydantic models in each server validate the actual structure at runtime.
ToolArgs = dict[str, Any]


async def dispatch_tool(
    table: Mapping[str, Callable[[ToolArgs], Awaitable[str]]],
    name: str,
    args: ToolArgs,
) -> tuple[str, bool]:
    """
    Route a tool call through a dispatch table with standard error handling.

    Returns (result_text, is_error).
    Duck-types FastAPI HTTPException to avoid importing FastAPI in this module,
    keeping the base class free of server-framework dependencies.
    """
    # Validate inputs before dispatching.
    if not isinstance(name, str) or not name.strip():
        logger.warning("dispatch_tool called with empty tool name")
        return "Tool name must be a non-empty string", True

    handler = table.get(name)
    if handler is None:
        logger.warning(f"Unknown tool requested: {name}")
        return f"Unknown tool: {name}", True

    try:
        result = await handler(args)
        return result, False
    except Exception as e:
        return _handle_tool_exception(name, e)


def _handle_tool_exception(name: str, e: Exception) -> tuple[str, bool]:
    """
    Classify and log a tool handler exception; return (message, is_error=True).

    Separating this from dispatch_tool keeps each function under ~30 lines.
    """
    # Duck-type FastAPI HTTPException to avoid importing it here.
    is_http_exc = hasattr(e, "status_code") and hasattr(e, "detail")
    if is_http_exc:
        status = e.status_code  # type: ignore[attr-defined]
        detail = e.detail  # type: ignore[attr-defined]
        logger.error(f"Tool '{name}' raised HTTP error {status}: {detail}")
        return f"HTTP error ({status}): {detail}", True

    logger.error(f"Tool '{name}' raised unexpected error: {e}")
    return f"Tool error: {e}", True


class MCPServer:
    """
    Base class for MCP servers.

    Subclasses declare server_name, server_version, http_host, http_port,
    app_module, and mcp_tools as class attributes, and override dispatch().

    run() starts the HTTP server via uvicorn.
    """

    server_name: str  # e.g. "web-search-mcp"
    server_version: str  # e.g. "3.0.0"
    http_host: str = "127.0.0.1"
    http_port: int  # e.g. 8004
    app_module: str  # uvicorn target, e.g. "WebSearchMCPServer:app"
    mcp_tools: list[dict]  # tool definitions (retained for subclass reference)

    async def dispatch(self, name: str, args: dict) -> tuple[str, bool]:
        """Handle a tools/call request. Subclasses must override this."""
        raise NotImplementedError(f"{type(self).__name__}.dispatch is not implemented")

    def run(self) -> None:
        """Launch the HTTP server via uvicorn."""
        import uvicorn

        uvicorn.run(
            self.app_module,
            host=self.http_host,
            port=self.http_port,
            log_level="info",
        )

    async def run_stdio(self) -> None:
        """Serve tool calls over stdin/stdout using line-delimited JSON-RPC.

        Reads one JSON object per line from stdin, dispatches via self.dispatch(),
        and writes one JSON object per line to stdout.  All log output goes to
        stderr so that stdout remains a clean communication channel.

        Request  line: {"id": <int>, "name": <str>, "args": {}}
        Response line: {"id": <int>, "result": <str>, "is_error": <bool>}

        The loop exits cleanly on stdin EOF.
        """
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        # Connect the raw stdin buffer (not the text wrapper) to the StreamReader.
        await loop.connect_read_pipe(lambda: protocol, sys.stdin.buffer)

        while True:
            line = await reader.readline()
            if not line:
                break  # stdin EOF — client closed the pipe

            req_id = 0
            try:
                req = json.loads(line)
                req_id = int(req.get("id", 0))
                result, is_error = await self.dispatch(
                    str(req.get("name", "")),
                    dict(req.get("args", {})),
                )
            except Exception as e:
                logger.error(f"run_stdio dispatch error: {e}")
                result = f"Internal server error: {e}"
                is_error = True

            resp = json.dumps({"id": req_id, "result": result, "is_error": is_error})
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
