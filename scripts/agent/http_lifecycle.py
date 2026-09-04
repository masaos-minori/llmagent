"""scripts/agent/http_lifecycle.py

HTTP subprocess MCP server lifecycle: start, health-poll, restart, shutdown.

Extracted from lifecycle.py. _ServerLifecycleRouter in factory.py delegates
to HttpServerLifecycleManager for all HTTP subprocess operations.

Refactored: HttpServerLifecycleManager is now a thin composition facade
delegating to six concern-specific modules:
- CommandValidator: command allowlist and symlink resolution checks
- StderrLogManager: stderr log file creation, appending, and tail retrieval
- ProcessTerminator: graceful and forced process termination
- HealthChecker: HTTP health check polling
- ProcessSnapshotProvider: process info snapshots
- ShutdownCoordinator: coordinated shutdown of all managed processes
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import signal
import subprocess  # nosec B404 — used to launch admin-controlled MCP server processes
import time
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import IO

import httpx
from shared.mcp_config import McpServerConfig

from agent.secrets_masker import _mask_secrets
from .http_lifecycle_process_snapshot import ProcessInfoSnapshot

from .http_lifecycle_command_validator import CommandValidator
from .http_lifecycle_errors import HttpStartupError, StartupFailure
from .http_lifecycle_health_checker import HealthChecker
from .http_lifecycle_process_terminator import ProcessTerminator
from .http_lifecycle_process_snapshot import ProcessSnapshotProvider
from .http_lifecycle_shutdown_coordinator import ShutdownCoordinator
from .http_lifecycle_stderr_log import StderrLogManager

logger = logging.getLogger(__name__)

MCPSERVER_HEALTH_TIMEOUT: float = 5.0


class HttpServerLifecycleManager:
    """Manages HTTP subprocess MCP servers: start, health-poll, restart, shutdown.

    When stderr log redirect is active (H-1), each subprocess writes stderr to a
    per-server log file at /opt/llm/logs/mcp_servers/{server_key}.stderr.log instead of a pipe.

    When process group shutdown is active (H-8), subprocesses are started with
    start_new_session=True and terminated via os.killpg() to include child processes.
    """

    def __init__(
        self,
        *,
        command_validator: CommandValidator | None = None,
        stderr_log_manager: StderrLogManager | None = None,
        process_terminator: ProcessTerminator | None = None,
        health_checker: HealthChecker | None = None,
        snapshot_provider: ProcessSnapshotProvider | None = None,
        shutdown_coordinator: ShutdownCoordinator | None = None,
    ) -> None:
        """Initialize HttpServerLifecycleManager with injected components."""
        self._command_validator = command_validator or CommandValidator()
        self._stderr_log_manager = stderr_log_manager or StderrLogManager()
        self._process_terminator = process_terminator or ProcessTerminator()
        self._health_checker = health_checker or HealthChecker()
        self._snapshot_provider = snapshot_provider or ProcessSnapshotProvider()
        self._shutdown_coordinator = shutdown_coordinator or ShutdownCoordinator()
        self._http_procs: dict[str, subprocess.Popen[bytes]] = {}
        self._http_pgids: dict[str, int] = {}
        self._stderr_files: dict[str, IO[bytes]] = {}
        self._stderr_log_paths: dict[str, str] = {}
        self._last_health_check: dict[str, float] = {}

    def _open_stderr_log(self, server_key: str, cfg: McpServerConfig) -> IO[bytes]:
        """Open an append-mode file for the server's stderr output and track its path."""
        return self._stderr_log_manager.open_log(server_key, cfg)

    def _read_stderr_tail(self, server_key: str) -> str:
        """Read the last N bytes from a server's stderr log file."""
        return self._stderr_log_manager.read_tail(server_key)

    def _rotate_log(self, log_dir: Path, safe_key: str, cfg: McpServerConfig) -> None:
        """Rotate stderr log file by shifting numbered backups."""
        self._stderr_log_manager.rotate_log(log_dir, safe_key, cfg)

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
        if time.monotonic() - last_check < 10.0:
            return True
        try:
            hc_timeout = self._health_checker.compute_health_check_timeout(cfg.startup_timeout_sec)
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout=hc_timeout)
            ) as client:
                resp = await client.get(cfg.url.rstrip("/") + "/health")
                self._last_health_check[server_key] = time.monotonic()
                return resp.status_code == HTTPStatus.OK
        except (httpx.HTTPError, OSError):
            self._last_health_check[server_key] = time.monotonic()
            return False

    def _cleanup_server_resources(self, server_key: str) -> str:
        """Read stderr tail, close stderr file handle, and remove tracking data for a server."""
        stderr_content = self._read_stderr_tail(server_key)
        fh = self._stderr_files.pop(server_key, None)
        if fh is not None:
            fh.close()
        self._stderr_log_paths.pop(server_key, None)
        self._last_health_check.pop(server_key, None)
        return stderr_content

    def get_process_info(self, server_key: str) -> ProcessInfoSnapshot | None:
        """Return a read-only snapshot for a managed subprocess, or None if unknown."""
        proc = self._http_procs.get(server_key)
        if proc is None:
            return None
        pgid = self._http_pgids.get(server_key)
        return self._snapshot_provider.get_info(server_key, proc, pgid)

    def get_process_snapshot(self, server_key: str) -> dict | None:
        """Return a dict snapshot for a managed subprocess, or None if unknown."""
        proc = self._http_procs.get(server_key)
        if proc is None:
            return None
        pgid = self._http_pgids.get(server_key)
        return self._snapshot_provider.get_snapshot(server_key, proc, pgid)

    def list_processes(self) -> list[ProcessInfoSnapshot]:
        """Return snapshots for all currently managed subprocess servers."""
        return self._snapshot_provider.list_processes(self)

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
        # Note: cfg.env keys are already validated against a denylist in
        # McpServerConfig._validate_cross_fields() at config-load time,
        # so no additional filtering is performed here.
        env = self._command_validator.filter_env(cfg.env)
        stderr_fh = self._open_stderr_log(server_key, cfg)
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
            cmd_executable = self._command_validator.validate(server_key, cfg.cmd[0])
        except ValueError as e:
            stderr_fh.close()
            self._stderr_files.pop(server_key, None)
            self._stderr_log_paths.pop(server_key, None)
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=str(e),
                    stderr_full="",
                )
            ) from e

        try:
            proc = subprocess.Popen(  # nosec B603 — cmd comes from admin-controlled config, not user input  # noqa: S603
                cfg.cmd,
                stdout=subprocess.DEVNULL,
                stderr=stderr_fh,
                env=env,
                start_new_session=True,
            )
        except Exception:
            stderr_fh.close()
            self._stderr_files.pop(server_key, None)
            self._stderr_log_paths.pop(server_key, None)
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
                await self._process_terminator.terminate(proc, server_key, timeout=5.0)
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
                self._stderr_log_paths.pop(server_key, None)
                self._http_procs.pop(server_key, None)
                self._http_pgids.pop(server_key, None)
            raise e
        self._http_procs[server_key] = proc

        health_url = cfg.url.rstrip("/") + "/health"
        if cfg.startup_timeout_sec > 0:
            deadline = time.monotonic() + cfg.startup_timeout_sec
            hc_timeout = self._health_checker.compute_health_check_timeout(cfg.startup_timeout_sec)
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout=hc_timeout)
            ) as client:
                while time.monotonic() < deadline:
                    if proc.poll() is not None:
                        stderr_full = self._cleanup_server_resources(server_key)
                        failure = StartupFailure(
                            server_key=server_key,
                            reason="exited early",
                            stderr_full=stderr_full,
                        )
                        logger.error(
                            "Lifecycle: %r exited early; stderr (%s chars): %s",
                            server_key,
                            len(stderr_full),
                            _mask_secrets(stderr_full[:500]),
                        )
                        self._http_procs.pop(server_key, None)
                        self._http_pgids.pop(server_key, None)
                        raise HttpStartupError(failure)
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
                        logger.info(
                            "Lifecycle: health-check poll %r: %s", server_key, e
                        )
                    if await self._interruptible_poll_sleep(0.5, shutdown_event):
                        stderr_full = self._cleanup_server_resources(server_key)
                        failure = StartupFailure(
                            server_key=server_key,
                            reason="shutdown requested",
                            stderr_full=stderr_full,
                        )
                        self._http_procs.pop(server_key, None)
                        self._http_pgids.pop(server_key, None)
                        raise HttpStartupError(failure)

            stderr_full = self._cleanup_server_resources(server_key)
            await self._process_terminator.terminate(proc, server_key, timeout=5.0)
            timeout_failure = StartupFailure(
                server_key=server_key,
                reason=f"did not become healthy within {cfg.startup_timeout_sec}s",
                stderr_full=stderr_full,
            )
            self._http_procs.pop(server_key, None)
            self._http_pgids.pop(server_key, None)
            raise HttpStartupError(timeout_failure)
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
        self._stderr_log_paths.pop(server_key, None)
        self._last_health_check.pop(server_key, None)
        proc = self._http_procs.pop(server_key, None)
        if proc is not None and proc.poll() is None:
            logger.info("Lifecycle: terminating %r for restart", server_key)
            await self._process_terminator.terminate(proc, server_key)
        self._http_pgids.pop(server_key, None)
        await self.start(server_key, cfg)

    @staticmethod
    def _absorb_sigint_during_shutdown(signum: int, frame: object) -> None:
        """Silently absorb SIGINT signals during shutdown_all() to prevent orphaned subprocesses.

        When a user presses Ctrl-C twice while shutdown_all() is running, the second signal would
        normally interrupt the cleanup loop and leave HTTP subprocesses alive. This handler
        catches those signals and logs a warning instead of propagating the exception.
        """
        logger.warning(
            "Lifecycle: SIGINT received during shutdown_all(); ignoring until cleanup completes"
        )

    async def shutdown_all(self) -> None:
        """Terminate all HTTP subprocess servers and clear internal state."""
        old_sigint: object | None = None
        try:
            old_sigint = signal.getsignal(signal.SIGINT)
        except ValueError:
            old_sigint = None

        if old_sigint is not None:
            try:
                signal.signal(signal.SIGINT, self._absorb_sigint_during_shutdown)
            except ValueError:
                try:
                    asyncio.get_running_loop().call_soon_threadsafe(
                        lambda: signal.signal(
                            signal.SIGINT, self._absorb_sigint_during_shutdown
                        )
                    )
                except Exception as exc:  # noqa: BLE001 — scheduling the SIGINT guard handler is best-effort; failure must not block shutdown
                    logger.debug(
                        "Lifecycle: could not schedule SIGINT guard handler: %s", exc
                    )

        try:
            keys = list(self._http_procs.keys())
            for key in keys:
                proc = self._http_procs.pop(key, None)
                if proc is None:
                    continue
                if proc.poll() is not None:
                    logger.debug("Lifecycle: %r already exited; removing entry", key)
                else:
                    try:
                        await self._process_terminator.terminate(proc, key, timeout=5.0)
                    except (OSError, TimeoutError) as e:
                        logger.warning(
                            "Lifecycle: error stopping HTTP subprocess %r: %s", key, e
                        )
                self._http_pgids.pop(key, None)
                stderr_fh = self._stderr_files.pop(key, None)
                if stderr_fh is not None:
                    try:
                        stderr_fh.close()
                    except OSError as close_err:
                        logger.warning(
                            "Lifecycle: error closing stderr log for %r: %s",
                            key,
                            close_err,
                        )
            self._stderr_log_paths.clear()
            self._last_health_check.clear()
        finally:
            if old_sigint is not None:
                try:
                    signal.signal(signal.SIGINT, old_sigint)
                except ValueError:
                    try:
                        asyncio.get_running_loop().call_soon_threadsafe(
                            lambda: signal.signal(signal.SIGINT, old_sigint)
                        )
                    except Exception:  # noqa: BLE001 — restoring the original SIGINT handler is best-effort; failure must not block shutdown
                        pass
