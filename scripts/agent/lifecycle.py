#!/usr/bin/env python3
"""scripts/agent/lifecycle.py

LifecycleState enum shared by lifecycle managers and callers.

ServerLifecycleManager facade has been removed — routing is now handled
by _ServerLifecycleRouter in lifecycle_router.py.
"""

from __future__ import annotations

from enum import Enum


class LifecycleState(Enum):
    """Transport state for HTTP MCP servers.

    Valid transitions:
      STOPPED  -> STARTING, FAILED, STOPPED
      STARTING -> RUNNING, FAILED, STOPPED, EXIT_UNCONFIRMED, SIGNAL_NOT_DELIVERED
      RUNNING  -> STOPPED, FAILED, STARTING, STOPPING
      STOPPING -> STOPPED, EXIT_UNCONFIRMED, SIGNAL_NOT_DELIVERED
      EXIT_UNCONFIRMED -> STARTING, STOPPED
      SIGNAL_NOT_DELIVERED -> STARTING, STOPPED
      FAILED   -> STARTING, STOPPED
      UNKNOWN  -> any
    """

    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"
    STOPPING = "stopping"
    EXIT_UNCONFIRMED = "exit_unconfirmed"
    SIGNAL_NOT_DELIVERED = "signal_not_delivered"


_VALID_TRANSITIONS: dict[LifecycleState, frozenset[LifecycleState]] = {
    LifecycleState.STOPPED: frozenset({LifecycleState.STARTING, LifecycleState.FAILED}),
    LifecycleState.STARTING: frozenset(
        {
            LifecycleState.RUNNING,
            LifecycleState.FAILED,
            LifecycleState.STOPPED,
            # A start/restart attempt whose termination signal left the exit
            # unconfirmed (restart refusal, startup-failure retention): the
            # router maps the attempt to the outcome state (REQ-006, REQ-008).
            LifecycleState.EXIT_UNCONFIRMED,
            LifecycleState.SIGNAL_NOT_DELIVERED,
        }
    ),
    LifecycleState.RUNNING: frozenset(
        {
            LifecycleState.STOPPED,
            LifecycleState.FAILED,
            LifecycleState.STARTING,
            LifecycleState.STOPPING,
        }
    ),
    LifecycleState.STOPPING: frozenset(
        {
            LifecycleState.STOPPED,
            LifecycleState.EXIT_UNCONFIRMED,
            LifecycleState.SIGNAL_NOT_DELIVERED,
        }
    ),
    LifecycleState.EXIT_UNCONFIRMED: frozenset(
        {LifecycleState.STARTING, LifecycleState.STOPPED}
    ),
    LifecycleState.SIGNAL_NOT_DELIVERED: frozenset(
        {LifecycleState.STARTING, LifecycleState.STOPPED}
    ),
    LifecycleState.FAILED: frozenset({LifecycleState.STARTING, LifecycleState.STOPPED}),
    LifecycleState.UNKNOWN: frozenset(LifecycleState),
}

# Same-state STOPPED->STOPPED is valid (e.g., during shutdown).
_VALID_TRANSITIONS[LifecycleState.STOPPED] |= frozenset({LifecycleState.STOPPED})


def assert_valid_transition(
    from_state: LifecycleState, to_state: LifecycleState
) -> None:
    """Raise ValueError when the transition from_state -> to_state is not legal."""
    valid_targets = _VALID_TRANSITIONS.get(from_state, frozenset())
    if to_state not in valid_targets:
        targets_str = (
            ", ".join(t.name for t in valid_targets) if valid_targets else "(none)"
        )
        raise ValueError(
            f"Invalid lifecycle transition: {from_state!r} -> {to_state!r}. "
            f"Valid targets from {from_state!r}: {targets_str}"
        )
