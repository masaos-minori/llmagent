"""scripts/agent/lifecycle_router.py — MCP server lifecycle routing and subprocess delegation.

Coordinating layer between ToolExecutor and agent/http_lifecycle.py:
  _ServerLifecycleRouter: coordinator (state tracking, cooldown, shutdown guard)
  _SubprocessLifecycleManager: subprocess operations (start/restart/shutdown)
Both implement LifecycleManagerProtocol.

Extracted from agent/factory.py so that factory.py holds AgentContext assembly only.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import time
from collections.abc import Awaitable, Callable

from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.tool_executor import ToolExecutor
from shared.tool_lifecycle import ServerCooldownError

from agent.http_lifecycle import HttpServerLifecycleManager
from agent.http_lifecycle_errors import TerminationOutcome
from agent.lifecycle import LifecycleState, assert_valid_transition
from agent.lifecycle_protocol import LifecycleManagerProtocol
from agent.services.models import ProcessInfoSnapshot

_logger = logging.getLogger(__name__)

# Cooldown duration for failed MCP subprocess starts (seconds)
_COOLDOWN_SECONDS: float = 30.0


def _is_http_subprocess_server(cfg: McpServerConfig) -> bool:
    """Return True when *cfg* is an HTTP server started as a subprocess."""
    return cfg.transport == TransportType.HTTP and (
        cfg.startup_mode == StartupMode.SUBPROCESS
    )


class _SubprocessLifecycleManager(LifecycleManagerProtocol):
    """Manages HTTP subprocess server lifecycle operations.

    Handles subprocess start/restart/shutdown while delegating state/cooldown
    logic to _ServerLifecycleRouter which coordinates via this instance.
    """

    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],
        tool_executor: ToolExecutor,
    ) -> None:
        """Initialize the subprocess lifecycle manager."""
        self._server_configs = server_configs
        self._http_mgr = HttpServerLifecycleManager()

    async def ensure_ready(self, server_key: str) -> None:
        """Ensure the HTTP subprocess server is running; start it if needed."""
        cfg = self._server_configs.get(server_key)
        if cfg is None or not _is_http_subprocess_server(cfg):
            return
        os_alive = self._http_mgr.verify_running(server_key)
        if not os_alive:
            _logger.info(
                "Lifecycle: %r not running; starting via ensure_ready", server_key
            )
            await self._http_mgr.start(server_key, cfg)
        else:
            app_healthy = await self._http_mgr.verify_running_async(server_key, cfg)
            if not app_healthy:
                _logger.warning(
                    "Lifecycle: %r OS-alive but app-unhealthy; restarting", server_key
                )
                await self._http_mgr.restart(server_key, cfg)

    async def shutdown_all(self) -> list[tuple[str, TerminationOutcome]]:
        """Shut down all managed HTTP subprocess servers."""
        return await self._http_mgr.shutdown_all()

    async def restart(self, server_key: str) -> None:
        """Restart one HTTP subprocess MCP server; the router pre-checks startup_mode."""
        cfg = self._server_configs.get(server_key)
        if cfg is None:
            return
        await self._http_mgr.restart(server_key, cfg)

    async def shutdown_idle(self) -> None:
        """No-op for idle shutdown — only applies to stdio servers."""

    def get_transport_state(self, server_key: str) -> LifecycleState:
        """Return the current lifecycle state for a server."""
        return LifecycleState.UNKNOWN

    async def start_http_subprocess(
        self,
        server_key: str,
        cfg: McpServerConfig,
        shutdown_event: asyncio.Event | None = None,
    ) -> subprocess.Popen[bytes] | None:
        """Start a single HTTP subprocess MCP server; returns the Popen object or None."""
        await self._http_mgr.start(server_key, cfg, shutdown_event=shutdown_event)
        return self._http_mgr._http_procs.get(server_key)

    def get_process_snapshot(self, server_key: str) -> dict | None:
        """Return process snapshot dict for a managed subprocess server, or None."""
        return self._http_mgr.get_process_snapshot(server_key)

    def cleanup_server_resources(self, server_key: str) -> str:
        """Clean up resources for a removed MCP server. Delegates to HttpServerLifecycleManager."""
        return self._http_mgr._cleanup_server_resources(server_key)

    def verify_running(self, server_key: str) -> bool:
        """Return whether the HTTP subprocess server is running; delegates to HttpServerLifecycleManager."""
        return self._http_mgr.verify_running(server_key)

    async def verify_running_async(self, server_key: str, cfg: McpServerConfig) -> bool:
        """Async /health liveness check for a server; delegates to HttpServerLifecycleManager."""
        return await self._http_mgr.verify_running_async(server_key, cfg)

    def get_process_info(self, server_key: str) -> ProcessInfoSnapshot | None:
        """Return ProcessInfoSnapshot for a managed subprocess server, or None; delegates."""
        return self._http_mgr.get_process_info(server_key)

    def list_processes(self) -> list[ProcessInfoSnapshot]:
        """Return ProcessInfoSnapshot list for all managed subprocess servers; delegates."""
        return self._http_mgr.list_processes()


class _ServerLifecycleRouter:
    """Coordinator for HTTP MCP server lifecycle management.

    Delegates subprocess operations to _SubprocessLifecycleManager while
    adding:
    - Shutdown guard (_shutting_down): prevents start/restart after shutdown begins.
    - LifecycleState tracking (_states): provides get_transport_state() with real values.
    - Process snapshot API: get_process_info() and list_processes() for observability.
    """

    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],
        tool_executor: ToolExecutor,
    ) -> None:
        """Initialize the lifecycle router with MCP server configurations."""
        self._server_configs = server_configs
        self._subprocess_mgr = _SubprocessLifecycleManager(
            server_configs, tool_executor
        )
        self._shutting_down: bool = False
        self._states: dict[str, LifecycleState] = {}
        self._failed_starts: dict[str, float] = {}

    def _set_state(self, server_key: str, new_state: LifecycleState) -> None:
        """Transition the server state with validation."""
        # First-time server: no prior state to validate against.
        if server_key not in self._states:
            _logger.info(
                "Lifecycle: initializing state for %r -> %r",
                server_key,
                new_state,
            )
            self._states[server_key] = new_state
            return

        current = self._states[server_key]
        try:
            assert_valid_transition(current, new_state)
        except ValueError:
            _logger.warning(
                "Lifecycle: invalid state transition %r -> %r for %r",
                current,
                new_state,
                server_key,
            )
        self._states[server_key] = new_state

    async def _run_lifecycle_transition(
        self,
        server_key: str,
        op: Callable[[], Awaitable[object]],
    ) -> None:
        """Run *op* as a STARTING transition, marking RUNNING on success or FAILED on error."""
        self._set_state(server_key, LifecycleState.STARTING)
        try:
            await op()
            self._failed_starts.pop(server_key, None)
            self._set_state(server_key, LifecycleState.RUNNING)
        except Exception:
            self._failed_starts[server_key] = time.monotonic()
            self._set_state(server_key, LifecycleState.FAILED)
            raise

    def _cooldown_remaining(self, server_key: str) -> float:
        """Return the seconds left in *server_key*'s cooldown window (0.0 when never failed)."""
        last_failure = self._failed_starts.get(server_key)
        if last_failure is None:
            return 0.0
        return _COOLDOWN_SECONDS - (time.monotonic() - last_failure)

    def _in_cooldown(self, server_key: str) -> bool:
        """Return True if the server is within its cooldown window."""
        last_failure = self._failed_starts.get(server_key)
        if not last_failure:
            return False
        remaining = self._cooldown_remaining(server_key)
        if remaining > 0:
            _logger.info(
                "Lifecycle: %r still in cooldown (%.1fs remaining)",
                server_key,
                remaining,
            )
            return True
        # Cooldown expired — remove stale entry
        del self._failed_starts[server_key]
        return False

    async def ensure_ready(self, server_key: str) -> None:
        """Ensure the HTTP subprocess server is running; start it if needed."""
        if self._shutting_down:
            _logger.debug(
                "Lifecycle: ensure_ready(%r) ignored — shutting down", server_key
            )
            return
        cfg = self._server_configs.get(server_key)
        if cfg is None or not _is_http_subprocess_server(cfg):
            return
        if self._in_cooldown(server_key):
            remaining = self._cooldown_remaining(server_key)
            raise ServerCooldownError(
                f"MCP server {server_key!r} is restarting. Try again in {max(0, remaining):.0f}s"
            )
        os_alive = self._subprocess_mgr.verify_running(server_key)
        if not os_alive:
            _logger.info(
                "Lifecycle: %r not running; starting via ensure_ready", server_key
            )
            await self._run_lifecycle_transition(
                server_key,
                lambda: self._subprocess_mgr.start_http_subprocess(server_key, cfg),
            )
        else:
            app_healthy = await self._subprocess_mgr.verify_running_async(
                server_key, cfg
            )
            if not app_healthy:
                _logger.warning(
                    "Lifecycle: %r OS-alive but app-unhealthy; restarting", server_key
                )
                await self._run_lifecycle_transition(
                    server_key,
                    lambda: self._subprocess_mgr.restart(server_key),
                )

    async def shutdown_all(self) -> list[tuple[str, TerminationOutcome]]:
        """Shut down all managed HTTP subprocess servers."""
        self._shutting_down = True
        unconfirmed = await self._subprocess_mgr.shutdown_all()
        for key in self._server_configs:
            self._set_state(key, LifecycleState.STOPPED)
        return unconfirmed

    async def start_http_subprocess(
        self,
        server_key: str,
        cfg: McpServerConfig,
        shutdown_event: asyncio.Event | None = None,
    ) -> subprocess.Popen[bytes] | None:
        """Start a single HTTP subprocess MCP server; returns the Popen object or None."""
        if self._shutting_down:
            _logger.debug(
                "Lifecycle: start_http_subprocess(%r) ignored — shutting down",
                server_key,
            )
            return None
        if self._in_cooldown(server_key):
            return None
        captured: subprocess.Popen[bytes] | None = None

        async def _start() -> None:
            nonlocal captured
            captured = await self._subprocess_mgr.start_http_subprocess(
                server_key, cfg, shutdown_event=shutdown_event
            )

        await self._run_lifecycle_transition(server_key, _start)
        return captured

    async def restart(self, server_key: str) -> None:
        """Restart a single HTTP subprocess MCP server."""
        if self._shutting_down:
            _logger.warning(
                "Lifecycle: restart(%r) ignored — shutting down", server_key
            )
            return
        cfg = self._server_configs.get(server_key)
        if cfg is None or cfg.startup_mode != StartupMode.SUBPROCESS:
            _logger.warning(
                "Lifecycle: restart %r: not a subprocess-mode server; manual restart required",
                server_key,
            )
            return
        if self._in_cooldown(server_key):
            return
        await self._run_lifecycle_transition(
            server_key, lambda: self._subprocess_mgr.restart(server_key)
        )

    async def shutdown_idle(self) -> None:
        """No-op for idle shutdown — only applies to stdio servers."""
        if self._shutting_down:
            _logger.debug("Lifecycle: shutdown_idle ignored — shutting down")
            return

    def get_transport_state(self, server_key: str) -> LifecycleState:
        """Return the current lifecycle state for a server."""
        return self._states.get(server_key, LifecycleState.UNKNOWN)

    def get_process_snapshot(self, server_key: str) -> dict | None:
        """Return process snapshot dict for a managed subprocess server, or None."""
        return self._subprocess_mgr.get_process_snapshot(server_key)

    def get_process_info(self, server_key: str) -> ProcessInfoSnapshot | None:
        """Return ProcessInfoSnapshot for a managed subprocess server, or None."""
        return self._subprocess_mgr.get_process_info(server_key)

    def list_processes(self) -> list[ProcessInfoSnapshot]:
        """Return list of ProcessInfoSnapshot for all managed subprocess servers."""
        return self._subprocess_mgr.list_processes()

    def get_subprocess_server_configs(self) -> list[tuple[str, McpServerConfig]]:
        """Return (key, config) pairs for all HTTP subprocess-mode servers."""
        return [
            (key, cfg)
            for key, cfg in self._server_configs.items()
            if _is_http_subprocess_server(cfg)
        ]

    def cleanup_server_resources(self, server_key: str) -> str:
        """Clean up resources for a removed MCP server. Delegates to HttpServerLifecycleManager."""
        return self._subprocess_mgr.cleanup_server_resources(server_key)
