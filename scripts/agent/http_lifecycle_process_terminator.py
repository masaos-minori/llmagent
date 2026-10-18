"""scripts/agent/http_lifecycle_process_terminator.py

Process termination for HTTP subprocess MCP servers.

Owns terminate-then-kill escalation logic via `terminate_with_timeout()`.
Enables independent unit testing of process termination behavior.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import time

logger = logging.getLogger(__name__)

# Poll interval for wait_exited(), which probes process-group liveness via
# os.killpg(); a different waiting mechanism would need a different default.
_DEFAULT_TERMINATE_POLL_INTERVAL_SEC: float = 0.1


def _resolve_pgid(proc: object) -> int | None:
    """Return the real process-group id of *proc*, or ``None`` if unavailable.

    ``os.killpg`` needs a group id, not a pid. The two are equal only when the
    child is a group leader, which the launch site guarantees by starting it
    with ``start_new_session=True``; an admin ``fields`` override can disable
    that. Resolving through ``os.getpgid`` targets the true group either way.
    A missing or non-integer pid, or a pid that no longer exists, yields
    ``None`` so the caller keeps its ``proc.terminate()`` fallback.
    """
    pid = getattr(proc, "pid", None)
    if not isinstance(pid, int):
        return None
    try:
        return os.getpgid(pid)
    except OSError:
        return None


def _already_exited(proc: object) -> bool:
    """Return True when ``proc.poll()`` reports an exit code."""
    poll = getattr(proc, "poll", None)
    if poll is None:
        return False
    try:
        return poll() is not None
    except (OSError, AttributeError, TypeError):
        return False


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
        pgid = _resolve_pgid(proc)
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
    ) -> bool:
        """Terminate a process with a strict timeout.

        Args:
            proc: subprocess.Popen instance representing the process.
            server_key: Unique identifier for the server.
            timeout: Maximum time to wait before escalating to SIGKILL.

        Raises:
            HttpStartupError: If process termination fails.
        """
        pgid = _resolve_pgid(proc)
        if pgid is None or not isinstance(pgid, int):
            if _already_exited(proc):
                logger.info("Process %s already exited", server_key)
                return True
            # Fallback to proc-level termination when pgid is unavailable
            logger.warning(
                "Lifecycle: %r terminated, but children may remain (no pgid available)",
                server_key,
            )
            terminate_method = getattr(proc, "terminate", None)
            if terminate_method is not None:
                try:
                    terminate_method()
                except (OSError, AttributeError, TypeError):
                    pass
            return True

        # Early-exit if process already exited
        if _already_exited(proc):
            logger.info("Process %s already exited", server_key)
            return True

        # Track whether we actually used pgid for termination
        used_pgid = False

        # Send SIGTERM
        try:
            os.killpg(pgid, signal.SIGTERM)  # nosec B603 — process-group signal to terminate an admin-started MCP server subprocess, not user input
            used_pgid = True
        except ProcessLookupError:
            logger.warning("Process group %d already terminated", pgid)
            # Fallback: try proc-level termination when process group is gone
            terminate_method = getattr(proc, "terminate", None)
            if terminate_method is not None:
                try:
                    terminate_method()
                except (OSError, AttributeError, TypeError):
                    pass
            return True
        except OSError:
            logger.warning(
                "Lifecycle: os.killpg() failed for %r pid=%d; falling back to proc.terminate()",
                server_key,
                getattr(proc, "pid", None),
            )
            terminate_method = getattr(proc, "terminate", None)
            if terminate_method is not None:
                try:
                    terminate_method()
                except (OSError, AttributeError, TypeError):
                    pass
            return True

        # Warn if pgid wasn't used (children may remain)
        if not used_pgid:
            logger.warning(
                "Lifecycle: %r terminated, but children may remain (no pgid available)",
                server_key,
            )

        # Wait with timeout
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)  # Check if process exists
                await asyncio.sleep(self._terminate_poll_interval_sec)
            except ProcessLookupError:
                logger.info("Process group %d exited within timeout", pgid)
                return True

        # Escalate to SIGKILL
        try:
            os.killpg(pgid, signal.SIGKILL)  # nosec B603 — process-group signal to force-kill an admin-started MCP server subprocess after a graceful-termination timeout
            logger.warning("Escalated to SIGKILL for process group %d", pgid)
            return True
        except ProcessLookupError:
            logger.info("Process group %d already exited after timeout")
            return True
        except OSError as e:
            logger.error(f"Failed to send SIGKILL to process group {pgid}: {e}")
            # Process may still be running — do not mark as terminated
            return False
