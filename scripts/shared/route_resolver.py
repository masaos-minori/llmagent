#!/usr/bin/env python3
"""shared/route_resolver.py
Tool-name to server-key resolution for ToolExecutor.

Routing priority:
  1. Tool registry (canonical source of truth from tool_registry.py; populated from tool_constants.py frozensets)

Config `tool_names` is NOT a routing input; it is drift validation metadata only.
Live /v1/tools discovery is used for startup validation only, not routing.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig

logger = logging.getLogger(__name__)


def build_discovery_map(
    server_tool_lists: dict[str, list[dict[str, object]]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


class ToolRouteResolver:
    """Map tool_name → server_key using ToolRegistry as the sole routing authority.
    Raises ValueError when the tool is not in the registry.
    """

    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        discovery_map: dict[str, str] | None = None,
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            server_configs: Accepted for backward compatibility with existing callers;
                not read or stored — routing never consults per-server config.
            discovery_map: Live /v1/tools validation data; used only by the
                currently-unreachable `_log_routing_coverage()` diagnostic, never by
                `resolve()`.
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message.
            known_tools: When provided, triggers a startup coverage log via
                `_log_routing_coverage()`. No production caller passes this today.
        """
        # Validation data from live /v1/tools (not used for routing).
        self._discovery_map: dict[str, str] = discovery_map or {}
        # Tool registry (canonical source of truth).
        from shared.tool_registry import ToolRegistry

        self._registry: ToolRegistry | None
        try:
            from shared.tool_registry import get_registry

            self._registry = get_registry()
        except (ImportError, RuntimeError) as exc:
            logger.warning("Failed to initialize ToolRegistry: %s", exc)
            self._registry = None
        # Config tool_names is NOT used for routing — only for drift validation.
        self._warn_on_missing = warn_on_missing
        self._strict_mode = strict_mode
        if known_tools:
            self._log_routing_coverage(known_tools)

    def resolve(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        # Priority 1: tool registry (canonical source of truth).
        if (key := self._lookup_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not in ToolRegistry; "
                "add it to the appropriate frozenset in shared/tool_constants.py.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def _lookup_registry(self, tool_name: str) -> str | None:
        """Look up a tool in the registry; returns server key or None."""
        if self._registry is not None:
            result: str | None = self._registry.get_server_for_tool(tool_name)
            return result
        return None

    def _raise_strict_error(self, tool_name: str) -> None:
        """Raise ValueError when strict_mode is enabled and no mapping found."""
        raise ValueError(
            f"ToolRouteResolver: tool {tool_name!r} not in ToolRegistry "
            f"and strict_mode=True; add it to the appropriate frozenset in shared/tool_constants.py"
        )

    def _log_routing_coverage(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via `ToolRegistry` — the same authority `resolve()`
        uses — not merely present in `discovery_map`. `discovery_map` is validation-only
        metadata from live /v1/tools responses and carries no routing authority: a tool
        present only in `discovery_map` but absent from the registry is UNMAPPED for this
        purpose, since `resolve()` would raise `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)
