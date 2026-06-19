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
import sqlite3
import sys
import time
import uuid
from typing import Any

import orjson
from shared.json_utils import dumps as _json_dumps

from mcp.dispatch import DispatchResult

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
    actual_visible_bytes: int = 0


def _truncate_with_meta(
    text: str, max_bytes: int = MCP_MAX_RESPONSE_BYTES
) -> TruncationResult:
    """Return TruncationResult with truncated text and metadata."""
    encoded = text.encode("utf-8")
    total = len(encoded)
    if total <= max_bytes:
        return TruncationResult(
            text=text, truncated=False, total_bytes=total, actual_visible_bytes=total
        )
    shown = encoded[:max_bytes].decode("utf-8", errors="ignore")
    actual_visible = len(shown.encode("utf-8"))
    truncated_text = (
        shown
        + f"\n[TRUNCATED: {total:,} bytes total, showing {actual_visible:,} bytes]"
    )
    return TruncationResult(
        text=truncated_text,
        truncated=True,
        total_bytes=total,
        actual_visible_bytes=actual_visible,
    )


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

    async def dispatch(self, name: str, args: ToolArgs) -> DispatchResult:
        """Handle a tools/call request. Subclasses must override this."""
        raise NotImplementedError(f"{type(self).__name__}.dispatch is not implemented")

    def list_tools(self) -> list[str]:
        """Return the tool names served by this instance.

        Used by the __list_tools__ introspection RPC (stdio mode) and by
        check_tool_definitions() in repl_health.py.
        """
        return [t["name"] for t in getattr(self, "mcp_tools", [])]

    def list_tools_with_server_key(self) -> list[dict[str, object]]:
        """Return tool metadata including server_key for live discovery-based routing.

        Each tool dict includes: name, description, inputSchema, server_key.
        Used by /v1/tools endpoint and startup tool discovery.
        """
        server_key = getattr(self, "server_key", type(self).__name__)
        tools = getattr(self, "mcp_tools", [])
        return [{**t, "server_key": server_key} for t in tools]

    def health(self) -> dict[str, object]:
        """Return a health status dict for HTTP server diagnostics.

        HTTP subclasses may override; stdio subclasses use process liveness instead.
        Returns a standardized shape: {status, ready, dependencies, details}.
        """
        deps: dict[str, str] = {}
        ready = len(deps) == 0
        return {
            "status": "ok",
            "ready": ready,
            "dependencies": deps,
            "details": {},
        }

    def _ensure_error_tracking(self) -> None:
        """Ensure per-instance error tracking lists are initialized (lazy init)."""
        if not hasattr(self, "_tool_error_timestamps"):
            self._tool_error_timestamps: list[float] = []
            self._error_window_sec: float = 300.0
            self._error_threshold: int = 3

    def _record_tool_error(self, tool_name: str) -> None:
        """Record a tool error timestamp; warn if repeated failures exceed threshold."""
        self._ensure_error_tracking()
        now = time.time()
        cutoff = now - self._error_window_sec
        self._tool_error_timestamps = [
            t for t in self._tool_error_timestamps if t > cutoff
        ]
        self._tool_error_timestamps.append(now)
        if len(self._tool_error_timestamps) >= self._error_threshold:
            logger.warning(
                "Repeated tool failures detected: %s failed %d times in %.0fs window",
                tool_name,
                len(self._tool_error_timestamps),
                self._error_window_sec,
            )

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
            actual_visible_bytes = 0
            try:
                req = orjson.loads(line)
                req_id = int(req.get("id", 0))
                name_raw = req.get("name", "")
                if not isinstance(name_raw, str):
                    raise ValueError(
                        f"Request 'name' must be str, got {type(name_raw).__name__}"
                    )
                name = name_raw
                if name == "__list_tools__":
                    # Reserved introspection call — return tool list as JSON string
                    result = _json_dumps({"tools": self.list_tools()})
                    is_error = False
                else:
                    dispatch_result = await self.dispatch(
                        name,
                        dict(req.get("args", {})),
                    )
                    tr = _truncate_with_meta(dispatch_result.output)
                    is_error = dispatch_result.is_error
                    result = tr.text
                    truncated = tr.truncated
                    total_bytes = tr.total_bytes
                    actual_visible_bytes = tr.actual_visible_bytes
            except orjson.JSONDecodeError as e:
                logger.error("run_stdio JSON decode error: %s", e)
                result = f"JSON decode error: {e}"
                is_error = True
            except (ValueError, OSError) as e:
                logger.error("run_stdio expected error: %s", e)
                result = f"Error: {e}"
                is_error = True
            except RuntimeError as e:
                logger.error("run_stdio runtime error: %s", e)
                result = f"Runtime error: {e}"
                is_error = True
            except (
                TypeError,
                AttributeError,
                KeyError,
                sqlite3.OperationalError,
                sqlite3.DatabaseError,
            ) as e:
                # Last-resort handler: stdio transport must always write a response.
                logger.error("run_stdio unexpected error: %s", e)
                result = f"Internal server error: {e}"
                is_error = True

            if is_error and name != "__list_tools__":
                self._record_tool_error(name)

            resp = _json_dumps(
                {
                    "id": req_id,
                    "result": result,
                    "is_error": is_error,
                    "truncated": truncated,
                    "total_bytes": total_bytes,
                    "actual_visible_bytes": actual_visible_bytes,
                },
            )
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
