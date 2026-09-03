"""scripts/agent/startup_mcp_starter.py

MCP server starter: subprocess startup, health verification, and retry-once-with-delay.

Extracted from scripts/agent/startup.py (REQ-002).
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from typing import TYPE_CHECKING

import httpx
from shared.logger import Logger
from shared.mcp_config import (
    McpServerConfig,
    SecurityProfile,
    StartupMode,
    TransportType,
)

from agent.context import AgentContext
from agent.output_tags import OutputTag
from agent.secrets_masker import _mask_secrets
from agent.shared.retry_helper import retry_once_with_delay

if TYPE_CHECKING:
    from agent.cli_view import CLIView

# Retry delay constant (moved from startup.py module level)
RETRY_DELAY_SEC = 1.0

logger = Logger(__name__, "/opt/llm/logs/agent.log")


class McpServerStarter:
    """Owns MCP subprocess startup, health verification, and retry-once-with-delay."""

    def __init__(
        self,
        ctx: AgentContext,
        view: CLIView,
        shutdown_event: asyncio.Event | None = None,
    ) -> None:
        self._ctx = ctx
        self._view = view
        self._shutdown_event = shutdown_event
        self._spawned_subprocesses: list[subprocess.Popen] = []

    async def start_servers(self) -> list[subprocess.Popen]:
        """Spawn subprocesses for HTTP subprocess MCP servers."""
        ctx = self._ctx
        if ctx.services_required.tools is None:
            raise RuntimeError("tools service not initialized")
        if ctx.services_required.lifecycle is None:
            raise RuntimeError("lifecycle service not initialized")
        last_startup_time = 0.0
        for key, cfg in ctx.cfg.mcp.mcp_servers.items():
            if self._shutdown_event is not None and self._shutdown_event.is_set():
                from agent.startup import StartupInterrupted

                raise StartupInterrupted(
                    f"shutdown requested before starting MCP subprocess {key!r}"
                )
            if (
                cfg.startup_mode == StartupMode.SUBPROCESS
                and cfg.transport == TransportType.HTTP
            ):
                if last_startup_time > 0 and cfg.startup_stagger_delay_sec > 0:
                    elapsed = time.monotonic() - last_startup_time
                    stagger_delay = max(0.0, cfg.startup_stagger_delay_sec - elapsed)
                    if stagger_delay > 0:
                        if await self._interruptible_sleep(stagger_delay):
                            from agent.startup import StartupInterrupted

                            raise StartupInterrupted(
                                f"shutdown requested during startup stagger delay for {key!r}"
                            )
                        logger.info(
                            "Staggering startup by %.1fs for %r", stagger_delay, key
                        )

                try:
                    started_at = await self._start_http_subprocess_once(key, cfg)
                    if started_at is not None:
                        last_startup_time = started_at
                except (OSError, RuntimeError) as e:
                    # First attempt failure — use retry helper
                    logger.info(
                        "First attempt failed for MCP subprocess %r: %s",
                        key,
                        _mask_secrets(str(e)),
                    )

                    result = await retry_once_with_delay(
                        lambda: self._start_http_subprocess_once(key, cfg),
                        delay=RETRY_DELAY_SEC,
                        shutdown_event=self._shutdown_event,
                        interrupt_msg=f"shutdown requested during startup retry delay for {key!r}",
                        production_mode=(
                            ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION
                        ),
                        fatal_prefix=f"{OutputTag.FATAL} MCP subprocess {key!r} failed to start after retry:",
                        non_fatal_prefix=f"MCP subprocess {key!r} failed to start after retry:",
                        view=self._view,
                    )
                    if result is not None:
                        last_startup_time = result
        return self._spawned_subprocesses

    async def verify_health(self) -> None:
        """Verify health of all MCP subprocess servers after startup."""
        ctx = self._ctx
        if ctx.services_required.tools is None:
            raise RuntimeError("tools service not initialized")
        if ctx.services_required.lifecycle is None:
            raise RuntimeError("lifecycle service not initialized")

        subprocess_servers = [
            (key, cfg)
            for key, cfg in ctx.cfg.mcp.mcp_servers.items()
            if cfg.startup_mode == StartupMode.SUBPROCESS
            and cfg.transport == TransportType.HTTP
        ]

        for server_key, cfg in subprocess_servers:
            if self._shutdown_event is not None and self._shutdown_event.is_set():
                from agent.startup import StartupInterrupted

                raise StartupInterrupted(
                    f"shutdown requested before health check for {server_key!r}"
                )
            url = cfg.url.rstrip("/") + "/health"
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url)
                    if resp.status_code != httpx.codes.OK:
                        raise RuntimeError(f"HTTP {resp.status_code}")
                    logger.info("Post-startup health check passed for %r", server_key)
            except Exception:  # noqa: BLE001 — any health-check failure triggers retry rather than aborting startup
                # Use retry helper instead of inline retry
                await retry_once_with_delay(
                    lambda: self._verify_single_health(server_key, cfg),
                    delay=RETRY_DELAY_SEC,
                    shutdown_event=self._shutdown_event,
                    interrupt_msg=f"shutdown requested during post-startup health check retry delay for {server_key!r}",
                    production_mode=(
                        ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION
                    ),
                    fatal_prefix=f"{OutputTag.FATAL} MCP subprocess {server_key!r} failed post-startup health check:",
                    non_fatal_prefix=f"Post-startup health check failed for {server_key!r}: ",
                    view=self._view,
                )
                # If we got here, retry succeeded — nothing more to do

    async def _start_http_subprocess_once(
        self, key: str, cfg: McpServerConfig
    ) -> float | None:
        """Attempt one start_http_subprocess() call.

        On success, tracks the spawned process and returns the new
        last_startup_time (`time.monotonic()`); returns None when the
        lifecycle manager reports no process was started.
        """
        proc = await self._ctx.services_required.lifecycle.start_http_subprocess(
            key, cfg, shutdown_event=self._shutdown_event
        )
        if proc is not None:
            self._spawned_subprocesses.append(proc)
            return time.monotonic()
        return None

    async def _verify_single_health(
        self, server_key: str, cfg: McpServerConfig
    ) -> None:
        """Verify health of a single MCP subprocess server."""
        url = cfg.url.rstrip("/") + "/health"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code != httpx.codes.OK:
                raise RuntimeError(f"HTTP {resp.status_code}")
            logger.info(
                "Post-startup health check passed for %r (after retry)",
                server_key,
            )

    async def _interruptible_sleep(self, delay: float) -> bool:
        """Sleep for `delay` seconds, racing against `_shutdown_event`.

        Returns True iff the shutdown event fired before `delay` elapsed.
        """
        if self._shutdown_event is None:
            await asyncio.sleep(delay)
            return False
        sleep_task = asyncio.ensure_future(asyncio.sleep(delay))
        shutdown_task = asyncio.ensure_future(self._shutdown_event.wait())
        done, pending = await asyncio.wait(
            {sleep_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        return shutdown_task in done
