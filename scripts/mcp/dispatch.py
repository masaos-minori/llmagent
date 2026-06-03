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


def _handle_tool_exception(name: str, e: Exception) -> tuple[str, bool]:
    """Classify and log a tool handler exception; return (message, is_error=True)."""
    # Duck-type FastAPI HTTPException to avoid importing it here.
    is_http_exc = hasattr(e, "status_code") and hasattr(e, "detail")
    if is_http_exc:
        status = e.status_code  # type: ignore[attr-defined]
        detail = e.detail  # type: ignore[attr-defined]
        logger.error(f"Tool '{name}' raised HTTP error {status}: {detail}")
        return f"HTTP error ({status}): {detail}", True

    logger.error(f"Tool '{name}' raised unexpected error: {e}")
    return f"Tool error: {e}", True


async def dispatch_tool(
    table: Mapping[str, Callable[[ToolArgs], Awaitable[str]]],
    name: str,
    args: ToolArgs,
) -> tuple[str, bool]:
    """Route a tool call through a dispatch table with standard error handling.

    Returns (result_text, is_error).
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
    except Exception as e:
        return _handle_tool_exception(name, e)
