"""scripts/agent/http_lifecycle.py

HTTP subprocess MCP server lifecycle: start, health-poll, restart, shutdown.

Extracted from lifecycle.py. _ServerLifecycleRouter in factory.py delegates
to HttpServerLifecycleManager for all HTTP subprocess operations.

Refactored: HttpServerLifecycleManager is a true composition facade delegating
all concern-specific work to six modules with zero pure-delegation wrappers:
- CommandValidator: command allowlist and symlink resolution checks
- StderrLogManager: stderr log file creation, appending, and tail retrieval
- ProcessTerminator: graceful and forced process termination
- HealthChecker: HTTP health check polling
- ProcessSnapshotProvider: process info snapshots
- ShutdownCoordinator: coordinated shutdown of all managed processes

Custom logic retained in this class:
- _read_stderr_tail: seek/read/decode implementation for stderr log tailing
- _wait_exited: asyncio-aware proc.poll() polling loop with timeout
- MCPSERVER_HEALTH_TIMEOUT: global constant for httpx.AsyncClient timeout
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil  # noqa: F401 — kept for tests patching agent.http_lifecycle.shutil.which (shared module object also used by CommandValidator)
import subprocess  # nosec B404 — used to launch admin-controlled MCP server processes
import time
from dataclasses import asdict
from http import HTTPStatus
from typing import IO, Any, NoReturn, cast

import httpx
from shared.mcp_config import McpServerConfig

from agent.secrets_masker import _mask_secrets
from agent.services.models import ProcessInfoSnapshot

from .http_lifecycle_command_validator import CommandValidator
from .http_lifecycle_errors import HttpStartupError, StartupFailure
from .http_lifecycle_health_checker import HEALTH_RECHECK_INTERVAL_SEC, HealthChecker
from .http_lifecycle_process_terminator import ProcessTerminator
from .http_lifecycle_shutdown_coordinator import ShutdownCoordinator
from .http_lifecycle_stderr_log_manager import StderrLogManager

logger = logging.getLogger(__name__)

MCPSERVER_HEALTH_TIMEOUT: float = 5.0
_TERMINATE_POLL_INTERVAL_SEC: float = 0.05
_STDERR_TAIL_BYTES: int = 64 * 1024
HEALTH_POLL_INTERVAL_SEC: float = 0.5
TERMINATE_TIMEOUT_SEC: float = 5.0
RESTART_TERMINATE_TIMEOUT_SEC: float = 3.0


class HttpServerLifecycleManager:
    """Manages HTTP subprocess MCP servers: start, health-poll, restart, shutdown.

    When stderr log redirect is active (H-1), each subprocess writes stderr to a
    per-server log file at /opt/llm/logs/mcp_servers/{server_key}.stderr.log instead of a pipe.

    When process group shutdown is active (H-8), subprocesses are started with
    start_new_session=True and terminated via os.killpg() to include child processes.
    """

    _ALLOWED_COMMANDS: frozenset[str] = frozenset(
        {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn"}
    )

    def __init__(
        self,
        *,
        command_validator: CommandValidator | None = None,
        stderr_log_manager: StderrLogManager | None = None,
        process_terminator: ProcessTerminator | None = None,
        health_checker: HealthChecker | None = None,
        shutdown_coordinator: ShutdownCoordinator | None = None,
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

    def _read_stderr_tail(self, server_key: str) -> str:
        """Read the last N bytes from a server's stderr log file."""
        log_path = self._stderr_log_manager.get_log_path(server_key)
        if not log_path:
            return ""
        try:
            with open(log_path, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - _STDERR_TAIL_BYTES))
                return f.read().decode(errors="replace")
        except OSError:
            return ""

    async def _wait_exited(self, proc: subprocess.Popen[bytes], timeout: float) -> bool:
        """Poll proc.poll() (non-blocking) until it exits or timeout elapses.

        Deliberately avoids asyncio.to_thread: wrapping a blocking proc.wait() in a
        thread cannot be cancelled once asyncio.wait_for's timeout fires, so a
        process stuck in an uninterruptible (D) state leaves a live, non-daemon
        ThreadPoolExecutor worker that CPython's interpreter-shutdown atexit hook
        (concurrent.futures.thread._python_exit) then blocks on indefinitely.
        """
        deadline = time.monotonic() + timeout
        while proc.poll() is None:
            if time.monotonic() >= deadline:
                return False
            await asyncio.sleep(_TERMINATE_POLL_INTERVAL_SEC)
        return True

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
            result = await HealthChecker.verify_running_async(server_key, cfg, url=url)
            self._last_health_check[server_key] = time.monotonic()
            return result
        except (httpx.HTTPError, OSError) as exc:
            logger.error("Health check failed for %s: %s", cfg.url, exc)
            self._last_health_check[server_key] = time.monotonic()
            return False

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
        stderr_content = self._read_stderr_tail(server_key)
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
        running = proc.poll() is None
        last_exit_code = proc.poll() if not running else None
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

    async def _interruptible_poll_sleep(
        self, delay: float, shutdown_event: asyncio.Event | None
    ) -> bool:
        """Sleep for `delay` seconds, racing against `shutdown_event`.

        Returns True iff the shutdown event fired before `delay` elapsed (caller
        should abort the health-poll loop); returns False if the full delay
        elapsed normally or no `shutdown_event` was configured.
        """
        if shutdown_event is None:
            await asyncio.sleep(delay)
            return False
        sleep_task = asyncio.ensure_future(asyncio.sleep(delay))
        shutdown_task = asyncio.ensure_future(shutdown_event.wait())
        done, pending = await asyncio.wait(
            {sleep_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        return shutdown_task in done

    async def _create_and_validate_proc(
        self,
        server_key: str,
        cfg: McpServerConfig,
    ) -> tuple[subprocess.Popen[bytes], IO[bytes]]:
        """Create and validate subprocess for the given server configuration.

        Validates the command, filters environment variables, creates the subprocess,
        and handles getpgid failure with resource cleanup.

        Returns:
            A tuple of (proc, stderr_fh) on success.

        Raises:
            HttpStartupError: If command validation fails or getpgid fails.
        """
        env = self._command_validator.filter_env(cfg.env)
        stderr_fh = self._stderr_log_manager.open_log(server_key, cfg)
        self._stderr_files[server_key] = stderr_fh
        if not cfg.cmd or not cfg.cmd[0]:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason="Empty command configuration",
                    stderr_full="",
                )
            )

        # Validate command using CommandValidator
        try:
            self._command_validator.validate(server_key, cfg.cmd[0])
        except ValueError as e:
            stderr_fh.close()
            self._stderr_files.pop(server_key, None)
            self._stderr_log_manager.forget(server_key)
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=str(e),
                    stderr_full="",
                )
            ) from e

        try:
            popen_kwargs: dict[str, Any] = {
                "stdout": subprocess.DEVNULL,
                "stderr": stderr_fh,
                "env": env,
                "start_new_session": True,
            }
            if cfg.fields:
                popen_kwargs.update(cfg.fields)
            proc = cast(
                subprocess.Popen[bytes],
                subprocess.Popen(  # nosec B603 — cmd comes from admin-controlled config, not user input  # noqa: S603
                    cfg.cmd, **popen_kwargs
                ),
            )
        except Exception:
            stderr_fh.close()
            self._stderr_files.pop(server_key, None)
            self._stderr_log_manager.forget(server_key)
            raise
        try:
            self._http_pgids[server_key] = os.getpgid(proc.pid)
        except OSError as e:
            logger.warning(
                "Lifecycle: getpgid() failed for %r pid=%d; cleaning up",
                server_key,
                proc.pid,
            )
            try:
                await self._process_terminator.terminate_with_timeout(
                    proc, server_key, timeout=TERMINATE_TIMEOUT_SEC
                )
                poll_result = proc.poll()
                if poll_result is not None and poll_result != 0:
                    logger.info(
                        "Lifecycle: subprocess %r (pid=%d) terminated with exit code %d",
                        server_key,
                        proc.pid,
                        poll_result,
                    )
            finally:
                # Always cleanup resources if getpgid fails, even if termination fails
                stderr_fh.close()
                self._stderr_files.pop(server_key, None)
                self._stderr_log_manager.forget(server_key)
                self._http_procs.pop(server_key, None)
                self._http_pgids.pop(server_key, None)
            raise e
        self._http_procs[server_key] = proc
        return proc, stderr_fh

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
        client: httpx.AsyncClient,
        deadline: float,
        shutdown_event: asyncio.Event | None,
    ) -> None:
        """Poll /health endpoint until the server becomes healthy or timeout expires.

        Polls the health endpoint in a loop, checking for early exit and shutdown
        events between polls. Raises HttpStartupError on early exit, shutdown,
        or timeout.

        Args:
            server_key: Server identifier key.
            cfg: Server configuration.
            proc: Subprocess instance to monitor.
            client: Async HTTP client for health check requests.
            deadline: Monotonic time at which to abort polling.
            shutdown_event: Optional event to race against poll sleep.

        Raises:
            HttpStartupError: On early exit, shutdown, or timeout.
        """
        health_url = cfg.url.rstrip("/") + "/health"
        hc_timeout = self._health_checker.compute_health_check_timeout(
            cfg.startup_timeout_sec, MCPSERVER_HEALTH_TIMEOUT
        )
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout=hc_timeout)
        ) as client:
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    stderr_full = self._cleanup_server_resources(server_key)
                    logger.error(
                        "Lifecycle: %r exited early; stderr (%s chars): %s",
                        server_key,
                        len(stderr_full),
                        _mask_secrets(stderr_full[:500]),
                    )
                    self._raise_startup_failure(server_key, "exited early", stderr_full)
                try:
                    resp = await client.get(health_url)
                    if resp.status_code == HTTPStatus.OK:
                        self._last_health_check[server_key] = time.monotonic()
                        logger.info(
                            "Lifecycle: HTTP subprocess %r ready",
                            server_key,
                        )
                        return
                except (httpx.HTTPError, OSError) as e:
                    logger.info("Lifecycle: health-check poll %r: %s", server_key, e)
                if await self._interruptible_poll_sleep(
                    HEALTH_POLL_INTERVAL_SEC, shutdown_event
                ):
                    stderr_full = self._cleanup_server_resources(server_key)
                    self._raise_startup_failure(
                        server_key, "shutdown requested", stderr_full
                    )

            stderr_full = self._cleanup_server_resources(server_key)
            await self._process_terminator.terminate_with_timeout(
                proc, server_key, timeout=TERMINATE_TIMEOUT_SEC
            )
            self._raise_startup_failure(
                server_key,
                f"did not become healthy within {cfg.startup_timeout_sec}s",
                stderr_full,
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
        proc, stderr_fh = await self._create_and_validate_proc(server_key, cfg)

        if cfg.startup_timeout_sec > 0:
            deadline = time.monotonic() + cfg.startup_timeout_sec
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout=MCPSERVER_HEALTH_TIMEOUT)
            ) as client:
                await self._health_poll_until_ready(
                    server_key, cfg, proc, client, deadline, shutdown_event
                )
        else:
            logger.info(
                "Lifecycle: skipping health check for %r (timeout=0)",
                server_key,
            )

    async def restart(self, server_key: str, cfg: McpServerConfig) -> None:
        """Terminate and restart an HTTP subprocess server."""
        stderr_fh = self._stderr_files.pop(server_key, None)
        if stderr_fh is not None:
            try:
                stderr_fh.close()
            except OSError:
                pass
        self._stderr_log_manager.forget(server_key)
        self._last_health_check.pop(server_key, None)
        proc = self._http_procs.pop(server_key, None)
        if proc is not None and proc.poll() is None:
            logger.info("Lifecycle: terminating %r for restart", server_key)
            await self._process_terminator.terminate_with_timeout(proc, server_key)
        self._http_pgids.pop(server_key, None)
        await self.start(server_key, cfg)

    async def shutdown_all(self) -> None:
        """Shut down all managed servers.

        Delegates to ShutdownCoordinator.shutdown_all().
        """
        await self._shutdown_coordinator.shutdown_all(self)
