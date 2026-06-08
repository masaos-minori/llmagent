"""agent/stdio_lifecycle.py
Stdio MCP server lifecycle: ondemand startup, idle shutdown.

Extracted from lifecycle.py. ServerLifecycleManager delegates here for
all stdio server operations.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum

from shared.mcp_config import McpServerConfig
from shared.tool_executor import StdioTransport, ToolExecutor

logger = logging.getLogger(__name__)


class TransportState(Enum):
    """Enumeration of transport states."""

    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass
class TransportHandle:
    """Combines a StdioTransport with its state and last error for unified tracking."""

    transport: StdioTransport | None
    state: TransportState
    last_error: str | None = field(default=None)


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
        # Initialize handles from pre-existing transports (e.g. persistent servers
        # started before this manager was constructed).
        self._handles: dict[str, TransportHandle] = {
            key: TransportHandle(
                transport=t,
                state=TransportState.RUNNING
                if t.is_alive()
                else TransportState.STOPPED,
            )
            for key, t in stdio_procs.items()
        }

    async def ensure_ready(self, server_key: str) -> None:
        """Start an ondemand stdio server on first call; no-op if already running."""
        cfg = self._server_configs.get(server_key)
        if cfg is None or cfg.transport != "stdio" or cfg.startup_mode != "ondemand":
            return
        await self._ensure_ondemand(server_key)

    async def _ensure_ondemand(self, server_key: str) -> None:
        """Double-checked locking to prevent concurrent starts."""
        handle = self._handles.get(server_key)
        if handle is not None and handle.state == TransportState.RUNNING:
            return
        lock = self._start_locks.setdefault(server_key, asyncio.Lock())
        async with lock:
            handle = self._handles.get(server_key)
            if handle is not None and handle.state == TransportState.RUNNING:
                return
            await self._start(server_key)

    async def _start(self, server_key: str) -> None:
        """Create and start a StdioTransport for the given server key."""
        cfg = self._server_configs.get(server_key)
        if cfg is None or not cfg.cmd:
            logger.warning(
                f"Lifecycle: cannot start {server_key!r}: no cmd configured",
            )
            self._handles[server_key] = TransportHandle(
                transport=None,
                state=TransportState.FAILED,
                last_error="no cmd configured",
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
            self._handles[server_key] = TransportHandle(
                transport=new_transport, state=TransportState.RUNNING
            )
            logger.info(f"Lifecycle: ondemand stdio server {server_key!r} started")
        except Exception as e:
            logger.error(
                f"Lifecycle: failed to start ondemand server {server_key!r}: {e}",
            )
            self._handles[server_key] = TransportHandle(
                transport=None, state=TransportState.FAILED, last_error=str(e)
            )

    async def _stop_stdio(self, key: str, transport: StdioTransport) -> None:
        """Stop one stdio transport and update its state; logs on failure."""
        try:
            await transport.stop()
            self._handles[key] = TransportHandle(
                transport=None, state=TransportState.STOPPED
            )
        except Exception as e:
            logger.warning("Lifecycle: error stopping stdio %r: %s", key, e)
            self._handles[key] = TransportHandle(
                transport=None, state=TransportState.FAILED, last_error=str(e)
            )

    async def shutdown_all(self) -> None:
        """Stop all running stdio server transports."""
        for key, transport in list(self._stdio_procs.items()):
            await self._stop_stdio(key, transport)

    def _is_idle_timeout(self, key: str, cfg: McpServerConfig, now: float) -> bool:
        """Return True when an ondemand server has exceeded its idle timeout."""
        if cfg.startup_mode != "ondemand" or cfg.idle_timeout_sec <= 0:
            return False
        last = self._last_called.get(key, 0.0)
        handle = self._handles.get(key)
        state = handle.state if handle else TransportState.STOPPED
        return now - last >= cfg.idle_timeout_sec and state == TransportState.RUNNING

    async def shutdown_idle(self) -> None:
        """Stop ondemand stdio servers that have exceeded idle_timeout_sec."""
        now = time.monotonic()
        for key, transport in list(self._stdio_procs.items()):
            cfg = self._server_configs.get(key)
            if cfg is None or not self._is_idle_timeout(key, cfg, now):
                continue
            logger.info("Lifecycle: idle timeout — stopping %r", key)
            await self._stop_stdio(key, transport)

    def get_transport_state(self, server_key: str) -> TransportState:
        """Get the current state of a transport."""
        handle = self._handles.get(server_key)
        return handle.state if handle else TransportState.STOPPED

    def set_transport_state(self, server_key: str, state: TransportState) -> None:
        """Set the state of a transport."""
        handle = self._handles.get(server_key)
        if handle is not None:
            handle.state = state
        else:
            self._handles[server_key] = TransportHandle(transport=None, state=state)

    async def restart(self, server_key: str) -> None:
        """Restart a stdio server by stopping and starting it."""
        handle = self._handles.get(server_key)
        if handle is not None and handle.transport is not None:
            await self._stop_stdio(server_key, handle.transport)
        await self._start(server_key)
