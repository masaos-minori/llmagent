#!/usr/bin/env python3
"""mcp_servers/server.py

Base class for MCP (Model Context Protocol) servers.
Provides HTTP launch logic shared by all MCP server scripts.

Tool dispatch helpers live in mcp/dispatch.py.
Audit log helpers live in mcp/audit.py.
"""

from __future__ import annotations

import dataclasses
import logging
import time
import uuid
from collections.abc import Callable, Sequence
from typing import Any, Protocol

from mcp_servers.dispatch import DispatchResult
from mcp_servers.health_response import HEALTH_STATUS_DEGRADED, HEALTH_STATUS_OK

# Library module: use standard getLogger without a dedicated log file.
logger = logging.getLogger(__name__)


# Type alias for MCP tool argument dictionaries.
# Pydantic models in each server validate the actual structure at runtime.
ToolArgs = dict[str, Any]

# Maximum response size returned to the agent; larger responses are truncated.
MCP_MAX_RESPONSE_BYTES: int = 512 * 1024

# Schema version advertised in each server's /v1/tools response; bump when the
# tool-schema shape changes in a way that matters to Agent-side discovery/validation.
MCP_TOOL_SCHEMA_VERSION: str = "1.0"


class _FastAPIApp(Protocol):
    """Minimal FastAPI app interface for middleware attachment."""

    def middleware(self, type_: str) -> Callable[[Callable], Callable]:
        """Attach a middleware function to the FastAPI application."""
        ...


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


def attach_auth_middleware(app: _FastAPIApp, token: str) -> None:
    """Register Bearer-token auth + X-Request-Id middleware on a FastAPI app.

    When token is non-empty, requests without a matching Authorization header
    receive a 401 response.  When token is empty, auth is skipped and the
    middleware only injects the X-Request-Id response header.
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.middleware("http")
    async def _auth_middleware(request: Request, call_next):  # noqa: ANN001,ANN202 — FastAPI middleware protocol
        """Authenticate requests by validating Bearer token header."""
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
    own_config_file: str = ""  # e.g. "web_search_mcp_server.toml"; set by subclasses
    mcp_tools: list[
        dict[str, Any]
    ]  # tool definitions (retained for subclass reference)

    async def dispatch(self, name: str, args: ToolArgs) -> DispatchResult:
        """Handle a tools/call request. Subclasses must override this."""
        raise NotImplementedError(f"{type(self).__name__}.dispatch is not implemented")

    def list_tools(self) -> list[str]:
        """Return the tool names served by this instance.

        Used by check_tool_definitions() in repl_health.py.
        """
        return [t["name"] for t in getattr(self, "mcp_tools", [])]

    def list_tools_with_server_key(self) -> list[dict[str, Any]]:
        """Return tool metadata including server_key for live discovery-based routing.

        Each tool dict includes: name, description, inputSchema, server_key.
        Used by /v1/tools endpoint and startup tool discovery.
        """
        server_key = getattr(self, "server_key", type(self).__name__)
        tools = getattr(self, "mcp_tools", [])
        return [{**t, "server_key": server_key} for t in tools]


def build_tools_response(tools: Sequence[Any], server_key: str) -> dict[str, Any]:
    """Build the /v1/tools response dict: schema_version + per-tool server_key tagging.

    Callable directly from each server's module-level FastAPI route handler (no MCPServer
    instance required) — see docstring on MCP_TOOL_SCHEMA_VERSION for the versioning contract.
    """
    return {
        "schema_version": MCP_TOOL_SCHEMA_VERSION,
        "tools": [{**t, "server_key": server_key} for t in tools],
    }

    def health(self) -> tuple[dict[str, object], int]:
        """Return a health status dict and HTTP status code for HTTP server diagnostics.

        Canonical response shape:
          status:                   "ok" (all deps healthy) or "degraded" (any dep failed)
          ready:                    True when status="ok", False when status="degraded"
          liveness:                 True if the server process is alive and can accept requests;
                                    False if it cannot (fatal internal state).
          restart_recommended:      True signals the watchdog that a process restart may resolve
                                    the failure; False means restart will not help.
          operator_action_required: True means human intervention is needed (missing credentials,
                                    missing binary, etc.).
          dependencies:             dict of dep_name -> error_message; empty when healthy
          details:                  server-specific supplementary info (may be empty)

        HTTP status code: 200 when ready=True, 503 when ready=False.

        Watchdog restart policy is gated on restart_recommended;
        operator_action_required=True produces a warning-only log.
        """
        deps: dict[str, str] = {}
        ready = len(deps) == 0
        status_code = 200 if ready else 503
        return {
            "status": HEALTH_STATUS_OK if ready else HEALTH_STATUS_DEGRADED,
            "ready": ready,
            "liveness": True,
            "restart_recommended": False,
            "operator_action_required": False,
            "dependencies": deps,
            "details": {},
        }, status_code

    def _ensure_error_tracking(self) -> None:
        """Ensure per-instance error tracking lists are initialized (lazy init)."""
        if not hasattr(self, "_tool_error_timestamps"):
            object.__setattr__(self, "_tool_error_timestamps", [])
            object.__setattr__(self, "_error_window_sec", 300.0)
            object.__setattr__(self, "_error_threshold", 3)

    def _record_tool_error(self, tool_name: str) -> None:
        """Record a tool error timestamp; warn if repeated failures exceed threshold."""
        self._ensure_error_tracking()
        now = time.time()
        cutoff = now - self._error_window_sec
        timestamps = [t for t in self._tool_error_timestamps if t > cutoff]
        object.__setattr__(self, "_tool_error_timestamps", timestamps)
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

        if self.own_config_file:
            from shared.config_loader import ConfigLoader

            ConfigLoader.restrict_to(self.own_config_file)

        uvicorn.run(
            self.app_module,
            host=self.http_host,
            port=self.http_port,
            log_level="info",
        )
