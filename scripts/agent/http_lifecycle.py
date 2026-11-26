"""scripts/agent/http_lifecycle.py

HTTP subprocess MCP server lifecycle: start, health-poll, restart, shutdown.

Two methods delegate with arguments rather than forwarding the call unchanged:
shutdown_all passes the manager and the shutdown budget to ShutdownCoordinator, and
_health_poll_until_ready passes the manager and this module's poll timings to
HealthChecker.poll_until_ready. SubprocessLauncher is instead constructed with this
class's components and the process-record registry, which it holds by reference.

Process tracking is one ManagedProcessRecord per server key in _records: a record is
released only when its exit is confirmed (REQ-001, REQ-002); no path pops tracking
before the exit is proved.

Custom logic retained in this class:
- per-server health request values resolved at the call site: the effective health
  timeout and the catalog `required_capability` passed to the poll
- process info snapshots: _build_snapshot and the snapshot accessors
- startup failure reporting: _raise_startup_failure and the start() orchestration
  that combines SubprocessLauncher with the health poll
"""

from __future__ import annotations

import asyncio
import logging
import subprocess  # nosec B404 — used to launch admin-controlled MCP server processes
import time
import tomllib
from collections.abc import Iterator
from dataclasses import asdict
from typing import IO, TYPE_CHECKING, NoReturn

import httpx
from shared.mcp_config import McpServerConfig, get_effective_health_timeout
from shared.tool_catalog import load_tool_catalog, required_capability_for

from agent.lifecycle import LifecycleState
from agent.services.models import ProcessInfoSnapshot

from .http_lifecycle_command_validator import CommandValidator
from .http_lifecycle_errors import (
    HttpStartupError,
    RestartBlockedError,
    StartupFailure,
    TerminationOutcome,
)
from .http_lifecycle_health_checker import (
    HEALTH_RECHECK_INTERVAL_SEC,
    HealthChecker,
    _terminate_for_startup_failure,
)
from .http_lifecycle_process_record import ManagedProcessRecord
from .http_lifecycle_process_terminator import ProcessTerminator
from .http_lifecycle_shutdown_coordinator import ShutdownCoordinator
from .http_lifecycle_stderr_log_manager import StderrLogManager
from .http_lifecycle_subprocess_launcher import SubprocessLauncher

if TYPE_CHECKING:
    from agent.shutdown_budget import ShutdownBudget

logger = logging.getLogger(__name__)

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
        self._records: dict[str, ManagedProcessRecord] = {}
        self._stderr_files: dict[str, IO[bytes]] = {}
        self._last_health_check: dict[str, float] = {}
        self._subprocess_launcher = subprocess_launcher or SubprocessLauncher(
            command_validator=self._command_validator,
            stderr_log_manager=self._stderr_log_manager,
            process_terminator=self._process_terminator,
            records=self._records,
            stderr_files=self._stderr_files,
            terminate_timeout_sec=TERMINATE_TIMEOUT_SEC,
        )

    def verify_running(self, server_key: str) -> bool:
        """Return True if the HTTP subprocess server is running, False if missing or exited."""
        record = self._records.get(server_key)
        if record is None or record.process.poll() is not None:
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
                server_key,
                cfg,
                url=url,
                timeout=get_effective_health_timeout(cfg),
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
        """Release the process record and remove tracking entries for a server key.

        Called by ShutdownCoordinator after a confirmed termination. Releases the
        record and delegates stderr/log cleanup to _clear_server_tracking_data.
        """
        self._records.pop(server_key, None)
        self._clear_server_tracking_data(server_key)

    def remove_process_entry(self, server_key: str) -> None:
        """Release the process record for a server.

        Post-confirmation release helper: the pre-termination call site in
        ShutdownCoordinator is removed by the record-ownership change (REQ-003).
        Does NOT close file handles or clear other tracking data — those are cleaned
        up after termination via cleanup_server_key().
        """
        self._records.pop(server_key, None)

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
        """Return a typed snapshot for a managed subprocess, or None if unknown.

        A retained record (exit not confirmed) still builds a snapshot: the
        retained process stays visible to status surfaces until its exit is
        confirmed (REQ-002, REQ-009).
        """
        record = self._records.get(server_key)
        if record is None:
            return None
        exit_code = record.process.poll()
        running = exit_code is None
        last_exit_code = None if running else exit_code
        stderr_log = self._stderr_log_manager.get_log_path(server_key) or ""
        return ProcessInfoSnapshot(
            server_key=server_key,
            managed=True,
            pid=record.pid,
            pgid=record.pgid,
            running=running,
            last_exit_code=last_exit_code,
            stderr_log=stderr_log,
            termination_outcome=(
                record.last_outcome.value if record.last_outcome is not None else None
            ),
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
            for key in list(self._records.keys())
            if (snap := self.get_process_info(key)) is not None
        ]

    def iter_records(self) -> Iterator[tuple[str, ManagedProcessRecord]]:
        """Yield (server_key, record) pairs for all managed HTTP subprocess servers.

        This method provides controlled access to the process records without
        exposing the internal `_records` dictionary directly. Callers receive
        an iterator and cannot modify the underlying dictionary.
        """
        yield from self._records.items()

    def _raise_startup_failure(
        self, server_key: str, reason: str, stderr_full: str
    ) -> NoReturn:
        """Release the process record and raise HttpStartupError with the given reason.

        Confirmed path only (the record is already releasable); an exit that could
        not be confirmed must use _raise_startup_failure_unconfirmed instead.
        """
        self._records.pop(server_key, None)
        raise HttpStartupError(
            StartupFailure(
                server_key=server_key, reason=reason, stderr_full=stderr_full
            )
        )

    def _raise_startup_failure_unconfirmed(
        self,
        server_key: str,
        reason: str,
        stderr_full: str,
        outcome: TerminationOutcome | None = None,
    ) -> NoReturn:
        """Raise HttpStartupError keeping a not-confirmed process fully tracked.

        Sibling of _raise_startup_failure for the exit-unconfirmed outcome: the
        record (process, pgid, stderr-log handle) is retained and flagged
        failed_start so shutdown_all() still names the server for manual cleanup.
        The termination outcome is recorded on the record so status surfaces
        report why the server is retained (REQ-009); when the caller does not
        supply one the failure is classified EXIT_UNCONFIRMED.
        """
        record = self._records.get(server_key)
        if record is not None:
            record.failed_start = True
            record.last_outcome = (
                outcome if outcome is not None else TerminationOutcome.EXIT_UNCONFIRMED
            )
        pid = record.pid if record is not None else None
        pgid = record.pgid if record is not None else None
        logger.error(
            "Lifecycle: %r pid=%s pgid=%s startup failure with exit not confirmed; "
            "process, pgid and stderr-log tracking retained, stop it manually with: "
            "kill -TERM -%s",
            server_key,
            pid,
            pgid,
            pgid,
        )
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
        them from http_lifecycle.py, the server's effective health timeout (REQ-001),
        and the catalog `required_capability` the readiness rule needs (the checker
        does not read the catalog itself).

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
            request_timeout_sec=get_effective_health_timeout(cfg),
            terminate_timeout_sec=TERMINATE_TIMEOUT_SEC,
            required_capability=self._resolve_required_capability(server_key),
        )

    def _resolve_required_capability(self, server_key: str) -> str | None:
        """Resolve the catalog `required_capability` for *server_key*.

        A missing or unreadable catalog resolves to None with a warning here, so the
        poll reads the body through the legacy `ready` fallback (D-6). The fail-closed
        FATAL for a missing catalog stays at discovery, which is the enforcement point
        for REQ-005.
        """
        try:
            catalog = load_tool_catalog()
        except (OSError, tomllib.TOMLDecodeError) as exc:
            logger.warning(
                "Lifecycle: tool catalog unavailable for %r: %s", server_key, exc
            )
            return None
        return required_capability_for(catalog, server_key)

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
        existing = self._records.get(server_key)
        if existing is not None and existing.process.poll() is None:
            if existing.failed_start:
                await self._reterminate_recorded_failed_start(server_key, existing)
            else:
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

    async def _reterminate_recorded_failed_start(
        self, server_key: str, record: ManagedProcessRecord
    ) -> None:
        """Re-terminate a tracked process left by an unconfirmed failed start.

        Called from start()'s reuse branch when the live process is the one
        recorded by _raise_startup_failure_unconfirmed. On a confirmed exit the
        record (process, pgid, stderr and health-check data) is released and
        start() falls through to a fresh launch; on an unconfirmed exit the
        record is kept and the startup failure is raised again.
        A process that is alive but has no matching record is never re-terminated.
        """
        logger.info(
            "Lifecycle: %r failed start with exit not confirmed; "
            "re-terminating before restart",
            server_key,
        )
        outcome = await _terminate_for_startup_failure(
            self, server_key, record.process, TERMINATE_TIMEOUT_SEC
        )
        record.last_outcome = outcome
        if outcome.confirmed:
            stderr_full = self._cleanup_server_resources(server_key)
            self._records.pop(server_key, None)
        else:
            stderr_full = self._stderr_log_manager.read_tail(server_key).decode(
                errors="replace"
            )
            self._raise_startup_failure_unconfirmed(
                server_key, "startup failure: prior exit not confirmed", stderr_full
            )

    async def restart(self, server_key: str, cfg: McpServerConfig) -> None:
        """Terminate and restart an HTTP subprocess server.

        A replacement is started only after the old process exit is confirmed.
        On an unconfirmed outcome the record is retained, the record state is set
        to EXIT_UNCONFIRMED, and RestartBlockedError is raised without starting a
        second live process (REQ-005, AC-2).
        """
        record = self._records.get(server_key)
        if record is not None:
            if record.process.poll() is None:
                logger.info("Lifecycle: terminating %r for restart", server_key)
                record.state = LifecycleState.STOPPING
                outcome = await self._process_terminator.terminate_with_timeout(
                    record.process, server_key, timeout=TERMINATE_TIMEOUT_SEC
                )
                record.last_outcome = outcome
                if not outcome.confirmed:
                    logger.error(
                        "Lifecycle: %r pid=%s not confirmed stopped before restart (%s)",
                        server_key,
                        record.process.pid,
                        outcome,
                    )
                    record.state = LifecycleState.EXIT_UNCONFIRMED
                    raise RestartBlockedError(
                        f"Lifecycle: restart of {server_key!r} blocked: exit of "
                        f"pid={record.process.pid} not confirmed ({outcome})"
                    )
            self._records.pop(server_key, None)
        self._clear_server_tracking_data(server_key)
        await self.start(server_key, cfg)

    async def shutdown_all(
        self, *, budget: ShutdownBudget | None = None
    ) -> list[tuple[str, TerminationOutcome]]:
        """Shut down all managed servers.

        Delegates to ShutdownCoordinator.shutdown_all(); returns the servers whose
        exit was not confirmed (empty when every started server was confirmed gone).

        Args:
            budget: The shutdown sequence's budget, forwarded unchanged so the
                coordinator can bound every wait in this shutdown by it (REQ-010).
        """
        return await self._shutdown_coordinator.shutdown_all(self, budget=budget)
