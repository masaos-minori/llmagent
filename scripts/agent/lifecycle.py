#!/usr/bin/env python3
"""agent/lifecycle.py

LifecycleState enum shared by lifecycle managers and callers.

ServerLifecycleManager facade has been removed — routing is now handled
by _ServerLifecycleRouter in factory.py.
"""

from __future__ import annotations

from enum import Enum


class LifecycleState(Enum):
    """Transport state for HTTP MCP servers.

    Valid transitions:
      STOPPED  -> STARTING, FAILED
      STARTING -> RUNNING, FAILED, STOPPED
      RUNNING  -> STOPPED, FAILED, STARTING
      FAILED   -> STARTING, STOPPED
      UNKNOWN  -> any
    """

    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


_VALID_TRANSITIONS: dict[LifecycleState, frozenset[LifecycleState]] = {
    LifecycleState.STOPPED: frozenset({LifecycleState.STARTING, LifecycleState.FAILED}),
    LifecycleState.STARTING: frozenset(
        {LifecycleState.RUNNING, LifecycleState.FAILED, LifecycleState.STOPPED}
    ),
    LifecycleState.RUNNING: frozenset(
        {LifecycleState.STOPPED, LifecycleState.FAILED, LifecycleState.STARTING}
    ),
    LifecycleState.FAILED: frozenset({LifecycleState.STARTING, LifecycleState.STOPPED}),
    LifecycleState.UNKNOWN: frozenset(LifecycleState),
}


def assert_valid_transition(
    from_state: LifecycleState, to_state: LifecycleState
) -> None:
    """Raise ValueError when the transition from_state -> to_state is not legal."""
    if to_state not in _VALID_TRANSITIONS.get(from_state, frozenset()):
        raise ValueError(
            f"Invalid lifecycle transition: {from_state!r} -> {to_state!r}"
        )
