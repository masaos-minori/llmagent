"""scripts/agent/http_lifecycle_process_record.py — single ownership record for one HTTP MCP subprocess.

ManagedProcessRecord: the single ownership record for one HTTP MCP subprocess.

One record owns the process handle, pid, pgid, stderr log handle, lifecycle
state, last termination outcome, and the startup-failure retention flag. It
replaces the three parallel tracking dicts in http_lifecycle.py (REQ-001) and
is released from the registry only when its exit is confirmed (REQ-002).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import IO

from agent.http_lifecycle_errors import TerminationOutcome
from agent.lifecycle import LifecycleState


@dataclass
class ManagedProcessRecord:
    """Per-server process record; outcome and state update in place.

    The record is mutable on purpose: ``state`` and ``last_outcome`` are
    rewritten during termination. ``stderr_log`` references the open file
    handle opened by ``StderrLogManager.open_log``; the manager keeps path and
    tail-read ownership (``forget``/``read_tail``).
    """

    process: subprocess.Popen[bytes]
    pid: int
    pgid: int | None
    stderr_log: IO[bytes] | None
    state: LifecycleState
    last_outcome: TerminationOutcome | None = None
    failed_start: bool = False

    @property
    def confirmed(self) -> bool:
        """True when the last termination outcome proved the process gone."""
        return self.last_outcome is not None and self.last_outcome.confirmed

    def settle(self, outcome: TerminationOutcome) -> bool:
        """Apply a termination outcome to the record; return True when releasable.

        A confirmed outcome moves the state to STOPPED and the caller releases
        the record from the registry. An unconfirmed outcome moves it to
        EXIT_UNCONFIRMED (or SIGNAL_NOT_DELIVERED) and the caller must retain
        it so status surfaces still name the process (REQ-002, REQ-003).
        """
        self.last_outcome = outcome
        if outcome.confirmed:
            self.state = LifecycleState.STOPPED
            return True
        self.state = (
            LifecycleState.SIGNAL_NOT_DELIVERED
            if outcome is TerminationOutcome.SIGNAL_NOT_DELIVERED
            else LifecycleState.EXIT_UNCONFIRMED
        )
        return False
