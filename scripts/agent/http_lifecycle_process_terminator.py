"""scripts/agent/http_lifecycle_process_terminator.py

Process termination for HTTP subprocess MCP servers.

Owns terminate-then-kill escalation logic via `terminate_with_timeout()`.
Enables independent unit testing of process termination behavior.

Every wait here can be clamped by a shutdown budget (REQ-010): the escalation
itself is never clamped, so SIGTERM and SIGKILL are always delivered and only the
observation of the exit gives up early, reported as an unconfirmed exit (OD-05).
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import time
from typing import TYPE_CHECKING

from agent.http_lifecycle_errors import TerminationOutcome

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agent.shutdown_budget import ShutdownBudget

# Poll interval for wait_exited(), which probes process-group liveness via
# os.killpg(); a different waiting mechanism would need a different default.
# Never clamped: a short window must not turn a wait into a busy loop.
_DEFAULT_TERMINATE_POLL_INTERVAL_SEC: float = 0.1

# Fallback window in which an exit must be observed after SIGKILL was delivered; a
# process that is still in the group after it is reported EXIT_UNCONFIRMED. With a
# budget this is clamped to what the shutdown sequence has left.
_DEFAULT_KILL_CONFIRM_TIMEOUT_SEC: float = 2.0


def _clamped_deadline(window: float, budget: ShutdownBudget | None) -> float:
    """Return the monotonic instant *window* seconds from now, never past the budget.

    Clamping at the point each deadline is computed is what keeps a caller without a
    budget on today's behavior exactly.
    """
    now = time.monotonic()
    if budget is None:
        return now + window
    return min(now + window, now + budget.remaining())


def _interrupt_requested(budget: ShutdownBudget | None) -> bool:
    """Return True when the shutdown sequence asked the step in progress to stop."""
    return budget is not None and budget.interrupt_requested


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


def _reap(proc: object) -> None:
    """Reap *proc* if it has exited so the group liveness probe stops seeing a zombie.

    ``os.killpg(pgid, 0)`` succeeds while an exited child is still unreaped, so a wait
    loop that only probes the group would run until its timeout.
    """
    poll = getattr(proc, "poll", None)
    if poll is None:
        return
    try:
        poll()
    except (OSError, AttributeError, TypeError):
        pass


def _signal_via_proc(proc: object) -> bool:
    """Send SIGTERM through ``proc.terminate()``; return True when the call was made."""
    terminate_method = getattr(proc, "terminate", None)
    if terminate_method is None:
        return False
    try:
        terminate_method()
    except (OSError, AttributeError, TypeError):
        return False
    return True


class ProcessTerminator:
    """Manages process termination with SIGTERM → SIGKILL escalation."""

    def __init__(
        self,
        *,
        terminate_poll_interval_sec: float | None = None,
        kill_confirm_timeout_sec: float | None = None,
    ) -> None:
        self._terminate_poll_interval_sec = (
            terminate_poll_interval_sec
            if terminate_poll_interval_sec is not None
            else _DEFAULT_TERMINATE_POLL_INTERVAL_SEC
        )
        self._kill_confirm_timeout_sec = (
            kill_confirm_timeout_sec
            if kill_confirm_timeout_sec is not None
            else _DEFAULT_KILL_CONFIRM_TIMEOUT_SEC
        )

    async def wait_exited(
        self,
        proc: object,
        server_key: str,
        poll_interval: float = 0.1,
        timeout: float = 5.0,
        *,
        budget: ShutdownBudget | None = None,
    ) -> bool:
        """Wait for a process to exit, up to `timeout` seconds.

        Args:
            proc: subprocess.Popen instance representing the process.
            server_key: Unique identifier for the server.
            poll_interval: Time between polls.
            timeout: Maximum time to wait before giving up.
            budget: When supplied, the wait ends at the shutdown deadline instead,
                and an interrupt request for the step in progress ends it at the next
                poll.

        Returns:
            True if process has exited, False if `timeout`, the deadline, or the
            interrupt came first.
        """
        pgid = _resolve_pgid(proc)
        if pgid is None:
            return False

        deadline = _clamped_deadline(timeout, budget)
        while time.monotonic() < deadline:
            if _interrupt_requested(budget):
                logger.warning(
                    "Lifecycle: interrupt requested while waiting for %r pid=%s to exit",
                    server_key,
                    getattr(proc, "pid", None),
                )
                return False
            _reap(proc)
            try:
                os.killpg(pgid, 0)  # Check if process exists
                await asyncio.sleep(poll_interval)
            except ProcessLookupError:
                return True
        return False

    def _confirm_window(self, budget: ShutdownBudget | None) -> float:
        """Return the post-SIGKILL confirm window, clamped to what the budget has left."""
        if budget is None:
            return self._kill_confirm_timeout_sec
        return min(self._kill_confirm_timeout_sec, budget.remaining())

    async def _confirm_group_gone(
        self, proc: object, pgid: int, *, budget: ShutdownBudget | None = None
    ) -> bool:
        """Return True when process group *pgid* is observed gone within the kill window."""
        deadline = time.monotonic() + self._confirm_window(budget)
        while True:
            _reap(proc)
            try:
                os.killpg(pgid, 0)
            except ProcessLookupError:
                return True
            if _interrupt_requested(budget):
                return False
            if time.monotonic() >= deadline:
                return False
            await asyncio.sleep(self._terminate_poll_interval_sec)

    async def terminate_with_timeout(
        self,
        proc: object,
        server_key: str,
        timeout: float,
        *,
        budget: ShutdownBudget | None = None,
    ) -> TerminationOutcome:
        """Terminate a process with a strict timeout and report what was proved.

        Args:
            proc: subprocess.Popen instance representing the process.
            server_key: Unique identifier for the server.
            timeout: Maximum time to wait before escalating to SIGKILL; every call
                site states its own bound.
            budget: When supplied, both waits are cut short by the shutdown deadline
                and by an interrupt request for the step in progress. The signals are
                not cut short: SIGTERM and SIGKILL are sent whatever the remaining
                time is (OD-05), and a wait that gave up reports an unconfirmed exit.

        Returns:
            ALREADY_EXITED: the exit was observed before any signal was sent.
            EXITED: the exit was observed after a signal (group gone within the
                bound, group already gone, or gone within the post-SIGKILL window).
            SIGNAL_NOT_DELIVERED: no signal call succeeded.
            EXIT_UNCONFIRMED: a signal call succeeded but the exit was not observed
                (no process group to probe, the SIGKILL call failed after SIGTERM,
                the group was still present after the post-SIGKILL window, or the
                deadline or an interrupt ended a wait first).
        """
        pid = getattr(proc, "pid", None)
        pgid = _resolve_pgid(proc)
        if pgid is None:
            if _already_exited(proc):
                logger.info("Process %s already exited", server_key)
                return TerminationOutcome.ALREADY_EXITED
            # No group to signal or probe: proc-level SIGTERM, exit cannot be observed
            logger.warning(
                "Lifecycle: %r pid=%s has no pgid; proc.terminate() fallback, exit not observed",
                server_key,
                pid,
            )
            if _signal_via_proc(proc):
                return TerminationOutcome.EXIT_UNCONFIRMED
            return TerminationOutcome.SIGNAL_NOT_DELIVERED

        if _already_exited(proc):
            logger.info("Process %s already exited", server_key)
            return TerminationOutcome.ALREADY_EXITED

        try:
            os.killpg(pgid, signal.SIGTERM)  # nosec B603 — process-group signal to terminate an admin-started MCP server subprocess, not user input
        except ProcessLookupError:
            logger.warning("%r pid=%s pgid=%d already gone", server_key, pid, pgid)
            _signal_via_proc(proc)
            return TerminationOutcome.ALREADY_EXITED
        except OSError as e:
            logger.warning(
                "Lifecycle: os.killpg(SIGTERM) failed for %r pid=%s pgid=%d: %s; falling back to proc.terminate()",
                server_key,
                pid,
                pgid,
                e,
            )
            if _signal_via_proc(proc):
                return TerminationOutcome.EXIT_UNCONFIRMED
            return TerminationOutcome.SIGNAL_NOT_DELIVERED

        deadline = _clamped_deadline(timeout, budget)
        while time.monotonic() < deadline:
            if _interrupt_requested(budget):
                logger.warning(
                    "Lifecycle: interrupt requested during the termination wait for "
                    "%r pid=%s pgid=%d; escalating without waiting",
                    server_key,
                    pid,
                    pgid,
                )
                break
            _reap(proc)
            try:
                os.killpg(pgid, 0)  # Check if process exists
                await asyncio.sleep(self._terminate_poll_interval_sec)
            except ProcessLookupError:
                logger.info("Process group %d exited within timeout", pgid)
                return TerminationOutcome.EXITED

        # Escalate to SIGKILL
        try:
            os.killpg(pgid, signal.SIGKILL)  # nosec B603 — process-group signal to force-kill an admin-started MCP server subprocess after a graceful-termination timeout
        except ProcessLookupError:
            logger.info(
                "%r pid=%s pgid=%d already exited after timeout",
                server_key,
                pid,
                pgid,
            )
            return TerminationOutcome.EXITED
        except OSError as e:
            logger.error(
                "Failed to send SIGKILL to %r pid=%s pgid=%d: %s",
                server_key,
                pid,
                pgid,
                e,
            )
            return TerminationOutcome.EXIT_UNCONFIRMED
        logger.warning(
            "Escalated to SIGKILL for %r pid=%s pgid=%d", server_key, pid, pgid
        )
        confirm_window = self._confirm_window(budget)
        if await self._confirm_group_gone(proc, pgid, budget=budget):
            return TerminationOutcome.EXITED
        logger.error(
            "%r pid=%s pgid=%d not confirmed gone within the %.2fs confirm window after SIGKILL",
            server_key,
            pid,
            pgid,
            confirm_window,
        )
        return TerminationOutcome.EXIT_UNCONFIRMED
