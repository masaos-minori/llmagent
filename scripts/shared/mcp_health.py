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


class McpServerHealthRegistry:
    """Tracks per-server health states for ToolExecutor dispatch gating."""

    def __init__(
        self,
        failure_threshold: int = 3,
        half_open_cooldown_sec: float = 30.0,
    ) -> None:
        self._states: dict[str, McpServerHealthState] = {}
        self._failure_counts: dict[str, int] = {}
        self._failure_threshold = failure_threshold
        self._half_open_cooldown_sec = half_open_cooldown_sec
        self._unavailable_since: dict[str, float] = {}

    def record_failure(self, server_key: str) -> McpServerHealthState:
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

    def record_success(self, server_key: str) -> None:
        prev = self.get_state(server_key)
        self._states[server_key] = McpServerHealthState.HEALTHY
        self._failure_counts[server_key] = 0
        self._unavailable_since.pop(server_key, None)
        if prev == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def get_state(self, server_key: str) -> McpServerHealthState:
        return self._states.get(server_key, McpServerHealthState.HEALTHY)

    def is_unavailable(self, server_key: str) -> bool:
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
