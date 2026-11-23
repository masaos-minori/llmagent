#!/usr/bin/env python3
"""scripts/agent/bg_task_monitor.py

Background task failure tracking: consecutive failure counting, threshold breach
notification, and pause state management.
"""

from __future__ import annotations

import asyncio
import contextvars
import itertools
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/agent.log")

# Threshold for background task consecutive failures
BG_FAILURE_THRESHOLD: int = 10

if TYPE_CHECKING:
    from agent.context import AgentContext
    from agent.session import SessionTarget

_instance_ids = itertools.count(1)


@dataclass(frozen=True)
class TaskIdentity:
    """Who created a background task: its type, instance, session and generation."""

    task_type: str
    instance_id: str
    session_id: int | None
    generation: int


# A task copies the context current at ``asyncio.create_task``, so an identity bound
# just before the call is visible inside the task (see ``bind_task_identity``) and to
# the monitor through ``task.get_context()``. The ``on_first_turn`` callable signature
# therefore stays unchanged.
_TASK_IDENTITY: contextvars.ContextVar[TaskIdentity | None] = contextvars.ContextVar(
    "bg_task_identity", default=None
)


def new_task_identity(
    task_type: str, session_id: int | None, generation: int
) -> TaskIdentity:
    """Build an identity with a fresh instance id."""
    return TaskIdentity(
        task_type, f"{task_type}-{next(_instance_ids)}", session_id, generation
    )


@contextmanager
def bind_task_identity(identity: TaskIdentity) -> Iterator[None]:
    """Bind ``identity`` for tasks created inside the ``with`` block.

    The one documented place a background task gets its identity: wrap the
    ``asyncio.create_task`` call, and read it back inside the task with
    ``current_task_identity`` / ``current_task_target``.
    """
    token = _TASK_IDENTITY.set(identity)
    try:
        yield
    finally:
        _TASK_IDENTITY.reset(token)


def current_task_identity() -> TaskIdentity | None:
    """Return the identity bound where the running task was created, if any."""
    return _TASK_IDENTITY.get()


def current_task_target() -> SessionTarget | None:
    """Return the session target captured where the running task was created."""
    from agent.session import SessionTarget  # lazy import: avoids an import cycle

    identity = _TASK_IDENTITY.get()
    if identity is None:
        return None
    return SessionTarget(identity.session_id, identity.generation)


class BgTaskMonitor:
    """Monitors background task failures and enforces threshold-based policies.

    Responsibilities:
      - Track consecutive failures per task type (tasks registered with an identity)
        or per task name (tasks without one)
      - Notify user at threshold breach (first hit + every 5 thereafter)
      - Pause agent when pause_on_critical_failure is enabled

    Note: The `consecutive_bg_failures` property was removed in favor of the explicit
    `get_consecutive_failures(task_name)` and `reset_consecutive_failures(task_name)`
    methods, which properly accept a task name parameter.
    """

    def __init__(
        self,
        ctx: AgentContext,
        *,
        tasks: set[asyncio.Task[Any]],
        on_discard: Callable[[asyncio.Task[Any]], None],
        on_error: Callable[[Exception], None] | None = None,
        pause_on_critical_failure: bool = False,
    ) -> None:
        """Initialize the background task monitor."""
        self._ctx = ctx
        self._tasks = tasks
        self._on_discard = on_discard
        self._on_error = on_error
        self._pause_on_critical_failure = pause_on_critical_failure
        self._consecutive_failures: dict[str, int] = {}
        self._bg_pause_state: dict[str, bool] = {}
        self._identities: dict[asyncio.Task[Any], TaskIdentity] = {}

    def register(
        self,
        task: asyncio.Task[Any],
        task_type: str,
        session_id: int | None,
        generation: int,
        instance_id: str | None = None,
    ) -> TaskIdentity:
        """Register ``task`` with its type, instance id, session id and generation."""
        identity = TaskIdentity(
            task_type,
            instance_id or f"{task_type}-{next(_instance_ids)}",
            session_id,
            generation,
        )
        self._identities[task] = identity
        return identity

    def _identity_of(self, task: asyncio.Task[Any]) -> TaskIdentity | None:
        """Return the explicit registration, else the identity bound at creation."""
        registered = self._identities.pop(task, None)
        if registered is not None:
            return registered
        return task.get_context().get(_TASK_IDENTITY)

    @property
    def bg_pause_state(self) -> dict[str, bool]:
        """Expose pause state for orchestrator-level turn blocking."""
        return self._bg_pause_state

    @bg_pause_state.setter
    def bg_pause_state(self, value: dict[str, bool]) -> None:
        """Set pause state for orchestrator-level turn blocking."""
        self._bg_pause_state = value

    def check_pause_state(self) -> tuple[bool, list[str]]:
        """Check if any background tasks are paused. Returns (is_paused, paused_names)."""
        paused = [name for name, is_paused in self._bg_pause_state.items() if is_paused]
        return len(paused) > 0, paused

    def on_task_done(self, task: asyncio.Task[Any]) -> None:
        """Handle a completed background task across all terminal states.

        A cancelled task is neither a failure nor a success: its counter resets to 0
        (DR-002) and it is discarded from the registry. A task that completes cleanly
        (returns normally, so ``exception()`` is ``None``) also resets the streak. A
        failed task runs the unchanged failure ladder. ``task.exception()`` is never
        called on a cancelled task (``CancelledError`` derives from ``BaseException``
        and would raise).
        """
        identity = self._identity_of(task)
        task_name = task.get_name() if identity is None else identity.task_type
        count = self._consecutive_failures.get(task_name, 0)

        if task.cancelled():
            count = 0
        else:
            exc = task.exception()
            if (
                exc is None
            ):  # clean completion resets the streak and resumes a paused type
                count = 0
                self._bg_pause_state.pop(task_name, None)
            else:
                count = self._count_failure(task_name, exc, count)
                if count == 1 and isinstance(exc, Exception):
                    self._report_first_failure(task_name, exc, identity)
                elif count >= BG_FAILURE_THRESHOLD and isinstance(exc, Exception):
                    self._report_threshold_failure(task_name, exc, count, identity)

        self._consecutive_failures[task_name] = count
        self._tasks.discard(task)

    def _count_failure(self, task_name: str, exc: BaseException, count: int) -> int:
        if isinstance(
            exc, asyncio.CancelledError
        ):  # coroutine surfaced CancelledError without the task being cancelled
            return 0
        if not isinstance(
            exc, Exception
        ):  # a non-Exception BaseException leaves the streak intact
            return count
        return count + 1

    @staticmethod
    def _describe(task_name: str, identity: TaskIdentity | None) -> str:
        """Return the task key plus session identity; never exception or title text."""
        if identity is None:
            return task_name
        return (
            f"{task_name} instance={identity.instance_id} "
            f"session={identity.session_id} generation={identity.generation}"
        )

    def _report_first_failure(
        self, task_name: str, exc: Exception, identity: TaskIdentity | None = None
    ) -> None:
        logger.warning(
            "First background task failure (%s): %s",
            self._describe(task_name, identity),
            type(exc).__name__,
        )
        if self._on_error is not None:
            try:
                self._on_error(exc)
            except Exception as notif_err:  # noqa: BLE001 — on_error callback must never raise; catch-all prevents notification failure from crashing the turn
                logger.error(
                    "Failed to notify user of background task failure: %s",
                    type(notif_err).__name__,
                )

    def _report_threshold_failure(
        self,
        task_name: str,
        exc: Exception,
        count: int,
        identity: TaskIdentity | None = None,
    ) -> None:
        described = self._describe(task_name, identity)
        if count == BG_FAILURE_THRESHOLD or (count - BG_FAILURE_THRESHOLD) % 5 == 0:
            logger.error(
                "Consecutive background task failures (%d) for '%s': %s",
                count,
                described,
                type(exc).__name__,
            )
            if count == BG_FAILURE_THRESHOLD:
                self.notify_bg_failure_threshold(task_name, count)
        else:
            logger.warning(
                "Background task failure #%d (%s): %s",
                count,
                described,
                type(exc).__name__,
            )

    def notify_bg_failure_threshold(self, task_name: str, count: int) -> None:
        """Guarantee the user is notified when a background task hits the failure threshold."""
        message = RuntimeError(
            f"Background task '{task_name}' has failed {count} consecutive times "
            f"(threshold: {BG_FAILURE_THRESHOLD})."
        )
        if self._on_error is not None:
            try:
                self._on_error(message)
            except Exception as notif_err:  # noqa: BLE001 — on_error callback must never raise; catch-all prevents notification failure from crashing the turn
                logger.critical(
                    "Failed to notify user of threshold breach for '%s': %s",
                    task_name,
                    type(notif_err).__name__,
                )
        else:
            logger.critical(str(message))
        if self._pause_on_critical_failure:
            self._bg_pause_state[task_name] = True
            logger.warning(
                "Background task type '%s' paused after reaching threshold.", task_name
            )

    def clear_first_failure(self, task_name: str) -> None:
        """Clear the first-failure warning counter for a task."""
        self._consecutive_failures[task_name] = 0

    def reset_consecutive_failures(self, task_name: str) -> None:
        """Reset consecutive failure counter for a successful task."""
        self._consecutive_failures[task_name] = 0

    def get_consecutive_failures(self, task_name: str) -> int:
        """Return the current consecutive failure count for a task name."""
        return self._consecutive_failures.get(task_name, 0)
