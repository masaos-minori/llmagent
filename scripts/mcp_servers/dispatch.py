"""scripts/mcp_servers/dispatch.py

Tool dispatch helpers extracted from mcp/server.py.
Kept separate so MCP servers can import dispatch_tool without pulling in the
full MCPServer base class.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

from shared.tool_constants import (
    CICD_WRITE_TOOLS,
    DELETE_TOOLS,
    GIT_WRITE_TOOLS,
    GITHUB_DANGEROUS_TOOLS,
    GITHUB_WRITE_TOOLS,
    RAG_WRITE_TOOLS,
    SHELL_TOOLS,
    WRITE_TOOLS,
)

from mcp_servers.models import CallToolResponse
from scripts.shared import tool_constants  # side-effecting classification

logger = logging.getLogger(__name__)

ToolArgs = dict[str, Any]

_duplicate_cache: dict[str, DispatchResult] = {}

_write_tools = (
    set(WRITE_TOOLS)
    | set(DELETE_TOOLS)
    | set(GIT_WRITE_TOOLS)
    | set(RAG_WRITE_TOOLS)
    | set(CICD_WRITE_TOOLS)
    | set(GITHUB_WRITE_TOOLS)
    | set(GITHUB_DANGEROUS_TOOLS)
    | set(SHELL_TOOLS)
)




@dataclass(frozen=True)
class DispatchResult:
    """Typed result from MCPServer.dispatch() and dispatch_tool()."""

    output: str
    is_error: bool

    @property
    def outcome(self) -> str:
        """Return 'error' if is_error, otherwise 'ok'."""
        return "error" if self.is_error else "ok"


DuplicateCacheKey = str
DuplicateCacheValue = DispatchResult

_duplicate_cache: dict[DuplicateCacheKey, DuplicateCacheValue] = {}


def _is_side_effecting(tool_name: str) -> bool:
    """Check if a tool name belongs to the write/dangerous/exec sets."""
    all_write_tools: set[str] = set()
    for s in (
        tool_constants.WRITE_TOOLS,
        tool_constants.DELETE_TOOLS,
        tool_constants.GIT_WRITE_TOOLS,
        tool_constants.RAG_WRITE_TOOLS,
        tool_constants.CICD_WRITE_TOOLS,
        tool_constants.GITHUB_WRITE_TOOLS,
        tool_constants.GITHUB_DANGEROUS_TOOLS,
        tool_constants.SHELL_TOOLS,
    ):
        all_write_tools.update(s)
    return tool_name in all_write_tools


def _to_call_tool_response(r: DispatchResult) -> CallToolResponse:
    """Convert a DispatchResult into a CallToolResponse."""
    return CallToolResponse(result=r.output, is_error=r.is_error)


async def dispatch_tool(
    table: Mapping[str, Callable[[ToolArgs], Awaitable[str]]],
    name: str,
    args: ToolArgs,
    idempotency_key: str | None = None,
) -> DispatchResult:
    """Route a tool call through a dispatch table.

    Returns a DispatchResult with output text and is_error flag.
    Raises for non-ValueError handler exceptions (caller is responsible for transport-level handling).
    ValueError from handlers is converted to an error result (user-input/validation errors).
    Unknown tool and empty name return error results without raising.
    If idempotency_key is provided and name is side-effecting, checks for duplicates.
    """
    if not isinstance(name, str) or not name.strip():
        logger.warning("dispatch_tool called with empty tool name")
        return DispatchResult(
            output="Tool name must be a non-empty string", is_error=True
        )

    handler = table.get(name)
    if handler is None:
        logger.warning("Unknown tool requested: %s", name)
        return DispatchResult(output=f"Unknown tool: {name}", is_error=True)

    # duplicate-check for side-effecting tools
    if idempotency_key is not None and _is_side_effecting(name):
        cached = _duplicate_cache.get(idempotency_key)
        if cached is not None:
            logger.info(
                "Duplicate tool call detected: %s (key=%s)", name, idempotency_key
            )
            return cached

    try:
        result = await handler(args)
        dispatched_result = DispatchResult(output=result, is_error=False)
        # cache the result for deduplication
        if idempotency_key is not None and _is_side_effecting(name):
            _duplicate_cache[idempotency_key] = dispatched_result
        return dispatched_result
    except ValueError as e:
        logger.warning("Tool '%s' validation error: %s", name, e)
        error_result = DispatchResult(output=f"Validation error: {e}", is_error=True)
        # cache the error result for deduplication
        if idempotency_key is not None and _is_side_effecting(name):
            _duplicate_cache[idempotency_key] = error_result
        return error_result
    # All other exceptions (RuntimeError, IOError, HTTPException, etc.) propagate to caller.
