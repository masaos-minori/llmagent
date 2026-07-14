"""agent/http_lifecycle.py

HTTP subprocess MCP server lifecycle: start, health-poll, restart, shutdown.

Extracted from lifecycle.py. _ServerLifecycleRouter in factory.py delegates
to HttpServerLifecycleManager for all HTTP subprocess operations.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import signal
import subprocess  # nosec B404 — used to launch admin-controlled MCP server processes
import time
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import IO

import httpx
from agent.services.models import ProcessInfoSnapshot
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
    """Manages HTTP subprocess MCP servers: start, health-poll, restart, shutdown.

    When stderr log redirect is active (H-1), each subprocess writes stderr to a
    per-server log file at /opt/llm/logs/mcp_servers/{server_key}.stderr.log instead of a pipe.

    When process group shutdown is active (H-8), subprocesses are started with
    start_new_session=True and terminated via os.killpg() to include child processes.
    """

    _STDERR_TAIL_BYTES = 64 * 1024
    _TERMINATE_POLL_INTERVAL_SEC: float = 0.05

    def __init__(self) -> None:
        self._http_procs: dict[str, subprocess.Popen[bytes]] = {}
        self._http_pgids: dict[str, int] = {}
        self._stderr_files: dict[str, IO[bytes]] = {}
        self._stderr_log_paths: dict[str, str] = {}

    def _open_stderr_log(self, server_key: str) -> IO[bytes]:
        safe_key = re.sub(r"[^A-Za-z0-9_-]", "_", server_key)
        log_dir = Path("/opt/llm/logs/mcp_servers")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{safe_key}.stderr.log"
        fh = log_path.open("ab")
        self._stderr_log_paths[server_key] = str(log_path)
        return fh

    def _read_stderr_tail(self, server_key: str) -> str:
        log_path = self._stderr_log_paths.get(server_key)
        if not log_path:
            return ""
        try:
            with open(log_path, "rb") as f:  # noqa: PTH123
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - self._STDERR_TAIL_BYTES))
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
            await asyncio.sleep(self._TERMINATE_POLL_INTERVAL_SEC)
        return True

    async def _terminate_with_timeout(
        self,
        proc: subprocess.Popen[bytes],
        server_key: str,
        timeout: float = 3.0,
    ) -> None:
        """Terminate proc; escalate to kill if terminate times out."""
        if proc.poll() is not None:
            return
        pgid = self._http_pgids.get(server_key)
        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGTERM)  # nosec B603
            except (ProcessLookupError, OSError):
                proc.terminate()
        else:
            proc.terminate()
        if await self._wait_exited(proc, timeout):
            return
        logger.warning(
            "Lifecycle: force-killing %r (terminate timed out)",
            server_key,
        )
        pgid = self._http_pgids.get(server_key)
        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGKILL)  # nosec B603
            except (ProcessLookupError, OSError):
                proc.kill()
        else:
            proc.kill()
        if not await self._wait_exited(proc, timeout):
            logger.warning(
                "Lifecycle: %r still not terminated after kill",
                server_key,
            )

    def verify_running(self, server_key: str) -> bool:
        """Return True if the HTTP subprocess server is running, False if missing or exited."""
        proc = self._http_procs.get(server_key)
        if proc is None or proc.poll() is not None:
            logger.warning(
                "Lifecycle: HTTP subprocess %r is not running;"
                " it should have been started at agent init",
                server_key,
            )
            return False
        return True

    def get_process_snapshot(self, server_key: str) -> dict | None:
        """Return {pid, pgid, running, last_exit_code} for a managed subprocess server, or None if unknown."""
        proc = self._http_procs.get(server_key)
        if proc is None:
            return None
        running = proc.poll() is None
        pgid = getattr(self, "_http_pgids", {}).get(server_key)
        return {
            "pid": proc.pid,
            "pgid": pgid,
            "running": running,
            "last_exit_code": proc.poll(),
        }

    def get_process_info(self, server_key: str) -> ProcessInfoSnapshot | None:
        """Return a read-only snapshot for a managed subprocess, or None if unknown."""
        proc = self._http_procs.get(server_key)
        if proc is None:
            return None
        running = proc.poll() is None
        last_exit_code = proc.poll() if not running else None
        pgid = getattr(self, "_http_pgids", {}).get(server_key)
        stderr_log = getattr(self, "_stderr_log_paths", {}).get(server_key, "")
        return ProcessInfoSnapshot(
            server_key=server_key,
            managed=True,
            pid=proc.pid,
            pgid=pgid,
            running=running,
            last_exit_code=last_exit_code,
            stderr_log=stderr_log,
        )

    def list_processes(self) -> list[ProcessInfoSnapshot]:
        """Return snapshots for all currently managed subprocess servers."""
        return [
            snap
            for key in list(self._http_procs.keys())
            if (snap := self.get_process_info(key)) is not None
        ]

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
                "Lifecycle: HTTP subprocess %r already running (reusing)",
                server_key,
            )
            return

        logger.info(
            "Lifecycle: starting HTTP subprocess %r: %s",
            server_key,
            cfg.cmd,
        )
        env = None
        if cfg.env:
            env = {**os.environ, **cfg.env}
        stderr_fh = self._open_stderr_log(server_key)
        self._stderr_files[server_key] = stderr_fh
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
        except OSError:
            pass
        self._http_procs[server_key] = proc

        health_url = cfg.url.rstrip("/") + "/health"
        if cfg.startup_timeout_sec > 0:
            deadline = time.monotonic() + cfg.startup_timeout_sec
            async with httpx.AsyncClient(timeout=2.0) as client:
                while time.monotonic() < deadline:
                    if proc.poll() is not None:
                        stderr_full = self._read_stderr_tail(server_key)
                        fh = self._stderr_files.pop(server_key, None)
                        if fh is not None:
                            fh.close()
                        self._stderr_log_paths.pop(server_key, None)
                        failure = StartupFailure(
                            server_key=server_key,
                            reason="exited early",
                            stderr_full=stderr_full,
                        )
                        logger.error(
                            "Lifecycle: %r exited early; stderr (%s chars): %s",
                            server_key,
                            len(stderr_full),
                            stderr_full[:500],
                        )
                        raise HttpStartupError(failure)
                    try:
                        resp = await client.get(health_url)
                        if resp.status_code == HTTPStatus.OK:
                            logger.info(
                                "Lifecycle: HTTP subprocess %r ready",
                                server_key,
                            )
                            return
                    except (httpx.HTTPError, OSError) as e:
                        logger.debug(
                            "Lifecycle: health-check poll %r: %s", server_key, e
                        )
                    await asyncio.sleep(0.5)

            stderr_full = self._read_stderr_tail(server_key)
            fh = self._stderr_files.pop(server_key, None)
            if fh is not None:
                fh.close()
            self._stderr_log_paths.pop(server_key, None)
            await self._terminate_with_timeout(proc, server_key)
            timeout_failure = StartupFailure(
                server_key=server_key,
                reason=f"did not become healthy within {cfg.startup_timeout_sec}s",
                stderr_full=stderr_full,
            )
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
        proc = self._http_procs.pop(server_key, None)
        if proc is not None and proc.poll() is None:
            logger.info("Lifecycle: terminating %r for restart", server_key)
            await self._terminate_with_timeout(proc, server_key)
        self._http_pgids.pop(server_key, None)
        await self.start(server_key, cfg)

    @staticmethod
    def _absorb_sigint_during_shutdown(signum: int, frame: object) -> None:
        logger.warning(
            "Lifecycle: SIGINT received during shutdown_all(); "
            "ignoring until cleanup completes"
        )

    async def shutdown_all(self) -> None:
        """Terminate all HTTP subprocess servers and clear internal state.

        Absorbs a second SIGINT that arrives while cleanup is already running so a user
        pressing Ctrl-C twice cannot abort the loop and orphan the remaining subprocesses.
        """
        old_sigint: object | None = None
        try:
            old_sigint = signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT, self._absorb_sigint_during_shutdown)
        except ValueError:
            # Not on the main thread — proceed without the guard rather than fail shutdown.
            old_sigint = None

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
                        await self._terminate_with_timeout(proc, key, timeout=5.0)
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
        finally:
            if old_sigint is not None:
                signal.signal(signal.SIGINT, old_sigint)
