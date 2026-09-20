"""scripts/agent/http_lifecycle_shutdown_coordinator.py

Shutdown coordinator for graceful HTTP server lifecycle management.

Delegates cleanup operations back to HttpServerLifecycleManager via its public
methods (cleanup_server_key, clear_all_health_checks, process_terminator).
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
from typing import TYPE_CHECKING, Any

from .http_lifecycle_process_terminator import ProcessTerminator

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agent.http_lifecycle import HttpServerLifecycleManager

_SHUTDOWN_TIMEOUT_SEC = 30.0
_KILL_TIMEOUT_SEC = 5.0


def _get_pgid(proc: subprocess.Popen[bytes]) -> int | None:
    """Return the process-group ID of *proc*, or ``None``."""
    pgid: int | None = getattr(proc, "pgid", None)
    if pgid is not None:
        return pgid
    try:
        pgid = os.getpgid(proc.pid)
        assert isinstance(pgid, int)
        return pgid
    except OSError:
        return None


def _absorb_sigint_during_shutdown(signum: int, frame: object) -> None:
    """Absorb SIGINT signals during shutdown_all() cleanup."""
    logger.warning(
        "Lifecycle: SIGINT received during shutdown_all(); ignoring until cleanup completes"
    )


class ShutdownCoordinator:
    """Coordinates shutdown of HTTP server process and associated resources."""

    _absorb_sigint_during_shutdown = staticmethod(_absorb_sigint_during_shutdown)

    async def shutdown_all(
        self,
        manager: HttpServerLifecycleManager,
        terminator: ProcessTerminator | None = None,
        fields: dict[str, Any] | None = None,
    ) -> None:
        """Gracefully shut down every managed server.

        Iterates over all entries in ``manager._http_procs``, delegates termination
        to ``ProcessTerminator.terminate_with_timeout`` for each process, then
        delegates cleanup back to the manager's public methods.

        Args:
            manager: The lifecycle manager owning the processes.
            terminator: Optional terminator instance; falls back to manager's.
            fields: Additional keyword arguments to pass to each
                ``terminate_with_timeout()`` call. If None, defaults to
                an empty dict.
        """
        old_sigint: object | None = None
        try:
            old_sigint = signal.getsignal(signal.SIGINT)
        except ValueError:
            old_sigint = None

        if old_sigint is not None:
            try:
                signal.signal(
                    signal.SIGINT, ShutdownCoordinator._absorb_sigint_during_shutdown
                )
            except ValueError:
                logger.debug("Lifecycle: could not set SIGINT guard handler")

        try:
            terminator = terminator or manager.process_terminator
            for server_key, proc in list(manager.iter_processes()):
                if proc is None:
                    continue
                # Pop before termination to avoid double-shutdown if terminated fails
                manager.remove_process_entry(server_key)
                if proc.poll() is not None:
                    logger.debug(
                        "Lifecycle: %r already exited; removing entry", server_key
                    )
                    manager.cleanup_server_key(server_key)
                    continue
                logger.info("Shutting down %s...", server_key)
                terminate_kwargs: dict[str, Any] = {
                    "timeout": _SHUTDOWN_TIMEOUT_SEC,
                }
                if fields:
                    terminate_kwargs.update(fields)
                try:
                    await terminator.terminate_with_timeout(
                        proc, server_key, **terminate_kwargs
                    )
                except (OSError, TimeoutError) as e:
                    logger.warning("Lifecycle: error terminating %r: %s", server_key, e)
                manager.cleanup_server_key(server_key)
            manager.clear_all_health_checks()
        finally:
            if old_sigint is not None:
                try:
                    signal.signal(signal.SIGINT, old_sigint)
                except ValueError:
                    pass
