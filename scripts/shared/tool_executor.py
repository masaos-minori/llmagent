#!/usr/bin/env python3
"""scripts/shared/tool_executor.py

MCP tool execution layer.

Provides HttpTransport implementation for POST /v1/call_tool over httpx.

ToolExecutor routes tool calls to the appropriate server via ToolRouteResolver
and delegates execution to the configured transport.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shared.runtime_tool_registry import RuntimeToolRegistry

import httpx

from shared.mcp_config import McpServerConfig
from shared.route_resolver import ToolRouteResolver
from shared.tool_lifecycle import LifecycleProtocol
from shared.tool_transport_invoker import ToolTransportInvoker
from shared.transport_dto import ToolCallResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# ToolExecutor
# ─────────────────────────────────────────────────────────────────────────────


class ToolExecutor(ToolTransportInvoker):
    """Routes tool calls to the appropriate MCP server transport."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client and server configurations.

        Args:
            http: AsyncHTTPClient instance for making requests.
            server_configs: Server configurations for MCP servers.
            concurrency_limits: Optional concurrency limits per server. A
                configured positive value caps that server; a server with no
                positive limit falls back to the process-wide
                DEFAULT_PER_SERVER_CONCURRENCY. An explicit 0/negative value
                opts out (unlimited). Note: this value is fixed at
                initialization time and cannot be changed later.
            lifecycle: Optional lifecycle protocol for MCP servers.
        """
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._resolver = ToolRouteResolver()

    def set_runtime_registry(self, registry: RuntimeToolRegistry) -> None:
        """Wire RuntimeToolRegistry into the existing resolver after discovery completes."""
        self._resolver.set_runtime_registry(registry)

    async def _raw_execute(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)
        return await self._run_precall_gates(server_key, tool_name, args)

    async def execute(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool."""
        return await self._raw_execute(tool_name, args)

    def get_error_counters(self) -> dict[str, dict[str, int]]:
        """Return per-server error counters: {server_key: {"transport": N, "tool": N}}."""
        return super().get_error_counters()
