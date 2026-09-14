"""scripts/agent/http_lifecycle_shutdown_coordinator.py

Shutdown coordinator for graceful HTTP server lifecycle management."""

from __future__ import annotations

import logging
import signal
from typing import TYPE_CHECKING

from .http_lifecycle_process_terminator import ProcessTerminator

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agent.http_lifecycle import HttpServerLifecycleManager
    from agent.http_lifecycle_process_terminator import ProcessTerminator

_SHUTDOWN_TIMEOUT_SEC = 30.0
_KILL_TIMEOUT_SEC = 5.0


def _get_pgid(proc: subprocess.Popen[bytes]) -> int | None:
    """Return the process-group ID of *proc*, or ``None``."""
    pgid: int | None = getattr(proc, "pgid", None)
    if pgid is not None:
        return pgid
    try:
        return os.getpgid(proc.pid)
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
    ) -> None:
        """Gracefully shut down every managed server.

        Iterates over all entries in ``manager._http_procs``, delegates termination
        to ``ProcessTerminator.terminate_with_timeout`` for each process.
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
            procs = manager._http_procs
            terminator = terminator or manager._process_terminator
            for server_key, proc in list(procs.items()):
                if proc is None:
                    continue
                if proc.poll() is not None:
                    logger.debug("Lifecycle: %r already exited; removing entry", server_key)
                    continue
                terminator = manager._process_terminator
                logger.info("Shutting down %s...", server_key)
                await terminator.terminate_with_timeout(
                    proc, server_key, _SHUTDOWN_TIMEOUT_SEC
                )
        finally:
            if old_sigint is not None:
                try:
                    signal.signal(signal.SIGINT, old_sigint)
                except ValueError:
                    pass
