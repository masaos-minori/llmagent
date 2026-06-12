"""agent/http_lifecycle.py
HTTP subprocess MCP server lifecycle: start, health-poll, restart, shutdown.

Extracted from lifecycle.py. ServerLifecycleManager imports and delegates
to HttpServerLifecycleManager for all HTTP subprocess operations.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess  # nosec B404 — used to launch admin-controlled MCP server processes
import time
from dataclasses import dataclass

import httpx
from shared.mcp_config import McpServerConfig

logger = logging.getLogger(__name__)


@dataclass
class StartupFailure:
    """Records the full stderr output and reason when an HTTP subprocess fails to start."""

    server_key: str
    reason: str
    stderr_full: str


class HttpStartupError(RuntimeError):
    """Raised when an HTTP subprocess MCP server fails to start."""

    def __init__(self, failure: StartupFailure) -> None:
        self.failure = failure
        super().__init__(failure.reason)


class HttpServerLifecycleManager:
    """Manages HTTP subprocess MCP servers: start, health-poll, restart, shutdown."""

    def __init__(self) -> None:
        self._http_procs: dict[str, subprocess.Popen[bytes]] = {}

    async def _terminate_with_timeout(
        self,
        proc: subprocess.Popen[bytes],
        server_key: str,
        timeout: float = 3.0,
    ) -> None:
        """Terminate proc; escalate to kill if terminate times out."""
        proc.terminate()
        try:
            await asyncio.wait_for(asyncio.to_thread(proc.wait), timeout=timeout)
        except TimeoutError:
            logger.warning(
                f"Lifecycle: force-killing {server_key!r} (terminate timed out)",
            )
            proc.kill()
            try:
                await asyncio.wait_for(asyncio.to_thread(proc.wait), timeout=timeout)
            except TimeoutError:
                logger.warning(
                    f"Lifecycle: {server_key!r} still not terminated after kill",
                )

    def verify_running(self, server_key: str) -> bool:
        """Check if an HTTP subprocess server is running and optionally restart it.

        Returns True if running, False if not running (and restart was attempted).
        """
        proc = self._http_procs.get(server_key)
        if proc is None or proc.poll() is not None:
            logger.warning(
                f"Lifecycle: HTTP subprocess {server_key!r} is not running;"
                " it should have been started at agent init",
            )
            return False
        return True

    async def start(
        self,
        server_key: str,
        cfg: McpServerConfig,
    ) -> None:
        """Start an HTTP MCP server subprocess and poll /health until ready.

        Idempotent: reuses an already-running process.
        Stores the full stderr in StartupFailure when the process exits early
        or the health-poll times out; raises RuntimeError in both cases.
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
            env = {**os.environ, **cfg.env}
        proc = subprocess.Popen(  # nosec B603 — cmd comes from admin-controlled config, not user input  # noqa: S603
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
                    stderr_full = (
                        proc.stderr.read().decode(errors="replace")
                        if proc.stderr
                        else ""
                    )
                    failure = StartupFailure(
                        server_key=server_key,
                        reason="exited early",
                        stderr_full=stderr_full,
                    )
                    logger.error(
                        f"Lifecycle: {server_key!r} exited early;"
                        f" stderr ({len(stderr_full)} chars): {stderr_full[:500]}",
                    )
                    raise HttpStartupError(failure)
                try:
                    resp = await client.get(health_url)
                    if resp.status_code == 200:
                        logger.info(
                            f"Lifecycle: HTTP subprocess {server_key!r} ready",
                        )
                        return
                except (httpx.HTTPError, OSError) as e:
                    logger.debug(f"Lifecycle: health-check poll {server_key!r}: {e}")
                await asyncio.sleep(0.5)

        # Handle timeout case with stderr collection
        stderr_full = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        await self._terminate_with_timeout(proc, server_key)
        timeout_failure = StartupFailure(
            server_key=server_key,
            reason=f"did not become healthy within {cfg.startup_timeout_sec}s",
            stderr_full=stderr_full,
        )
        raise HttpStartupError(timeout_failure)

    async def restart(self, server_key: str, cfg: McpServerConfig) -> None:
        """Terminate and restart an HTTP subprocess server."""
        proc = self._http_procs.pop(server_key, None)
        if proc is not None and proc.poll() is None:
            logger.info(f"Lifecycle: terminating {server_key!r} for restart")
            await self._terminate_with_timeout(proc, server_key)
        await self.start(server_key, cfg)

    async def shutdown_all(self) -> None:
        """Terminate all HTTP subprocess servers."""
        for key, proc in list(self._http_procs.items()):
            if proc.poll() is None:
                try:
                    await self._terminate_with_timeout(proc, key, timeout=5.0)
                except (OSError, TimeoutError) as e:
                    logger.warning(
                        f"Lifecycle: error stopping HTTP subprocess {key!r}: {e}"
                    )
