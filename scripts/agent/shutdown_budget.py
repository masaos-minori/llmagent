#!/usr/bin/env python3
"""scripts/agent/shutdown_budget.py

ShutdownBudget — one clock and one outcome vocabulary for the bounded shutdown
sequence (cliplc004 REQ-001, REQ-002, REQ-012).

Responsibilities:
  - Arm one global deadline on the first shutdown request; later requests never
    extend it
  - Publish the acceptance phase (accepting -> draining -> closed) that decides
    whether new work is still accepted
  - Hand every step only the time that is left via remaining()
  - Carry the step-name constants, the outcome vocabulary, and the step-record
    and report types the coordinator records

No I/O, no asyncio, no imports from agent services: every layer may hold this
module without violating the .importlinter contracts.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

# The eight named shutdown steps, in the order the coordinator runs them (REQ-001).
STEP_ENTER_SHUTDOWN: Final = "enter_shutdown"
STEP_SETTLE_WRITERS: Final = "settle_writers"
STEP_PERSIST_SNAPSHOT: Final = "persist_snapshot"
STEP_CHECKPOINT: Final = "checkpoint"
STEP_BACKUP: Final = "backup"
STEP_TERMINATE_LIFECYCLES: Final = "terminate_lifecycles"
STEP_CLOSE_HOOKS: Final = "close_hooks"
STEP_REPORT: Final = "report"

SHUTDOWN_STEPS: Final[tuple[str, ...]] = (
    STEP_ENTER_SHUTDOWN,
    STEP_SETTLE_WRITERS,
    STEP_PERSIST_SNAPSHOT,
    STEP_CHECKPOINT,
    STEP_BACKUP,
    STEP_TERMINATE_LIFECYCLES,
    STEP_CLOSE_HOOKS,
    STEP_REPORT,
)


class ShutdownPhase(StrEnum):
    """Whether the shutdown machine still accepts new work."""

    ACCEPTING = "accepting"
    """New turns, commands, and writes are accepted."""
    DRAINING = "draining"
    """Shutdown has begun; new work is refused and the sequence is running."""
    CLOSED = "closed"
    """The sequence finished; a late dispatch is refused, not queued."""


class ShutdownOutcome(StrEnum):
    """What one shutdown step proved about itself."""

    COMPLETED = "completed"
    """The step ran to its normal end within its bound."""
    TIMED_OUT = "timed_out"
    """The step's bound or the global deadline ran out before it finished."""
    FAILED = "failed"
    """The step raised; the sequence advanced past it."""
    NOT_STARTED = "not_started"
    """The step was blocked by an unsettled writer and never began (OD-02)."""
    OUTCOME_UNKNOWN = "outcome_unknown"
    """The step was abandoned while still running; its effect is unknown."""


@dataclass(frozen=True)
class ShutdownStepRecord:
    """One step's outcome line.

    detail is a reason category plus a bounded, path-free summary;
    paths and exception text stay in the logger.
    """

    name: str
    outcome: ShutdownOutcome
    elapsed_s: float
    detail: str = ""


@dataclass(frozen=True)
class ShutdownReport:
    """The whole sequence: one record per step plus the counts the report step
    prints. Assembled by appending records; not mutated afterwards."""

    records: tuple[ShutdownStepRecord, ...] = ()
    refused_write_count: int = 0
    unsettled_writers: tuple[str, ...] = ()


class ShutdownBudget:
    """One global shutdown deadline, armed by the first shutdown request.

    Arming is idempotent: arm() records only the first request, which is what
    makes the first signal win and keeps remaining() from being extended by a
    user pressing Ctrl-C repeatedly. Mutable state is guarded by a lock because
    arming and the interrupt request can arrive from a signal-handler thread
    while the event loop reads remaining().
    """

    def __init__(
        self,
        total_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Initialize unarmed with the total window and a monotonic clock."""
        if total_seconds < 0:
            raise ValueError(f"total_seconds must be >= 0, got {total_seconds!r}")
        self._total_seconds = total_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._deadline: float | None = None
        self._phase = ShutdownPhase.ACCEPTING
        self._interrupt_requested = False

    @property
    def armed(self) -> bool:
        """Return True once the first shutdown request has set the deadline."""
        with self._lock:
            return self._deadline is not None

    @property
    def phase(self) -> ShutdownPhase:
        """Return the current acceptance phase."""
        with self._lock:
            return self._phase

    @property
    def interrupt_requested(self) -> bool:
        """Return True once a second SIGINT has asked the running step to stop."""
        with self._lock:
            return self._interrupt_requested

    def arm(self) -> bool:
        """Record the first shutdown request; return False for every later one."""
        with self._lock:
            if self._deadline is not None:
                return False
            self._deadline = self._clock() + self._total_seconds
            self._phase = ShutdownPhase.DRAINING
            return True

    def mark_closed(self) -> None:
        """Move the phase to closed when the sequence finishes."""
        with self._lock:
            self._phase = ShutdownPhase.CLOSED

    def request_interrupt(self) -> None:
        """Mark the running step interrupted (the second-SIGINT channel, REQ-011)."""
        with self._lock:
            self._interrupt_requested = True

    def remaining(self) -> float:
        """Time left until the deadline, clamped to >= 0; the full window unarmed."""
        with self._lock:
            if self._deadline is None:
                return self._total_seconds
            return max(0.0, self._deadline - self._clock())
