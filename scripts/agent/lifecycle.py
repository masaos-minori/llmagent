#!/usr/bin/env python3
"""agent/lifecycle.py
MCP server lifecycle facade.

Delegates HTTP subprocess management to HttpServerLifecycleManager
and stdio ondemand management to StdioServerLifecycleManager.

Provides the same ServerLifecycleManager public API so all callers
(factory.py, repl.py, watchdog) are unaffected.
"""

from __future__ import annotations

import logging
import time
from enum import Enum

from shared.mcp_config import McpServerConfig
from shared.tool_executor import StdioTransport, ToolExecutor

from agent.http_lifecycle import HttpServerLifecycleManager
from agent.stdio_lifecycle import StdioServerLifecycleManager, TransportState

logger = logging.getLogger(__name__)


class LifecycleState(Enum):
    """Unified transport state for all server types (HTTP and stdio)."""

    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


def _transport_state_to_lifecycle(state: TransportState) -> LifecycleState:
    """Map TransportState to the unified LifecycleState enum."""
    if state == TransportState.RUNNING:
        return LifecycleState.RUNNING
    if state == TransportState.FAILED:
        return LifecycleState.FAILED
    return LifecycleState.STOPPED


class ServerLifecycleManager:
    """Facade: delegates to HttpServerLifecycleManager and StdioServerLifecycleManager."""

    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],
        tool_executor: ToolExecutor,
        stdio_procs: dict[str, StdioTransport],
    ) -> None:
        self._server_configs = server_configs
        self._tool_executor = tool_executor
        self._stdio_procs = stdio_procs
        self._last_called: dict[str, float] = {
            key: time.monotonic() for key in server_configs
        }
        self._http_mgr = HttpServerLifecycleManager()
        self._stdio_mgr = StdioServerLifecycleManager(
            server_configs,
            tool_executor,
            stdio_procs,
            self._last_called,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    async def ensure_ready(self, server_key: str) -> None:
        """Ensure the server for server_key is ready to accept calls."""
        self._last_called[server_key] = time.monotonic()
        cfg = self._server_configs.get(server_key)
        if cfg is None:
            return
        if cfg.transport == "http" and cfg.startup_mode == "subprocess":
            self._http_mgr.verify_running(server_key)
            return
        if cfg.transport != "stdio" or cfg.startup_mode == "persistent":
            return
        await self._stdio_mgr.ensure_ready(server_key)

    async def shutdown_all(self) -> None:
        """Stop all running MCP server subprocesses (stdio and HTTP subprocess)."""
        await self._stdio_mgr.shutdown_all()
        await self._http_mgr.shutdown_all()

    async def start_http_subprocess(
        self,
        server_key: str,
        cfg: McpServerConfig,
    ) -> None:
        """Start an HTTP MCP server subprocess and wait for /health to become ready."""
        await self._http_mgr.start(server_key, cfg)

    async def restart(self, server_key: str) -> None:
        """Terminate and restart an HTTP subprocess server."""
        cfg = self._server_configs.get(server_key)
        if cfg is None or cfg.startup_mode != "subprocess":
            logger.warning(
                f"Lifecycle: restart {server_key!r}: not a subprocess-mode server;"
                " manual restart required",
            )
            return
        await self._http_mgr.restart(server_key, cfg)

    async def shutdown_idle(self) -> None:
        """Stop ondemand stdio servers that have exceeded idle_timeout_sec."""
        await self._stdio_mgr.shutdown_idle()

    # ── Status API for monitoring ────────────────────────────────────────────

    def get_transport_state(self, server_key: str) -> LifecycleState:
        """Get the unified lifecycle state for a server."""
        cfg = self._server_configs.get(server_key)
        if cfg is None:
            return LifecycleState.UNKNOWN
        if cfg.transport == "http":
            return LifecycleState.UNKNOWN
        if cfg.transport == "stdio":
            raw = self._stdio_mgr.get_transport_state(server_key)
            return _transport_state_to_lifecycle(raw)
        return LifecycleState.UNKNOWN

    async def restart_stdio(self, server_key: str) -> None:
        """Restart a stdio server."""
        cfg = self._server_configs.get(server_key)
        if cfg is None or cfg.transport != "stdio":
            logger.warning(
                f"Lifecycle: restart_stdio {server_key!r}: not a stdio server",
            )
            return
        await self._stdio_mgr.restart(server_key)
