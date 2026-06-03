"""agent/stdio_lifecycle.py
Stdio MCP server lifecycle: ondemand startup, idle shutdown.

Extracted from lifecycle.py. ServerLifecycleManager delegates here for
all stdio server operations.
"""

from __future__ import annotations

import asyncio
import logging
import time

from shared.mcp_config import McpServerConfig
from shared.tool_executor import StdioTransport, ToolExecutor

logger = logging.getLogger(__name__)


class StdioServerLifecycleManager:
    """Manages ondemand stdio MCP server subprocess lifecycle."""

    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],
        tool_executor: ToolExecutor,
        stdio_procs: dict[str, StdioTransport],
        last_called: dict[str, float],
    ) -> None:
        self._server_configs = server_configs
        self._tool_executor = tool_executor
        self._stdio_procs = stdio_procs
        self._last_called = last_called
        self._start_locks: dict[str, asyncio.Lock] = {}

    async def ensure_ready(self, server_key: str) -> None:
        """Start an ondemand stdio server on first call; no-op if already running."""
        cfg = self._server_configs.get(server_key)
        if cfg is None or cfg.transport != "stdio" or cfg.startup_mode != "ondemand":
            return
        await self._ensure_ondemand(server_key)

    async def _ensure_ondemand(self, server_key: str) -> None:
        """Double-checked locking to prevent concurrent starts."""
        transport = self._stdio_procs.get(server_key)
        if transport is not None and transport.is_alive():
            return
        lock = self._start_locks.setdefault(server_key, asyncio.Lock())
        async with lock:
            transport = self._stdio_procs.get(server_key)
            if transport is not None and transport.is_alive():
                return
            await self._start(server_key)

    async def _start(self, server_key: str) -> None:
        """Create and start a StdioTransport for the given server key."""
        cfg = self._server_configs.get(server_key)
        if cfg is None or not cfg.cmd:
            logger.warning(
                f"Lifecycle: cannot start {server_key!r}: no cmd configured",
            )
            return
        new_transport = StdioTransport(
            cfg.cmd,
            server_key=server_key,
            working_dir=cfg.working_dir,
            env=cfg.env or None,
        )
        try:
            await new_transport.start()
            self._tool_executor.set_transport(server_key, new_transport)
            self._stdio_procs[server_key] = new_transport
            logger.info(f"Lifecycle: ondemand stdio server {server_key!r} started")
        except Exception as e:
            logger.error(
                f"Lifecycle: failed to start ondemand server {server_key!r}: {e}",
            )

    async def shutdown_all(self) -> None:
        """Stop all running stdio server transports."""
        for key, transport in list(self._stdio_procs.items()):
            try:
                await transport.stop()
            except Exception as e:
                logger.warning(f"Lifecycle: error stopping stdio {key!r}: {e}")

    async def shutdown_idle(self) -> None:
        """Stop ondemand stdio servers that have exceeded idle_timeout_sec."""
        now = time.monotonic()
        for key, transport in list(self._stdio_procs.items()):
            cfg = self._server_configs.get(key)
            if cfg is None or cfg.startup_mode != "ondemand":
                continue
            if cfg.idle_timeout_sec <= 0:
                continue
            last = self._last_called.get(key, 0.0)
            if now - last >= cfg.idle_timeout_sec and transport.is_alive():
                logger.info(f"Lifecycle: idle timeout — stopping {key!r}")
                try:
                    await transport.stop()
                except Exception as e:
                    logger.warning(f"Lifecycle: error stopping idle {key!r}: {e}")
