#!/usr/bin/env python3
"""scripts/agent/bg_task_monitor.py

Background task failure tracking: consecutive failure counting, threshold breach
notification, and pause state management.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/agent.log")

# Threshold for background task consecutive failures
BG_FAILURE_THRESHOLD: int = 10

if TYPE_CHECKING:
    from agent.context import AgentContext


@dataclass(frozen=True)
class BgTaskMeta:
    """Type and session identity captured when a background task is registered.

    ``instance_id`` records the raw task name so type-grouped reporting can
    still name the concrete task instance.
    """

    task_type: str
    instance_id: str
    session_id: int | None
    generation: int | None


# Task identity registry: populated by register()/register_task_meta() and
# consumed (and popped) by BgTaskMonitor.on_task_done. Module-level so callers
# without a monitor reference can attach metadata through the existing
# task-done path.
_task_meta: dict[asyncio.Task[Any], BgTaskMeta] = {}


def register_task_meta(
    task: asyncio.Task[Any],
    *,
    task_type: str,
    session_id: int | None = None,
    generation: int | None = None,
) -> None:
    """Attach type and session identity to a task for the next on_task_done.

    Use when the monitor object is unreachable at task-creation time; the
    monitor reads the metadata when the existing done callback runs and groups
    failures by task_type (REQ-005).
    """
    _task_meta[task] = BgTaskMeta(task_type, task.get_name(), session_id, generation)


class BgTaskMonitor:
    """Monitors background task failures and enforces threshold-based policies.

    Responsibilities:
      - Track consecutive failures per task type (registered tasks, REQ-005) or
        task name (unregistered tasks)
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

    def register(
        self,
        task: asyncio.Task[Any],
        *,
        task_type: str,
        session_id: int | None = None,
        generation: int | None = None,
    ) -> None:
        """Track a task with type and session identity; failures group by type.

        The task joins the registry and its done callback runs through
        ``on_task_done``, which keys counters and pause state by ``task_type``
        while the metadata keeps session id and generation for attribution.
        """
        register_task_meta(
            task, task_type=task_type, session_id=session_id, generation=generation
        )
        self._tasks.add(task)
        if task.done():
            self.on_task_done(task)
        else:
            task.add_done_callback(self.on_task_done)

    def on_task_done(self, task: asyncio.Task[Any]) -> None:
        """Handle a completed background task across all terminal states.

        A cancelled task is neither a failure nor a success: its counter resets to 0
        (DR-002) and it is discarded from the registry. A task that completes cleanly
        (returns normally, so ``exception()`` is ``None``) also resets the streak. A
        failed task runs the unchanged failure ladder. ``task.exception()`` is never
        called on a cancelled task (``CancelledError`` derives from ``BaseException``
        and would raise).

        Registered tasks count under their task type (REQ-005); unregistered
        tasks keep the existing name-based keys.
        """
        meta = _task_meta.pop(task, None)
        task_name = meta.task_type if meta is not None else task.get_name()
        if meta is not None:
            logger.debug(
                "Background task '%s' (type=%s session=%s generation=%s) finished",
                meta.instance_id,
                meta.task_type,
                meta.session_id,
                meta.generation,
            )
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
                    self._report_first_failure(task_name, exc)
                elif count >= BG_FAILURE_THRESHOLD and isinstance(exc, Exception):
                    self._report_threshold_failure(task_name, exc, count)

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

    def _report_first_failure(self, task_name: str, exc: Exception) -> None:
        # Class name only (AC-2): raw reasons can embed request or DB details.
        logger.warning(
            "First background task failure (%s): %s", task_name, type(exc).__name__
        )
        if self._on_error is not None:
            try:
                self._on_error(exc)
            except Exception as notif_err:  # noqa: BLE001 — on_error callback must never raise; catch-all prevents notification failure from crashing the turn
                logger.error(
                    "Failed to notify user of background task failure: %s",
                    notif_err,
                )

    def _report_threshold_failure(
        self, task_name: str, exc: Exception, count: int
    ) -> None:
        if count == BG_FAILURE_THRESHOLD or (count - BG_FAILURE_THRESHOLD) % 5 == 0:
            logger.error(
                "Consecutive background task failures (%d) for '%s': %s",
                count,
                task_name,
                type(exc).__name__,
            )
            if count == BG_FAILURE_THRESHOLD:
                self.notify_bg_failure_threshold(task_name, count)
        else:
            logger.warning(
                "Background task failure #%d (%s): %s",
                count,
                task_name,
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
                    notif_err,
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
