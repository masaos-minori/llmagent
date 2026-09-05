"""scripts/agent/http_lifecycle_process_terminator.py

Process termination for HTTP subprocess MCP servers.

Owns terminate-then-kill escalation logic currently inline in HttpServerLifecycleManager.start().
Enables independent unit testing of process termination behavior.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import time

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

    async def terminate(
        self, proc: object, server_key: str, timeout: float = 5.0
    ) -> None:
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
            from agent.http_lifecycle_errors import HttpStartupError, StartupFailure

            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Cannot determine PID for process {proc}",
                    stderr_full="",
                )
            )

        # Send SIGTERM to process group
        try:
            os.killpg(pgid, signal.SIGTERM)  # nosec B603 — process-group signal to terminate an admin-started MCP server subprocess, not user input
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
                await asyncio.sleep(self._terminate_poll_interval_sec)
            except ProcessLookupError:
                logger.info("Process group %d exited gracefully", pgid)
                return

        # Escalate to SIGKILL
        try:
            os.killpg(pgid, signal.SIGKILL)  # nosec B603 — process-group signal to force-kill an admin-started MCP server subprocess after a graceful-termination timeout
            logger.warning("Escalated to SIGKILL for process group %d", pgid)
        except ProcessLookupError:
            logger.info("Process group %d already exited after SIGTERM timeout", pgid)
        except PermissionError:
            logger.warning(
                "Permission denied when sending SIGKILL to process group %d", pgid
            )

    async def wait_exited(
        self,
        proc: object,
        server_key: str,
        poll_interval: float = 0.1,
        timeout: float = 5.0,
    ) -> bool:
        """Wait for a process to exit, up to `timeout` seconds.

        Args:
            proc: subprocess.Popen instance representing the process.
            server_key: Unique identifier for the server.
            poll_interval: Time between polls.
            timeout: Maximum time to wait before giving up.

        Returns:
            True if process has exited, False if `timeout` elapsed first.
        """
        pgid = getattr(proc, "pid", None)
        if pgid is None:
            return False

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)  # Check if process exists
                await asyncio.sleep(poll_interval)
            except ProcessLookupError:
                return True
        return False

    async def terminate_with_timeout(
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
            from agent.http_lifecycle_errors import HttpStartupError, StartupFailure

            raise HttpStartupError(
                StartupFailure(
                    server_key=server_key,
                    reason=f"Cannot determine PID for process {proc}",
                    stderr_full="",
                )
            )

        # Send SIGTERM
        try:
            os.killpg(pgid, signal.SIGTERM)  # nosec B603 — process-group signal to terminate an admin-started MCP server subprocess, not user input
        except ProcessLookupError:
            logger.warning("Process group %d already terminated", pgid)
            return

        # Wait with timeout
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)  # Check if process exists
                await asyncio.sleep(self._terminate_poll_interval_sec)
            except ProcessLookupError:
                logger.info("Process group %d exited within timeout", pgid)
                return

        # Escalate to SIGKILL
        try:
            os.killpg(pgid, signal.SIGKILL)  # nosec B603 — process-group signal to force-kill an admin-started MCP server subprocess after a graceful-termination timeout
            logger.warning("Escalated to SIGKILL for process group %d", pgid)
        except ProcessLookupError:
            logger.info("Process group %d already exited after timeout")
