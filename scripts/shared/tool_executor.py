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

from shared.http_transport import HttpTransport
from shared.mcp_config import (
    McpServerConfig,
    StartupMode,
)
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
        """Initialize with HTTP client and server configurations."""
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._server_configs = server_configs

        self._resolver = ToolRouteResolver()

    def set_runtime_registry(self, registry: RuntimeToolRegistry) -> None:
        """Wire RuntimeToolRegistry into the existing resolver after discovery completes."""
        self._resolver.set_runtime_registry(registry)

    def _check_startup_mode(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    async def _ensure_lifecycle_ready(self, server_key: str) -> ToolCallResult | None:
        """Ensure the MCP server lifecycle is ready; returns error result if not."""
        if self._lifecycle is None:
            return None
        try:
            await self._lifecycle.ensure_ready(server_key)
        except (OSError, RuntimeError) as e:
            msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
            logger.error(msg)
            if self._health_registry is not None:
                self._health_registry.record_failure(server_key)
            return self._error_result(server_key, msg, error_type="transport")
        return None

    def _resolve_transport(self, server_key: str) -> HttpTransport | None:
        """Resolve the transport for a server key; returns None if missing."""
        return self._transports.get(server_key)

    def _run_gate_chain(self, server_key: str) -> ToolCallResult | None:
        """Run the startup-mode and health gates in order; return the first error, or None if both pass.

        The lifecycle gate (_ensure_lifecycle_ready) is async and stays a separate
        await in _raw_execute immediately after this call, preserving call order.
        """
        if err := self._check_startup_mode(server_key):
            return err
        if err := self._check_health(server_key):
            return err
        return None

    async def _raw_execute(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        if err := self._run_gate_chain(server_key):
            return err

        # Lifecycle ensure_ready
        lifecycle_err = await self._ensure_lifecycle_ready(server_key)
        if lifecycle_err is not None:
            return lifecycle_err

        # Transport resolution
        transport = self._resolve_transport(server_key)
        if transport is None:
            return self._error_result(
                server_key, self._transport_missing_msg(server_key), error_type="tool"
            )

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)
        return await self._invoke_and_record(
            server_key, transport, tool_name, args, sem
        )

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
