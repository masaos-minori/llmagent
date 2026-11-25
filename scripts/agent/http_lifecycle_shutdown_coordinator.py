"""scripts/agent/http_lifecycle_shutdown_coordinator.py

Shutdown coordinator for graceful HTTP server lifecycle management.

Delegates cleanup operations back to HttpServerLifecycleManager via its public
methods (cleanup_server_key, clear_all_health_checks, process_terminator).

When a shutdown budget is supplied (REQ-010):

  - every per-server wait is clamped to ``budget.remaining()``, so the lifecycle
    step cannot extend the shutdown sequence past its one deadline
  - SIGINT received during cleanup is forwarded to ``budget.request_interrupt()``
    instead of being absorbed, so a second Ctrl-C stops the waits rather than
    being swallowed (REQ-011)
  - the SIGTERM and SIGKILL sends themselves are never clamped: a spent deadline
    shortens the waiting, it does not skip a signal (OD-05)
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import subprocess
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .http_lifecycle_errors import TerminationOutcome
from .http_lifecycle_process_terminator import ProcessTerminator

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agent.http_lifecycle import HttpServerLifecycleManager
    from agent.shutdown_budget import ShutdownBudget

# Fallback bound on the SIGTERM wait of the shutdown path (shutdown_all) when no
# budget is supplied; the post-SIGKILL confirmation window is owned by
# ProcessTerminator. With a budget the bound is min(this, budget.remaining()).
_SHUTDOWN_TIMEOUT_SEC = 30.0


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
    """Absorb SIGINT signals during a shutdown_all() cleanup that has no budget.

    Only the no-budget paths (a restart, a startup rollback) reach this: with a
    budget present the signal is forwarded to it instead, so the interrupt is not
    swallowed (REQ-011).
    """
    logger.warning(
        "Lifecycle: SIGINT received during shutdown_all(); ignoring until cleanup completes"
    )


def _request_interrupt_on_sigint(
    budget: ShutdownBudget,
) -> Callable[[int, object], None]:
    """Return the SIGINT handler for a cleanup that runs inside the shutdown budget.

    The handler does the one thing the budget's interrupt channel can do from a
    signal handler: set it. The waits inside ProcessTerminator read that event and
    stop at their next boundary, and the step records what was and was not proved.
    """

    def _handler(signum: int, frame: object) -> None:
        logger.warning(
            "Lifecycle: SIGINT received during shutdown_all(); interrupt requested "
            "for the termination in progress"
        )
        budget.request_interrupt()

    return _handler


def _termination_window(budget: ShutdownBudget | None) -> float:
    """Return the SIGTERM-wait bound for this shutdown, clamped to the budget.

    A spent deadline gives 0.0, which skips the waiting but not the signals: the
    terminator still sends SIGTERM and SIGKILL and reports what it could not prove.
    """
    if budget is None:
        return _SHUTDOWN_TIMEOUT_SEC
    return min(_SHUTDOWN_TIMEOUT_SEC, budget.remaining())


class ShutdownCoordinator:
    """Coordinates shutdown of HTTP server process and associated resources."""

    _absorb_sigint_during_shutdown = staticmethod(_absorb_sigint_during_shutdown)

    @staticmethod
    async def _terminate_one(
        manager: HttpServerLifecycleManager,
        terminator: ProcessTerminator,
        server_key: str,
        proc: subprocess.Popen[bytes],
        terminate_kwargs: dict[str, Any],
    ) -> TerminationOutcome:
        """Terminate one server and settle its tracking; return what was proved.

        The process entry was already removed by shutdown_all so the same shutdown is
        never attempted twice. Only a confirmed exit clears the remaining tracking; an
        unconfirmed one keeps the pgid and stderr-log tracking for manual cleanup.
        """
        logger.info("Shutting down %s...", server_key)
        pid = getattr(proc, "pid", None)
        try:
            outcome = await terminator.terminate_with_timeout(
                proc, server_key, **terminate_kwargs
            )
        except OSError as e:
            logger.error(
                "Lifecycle: error terminating %r pid=%s (%s); "
                "pgid and stderr-log tracking retained for manual cleanup.",
                server_key,
                pid,
                e,
            )
            return TerminationOutcome.EXIT_UNCONFIRMED
        if outcome.confirmed:
            manager.cleanup_server_key(server_key)
            return outcome
        pgid = _get_pgid(proc)
        logger.error(
            "Lifecycle: %r pid=%s pgid=%s not confirmed stopped (%s); pgid and "
            "stderr-log tracking retained, stop it manually with: kill -TERM -%s",
            server_key,
            pid,
            pgid,
            outcome,
            pgid,
        )
        return outcome

    async def shutdown_all(
        self,
        manager: HttpServerLifecycleManager,
        terminator: ProcessTerminator | None = None,
        fields: dict[str, Any] | None = None,
        *,
        budget: ShutdownBudget | None = None,
    ) -> list[tuple[str, TerminationOutcome]]:
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
            budget: The shutdown sequence's budget. When supplied, every wait in this
                shutdown is clamped to ``budget.remaining()`` and a SIGINT delivered
                during cleanup is forwarded to the budget as an interrupt request.
                When None, the module fallback window is used and the signal is
                absorbed as before.

        Returns:
            One ``(server_key, outcome)`` pair per server whose exit was not
            confirmed; empty when every started server was confirmed gone. A server
            whose wait was cut short by the deadline or the interrupt is in this list
            with an unconfirmed outcome, never as a clean shutdown.
        """
        old_sigint: object | None = None
        try:
            old_sigint = signal.getsignal(signal.SIGINT)
        except ValueError:
            old_sigint = None

        if old_sigint is not None:
            guard = (
                _request_interrupt_on_sigint(budget)
                if budget is not None
                else ShutdownCoordinator._absorb_sigint_during_shutdown
            )
            try:
                signal.signal(signal.SIGINT, guard)
            except ValueError:
                logger.debug("Lifecycle: could not set SIGINT guard handler")

        try:
            terminator = terminator or manager.process_terminator
            terminate_kwargs: dict[str, Any] = {
                "timeout": _termination_window(budget),
                "budget": budget,
            }
            if fields:
                terminate_kwargs.update(fields)
            running: list[tuple[str, subprocess.Popen[bytes]]] = []
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
                running.append((server_key, proc))
            # Terminate together so total time is bounded by one timeout and every
            # server is signalled before any wait begins.
            outcomes = await asyncio.gather(
                *(
                    ShutdownCoordinator._terminate_one(
                        manager, terminator, server_key, proc, terminate_kwargs
                    )
                    for server_key, proc in running
                )
            )
            manager.clear_all_health_checks()
            return [
                (server_key, outcome)
                for (server_key, _), outcome in zip(running, outcomes, strict=True)
                if not outcome.confirmed
            ]
        finally:
            if old_sigint is not None:
                try:
                    signal.signal(signal.SIGINT, old_sigint)
                except ValueError:
                    pass
