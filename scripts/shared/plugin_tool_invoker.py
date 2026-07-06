#!/usr/bin/env python3
"""shared/plugin_tool_invoker.py — Plugin tool execution layer."""

import logging
from typing import Any

from shared import plugin_registry
from shared.transport_dto import ToolCallResult

logger = logging.getLogger(__name__)

_PLUGIN_RESULT_TUPLE_LENGTH = 2


class PluginToolInvoker:
    """Executes plugin tools registered via plugin_registry.register_tool().

    Returns None if no plugin tool is registered for the given name.
    Converts plugin exceptions to ToolCallResult(is_error=True) to keep errors local.
    Performs defensive runtime validation of return value contract even though
    registration-time annotation checks are canonical.
    """

    async def try_execute(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult | None:
        """Execute a plugin tool; return None if not a plugin tool."""
        plugin_fn = plugin_registry.get_tool(tool_name)
        if plugin_fn is None:
            return None
        try:
            result_raw = await plugin_fn(args)
        except Exception as e:  # noqa: BLE001 — plugin errors must not propagate
            msg = f"[plugin error] {tool_name}: {e}"
            logger.error(msg)
            return ToolCallResult(
                output=msg,
                is_error=True,
                request_id="",
                server_key="",
                error_type="tool",
            )
        try:
            if (
                not isinstance(result_raw, tuple)
                or len(result_raw) != _PLUGIN_RESULT_TUPLE_LENGTH
            ):
                raise ValueError(
                    f"Plugin tool {tool_name!r} must return exactly tuple[str, bool]"
                    f" (2 elements), got {type(result_raw).__name__}"
                    f" with len={len(result_raw) if isinstance(result_raw, tuple) else 'N/A'}"
                )
            output, is_error = result_raw[0], result_raw[1]
            if not isinstance(output, str):
                raise TypeError(
                    f"Plugin {tool_name!r}: output must be str, got {type(output).__name__}"
                )
            if not isinstance(is_error, bool):
                raise TypeError(f"Plugin {tool_name!r}: is_error must be bool")
        except (ValueError, TypeError) as contract_err:
            msg = f"[plugin contract violation] {tool_name}: {contract_err}"
            logger.error(msg)
            return ToolCallResult(
                output=msg,
                is_error=True,
                request_id="",
                server_key="",
                error_type="plugin_contract",
            )
        return ToolCallResult(
            output=output,
            is_error=is_error,
            request_id="",
            server_key="",
            error_type="tool" if is_error else "",
        )
