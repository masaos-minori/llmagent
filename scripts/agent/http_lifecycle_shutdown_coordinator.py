"""Shutdown coordinator for graceful HTTP server lifecycle management."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import subprocess
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agent.http_lifecycle import HttpServerLifecycleManager

_SHUTDOWN_TIMEOUT_SEC = 30.0
_KILL_TIMEOUT_SEC = 5.0
_TERMINATE_ERRORS = (OSError, ProcessLookupError, ChildProcessError)
_KILL_ERRORS = (OSError, ProcessLookupError, ChildProcessError)


def _get_pgid(proc: subprocess.Popen[bytes]) -> int | None:
    """Return the process-group ID of *proc*, or ``None``."""
    pgid: int | None = getattr(proc, "pgid", None)
    if pgid is not None:
        return pgid
    try:
        return os.getpgid(proc.pid)
    except OSError:
        return None


def _kill_pg(pgid: int) -> None:
    """Send SIGTERM to the process group identified by *pgid*."""
    try:
        os.killpg(pgid, signal.SIGTERM)
    except (OSError, ProcessLookupError):
        pass


def _kill_pg_force(pgid: int) -> None:
    """Send SIGKILL to the process group identified by *pgid*."""
    try:
        os.killpg(pgid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        pass


class ShutdownCoordinator:
    """Coordinates shutdown of HTTP server process and associated resources."""

    @staticmethod
    async def shutdown_all(manager: HttpServerLifecycleManager) -> None:
        """Gracefully shut down every managed server.

        Iterates over all entries in ``manager._http_procs``, sends SIGTERM to each
        process group, and falls back to SIGKILL when the timeout expires.
        """
        procs = manager._http_procs
        for server_key, proc in list(procs.items()):
            if proc is None:
                continue
            pgid = manager._http_pgids.get(server_key) or _get_pgid(proc)
            logger.info("Shutting down %s...", server_key)
            try:
                if pgid is not None:
                    _kill_pg(pgid)
                else:
                    proc.terminate()
            except _TERMINATE_ERRORS as exc:
                logger.warning("%s: failed to send SIGTERM: %s", server_key, exc)

            deadline = asyncio.get_event_loop().time() + _SHUTDOWN_TIMEOUT_SEC
            while asyncio.get_event_loop().time() < deadline:
                poll_result = proc.poll()
                if poll_result is not None:
                    logger.info(
                        "%s terminated gracefully with code %d", server_key, poll_result
                    )
                    break
                await asyncio.sleep(0.05)
            else:
                logger.warning(
                    "%s did not stop within %.1fs, sending SIGKILL",
                    server_key,
                    _SHUTDOWN_TIMEOUT_SEC,
                )
                try:
                    if pgid is not None:
                        _kill_pg_force(pgid)
                    else:
                        proc.kill()
                except _KILL_ERRORS as exc:
                    logger.warning("%s: failed to send SIGKILL: %s", server_key, exc)

                kill_deadline = asyncio.get_event_loop().time() + _KILL_TIMEOUT_SEC
                while asyncio.get_event_loop().time() < kill_deadline:
                    poll_result = proc.poll()
                    if poll_result is not None:
                        logger.info("%s killed with code %d", server_key, poll_result)
                        break
                    await asyncio.sleep(0.05)
                else:
                    logger.error("%s could not be killed after SIGKILL", server_key)
