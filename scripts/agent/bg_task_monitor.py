#!/usr/bin/env python3
"""scripts/agent/bg_task_monitor.py

Background task failure tracking: consecutive failure counting, threshold breach
notification, and pause state management.

Extracted from orchestrator.py (_discard_and_log, _notify_bg_failure_threshold).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/agent.log")

# Threshold for background task consecutive failures
BG_FAILURE_THRESHOLD: int = 10

if TYPE_CHECKING:
    from agent.context import AgentContext

class BgTaskMonitor:
    """Monitors background task failures and enforces threshold-based policies.

    Responsibilities:
      - Track consecutive failures per task name
      - Notify user at threshold breach (first hit + every 5 thereafter)
      - Pause agent when pause_on_critical_failure is enabled
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

    @property
    def consecutive_bg_failures(self) -> int:
        """Return the current consecutive failure count for the default task."""
        return self.get_consecutive_failures("unknown_bg_task")

    @consecutive_bg_failures.setter
    def consecutive_bg_failures(self, value: int) -> None:
        """Reset consecutive failure counter for the default task."""
        self.reset_consecutive_failures("unknown_bg_task")

    def check_pause_state(self) -> tuple[bool, list[str]]:
        """Check if any background tasks are paused. Returns (is_paused, paused_names)."""
        paused = [name for name, is_paused in self._bg_pause_state.items() if is_paused]
        return len(paused) > 0, paused

    def on_task_done(self, task: asyncio.Task[Any]) -> None:
        """Callback invoked when a background task completes."""
        task_name = task.get_name()
        exc = task.exception()
        count = self._consecutive_failures.get(task_name, 0)

        if exc is not None:
            if isinstance(exc, asyncio.CancelledError):
                count = 0
            elif isinstance(exc, Exception):
                count += 1
                if count == 1:
                    logger.warning(
                        "First background task failure (%s): %s", task_name, exc
                    )
                    if self._on_error is not None:
                        try:
                            self._on_error(exc)
                        except Exception as notif_err:  # noqa: BLE001 — on_error callback must never raise; catch-all prevents notification failure from crashing the turn
                            logger.error(
                                "Failed to notify user of background task failure: %s",
                                notif_err,
                            )
                elif count >= BG_FAILURE_THRESHOLD:
                    if (
                        count == BG_FAILURE_THRESHOLD
                        or (count - BG_FAILURE_THRESHOLD) % 5 == 0
                    ):
                        logger.error(
                            "Consecutive background task failures (%d) for '%s': %s",
                            count,
                            task_name,
                            exc,
                        )
                        if count == BG_FAILURE_THRESHOLD:
                            self._notify_threshold_breach(task_name, count)
                    else:
                        logger.warning(
                            "Background task failure #%d (%s): %s",
                            count,
                            task_name,
                            exc,
                        )
        else:
            count = 0

        self._consecutive_failures[task_name] = count
        self._tasks.discard(task)

    def notify_bg_failure_threshold(self, task_name: str, count: int) -> None:
        """Guarantee the user is notified when a background task hits the failure threshold.

        Backward-compatible alias for _notify_threshold_breach.
        """
        self._notify_threshold_breach(task_name, count)

    def _notify_threshold_breach(self, task_name: str, count: int) -> None:
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
