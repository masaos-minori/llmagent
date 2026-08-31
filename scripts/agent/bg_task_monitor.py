#!/usr/bin/env python3
"""scripts/agent/bg_task_monitor.py

Background task failure tracking and threshold notification, extracted from
Orchestrator (see
`issues/done/20260829-080923_refactor_001_orchestrator_separation.md`).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from shared.logger import Logger

# Threshold for the first-turn background task's consecutive-failure counter
# (see `BgTaskMonitor.discard_and_log` / `self._consecutive_bg_failures`).
#
# - Effect: log-level selection only. Below this threshold, failures log via
#   `logger.warning`; at or above it, they log via `logger.error`. There is no
#   circuit-breaking or task-disabling behavior — the background task keeps
#   being scheduled on every first turn regardless of this counter's value.
# - Scope: applies only to the first-turn session-title-generation background
#   task (`self._on_first_turn`, scheduled from `TurnCoordinator.append_user_message`).
#   It is not a general-purpose background-task failure budget.
# - Reset semantics: the counter resets to 0 on a successful completion or on
#   `asyncio.CancelledError`; it is NOT reset by `/clear` or `/session load`
#   (see `discard_and_log`'s docstring for why).
# - Configurability: evaluated and deferred. Moving this into `AgentConfig`
#   would require touching `config/agent.toml`, `config_dataclasses.py`,
#   `config_validators.py`, and `config_builders.py` in addition to this file,
#   which is disproportionate for a value whose only effect is a log-level
#   choice. If this is revisited, `ToolConfig.tool_error_max_consecutive`
#   (`scripts/agent/config_dataclasses.py:168`) is the copyable precedent for
#   wiring a similar threshold through config.
BG_FAILURE_THRESHOLD: int = 10

logger = Logger(__name__, "/opt/llm/logs/agent.log")


class BgTaskMonitor:
    """Tracks consecutive background-task failures and notifies on threshold breach."""

    def __init__(
        self,
        background_tasks: set[asyncio.Task[object]],
        *,
        on_error: Callable[[Exception], None] | None = None,
        pause_on_critical_failure: bool = False,
    ) -> None:
        """Initialize the monitor with the shared background-task set, an error
        callback, and the pause opt-in flag."""
        self._background_tasks = background_tasks
        self._on_error = on_error
        # Opt-in: when True, a background task type is paused (see
        # `_bg_pause_state`) once its consecutive-failure count reaches
        # `BG_FAILURE_THRESHOLD`. Defaults to False so existing callers are
        # unaffected until they explicitly opt in.
        self._pause_on_critical_failure = pause_on_critical_failure
        # Per-task-type pause flags, keyed by `asyncio.Task.get_name()`. A
        # `True` entry blocks further `handle_turn()` processing until the
        # process is restarted (see `notify_bg_failure_threshold` and the
        # guard at the top of `Orchestrator.handle_turn`).
        self._bg_pause_state: dict[str, bool] = {}
        # Scoped to a single background-task type today (the first-turn
        # session-title-generation task handled by `discard_and_log`). Do not
        # reuse this single counter for a second, distinct background-task
        # type — give any new task type its own counter instead, since a
        # shared counter would conflate unrelated failure streams and distort
        # the log-level threshold in `discard_and_log`.
        self._consecutive_bg_failures: int = 0

    def discard_and_log(self, task: asyncio.Task[Any]) -> None:
        """Callback for first-turn background task completion.

        Cross-session accumulation: `self._consecutive_bg_failures` can span
        multiple `/clear` / `/session load` cycles within one process
        lifetime. `Orchestrator` is a long-lived singleton constructed once
        (`startup.py:117`) and reused across
        `conversation_service.clear_conversation` and
        `agent/services/session_restore.py:46` — neither of those reset
        points touches this counter, so a failure streak that started before
        a `/clear` or session switch continues to count toward
        `BG_FAILURE_THRESHOLD` afterward. Only a successful
        completion or an `asyncio.CancelledError` completion of this
        callback resets it to 0.
        """
        task_name = task.get_name()
        exc = task.exception()
        if exc is not None:
            if isinstance(exc, asyncio.CancelledError):
                # Task was cancelled — reset counter, do not log as error.
                self._consecutive_bg_failures = 0
            else:
                self._consecutive_bg_failures += 1
                if self._consecutive_bg_failures == 1:
                    logger.warning(
                        "First background task failure (%s): %s", task_name, exc
                    )
                    # Surface first-turn failure to user immediately
                    if isinstance(exc, Exception) and self._on_error is not None:
                        try:
                            self._on_error(exc)
                        except Exception as notif_err:  # noqa: BLE001 — caller-supplied error callback must not raise and crash the background-task monitor
                            logger.error(
                                "Failed to notify user of background task failure: %s",
                                notif_err,
                            )
                elif self._consecutive_bg_failures >= BG_FAILURE_THRESHOLD:
                    if (
                        self._consecutive_bg_failures == BG_FAILURE_THRESHOLD
                        or (self._consecutive_bg_failures - BG_FAILURE_THRESHOLD) % 5
                        == 0
                    ):
                        logger.error(
                            "Consecutive background task failures (%d) for '%s': %s",
                            self._consecutive_bg_failures,
                            task_name,
                            exc,
                        )
                        if self._consecutive_bg_failures == BG_FAILURE_THRESHOLD:
                            self.notify_bg_failure_threshold(
                                task_name, self._consecutive_bg_failures
                            )
                    else:
                        logger.warning(
                            "Background task failure #%d (%s): %s",
                            self._consecutive_bg_failures,
                            task_name,
                            exc,
                        )
        else:
            # Task completed successfully — reset counter
            self._consecutive_bg_failures = 0
        self._background_tasks.discard(task)

    def notify_bg_failure_threshold(self, task_name: str, count: int) -> None:
        """Guarantee the user is notified when a background task hits the failure threshold."""
        message = RuntimeError(
            f"Background task '{task_name}' has failed {count} consecutive times "
            f"(threshold: {BG_FAILURE_THRESHOLD})."
        )
        if self._on_error is not None:
            try:
                self._on_error(message)
            except Exception as notif_err:  # noqa: BLE001 — caller-supplied error callback must not raise and crash the background-task monitor
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
