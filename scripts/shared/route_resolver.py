#!/usr/bin/env python3
"""scripts/shared/route_resolver.py

Tool-name to server-key resolution for ToolExecutor.

`RuntimeToolRegistry` (populated from live `/v1/tools` discovery via
`ToolExecutor.set_runtime_registry()`) is the sole routing authority. When a tool is not
found there, `resolve()` either raises `ValueError` immediately (strict_mode) or logs a
warning and then raises. `ToolRegistry` is no longer consulted here.

Config `tool_names` is NOT a routing input; it is drift validation metadata only.
Live /v1/tools discovery is used for startup validation only, not routing.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from shared.runtime_tool_registry import RuntimeToolRegistry

logger = logging.getLogger(__name__)


class ToolRouteResolver:
    """Map tool_name → server_key using RuntimeToolRegistry as the sole routing authority.

    RuntimeToolRegistry is populated from live /v1/tools discovery. Raises ValueError
    when the tool is not found there.
    """

    def __init__(
        self,
        *,
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
                Note: if `strict_mode=True`, this warning is never emitted because
                `strict_mode=True` causes `resolve()` to raise `ValueError` directly
                via `_raise_strict_error()` before reaching the `warn_on_missing` check.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message. Also bypasses the `warn_on_missing` warning log
                entirely: when `strict_mode=True`, `resolve()` calls `_raise_strict_error()`
                (a `NoReturn` path) before ever reaching the `warn_on_missing` check, so
                both `strict_mode=True` and `strict_mode=False` always raise `ValueError`
                on an unresolved tool — the difference is in error-message wording only.
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        # RuntimeToolRegistry (sole routing authority).
        self._runtime_registry: RuntimeToolRegistry | None = runtime_registry
        self._warn_on_missing = warn_on_missing
        self._strict_mode = strict_mode

    def resolve(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not found in RuntimeToolRegistry; "
                "ensure MCP servers are healthy and discovery completed.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def _lookup_runtime_registry(self, tool_name: str) -> str | None:
        """Look up a tool in RuntimeToolRegistry; returns server key or None."""
        if self._runtime_registry is not None:
            return self._runtime_registry.resolve(tool_name)
        return None

    def set_runtime_registry(self, registry: RuntimeToolRegistry | None) -> None:
        """Replace the RuntimeToolRegistry consulted by resolve(), in place."""
        self._runtime_registry = registry

    def _raise_strict_error(self, tool_name: str) -> NoReturn:
        """Raise ValueError when strict_mode is enabled and no mapping found."""
        raise ValueError(
            f"ToolRouteResolver: tool {tool_name!r} not found in RuntimeToolRegistry "
            f"and strict_mode=True; ensure MCP servers are healthy and discovery completed"
        )
