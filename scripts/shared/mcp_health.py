#!/usr/bin/env python3
"""scripts/shared/mcp_health.py — MCP server health tracking for dispatch gating."""

import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)


class McpServerHealthState(Enum):
    """Represents the health status of an MCP server."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"  # failing but not yet unavailable
    UNAVAILABLE = "unavailable"
    HALF_OPEN = "half_open"
    UNKNOWN = "unknown"


class McpServerHealthRegistry:
    """Tracks per-server health states for ToolExecutor dispatch gating."""

    def __init__(
        self,
        failure_threshold: int = 3,
        half_open_cooldown_sec: float = 30.0,
    ) -> None:
        """Initialize with failure threshold and half-open cooldown duration."""
        self._states: dict[str, McpServerHealthState] = {}
        self._failure_counts: dict[str, int] = {}
        self._failure_threshold = failure_threshold
        self._half_open_cooldown_sec = half_open_cooldown_sec
        self._unavailable_since: dict[str, float] = {}
        # Servers with a HALF_OPEN trial currently in flight. At most one trial
        # per server may dispatch while HALF_OPEN; this set enforces that single
        # trial window.
        self._half_open_trials: set[str] = set()

    def record_failure(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        if was_half_open or count >= self._failure_threshold:
            self._states[server_key] = McpServerHealthState.UNAVAILABLE
            self._unavailable_since[server_key] = time.monotonic()
            if was_half_open:
                self.release_trial(server_key)
                logger.warning(
                    "Health: %r trial probe failed → UNAVAILABLE (cooldown reset)",
                    server_key,
                )
            return McpServerHealthState.UNAVAILABLE
        self._states[server_key] = McpServerHealthState.DEGRADED
        return McpServerHealthState.DEGRADED

    def record_success(self, server_key: str) -> None:
        """Record a successful call and reset the server to HEALTHY.

        In addition to setting the state to `HEALTHY`, this clears
        `_failure_counts` and `_unavailable_since` for `server_key`.
        Clearing `_failure_counts` matters because
        `record_failure()` compares the running count against
        `_failure_threshold`; without this reset, a later `record_failure()`
        call could jump straight back to `UNAVAILABLE` using a stale count
        left over from before this success.
        """
        prev = self.get_state(server_key)
        self._states[server_key] = McpServerHealthState.HEALTHY
        self._failure_counts[server_key] = 0
        self._unavailable_since.pop(server_key, None)
        if prev == McpServerHealthState.HALF_OPEN:
            self.release_trial(server_key)
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def get_state(self, server_key: str) -> McpServerHealthState:
        """Get the current health state for a server, defaulting to HEALTHY."""
        return self._states.get(server_key, McpServerHealthState.HEALTHY)

    def is_unavailable(self, server_key: str) -> bool:
        """Return whether dispatch to `server_key` should currently be blocked.

        Not a pure getter: as a side effect, once a server has been in
        `UNAVAILABLE` for at least `_half_open_cooldown_sec`, this call
        transitions its state to `HALF_OPEN` (a single-trial dispatch window)
        and returns `False` for that call, allowing exactly one trial dispatch
        through. Callers must not assume repeated calls are idempotent.
        """
        state = self.get_state(server_key)
        if state != McpServerHealthState.UNAVAILABLE:
            return False
        since = self._unavailable_since.get(server_key, 0.0)
        if time.monotonic() - since >= self._half_open_cooldown_sec:
            self._states[server_key] = McpServerHealthState.HALF_OPEN
            self.acquire_trial(server_key)
            logger.info(
                "Health: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)",
                server_key,
            )
            return False
        return True

    def acquire_trial(self, server_key: str) -> bool:
        """Mark a HALF_OPEN trial as in-flight for `server_key`.

        Returns True if this call acquired the single trial slot (no trial was
        already in flight), False if a trial is already in flight. Must be called
        synchronously — with no `await` between the HALF_OPEN state check and this
        call — so that a concurrent asyncio burst yields exactly one trial.
        """
        if server_key in self._half_open_trials:
            return False
        self._half_open_trials.add(server_key)
        return True

    def release_trial(self, server_key: str) -> None:
        """Clear the HALF_OPEN trial flag for `server_key`.

        Idempotent; safe to call on every exit path (success, failure, or
        cancellation).
        """
        self._half_open_trials.discard(server_key)

    def trial_in_flight(self, server_key: str) -> bool:
        """Return whether a HALF_OPEN trial is currently in flight for `server_key`."""
        return server_key in self._half_open_trials
