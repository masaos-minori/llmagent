#!/usr/bin/env python3
"""mcp/server.py
Base class for MCP (Model Context Protocol) servers.
Provides HTTP launch logic shared by all MCP server scripts.

Tool dispatch helpers live in mcp/dispatch.py.
Audit log helpers live in mcp/audit.py.
"""

import asyncio
import dataclasses
import logging
import sys
import uuid
from typing import Any

import orjson

# Library module: use standard getLogger without a dedicated log file.
logger = logging.getLogger(__name__)

# Type alias for MCP tool argument dictionaries.
# Pydantic models in each server validate the actual structure at runtime.
ToolArgs = dict[str, Any]

# Maximum response size returned to the agent; larger responses are truncated.
MCP_MAX_RESPONSE_BYTES: int = 512 * 1024


@dataclasses.dataclass(frozen=True)
class TruncationResult:
    """Metadata returned by _truncate_with_meta()."""

    text: str
    truncated: bool
    total_bytes: int


def _truncate_with_meta(
    text: str, max_bytes: int = MCP_MAX_RESPONSE_BYTES
) -> TruncationResult:
    """Return TruncationResult with truncated text and metadata."""
    encoded = text.encode("utf-8")
    total = len(encoded)
    if total <= max_bytes:
        return TruncationResult(text=text, truncated=False, total_bytes=total)
    shown = encoded[:max_bytes].decode("utf-8", errors="ignore")
    truncated_text = (
        shown + f"\n[TRUNCATED: {total:,} bytes total, showing {max_bytes:,} bytes]"
    )
    return TruncationResult(text=truncated_text, truncated=True, total_bytes=total)


def attach_auth_middleware(app: Any, token: str) -> None:
    """Register Bearer-token auth + X-Request-Id middleware on a FastAPI app.

    When token is non-empty, requests without a matching Authorization header
    receive a 401 response.  When token is empty, auth is skipped and the
    middleware only injects the X-Request-Id response header.
    """
    from fastapi import (
        Request,  # noqa: PLC0415 — lazy: fastapi not needed for stdio-only servers
    )
    from fastapi.responses import (
        JSONResponse,  # noqa: PLC0415 — lazy: fastapi not needed for stdio-only servers
    )

    @app.middleware("http")
    async def _auth_middleware(request: Request, call_next):  # noqa: ANN001,ANN202 — FastAPI middleware protocol
        req_id = str(uuid.uuid4())
        request.state.request_id = req_id
        if token:
            auth = request.headers.get("Authorization", "")
            if auth != f"Bearer {token}":
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
        response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        return response


class MCPServer:
    """Base class for MCP servers.

    Subclasses declare server_name, server_version, http_host, http_port,
    app_module, and mcp_tools as class attributes, and override dispatch().

    run_http() starts the HTTP server via uvicorn.
    """

    server_name: str  # e.g. "web-search-mcp"
    server_version: str  # e.g. "3.0.0"
    http_host: str = "127.0.0.1"
    http_port: int  # e.g. 8004
    app_module: str  # uvicorn target, e.g. "WebSearchMCPServer:app"
    mcp_tools: list[
        dict[str, Any]
    ]  # tool definitions (retained for subclass reference)

    async def dispatch(self, name: str, args: ToolArgs) -> tuple[str, bool]:
        """Handle a tools/call request. Subclasses must override this."""
        raise NotImplementedError(f"{type(self).__name__}.dispatch is not implemented")

    def list_tools(self) -> list[str]:
        """Return the tool names served by this instance.

        Used by the __list_tools__ introspection RPC (stdio mode) and by
        check_tool_definitions() in repl_health.py.
        """
        return [t["name"] for t in getattr(self, "mcp_tools", [])]

    def health(self) -> dict[str, str]:
        """Return a health status dict for HTTP server diagnostics.

        HTTP subclasses may override; stdio subclasses use process liveness instead.
        """
        return {"status": "ok"}

    def run_http(self) -> None:
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
        Response line: {"id": <int>, "result": <str>, "is_error": <bool>,
                        "truncated": <bool>, "total_bytes": <int>}

        The reserved name "__list_tools__" returns the server's tool list without
        going through dispatch(), enabling transport-independent tool introspection.

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
            truncated = False
            total_bytes = 0
            try:
                req = orjson.loads(line)
                req_id = int(req.get("id", 0))
                name = str(req.get("name", ""))
                if name == "__list_tools__":
                    # Reserved introspection call — return tool list as JSON string
                    result = orjson.dumps({"tools": self.list_tools()}).decode()
                    is_error = False
                else:
                    raw_result, is_error = await self.dispatch(
                        name,
                        dict(req.get("args", {})),
                    )
                    tr = _truncate_with_meta(raw_result)
                    result = tr.text
                    truncated = tr.truncated
                    total_bytes = tr.total_bytes
            except orjson.JSONDecodeError as e:
                logger.error(f"run_stdio JSON decode error: {e}")
                result = f"JSON decode error: {e}"
                is_error = True
            except Exception as e:
                # Last-resort handler: stdio transport must always write a response.
                logger.error(f"run_stdio unexpected error: {e}")
                result = f"Internal server error: {e}"
                is_error = True

            resp = orjson.dumps(
                {
                    "id": req_id,
                    "result": result,
                    "is_error": is_error,
                    "truncated": truncated,
                    "total_bytes": total_bytes,
                },
            ).decode()
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
