#!/usr/bin/env python3
"""agent/lifecycle.py
MCP server lifecycle management for AgentREPL.

ServerLifecycleManager handles ondemand startup of stdio MCP servers and
graceful shutdown of all subprocess-backed servers.  It implements
LifecycleProtocol from shared/tool_executor.py so it can be injected into
ToolExecutor without creating an agent -> shared circular import.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess  # nosec B404 — MCP server subprocess management; cmd comes from config, never user input
import time

import httpx
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
        # subprocess.Popen handles for HTTP servers launched by startup_mode="subprocess"
        self._http_procs: dict[str, subprocess.Popen[bytes]] = {}
        # Per-server asyncio.Lock prevents concurrent ondemand startup races.
        self._start_locks: dict[str, asyncio.Lock] = {}
        # Initialize with current time so servers are not idle-stopped immediately at startup.
        self._last_called: dict[str, float] = {
            key: time.monotonic() for key in server_configs
        }

    async def ensure_ready(self, server_key: str) -> None:
        """Ensure the MCP server for server_key is ready to accept calls.

        HTTP subprocess servers: no-op when already alive (started by _start_subprocess_servers).
        Persistent stdio servers: no-op (started at agent init).
        Ondemand stdio servers: start subprocess on first call; serialize concurrent starts.
        """
        self._last_called[server_key] = time.monotonic()
        cfg = self._server_configs.get(server_key)
        if cfg is None:
            return
        # HTTP subprocess servers are started eagerly; just verify liveness.
        if cfg.transport == "http" and cfg.startup_mode == "subprocess":
            proc = self._http_procs.get(server_key)
            if proc is None or proc.poll() is not None:
                logger.warning(
                    f"Lifecycle: HTTP subprocess {server_key!r} is not running;"
                    " it should have been started at agent init",
                )
            return
        if cfg.transport != "stdio":
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
                    f"Lifecycle: cannot start {server_key!r}: no cmd configured",
                )
                return
            new_transport = StdioTransport(
                startup_cfg.cmd,
                server_key=server_key,
                working_dir=startup_cfg.working_dir,
                env=startup_cfg.env or None,
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
        """Stop all running MCP server subprocesses (stdio and HTTP subprocess)."""
        for key, transport in list(self._stdio_procs.items()):
            try:
                await transport.stop()
            except Exception as e:
                logger.warning(f"Lifecycle: error stopping stdio {key!r}: {e}")
        for key, proc in list(self._http_procs.items()):
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception as e:
                    logger.warning(
                        f"Lifecycle: error stopping HTTP subprocess {key!r}: {e}"
                    )

    async def start_http_subprocess(
        self,
        server_key: str,
        cfg: McpServerConfig,
    ) -> None:
        """Start an HTTP MCP server as a subprocess and wait for /health to become ready.

        If a process for server_key is already alive, reuse it (idempotent).
        Polls cfg.url/health every 0.5 s up to cfg.startup_timeout_sec seconds.
        Raises RuntimeError on timeout.
        """
        existing = self._http_procs.get(server_key)
        if existing is not None and existing.poll() is None:
            logger.info(
                f"Lifecycle: HTTP subprocess {server_key!r} already running (reusing)",
            )
            return

        logger.info(
            f"Lifecycle: starting HTTP subprocess {server_key!r}: {cfg.cmd}",
        )
        env = None
        if cfg.env:
            import os  # noqa: PLC0415

            env = {**os.environ, **cfg.env}
        proc = subprocess.Popen(  # nosec B603  # noqa: S603 — cmd comes from McpServerConfig; never from user input
            cfg.cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=env,
        )
        self._http_procs[server_key] = proc

        health_url = cfg.url.rstrip("/") + "/health"
        deadline = time.monotonic() + cfg.startup_timeout_sec
        async with httpx.AsyncClient(timeout=2.0) as client:
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    stderr_out = (
                        proc.stderr.read().decode(errors="replace")
                        if proc.stderr
                        else ""
                    )
                    raise RuntimeError(
                        f"Lifecycle: HTTP subprocess {server_key!r} exited early;"
                        f" stderr: {stderr_out[:200]}",
                    )
                try:
                    resp = await client.get(health_url)
                    if resp.status_code == 200:
                        logger.info(
                            f"Lifecycle: HTTP subprocess {server_key!r} ready",
                        )
                        return
                except Exception as e:
                    logger.debug(f"Lifecycle: health-check poll {server_key!r}: {e}")
                await asyncio.sleep(0.5)

        proc.terminate()
        raise RuntimeError(
            f"Lifecycle: HTTP subprocess {server_key!r} did not become healthy"
            f" within {cfg.startup_timeout_sec}s",
        )

    async def shutdown_idle(self) -> None:
        """Stop ondemand stdio servers that have exceeded their idle_timeout_sec."""
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
