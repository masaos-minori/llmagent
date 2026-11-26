"""scripts/agent/http_lifecycle_subprocess_launcher.py — Spawn and validate the HTTP MCP subprocess that the lifecycle manager tracks.

Subprocess startup cluster extracted from HttpServerLifecycleManager: command
validation, stderr-log wiring, `Popen` construction from the immutable launch
specification, process-group id capture, and the failure paths that release resources
before a startup error is raised.

`HttpServerLifecycleManager` keeps ownership of the process-record registry and of the
collaborator components; they are injected here by reference, so the extracted code
mutates the same objects and startup behavior is unchanged. A record is inserted on a
successful launch and released only when its exit is confirmed (REQ-001, REQ-002).
"""

from __future__ import annotations

import logging
import os
import subprocess  # nosec B404 — used to launch admin-controlled MCP server processes
from typing import IO, NoReturn, cast

from shared.mcp_config import McpServerConfig

from agent.lifecycle import LifecycleState

from .http_lifecycle_command_validator import CommandValidator
from .http_lifecycle_errors import HttpStartupError, StartupFailure, TerminationOutcome
from .http_lifecycle_launch_spec import build_launch_spec
from .http_lifecycle_process_record import ManagedProcessRecord
from .http_lifecycle_process_terminator import ProcessTerminator
from .http_lifecycle_stderr_log_manager import StderrLogManager

logger = logging.getLogger(__name__)


class SubprocessLauncher:
    """Creates and validates HTTP MCP subprocesses, releasing resources on failure."""

    def __init__(
        self,
        *,
        command_validator: CommandValidator,
        stderr_log_manager: StderrLogManager,
        process_terminator: ProcessTerminator,
        records: dict[str, ManagedProcessRecord],
        stderr_files: dict[str, IO[bytes]],
        terminate_timeout_sec: float,
    ) -> None:
        """Initialize with the manager's components and registries, held by reference."""
        self._command_validator = command_validator
        self._stderr_log_manager = stderr_log_manager
        self._process_terminator = process_terminator
        self._records = records
        self._stderr_files = stderr_files
        self._terminate_timeout_sec = terminate_timeout_sec

    async def create_and_validate_proc(
        self,
        server_key: str,
        cfg: McpServerConfig,
    ) -> tuple[subprocess.Popen[bytes], IO[bytes]]:
        """Create and validate subprocess for the given server configuration.

        Validates the command, builds the immutable launch specification from the
        validated path and file identity, re-checks that identity, spawns from the
        specification only, and handles getpgid failure with resource cleanup.

        Returns:
            A tuple of (proc, stderr_fh) on success.

        Raises:
            HttpStartupError: If command validation fails, the launch target changed
                between validation and spawn, or getpgid fails.
        """
        stderr_fh = self._stderr_log_manager.open_log(server_key, cfg)
        self._stderr_files[server_key] = stderr_fh
        if not cfg.cmd or not cfg.cmd[0]:
            self.close_stderr_log(server_key, stderr_fh)
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason="Empty command configuration",
                    stderr_full="",
                )
            )

        # Validate command using CommandValidator, then build the one specification the
        # spawn may use: argv, environment, and stderr come from it and nothing else.
        try:
            resolved_path, identity = self._command_validator.validate(
                server_key, cfg.cmd[0]
            )
            spec = build_launch_spec(
                server_key, cfg, resolved_path, identity, stderr_fh
            )
        except (ValueError, HttpStartupError) as e:
            self.close_stderr_log(server_key, stderr_fh)
            # An HttpStartupError already carries the server key in its message, so its
            # own reason is reused instead of wrapping the whole message in a new one.
            reason = e.failure.reason if isinstance(e, HttpStartupError) else str(e)
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=reason,
                    stderr_full="",
                )
            ) from e

        try:
            # REQ-003 (AC-1): the file behind the validated path must still be the same
            # file, whatever happened to PATH or a symlink in the meantime.
            identity_mismatch = spec.verify_identity()
            if identity_mismatch is not None:
                raise HttpStartupError(
                    StartupFailure(
                        server_key=server_key,
                        reason=identity_mismatch,
                        stderr_full="",
                    )
                )
            proc = cast(
                subprocess.Popen[bytes],
                subprocess.Popen(  # nosec B603  # noqa: S603  # — argv[0] is the validator-resolved absolute path, not a config string
                    spec.argv, **spec.popen_kwargs()
                ),
            )
        except Exception:
            self.close_stderr_log(server_key, stderr_fh)
            raise
        try:
            pgid = os.getpgid(proc.pid)
        except OSError as e:
            await self.handle_getpgid_failure(server_key, proc, stderr_fh, e)
        self._records[server_key] = ManagedProcessRecord(
            process=proc,
            pid=proc.pid,
            pgid=pgid,
            stderr_log=stderr_fh,
            state=LifecycleState.RUNNING,
        )
        return proc, stderr_fh

    def close_stderr_log(self, server_key: str, stderr_fh: IO[bytes]) -> None:
        """Close a startup-attempt stderr handle and drop its log tracking entries."""
        stderr_fh.close()
        self._stderr_files.pop(server_key, None)
        self._stderr_log_manager.forget(server_key)

    async def handle_getpgid_failure(
        self,
        server_key: str,
        proc: subprocess.Popen[bytes],
        stderr_fh: IO[bytes],
        error: OSError,
    ) -> NoReturn:
        """Terminate a process whose pgid could not be resolved, then re-raise *error*.

        The record (pgid None, the honest state) is registered before the termination
        attempt and released only when the exit is confirmed; an unconfirmed outcome
        retains the record and logs the pid so the process can be stopped manually.
        Stderr resources are always released regardless of the termination outcome.
        """
        logger.warning(
            "Lifecycle: getpgid() failed for %r pid=%d; cleaning up",
            server_key,
            proc.pid,
        )
        record = ManagedProcessRecord(
            process=proc,
            pid=proc.pid,
            pgid=None,
            stderr_log=stderr_fh,
            state=LifecycleState.RUNNING,
        )
        self._records[server_key] = record
        try:
            outcome = await self._process_terminator.terminate_with_timeout(
                proc, server_key, timeout=self._terminate_timeout_sec
            )
            record.settle(outcome)
            if not outcome.confirmed:
                logger.error(
                    "Lifecycle: %r pid=%d not confirmed stopped after getpgid() failure (%s); "
                    "process record retained",
                    server_key,
                    proc.pid,
                    outcome,
                )
            poll_result = proc.poll()
            if poll_result is not None and poll_result != 0:
                logger.info(
                    "Lifecycle: subprocess %r (pid=%d) terminated with exit code %d",
                    server_key,
                    proc.pid,
                    poll_result,
                )
            if outcome.confirmed:
                self._records.pop(server_key, None)
        except Exception as term_err:
            record.settle(TerminationOutcome.EXIT_UNCONFIRMED)
            logger.error(
                "Lifecycle: getpgid() failed AND termination raised for %r (pid=%d): %s.",
                server_key,
                proc.pid,
                term_err,
            )
            raise
        finally:
            self.close_stderr_log(server_key, stderr_fh)
        raise error
