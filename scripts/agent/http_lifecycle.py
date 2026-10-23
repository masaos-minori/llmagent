"""scripts/agent/http_lifecycle.py

HTTP subprocess MCP server lifecycle: start, health-poll, restart, shutdown.

Extracted from lifecycle.py. _ServerLifecycleRouter in lifecycle_router.py delegates
to HttpServerLifecycleManager for all HTTP subprocess operations.

Refactored: HttpServerLifecycleManager is a composition facade that delegates
concern-specific work to six modules:
- CommandValidator: command allowlist and symlink resolution checks
- StderrLogManager: stderr log file creation, appending, and tail retrieval
- ProcessTerminator: graceful and forced process termination
- HealthChecker: HTTP health check polling, including the startup readiness poll loop
- ShutdownCoordinator: coordinated shutdown of all managed processes
- SubprocessLauncher: subprocess spawn, pgid capture, and startup failure cleanup

Two methods delegate with arguments rather than forwarding the call unchanged:
shutdown_all passes the manager to ShutdownCoordinator, and
_health_poll_until_ready passes the manager and this module's poll timings to
HealthChecker.poll_until_ready. SubprocessLauncher is instead constructed with this
class's components and tracking dicts, which it holds by reference.

Custom logic retained in this class:
- MCPSERVER_HEALTH_TIMEOUT: global constant for httpx.AsyncClient timeout
- process info snapshots: _build_snapshot and the snapshot accessors
- startup failure reporting: _raise_startup_failure and the start() orchestration
  that combines SubprocessLauncher with the health poll
"""

from __future__ import annotations

import asyncio
import logging
import subprocess  # nosec B404 — used to launch admin-controlled MCP server processes
import time
from collections.abc import Iterator
from dataclasses import asdict
from typing import IO, NoReturn

import httpx
from shared.mcp_config import McpServerConfig

from agent.services.models import ProcessInfoSnapshot

from .http_lifecycle_command_validator import CommandValidator
from .http_lifecycle_errors import HttpStartupError, StartupFailure, TerminationOutcome
from .http_lifecycle_health_checker import HEALTH_RECHECK_INTERVAL_SEC, HealthChecker
from .http_lifecycle_process_terminator import ProcessTerminator
from .http_lifecycle_shutdown_coordinator import ShutdownCoordinator
from .http_lifecycle_stderr_log_manager import StderrLogManager
from .http_lifecycle_subprocess_launcher import SubprocessLauncher

logger = logging.getLogger(__name__)

MCPSERVER_HEALTH_TIMEOUT: float = 5.0
HEALTH_POLL_INTERVAL_SEC: float = 0.5
TERMINATE_TIMEOUT_SEC: float = 5.0


class HttpServerLifecycleManager:
    """Manages HTTP subprocess MCP servers: start, health-poll, restart, shutdown.

    When stderr log redirect is active (H-1), each subprocess writes stderr to a
    per-server log file at /opt/llm/logs/mcp_servers/{server_key}.stderr.log instead of a pipe.

    When process group shutdown is active (H-8), subprocesses are started with
    start_new_session=True and terminated via os.killpg() to include child processes.
    """

    _ALLOWED_COMMANDS: frozenset[str] = frozenset(
        {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn", "uv"}
    )

    def __init__(
        self,
        *,
        command_validator: CommandValidator | None = None,
        stderr_log_manager: StderrLogManager | None = None,
        process_terminator: ProcessTerminator | None = None,
        health_checker: HealthChecker | None = None,
        shutdown_coordinator: ShutdownCoordinator | None = None,
        subprocess_launcher: SubprocessLauncher | None = None,
    ) -> None:
        """Initialize HttpServerLifecycleManager with injected components."""
        self._command_validator = command_validator or CommandValidator(
            allowed_commands=type(self)._ALLOWED_COMMANDS
        )
        self._stderr_log_manager = stderr_log_manager or StderrLogManager()
        self._process_terminator = process_terminator or ProcessTerminator()
        self._health_checker = health_checker or HealthChecker()
        self._shutdown_coordinator = shutdown_coordinator or ShutdownCoordinator()
        self._http_procs: dict[str, subprocess.Popen[bytes]] = {}
        self._http_pgids: dict[str, int] = {}
        self._stderr_files: dict[str, IO[bytes]] = {}
        self._last_health_check: dict[str, float] = {}
        self._subprocess_launcher = subprocess_launcher or SubprocessLauncher(
            command_validator=self._command_validator,
            stderr_log_manager=self._stderr_log_manager,
            process_terminator=self._process_terminator,
            http_procs=self._http_procs,
            http_pgids=self._http_pgids,
            stderr_files=self._stderr_files,
            terminate_timeout_sec=TERMINATE_TIMEOUT_SEC,
        )

    def verify_running(self, server_key: str) -> bool:
        """Return True if the HTTP subprocess server is running, False if missing or exited."""
        proc = self._http_procs.get(server_key)
        if proc is None or proc.poll() is not None:
            logger.warning(
                "Lifecycle: HTTP subprocess %r is not running; it should have been started at agent init",
                server_key,
            )
            return False
        return True

    async def verify_running_async(self, server_key: str, cfg: McpServerConfig) -> bool:
        """Check liveness via HTTP /health endpoint, rate-limited by re-check interval."""
        if not self.verify_running(server_key):
            return False
        last_check = self._last_health_check.get(server_key, 0.0)
        if time.monotonic() - last_check < HEALTH_RECHECK_INTERVAL_SEC:
            return True
        url = cfg.url.rstrip("/") + "/health"
        try:
            result = await HealthChecker.verify_running_async(
                server_key, cfg, url=url, headers=cfg.auth_headers()
            )
            self._mark_health_checked(server_key)
            return result
        except (httpx.HTTPError, OSError) as exc:
            logger.error("Health check failed for %s: %s", cfg.url, exc)
            self._mark_health_checked(server_key)
            return False

    def _mark_health_checked(self, server_key: str) -> None:
        """Record the time of a health observation to rate-limit the next check."""
        self._last_health_check[server_key] = time.monotonic()

    def _clear_server_tracking_data(self, server_key: str) -> None:
        """Remove health check timestamps, stderr file handles, and paths for a server."""
        fh = self._stderr_files.pop(server_key, None)
        if fh is not None:
            try:
                fh.close()
            except OSError:
                pass
        self._stderr_log_manager.forget(server_key)
        self._last_health_check.pop(server_key, None)

    def _cleanup_server_resources(self, server_key: str) -> str:
        """Read stderr tail, close stderr file handle, and remove tracking data for a server."""
        stderr_content = self._stderr_log_manager.read_tail(server_key).decode(
            errors="replace"
        )
        self._clear_server_tracking_data(server_key)
        return stderr_content

    def cleanup_server_key(self, server_key: str) -> None:
        """Remove process tracking entries for a server key.

        Called by ShutdownCoordinator after terminating a server process.
        Removes the process entry, pgid entry, and delegates stderr/log cleanup
        to _clear_server_tracking_data.
        """
        self._http_procs.pop(server_key, None)
        self._http_pgids.pop(server_key, None)
        self._clear_server_tracking_data(server_key)

    def remove_process_entry(self, server_key: str) -> None:
        """Remove the process entry from tracking.

        Called before termination to prevent double-shutdown if termination fails.
        Does NOT close file handles or clear other tracking data — those are cleaned
        up after termination via cleanup_server_key().
        """
        self._http_procs.pop(server_key, None)

    def clear_all_health_checks(self) -> None:
        """Clear all health check timestamps.

        Called by ShutdownCoordinator at the end of shutdown_all().
        """
        self._last_health_check.clear()

    @property
    def process_terminator(self) -> ProcessTerminator:
        """Return the configured ProcessTerminator."""
        return self._process_terminator

    def _build_snapshot(self, server_key: str) -> ProcessInfoSnapshot | None:
        """Return a typed snapshot for a managed subprocess, or None if unknown."""
        proc = self._http_procs.get(server_key)
        if proc is None:
            return None
        exit_code = proc.poll()
        running = exit_code is None
        last_exit_code = None if running else exit_code
        pgid = self._http_pgids.get(server_key)
        stderr_log = self._stderr_log_manager.get_log_path(server_key) or ""
        return ProcessInfoSnapshot(
            server_key=server_key,
            managed=True,
            pid=proc.pid,
            pgid=pgid,
            running=running,
            last_exit_code=last_exit_code,
            stderr_log=stderr_log,
        )

    def get_process_info(self, server_key: str) -> ProcessInfoSnapshot | None:
        """Return a read-only snapshot for a managed subprocess, or None if unknown."""
        return self._build_snapshot(server_key)

    def get_process_snapshot(self, server_key: str) -> dict | None:
        """Return a dict snapshot for a managed subprocess, or None if unknown."""
        snap = self._build_snapshot(server_key)
        if snap is None:
            return None
        return asdict(snap)

    def list_processes(self) -> list[ProcessInfoSnapshot]:
        """Return snapshots for all currently managed subprocess servers."""
        return [
            snap
            for key in list(self._http_procs.keys())
            if (snap := self.get_process_info(key)) is not None
        ]

    def iter_processes(self) -> Iterator[tuple[str, subprocess.Popen[bytes]]]:
        """Yield (server_key, proc) pairs for all managed HTTP subprocess servers.

        This method provides controlled access to managed processes without
        exposing the internal `_http_procs` dictionary directly. Callers receive
        an iterator and cannot modify the underlying dictionary.
        """
        yield from self._http_procs.items()

    def _raise_startup_failure(
        self, server_key: str, reason: str, stderr_full: str
    ) -> NoReturn:
        """Drop tracked process/pgid entries and raise HttpStartupError with the given reason."""
        self._http_procs.pop(server_key, None)
        self._http_pgids.pop(server_key, None)
        raise HttpStartupError(
            StartupFailure(
                server_key=server_key, reason=reason, stderr_full=stderr_full
            )
        )

    async def _health_poll_until_ready(
        self,
        server_key: str,
        cfg: McpServerConfig,
        proc: subprocess.Popen[bytes],
        deadline: float,
        shutdown_event: asyncio.Event | None,
    ) -> None:
        """Delegate the /health readiness poll loop to HealthChecker.poll_until_ready.

        Supplies this module's poll timings so the health checker does not import
        them from http_lifecycle.py.

        Args:
            server_key: Server identifier key.
            cfg: Server configuration.
            proc: Subprocess instance to monitor.
            deadline: Monotonic time at which to abort polling.
            shutdown_event: Optional event to race against poll sleep.

        Raises:
            HttpStartupError: On early exit, shutdown, or timeout.
        """
        await self._health_checker.poll_until_ready(
            self,
            server_key,
            cfg,
            proc,
            deadline,
            shutdown_event,
            poll_interval_sec=HEALTH_POLL_INTERVAL_SEC,
            request_timeout_sec=MCPSERVER_HEALTH_TIMEOUT,
            terminate_timeout_sec=TERMINATE_TIMEOUT_SEC,
        )

    async def start(
        self,
        server_key: str,
        cfg: McpServerConfig,
        shutdown_event: asyncio.Event | None = None,
    ) -> None:
        """Start an HTTP MCP server subprocess and poll /health until ready.

        Idempotent: reuses an already-running process.
        Stores the full stderr in StartupFailure when the process exits early
        or the health-poll times out; raises RuntimeError in both cases.
        When `shutdown_event` fires mid-poll, aborts within roughly one poll
        interval (0.5s) instead of waiting up to the full startup timeout.
        """
        existing = self._http_procs.get(server_key)
        if existing is not None and existing.poll() is None:
            logger.info(
                "Lifecycle: HTTP subprocess %r already running (reusing)",
                server_key,
            )
            return

        logger.info(
            "Lifecycle: starting HTTP subprocess %r: %s",
            server_key,
            cfg.cmd,
        )
        proc, stderr_fh = await self._subprocess_launcher.create_and_validate_proc(
            server_key, cfg
        )

        if cfg.startup_timeout_sec > 0:
            deadline = time.monotonic() + cfg.startup_timeout_sec
            await self._health_poll_until_ready(
                server_key, cfg, proc, deadline, shutdown_event
            )
        else:
            logger.info(
                "Lifecycle: skipping health check for %r (timeout=0)",
                server_key,
            )

    async def restart(self, server_key: str, cfg: McpServerConfig) -> None:
        """Terminate and restart an HTTP subprocess server."""
        self._clear_server_tracking_data(server_key)
        proc = self._http_procs.pop(server_key, None)
        if proc is not None and proc.poll() is None:
            logger.info("Lifecycle: terminating %r for restart", server_key)
            outcome = await self._process_terminator.terminate_with_timeout(
                proc, server_key, timeout=TERMINATE_TIMEOUT_SEC
            )
            if not outcome.confirmed:
                logger.error(
                    "Lifecycle: %r pid=%s not confirmed stopped before restart (%s)",
                    server_key,
                    proc.pid,
                    outcome,
                )
        self._http_pgids.pop(server_key, None)
        await self.start(server_key, cfg)

    async def shutdown_all(self) -> list[tuple[str, TerminationOutcome]]:
        """Shut down all managed servers.

        Delegates to ShutdownCoordinator.shutdown_all(); returns the servers whose
        exit was not confirmed (empty when every started server was confirmed gone).
        """
        return await self._shutdown_coordinator.shutdown_all(self)
