"""mcp/dispatch.py
Tool dispatch helpers extracted from mcp/server.py.
Kept separate so MCP servers can import dispatch_tool without pulling in the
full MCPServer base class.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

logger = logging.getLogger(__name__)

ToolArgs = dict[str, Any]


async def dispatch_tool(
    table: Mapping[str, Callable[[ToolArgs], Awaitable[str]]],
    name: str,
    args: ToolArgs,
) -> tuple[str, bool]:
    """Route a tool call through a dispatch table.

    Returns (result_text, is_error).
    Raises for non-ValueError handler exceptions (caller is responsible for transport-level handling).
    ValueError from handlers is converted to an error result (user-input/validation errors).
    Unknown tool and empty name return error results without raising.
    """
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
    except ValueError as e:
        # Validation / user-input errors: return as tool error, not server fault
        logger.warning(f"Tool '{name}' validation error: {e}")
        return f"Validation error: {e}", True
    # All other exceptions (RuntimeError, IOError, HTTPException, etc.) propagate to caller.
