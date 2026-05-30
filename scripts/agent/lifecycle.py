#!/usr/bin/env python3
"""
agent/lifecycle.py
MCP server lifecycle management for AgentREPL.

ServerLifecycleManager handles ondemand startup of stdio MCP servers and
graceful shutdown of all subprocess-backed servers.  It implements
LifecycleProtocol from shared/tool_executor.py so it can be injected into
ToolExecutor without creating an agent -> shared circular import.
"""

from __future__ import annotations

import asyncio
import logging

from shared.mcp_config import McpServerConfig
from shared.tool_executor import StdioTransport, ToolExecutor

logger = logging.getLogger(__name__)


class ServerLifecycleManager:
    """Manages startup and shutdown of MCP server subprocesses.

    Persistent stdio servers are started by AgentREPL._start_stdio_servers()
    at agent initialisation.  Ondemand servers are started here on the first
    tool call that routes to them via ensure_ready().
    """

    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],
        tool_executor: ToolExecutor,
        stdio_procs: dict[str, StdioTransport],
    ) -> None:
        self._server_configs = server_configs
        self._tool_executor = tool_executor
        self._stdio_procs = stdio_procs
        # Per-server asyncio.Lock prevents concurrent ondemand startup races.
        self._start_locks: dict[str, asyncio.Lock] = {}

    async def ensure_ready(self, server_key: str) -> None:
        """Ensure the MCP server for server_key is ready to accept calls.

        HTTP servers: no-op (external process managed outside agent lifetime).
        Persistent stdio servers: no-op (started at agent init by _start_stdio_servers).
        Ondemand stdio servers: start subprocess on first call; serialize concurrent starts.
        """
        cfg = self._server_configs.get(server_key)
        if cfg is None or cfg.transport != "stdio":
            return
        if cfg.startup_mode == "persistent":
            return

        # ondemand: check liveness without locking first for the fast path
        transport = self._stdio_procs.get(server_key)
        if transport is not None and transport.is_alive():
            return

        # Acquire per-server lock to serialise concurrent startup attempts
        lock = self._start_locks.setdefault(server_key, asyncio.Lock())
        async with lock:
            # Double-check after acquiring lock to avoid double-start
            transport = self._stdio_procs.get(server_key)
            if transport is not None and transport.is_alive():
                return
            startup_cfg = self._server_configs.get(server_key)
            if startup_cfg is None or not startup_cfg.cmd:
                logger.warning(
                    f"Lifecycle: cannot start {server_key!r}: no cmd configured"
                )
                return
            new_transport = StdioTransport(startup_cfg.cmd, server_key=server_key)
            try:
                await new_transport.start()
                self._tool_executor.set_transport(server_key, new_transport)
                self._stdio_procs[server_key] = new_transport
                logger.info(f"Lifecycle: ondemand stdio server {server_key!r} started")
            except Exception as e:
                logger.error(
                    f"Lifecycle: failed to start ondemand server {server_key!r}: {e}"
                )

    async def shutdown_all(self) -> None:
        """Stop all running stdio MCP server subprocesses."""
        for key, transport in list(self._stdio_procs.items()):
            try:
                await transport.stop()
            except Exception as e:
                logger.warning(f"Lifecycle: error stopping {key!r}: {e}")

    async def shutdown_idle(self) -> None:
        """Stop ondemand stdio servers that have exceeded their idle_timeout_sec.

        Skeleton implementation: idle timeout enforcement is not yet wired to a
        call-time tracking mechanism.  Reserved for future work.
        """
