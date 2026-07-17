#!/usr/bin/env python3
"""shared/mcp_health.py — MCP server health tracking for dispatch gating."""

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
        self._degraded_reasons: dict[str, str] = {}

    def record_failure(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        if was_half_open or count >= self._failure_threshold:
            self._states[server_key] = McpServerHealthState.UNAVAILABLE
            self._unavailable_since[server_key] = time.monotonic()
            if was_half_open:
                logger.warning(
                    "Health: %r trial probe failed → UNAVAILABLE (cooldown reset)",
                    server_key,
                )
            return McpServerHealthState.UNAVAILABLE
        self._states[server_key] = McpServerHealthState.DEGRADED
        return McpServerHealthState.DEGRADED

    def record_degraded(self, server_key: str, reason: str | None = None) -> None:
        """Record a reachable-but-degraded server without triggering UNAVAILABLE.

        Does not downgrade a server currently in `UNAVAILABLE` or `HALF_OPEN`
        state: those states gate dispatch via `is_unavailable()`, and `HALF_OPEN`
        additionally represents a single-trial probe window. Allowing a
        reachable-but-degraded watchdog probe to overwrite either state with
        `DEGRADED` would silently defeat the circuit breaker (`is_unavailable()`
        would start returning `False` again) or consume the trial window without
        an actual trial outcome. When guarded, this method logs at `debug` level
        and returns without mutating `_states` or `_degraded_reasons`.
        """
        current = self.get_state(server_key)
        if current in (
            McpServerHealthState.UNAVAILABLE,
            McpServerHealthState.HALF_OPEN,
        ):
            logger.debug(
                "Health: ignored degraded probe for %r, current state=%s",
                server_key,
                current.value,
            )
            return
        self._states[server_key] = McpServerHealthState.DEGRADED
        if reason is not None:
            self._degraded_reasons[server_key] = reason
        logger.warning(
            "Health: %r is DEGRADED (reason=%s)", server_key, reason or "unknown"
        )

    def get_degraded_reason(self, server_key: str) -> str | None:
        """Return the last recorded degraded reason for a server, or None."""
        return self._degraded_reasons.get(server_key)

    def record_success(self, server_key: str) -> None:
        """Record a successful call and reset the server to HEALTHY.

        In addition to setting the state to `HEALTHY`, this clears
        `_failure_counts`, `_unavailable_since`, and `_degraded_reasons` for
        `server_key`. Clearing `_failure_counts` matters because
        `record_failure()` compares the running count against
        `_failure_threshold`; without this reset, a later `record_failure()`
        call could jump straight back to `UNAVAILABLE` using a stale count
        left over from before this success.
        """
        prev = self.get_state(server_key)
        self._states[server_key] = McpServerHealthState.HEALTHY
        self._failure_counts[server_key] = 0
        self._unavailable_since.pop(server_key, None)
        self._degraded_reasons.pop(server_key, None)
        if prev == McpServerHealthState.HALF_OPEN:
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
            logger.info(
                "Health: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)",
                server_key,
            )
            return False
        return True
