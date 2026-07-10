"""mcp_servers/dispatch.py
Tool dispatch helpers extracted from mcp/server.py.
Kept separate so MCP servers can import dispatch_tool without pulling in the
full MCPServer base class.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

ToolArgs = dict[str, Any]


@dataclass(frozen=True)
class DispatchResult:
    """Typed result from MCPServer.dispatch() and dispatch_tool()."""

    output: str
    is_error: bool


async def dispatch_tool(
    table: Mapping[str, Callable[[ToolArgs], Awaitable[str]]],
    name: str,
    args: ToolArgs,
) -> DispatchResult:
    """Route a tool call through a dispatch table.

    Returns a DispatchResult with output text and is_error flag.
    Raises for non-ValueError handler exceptions (caller is responsible for transport-level handling).
    ValueError from handlers is converted to an error result (user-input/validation errors).
    Unknown tool and empty name return error results without raising.
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

    try:
        result = await handler(args)
        return DispatchResult(output=result, is_error=False)
    except ValueError as e:
        # Validation / user-input errors: return as tool error, not server fault
        logger.warning("Tool '%s' validation error: %s", name, e)
        return DispatchResult(output=f"Validation error: {e}", is_error=True)
    # All other exceptions (RuntimeError, IOError, HTTPException, etc.) propagate to caller.
