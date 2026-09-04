"""scripts/agent/http_lifecycle_process_terminator.py

Process termination for HTTP subprocess MCP servers.

Owns terminate-then-kill escalation logic currently inline in HttpServerLifecycleManager.start().
Enables independent unit testing of process termination behavior.
"""

from __future__ import annotations

import logging
import os
import signal
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.http_lifecycle_errors import HttpStartupError, StartupFailure

logger = logging.getLogger(__name__)

_DEFAULT_TERMINATE_POLL_INTERVAL_SEC: float = 0.1


class ProcessTerminator:
    """Manages process termination with SIGTERM → SIGKILL escalation."""

    def __init__(
        self,
        *,
        terminate_poll_interval_sec: float | None = None,
    ) -> None:
        self._terminate_poll_interval_sec = (
            terminate_poll_interval_sec
            if terminate_poll_interval_sec is not None
            else _DEFAULT_TERMINATE_POLL_INTERVAL_SEC
        )

    def terminate(self, proc: object, server_key: str, timeout: float = 5.0) -> None:
        """Terminate a process group with SIGTERM → SIGKILL escalation.

        Args:
            proc: subprocess.Popen instance representing the process.
            server_key: Unique identifier for the server.
            timeout: Maximum time to wait before escalating to SIGKILL.

        Raises:
            HttpStartupError: If process termination fails.
        """
        pgid = getattr(proc, "pid", None)
        if pgid is None:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Cannot determine PID for process {proc}",
                    stderr_full="",
                )
            )

        # Send SIGTERM to process group
        try:
            os.killpg(pgid, signal.SIGTERM)  # nosec B603
        except ProcessLookupError:
            logger.warning("Process group %d already terminated", pgid)
            return
        except PermissionError:
            logger.warning(
                "Permission denied when sending SIGTERM to process group %d", pgid
            )
            return

        # Wait for process to exit within timeout
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)  # Check if process exists
                time.sleep(self._terminate_poll_interval_sec)
            except ProcessLookupError:
                logger.info("Process group %d exited gracefully", pgid)
                return

        # Escalate to SIGKILL
        try:
            os.killpg(pgid, signal.SIGKILL)  # nosec B603
            logger.warning("Escalated to SIGKILL for process group %d", pgid)
        except ProcessLookupError:
            logger.info("Process group %d already exited after SIGTERM timeout", pgid)
        except PermissionError:
            logger.warning(
                "Permission denied when sending SIGKILL to process group %d", pgid
            )

    def wait_exited(
        self, proc: object, server_key: str, poll_interval: float = 0.1
    ) -> bool:
        """Wait for a process to exit.

        Args:
            proc: subprocess.Popen instance representing the process.
            server_key: Unique identifier for the server.
            poll_interval: Time between polls.

        Returns:
            True if process has exited, False otherwise.
        """
        pgid = getattr(proc, "pid", None)
        if pgid is None:
            return False

        while True:
            try:
                os.killpg(pgid, 0)  # Check if process exists
                time.sleep(poll_interval)
            except ProcessLookupError:
                return True

    def terminate_with_timeout(
        self, proc: object, server_key: str, timeout: float = 5.0
    ) -> None:
        """Terminate a process with a strict timeout.

        Args:
            proc: subprocess.Popen instance representing the process.
            server_key: Unique identifier for the server.
            timeout: Maximum time to wait before escalating to SIGKILL.

        Raises:
            HttpStartupError: If process termination fails.
        """
        pgid = getattr(proc, "pid", None)
        if pgid is None:
            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Cannot determine PID for process {proc}",
                    stderr_full="",
                )
            )

        # Send SIGTERM
        try:
            os.killpg(pgid, signal.SIGTERM)  # nosec B603
        except ProcessLookupError:
            logger.warning("Process group %d already terminated", pgid)
            return

        # Wait with timeout
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)  # Check if process exists
                time.sleep(self._terminate_poll_interval_sec)
            except ProcessLookupError:
                logger.info("Process group %d exited within timeout", pgid)
                return

        # Escalate to SIGKILL
        try:
            os.killpg(pgid, signal.SIGKILL)  # nosec B603
            logger.warning("Escalated to SIGKILL for process group %d", pgid)
        except ProcessLookupError:
            logger.info("Process group %d already exited after timeout")
