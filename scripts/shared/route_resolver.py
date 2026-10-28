#!/usr/bin/env python3
"""scripts/shared/route_resolver.py

Tool-name to server-key resolution for ToolExecutor.

`RuntimeToolRegistry` (populated from live `/v1/tools` discovery via
`ToolExecutor.set_runtime_registry()`) is the sole routing authority. When a tool is not
found there, `resolve()` raises `ToolRoutingError` (a `ValueError` subclass) carrying a
`kind`: `not_ready` when no registry is wired, `posture_excluded` / `server_unavailable`
when the registry dropped the tool, and `unknown_tool` otherwise.
`ToolRegistry` is no longer consulted here.

Config `tool_names` is NOT a routing input; it is drift validation metadata only.
Live /v1/tools discovery is used for startup validation only, not routing.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.runtime_tool_registry import RuntimeToolRegistry

logger = logging.getLogger(__name__)


class ToolRoutingError(ValueError):
    """Raise when `ToolRouteResolver.resolve()` cannot map a tool to a server.

    A `ValueError` subclass carrying the failure `kind` and the offending `tool_name`:
      - `not_ready`: no `RuntimeToolRegistry` is wired yet
      - `posture_excluded`: the registry dropped the tool for a Security Posture reason
      - `server_unavailable`: the registry dropped the tool as unavailable or disabled
      - `unknown_tool`: the name was never registered
    """

    def __init__(
        self,
        kind: str,
        tool_name: str,
        message: str,
    ) -> None:
        """Store the failure `kind` and `tool_name`, then call `super().__init__(message)`."""
        self.kind = kind
        self.tool_name = tool_name
        super().__init__(message)


class ToolRouteResolver:
    """Map tool_name → server_key using RuntimeToolRegistry as the sole routing authority.

    RuntimeToolRegistry is populated from live /v1/tools discovery. Raises
    `ToolRoutingError` (a `ValueError` subclass) when the tool is not found there.
    """

    def __init__(
        self,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        self._runtime_registry: RuntimeToolRegistry | None = runtime_registry

    def resolve(self, tool_name: str) -> str:
        """Return the server key for tool_name; raise `ToolRoutingError` when no match.

        With no wired registry the kind is `not_ready`; otherwise a dropped tool reports
        `posture_excluded` or `server_unavailable` (via `RuntimeToolRegistry.exclusion_reason`)
        and an unregistered name reports `unknown_tool`. The message keeps the
        `Unknown tool: <name>` prefix so log searches stay valid.
        """
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        if self._runtime_registry is None:
            raise ToolRoutingError(
                "not_ready",
                tool_name,
                f"Unknown tool: {tool_name!r} (RuntimeToolRegistry not ready)",
            )
        reason = self._runtime_registry.exclusion_reason(tool_name)
        if reason == "posture":
            kind = "posture_excluded"
        elif reason in ("unavailable", "disabled"):
            kind = "server_unavailable"
        else:
            kind = "unknown_tool"
        raise ToolRoutingError(kind, tool_name, f"Unknown tool: {tool_name!r}")

    def _lookup_runtime_registry(self, tool_name: str) -> str | None:
        """Look up a tool in RuntimeToolRegistry; returns server key or None."""
        if self._runtime_registry is not None:
            return self._runtime_registry.resolve(tool_name)
        return None

    def set_runtime_registry(self, registry: RuntimeToolRegistry) -> None:
        """Replace the RuntimeToolRegistry consulted by resolve(), in place.

        Raises `TypeError` when given `None`: an unwired resolver must never be
        re-established as unwired.
        """
        if registry is None:
            raise TypeError("runtime registry must not be None")
        self._runtime_registry = registry
