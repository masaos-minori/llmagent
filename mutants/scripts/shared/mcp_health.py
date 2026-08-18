#!/usr/bin/env python3
"""scripts/shared/mcp_health.py — MCP server health tracking for dispatch gating."""

import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


class McpServerHealthState(Enum):
    """Represents the health status of an MCP server."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"  # failing but not yet unavailable
    UNAVAILABLE = "unavailable"
    HALF_OPEN = "half_open"
    UNKNOWN = "unknown"
mutants_xǁMcpServerHealthRegistryǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut: MutantDict = {}  # type: ignore
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut: MutantDict = {}  # type: ignore
mutants_xǁMcpServerHealthRegistryǁget_degraded_reason__mutmut: MutantDict = {}  # type: ignore
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut: MutantDict = {}  # type: ignore
mutants_xǁMcpServerHealthRegistryǁget_state__mutmut: MutantDict = {}  # type: ignore
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut: MutantDict = {}  # type: ignore


class McpServerHealthRegistry:
    """Tracks per-server health states for ToolExecutor dispatch gating."""

    @_mutmut_mutated(mutants_xǁMcpServerHealthRegistryǁ__init____mutmut)
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

    def xǁMcpServerHealthRegistryǁ__init____mutmut_orig(
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

    def xǁMcpServerHealthRegistryǁ__init____mutmut_1(
        self,
        failure_threshold: int = 4,
        half_open_cooldown_sec: float = 30.0,
    ) -> None:
        """Initialize with failure threshold and half-open cooldown duration."""
        self._states: dict[str, McpServerHealthState] = {}
        self._failure_counts: dict[str, int] = {}
        self._failure_threshold = failure_threshold
        self._half_open_cooldown_sec = half_open_cooldown_sec
        self._unavailable_since: dict[str, float] = {}
        self._degraded_reasons: dict[str, str] = {}

    def xǁMcpServerHealthRegistryǁ__init____mutmut_2(
        self,
        failure_threshold: int = 3,
        half_open_cooldown_sec: float = 31.0,
    ) -> None:
        """Initialize with failure threshold and half-open cooldown duration."""
        self._states: dict[str, McpServerHealthState] = {}
        self._failure_counts: dict[str, int] = {}
        self._failure_threshold = failure_threshold
        self._half_open_cooldown_sec = half_open_cooldown_sec
        self._unavailable_since: dict[str, float] = {}
        self._degraded_reasons: dict[str, str] = {}

    def xǁMcpServerHealthRegistryǁ__init____mutmut_3(
        self,
        failure_threshold: int = 3,
        half_open_cooldown_sec: float = 30.0,
    ) -> None:
        """Initialize with failure threshold and half-open cooldown duration."""
        self._states: dict[str, McpServerHealthState] = None
        self._failure_counts: dict[str, int] = {}
        self._failure_threshold = failure_threshold
        self._half_open_cooldown_sec = half_open_cooldown_sec
        self._unavailable_since: dict[str, float] = {}
        self._degraded_reasons: dict[str, str] = {}

    def xǁMcpServerHealthRegistryǁ__init____mutmut_4(
        self,
        failure_threshold: int = 3,
        half_open_cooldown_sec: float = 30.0,
    ) -> None:
        """Initialize with failure threshold and half-open cooldown duration."""
        self._states: dict[str, McpServerHealthState] = {}
        self._failure_counts: dict[str, int] = None
        self._failure_threshold = failure_threshold
        self._half_open_cooldown_sec = half_open_cooldown_sec
        self._unavailable_since: dict[str, float] = {}
        self._degraded_reasons: dict[str, str] = {}

    def xǁMcpServerHealthRegistryǁ__init____mutmut_5(
        self,
        failure_threshold: int = 3,
        half_open_cooldown_sec: float = 30.0,
    ) -> None:
        """Initialize with failure threshold and half-open cooldown duration."""
        self._states: dict[str, McpServerHealthState] = {}
        self._failure_counts: dict[str, int] = {}
        self._failure_threshold = None
        self._half_open_cooldown_sec = half_open_cooldown_sec
        self._unavailable_since: dict[str, float] = {}
        self._degraded_reasons: dict[str, str] = {}

    def xǁMcpServerHealthRegistryǁ__init____mutmut_6(
        self,
        failure_threshold: int = 3,
        half_open_cooldown_sec: float = 30.0,
    ) -> None:
        """Initialize with failure threshold and half-open cooldown duration."""
        self._states: dict[str, McpServerHealthState] = {}
        self._failure_counts: dict[str, int] = {}
        self._failure_threshold = failure_threshold
        self._half_open_cooldown_sec = None
        self._unavailable_since: dict[str, float] = {}
        self._degraded_reasons: dict[str, str] = {}

    def xǁMcpServerHealthRegistryǁ__init____mutmut_7(
        self,
        failure_threshold: int = 3,
        half_open_cooldown_sec: float = 30.0,
    ) -> None:
        """Initialize with failure threshold and half-open cooldown duration."""
        self._states: dict[str, McpServerHealthState] = {}
        self._failure_counts: dict[str, int] = {}
        self._failure_threshold = failure_threshold
        self._half_open_cooldown_sec = half_open_cooldown_sec
        self._unavailable_since: dict[str, float] = None
        self._degraded_reasons: dict[str, str] = {}

    def xǁMcpServerHealthRegistryǁ__init____mutmut_8(
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
        self._degraded_reasons: dict[str, str] = None

    @_mutmut_mutated(mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut)
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_orig(self, server_key: str) -> McpServerHealthState:
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_1(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = None
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_2(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(None) == McpServerHealthState.HALF_OPEN
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_3(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) != McpServerHealthState.HALF_OPEN
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_4(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = None
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_5(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) - 1
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_6(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(None, 0) + 1
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_7(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, None) + 1
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_8(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(0) + 1
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_9(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, ) + 1
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_10(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 1) + 1
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_11(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 2
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_12(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = None
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_13(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        if was_half_open and count >= self._failure_threshold:
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_14(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        if was_half_open or count > self._failure_threshold:
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

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_15(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        if was_half_open or count >= self._failure_threshold:
            self._states[server_key] = None
            self._unavailable_since[server_key] = time.monotonic()
            if was_half_open:
                logger.warning(
                    "Health: %r trial probe failed → UNAVAILABLE (cooldown reset)",
                    server_key,
                )
            return McpServerHealthState.UNAVAILABLE
        self._states[server_key] = McpServerHealthState.DEGRADED
        return McpServerHealthState.DEGRADED

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_16(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        if was_half_open or count >= self._failure_threshold:
            self._states[server_key] = McpServerHealthState.UNAVAILABLE
            self._unavailable_since[server_key] = None
            if was_half_open:
                logger.warning(
                    "Health: %r trial probe failed → UNAVAILABLE (cooldown reset)",
                    server_key,
                )
            return McpServerHealthState.UNAVAILABLE
        self._states[server_key] = McpServerHealthState.DEGRADED
        return McpServerHealthState.DEGRADED

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_17(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        if was_half_open or count >= self._failure_threshold:
            self._states[server_key] = McpServerHealthState.UNAVAILABLE
            self._unavailable_since[server_key] = time.monotonic()
            if was_half_open:
                logger.warning(
                    None,
                    server_key,
                )
            return McpServerHealthState.UNAVAILABLE
        self._states[server_key] = McpServerHealthState.DEGRADED
        return McpServerHealthState.DEGRADED

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_18(self, server_key: str) -> McpServerHealthState:
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
                    None,
                )
            return McpServerHealthState.UNAVAILABLE
        self._states[server_key] = McpServerHealthState.DEGRADED
        return McpServerHealthState.DEGRADED

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_19(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        if was_half_open or count >= self._failure_threshold:
            self._states[server_key] = McpServerHealthState.UNAVAILABLE
            self._unavailable_since[server_key] = time.monotonic()
            if was_half_open:
                logger.warning(
                    server_key,
                )
            return McpServerHealthState.UNAVAILABLE
        self._states[server_key] = McpServerHealthState.DEGRADED
        return McpServerHealthState.DEGRADED

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_20(self, server_key: str) -> McpServerHealthState:
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
                    )
            return McpServerHealthState.UNAVAILABLE
        self._states[server_key] = McpServerHealthState.DEGRADED
        return McpServerHealthState.DEGRADED

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_21(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        if was_half_open or count >= self._failure_threshold:
            self._states[server_key] = McpServerHealthState.UNAVAILABLE
            self._unavailable_since[server_key] = time.monotonic()
            if was_half_open:
                logger.warning(
                    "XXHealth: %r trial probe failed → UNAVAILABLE (cooldown reset)XX",
                    server_key,
                )
            return McpServerHealthState.UNAVAILABLE
        self._states[server_key] = McpServerHealthState.DEGRADED
        return McpServerHealthState.DEGRADED

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_22(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        if was_half_open or count >= self._failure_threshold:
            self._states[server_key] = McpServerHealthState.UNAVAILABLE
            self._unavailable_since[server_key] = time.monotonic()
            if was_half_open:
                logger.warning(
                    "health: %r trial probe failed → unavailable (cooldown reset)",
                    server_key,
                )
            return McpServerHealthState.UNAVAILABLE
        self._states[server_key] = McpServerHealthState.DEGRADED
        return McpServerHealthState.DEGRADED

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_23(self, server_key: str) -> McpServerHealthState:
        """Record a failure for the given server and update its health state."""
        was_half_open = self.get_state(server_key) == McpServerHealthState.HALF_OPEN
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        if was_half_open or count >= self._failure_threshold:
            self._states[server_key] = McpServerHealthState.UNAVAILABLE
            self._unavailable_since[server_key] = time.monotonic()
            if was_half_open:
                logger.warning(
                    "HEALTH: %R TRIAL PROBE FAILED → UNAVAILABLE (COOLDOWN RESET)",
                    server_key,
                )
            return McpServerHealthState.UNAVAILABLE
        self._states[server_key] = McpServerHealthState.DEGRADED
        return McpServerHealthState.DEGRADED

    def xǁMcpServerHealthRegistryǁrecord_failure__mutmut_24(self, server_key: str) -> McpServerHealthState:
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
        self._states[server_key] = None
        return McpServerHealthState.DEGRADED

    @_mutmut_mutated(mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut)
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

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_orig(self, server_key: str, reason: str | None = None) -> None:
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

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_1(self, server_key: str, reason: str | None = None) -> None:
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
        current = None
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

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_2(self, server_key: str, reason: str | None = None) -> None:
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
        current = self.get_state(None)
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

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_3(self, server_key: str, reason: str | None = None) -> None:
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
        if current not in (
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

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_4(self, server_key: str, reason: str | None = None) -> None:
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
                None,
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

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_5(self, server_key: str, reason: str | None = None) -> None:
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
                None,
                current.value,
            )
            return
        self._states[server_key] = McpServerHealthState.DEGRADED
        if reason is not None:
            self._degraded_reasons[server_key] = reason
        logger.warning(
            "Health: %r is DEGRADED (reason=%s)", server_key, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_6(self, server_key: str, reason: str | None = None) -> None:
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
                None,
            )
            return
        self._states[server_key] = McpServerHealthState.DEGRADED
        if reason is not None:
            self._degraded_reasons[server_key] = reason
        logger.warning(
            "Health: %r is DEGRADED (reason=%s)", server_key, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_7(self, server_key: str, reason: str | None = None) -> None:
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

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_8(self, server_key: str, reason: str | None = None) -> None:
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
                current.value,
            )
            return
        self._states[server_key] = McpServerHealthState.DEGRADED
        if reason is not None:
            self._degraded_reasons[server_key] = reason
        logger.warning(
            "Health: %r is DEGRADED (reason=%s)", server_key, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_9(self, server_key: str, reason: str | None = None) -> None:
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
                )
            return
        self._states[server_key] = McpServerHealthState.DEGRADED
        if reason is not None:
            self._degraded_reasons[server_key] = reason
        logger.warning(
            "Health: %r is DEGRADED (reason=%s)", server_key, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_10(self, server_key: str, reason: str | None = None) -> None:
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
                "XXHealth: ignored degraded probe for %r, current state=%sXX",
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

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_11(self, server_key: str, reason: str | None = None) -> None:
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
                "health: ignored degraded probe for %r, current state=%s",
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

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_12(self, server_key: str, reason: str | None = None) -> None:
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
                "HEALTH: IGNORED DEGRADED PROBE FOR %R, CURRENT STATE=%S",
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

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_13(self, server_key: str, reason: str | None = None) -> None:
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
        self._states[server_key] = None
        if reason is not None:
            self._degraded_reasons[server_key] = reason
        logger.warning(
            "Health: %r is DEGRADED (reason=%s)", server_key, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_14(self, server_key: str, reason: str | None = None) -> None:
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
        if reason is None:
            self._degraded_reasons[server_key] = reason
        logger.warning(
            "Health: %r is DEGRADED (reason=%s)", server_key, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_15(self, server_key: str, reason: str | None = None) -> None:
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
            self._degraded_reasons[server_key] = None
        logger.warning(
            "Health: %r is DEGRADED (reason=%s)", server_key, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_16(self, server_key: str, reason: str | None = None) -> None:
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
            None, server_key, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_17(self, server_key: str, reason: str | None = None) -> None:
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
            "Health: %r is DEGRADED (reason=%s)", None, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_18(self, server_key: str, reason: str | None = None) -> None:
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
            "Health: %r is DEGRADED (reason=%s)", server_key, None
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_19(self, server_key: str, reason: str | None = None) -> None:
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
            server_key, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_20(self, server_key: str, reason: str | None = None) -> None:
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
            "Health: %r is DEGRADED (reason=%s)", reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_21(self, server_key: str, reason: str | None = None) -> None:
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
            "Health: %r is DEGRADED (reason=%s)", server_key, )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_22(self, server_key: str, reason: str | None = None) -> None:
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
            "XXHealth: %r is DEGRADED (reason=%s)XX", server_key, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_23(self, server_key: str, reason: str | None = None) -> None:
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
            "health: %r is degraded (reason=%s)", server_key, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_24(self, server_key: str, reason: str | None = None) -> None:
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
            "HEALTH: %R IS DEGRADED (REASON=%S)", server_key, reason or "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_25(self, server_key: str, reason: str | None = None) -> None:
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
            "Health: %r is DEGRADED (reason=%s)", server_key, reason and "unknown"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_26(self, server_key: str, reason: str | None = None) -> None:
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
            "Health: %r is DEGRADED (reason=%s)", server_key, reason or "XXunknownXX"
        )

    def xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_27(self, server_key: str, reason: str | None = None) -> None:
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
            "Health: %r is DEGRADED (reason=%s)", server_key, reason or "UNKNOWN"
        )

    @_mutmut_mutated(mutants_xǁMcpServerHealthRegistryǁget_degraded_reason__mutmut)
    def get_degraded_reason(self, server_key: str) -> str | None:
        """Return the last recorded degraded reason for a server, or None."""
        return self._degraded_reasons.get(server_key)

    def xǁMcpServerHealthRegistryǁget_degraded_reason__mutmut_orig(self, server_key: str) -> str | None:
        """Return the last recorded degraded reason for a server, or None."""
        return self._degraded_reasons.get(server_key)

    def xǁMcpServerHealthRegistryǁget_degraded_reason__mutmut_1(self, server_key: str) -> str | None:
        """Return the last recorded degraded reason for a server, or None."""
        return self._degraded_reasons.get(None)

    @_mutmut_mutated(mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut)
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

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_orig(self, server_key: str) -> None:
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

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_1(self, server_key: str) -> None:
        """Record a successful call and reset the server to HEALTHY.

        In addition to setting the state to `HEALTHY`, this clears
        `_failure_counts`, `_unavailable_since`, and `_degraded_reasons` for
        `server_key`. Clearing `_failure_counts` matters because
        `record_failure()` compares the running count against
        `_failure_threshold`; without this reset, a later `record_failure()`
        call could jump straight back to `UNAVAILABLE` using a stale count
        left over from before this success.
        """
        prev = None
        self._states[server_key] = McpServerHealthState.HEALTHY
        self._failure_counts[server_key] = 0
        self._unavailable_since.pop(server_key, None)
        self._degraded_reasons.pop(server_key, None)
        if prev == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_2(self, server_key: str) -> None:
        """Record a successful call and reset the server to HEALTHY.

        In addition to setting the state to `HEALTHY`, this clears
        `_failure_counts`, `_unavailable_since`, and `_degraded_reasons` for
        `server_key`. Clearing `_failure_counts` matters because
        `record_failure()` compares the running count against
        `_failure_threshold`; without this reset, a later `record_failure()`
        call could jump straight back to `UNAVAILABLE` using a stale count
        left over from before this success.
        """
        prev = self.get_state(None)
        self._states[server_key] = McpServerHealthState.HEALTHY
        self._failure_counts[server_key] = 0
        self._unavailable_since.pop(server_key, None)
        self._degraded_reasons.pop(server_key, None)
        if prev == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_3(self, server_key: str) -> None:
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
        self._states[server_key] = None
        self._failure_counts[server_key] = 0
        self._unavailable_since.pop(server_key, None)
        self._degraded_reasons.pop(server_key, None)
        if prev == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_4(self, server_key: str) -> None:
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
        self._failure_counts[server_key] = None
        self._unavailable_since.pop(server_key, None)
        self._degraded_reasons.pop(server_key, None)
        if prev == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_5(self, server_key: str) -> None:
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
        self._failure_counts[server_key] = 1
        self._unavailable_since.pop(server_key, None)
        self._degraded_reasons.pop(server_key, None)
        if prev == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_6(self, server_key: str) -> None:
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
        self._unavailable_since.pop(None, None)
        self._degraded_reasons.pop(server_key, None)
        if prev == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_7(self, server_key: str) -> None:
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
        self._unavailable_since.pop(None)
        self._degraded_reasons.pop(server_key, None)
        if prev == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_8(self, server_key: str) -> None:
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
        self._unavailable_since.pop(server_key, )
        self._degraded_reasons.pop(server_key, None)
        if prev == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_9(self, server_key: str) -> None:
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
        self._degraded_reasons.pop(None, None)
        if prev == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_10(self, server_key: str) -> None:
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
        self._degraded_reasons.pop(None)
        if prev == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_11(self, server_key: str) -> None:
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
        self._degraded_reasons.pop(server_key, )
        if prev == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_12(self, server_key: str) -> None:
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
        if prev != McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r trial probe succeeded → HEALTHY", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_13(self, server_key: str) -> None:
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
            logger.info(None, server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_14(self, server_key: str) -> None:
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
            logger.info("Health: %r trial probe succeeded → HEALTHY", None)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_15(self, server_key: str) -> None:
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
            logger.info(server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_16(self, server_key: str) -> None:
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
            logger.info("Health: %r trial probe succeeded → HEALTHY", )

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_17(self, server_key: str) -> None:
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
            logger.info("XXHealth: %r trial probe succeeded → HEALTHYXX", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_18(self, server_key: str) -> None:
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
            logger.info("health: %r trial probe succeeded → healthy", server_key)

    def xǁMcpServerHealthRegistryǁrecord_success__mutmut_19(self, server_key: str) -> None:
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
            logger.info("HEALTH: %R TRIAL PROBE SUCCEEDED → HEALTHY", server_key)

    @_mutmut_mutated(mutants_xǁMcpServerHealthRegistryǁget_state__mutmut)
    def get_state(self, server_key: str) -> McpServerHealthState:
        """Get the current health state for a server, defaulting to HEALTHY."""
        return self._states.get(server_key, McpServerHealthState.HEALTHY)

    def xǁMcpServerHealthRegistryǁget_state__mutmut_orig(self, server_key: str) -> McpServerHealthState:
        """Get the current health state for a server, defaulting to HEALTHY."""
        return self._states.get(server_key, McpServerHealthState.HEALTHY)

    def xǁMcpServerHealthRegistryǁget_state__mutmut_1(self, server_key: str) -> McpServerHealthState:
        """Get the current health state for a server, defaulting to HEALTHY."""
        return self._states.get(None, McpServerHealthState.HEALTHY)

    def xǁMcpServerHealthRegistryǁget_state__mutmut_2(self, server_key: str) -> McpServerHealthState:
        """Get the current health state for a server, defaulting to HEALTHY."""
        return self._states.get(server_key, None)

    def xǁMcpServerHealthRegistryǁget_state__mutmut_3(self, server_key: str) -> McpServerHealthState:
        """Get the current health state for a server, defaulting to HEALTHY."""
        return self._states.get(McpServerHealthState.HEALTHY)

    def xǁMcpServerHealthRegistryǁget_state__mutmut_4(self, server_key: str) -> McpServerHealthState:
        """Get the current health state for a server, defaulting to HEALTHY."""
        return self._states.get(server_key, )

    @_mutmut_mutated(mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut)
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

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_orig(self, server_key: str) -> bool:
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

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_1(self, server_key: str) -> bool:
        """Return whether dispatch to `server_key` should currently be blocked.

        Not a pure getter: as a side effect, once a server has been in
        `UNAVAILABLE` for at least `_half_open_cooldown_sec`, this call
        transitions its state to `HALF_OPEN` (a single-trial dispatch window)
        and returns `False` for that call, allowing exactly one trial dispatch
        through. Callers must not assume repeated calls are idempotent.
        """
        state = None
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

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_2(self, server_key: str) -> bool:
        """Return whether dispatch to `server_key` should currently be blocked.

        Not a pure getter: as a side effect, once a server has been in
        `UNAVAILABLE` for at least `_half_open_cooldown_sec`, this call
        transitions its state to `HALF_OPEN` (a single-trial dispatch window)
        and returns `False` for that call, allowing exactly one trial dispatch
        through. Callers must not assume repeated calls are idempotent.
        """
        state = self.get_state(None)
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

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_3(self, server_key: str) -> bool:
        """Return whether dispatch to `server_key` should currently be blocked.

        Not a pure getter: as a side effect, once a server has been in
        `UNAVAILABLE` for at least `_half_open_cooldown_sec`, this call
        transitions its state to `HALF_OPEN` (a single-trial dispatch window)
        and returns `False` for that call, allowing exactly one trial dispatch
        through. Callers must not assume repeated calls are idempotent.
        """
        state = self.get_state(server_key)
        if state == McpServerHealthState.UNAVAILABLE:
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

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_4(self, server_key: str) -> bool:
        """Return whether dispatch to `server_key` should currently be blocked.

        Not a pure getter: as a side effect, once a server has been in
        `UNAVAILABLE` for at least `_half_open_cooldown_sec`, this call
        transitions its state to `HALF_OPEN` (a single-trial dispatch window)
        and returns `False` for that call, allowing exactly one trial dispatch
        through. Callers must not assume repeated calls are idempotent.
        """
        state = self.get_state(server_key)
        if state != McpServerHealthState.UNAVAILABLE:
            return True
        since = self._unavailable_since.get(server_key, 0.0)
        if time.monotonic() - since >= self._half_open_cooldown_sec:
            self._states[server_key] = McpServerHealthState.HALF_OPEN
            logger.info(
                "Health: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_5(self, server_key: str) -> bool:
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
        since = None
        if time.monotonic() - since >= self._half_open_cooldown_sec:
            self._states[server_key] = McpServerHealthState.HALF_OPEN
            logger.info(
                "Health: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_6(self, server_key: str) -> bool:
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
        since = self._unavailable_since.get(None, 0.0)
        if time.monotonic() - since >= self._half_open_cooldown_sec:
            self._states[server_key] = McpServerHealthState.HALF_OPEN
            logger.info(
                "Health: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_7(self, server_key: str) -> bool:
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
        since = self._unavailable_since.get(server_key, None)
        if time.monotonic() - since >= self._half_open_cooldown_sec:
            self._states[server_key] = McpServerHealthState.HALF_OPEN
            logger.info(
                "Health: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_8(self, server_key: str) -> bool:
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
        since = self._unavailable_since.get(0.0)
        if time.monotonic() - since >= self._half_open_cooldown_sec:
            self._states[server_key] = McpServerHealthState.HALF_OPEN
            logger.info(
                "Health: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_9(self, server_key: str) -> bool:
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
        since = self._unavailable_since.get(server_key, )
        if time.monotonic() - since >= self._half_open_cooldown_sec:
            self._states[server_key] = McpServerHealthState.HALF_OPEN
            logger.info(
                "Health: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_10(self, server_key: str) -> bool:
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
        since = self._unavailable_since.get(server_key, 1.0)
        if time.monotonic() - since >= self._half_open_cooldown_sec:
            self._states[server_key] = McpServerHealthState.HALF_OPEN
            logger.info(
                "Health: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_11(self, server_key: str) -> bool:
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
        if time.monotonic() + since >= self._half_open_cooldown_sec:
            self._states[server_key] = McpServerHealthState.HALF_OPEN
            logger.info(
                "Health: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_12(self, server_key: str) -> bool:
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
        if time.monotonic() - since > self._half_open_cooldown_sec:
            self._states[server_key] = McpServerHealthState.HALF_OPEN
            logger.info(
                "Health: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_13(self, server_key: str) -> bool:
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
            self._states[server_key] = None
            logger.info(
                "Health: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_14(self, server_key: str) -> bool:
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
                None,
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_15(self, server_key: str) -> bool:
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
                None,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_16(self, server_key: str) -> bool:
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
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_17(self, server_key: str) -> bool:
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
                )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_18(self, server_key: str) -> bool:
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
                "XXHealth: %r transitioning UNAVAILABLE → HALF_OPEN (trial probe)XX",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_19(self, server_key: str) -> bool:
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
                "health: %r transitioning unavailable → half_open (trial probe)",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_20(self, server_key: str) -> bool:
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
                "HEALTH: %R TRANSITIONING UNAVAILABLE → HALF_OPEN (TRIAL PROBE)",
                server_key,
            )
            return False
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_21(self, server_key: str) -> bool:
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
            return True
        return True

    def xǁMcpServerHealthRegistryǁis_unavailable__mutmut_22(self, server_key: str) -> bool:
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
        return False

mutants_xǁMcpServerHealthRegistryǁ__init____mutmut['_mutmut_orig'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁ__init____mutmut['xǁMcpServerHealthRegistryǁ__init____mutmut_1'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁ__init____mutmut['xǁMcpServerHealthRegistryǁ__init____mutmut_2'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁ__init____mutmut['xǁMcpServerHealthRegistryǁ__init____mutmut_3'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁ__init____mutmut['xǁMcpServerHealthRegistryǁ__init____mutmut_4'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁ__init____mutmut['xǁMcpServerHealthRegistryǁ__init____mutmut_5'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁ__init____mutmut['xǁMcpServerHealthRegistryǁ__init____mutmut_6'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁ__init____mutmut['xǁMcpServerHealthRegistryǁ__init____mutmut_7'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁ__init____mutmut['xǁMcpServerHealthRegistryǁ__init____mutmut_8'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁ__init____mutmut_8 # type: ignore # mutmut generated

mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['_mutmut_orig'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_orig # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_1'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_1 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_2'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_2 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_3'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_3 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_4'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_4 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_5'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_5 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_6'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_6 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_7'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_7 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_8'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_8 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_9'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_9 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_10'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_10 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_11'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_11 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_12'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_12 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_13'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_13 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_14'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_14 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_15'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_15 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_16'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_16 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_17'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_17 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_18'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_18 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_19'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_19 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_20'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_20 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_21'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_21 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_22'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_22 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_23'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_23 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_failure__mutmut['xǁMcpServerHealthRegistryǁrecord_failure__mutmut_24'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_failure__mutmut_24 # type: ignore # mutmut generated

mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['_mutmut_orig'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_orig # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_1'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_1 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_2'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_2 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_3'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_3 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_4'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_4 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_5'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_5 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_6'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_6 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_7'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_7 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_8'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_8 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_9'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_9 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_10'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_10 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_11'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_11 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_12'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_12 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_13'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_13 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_14'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_14 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_15'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_15 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_16'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_16 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_17'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_17 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_18'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_18 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_19'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_19 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_20'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_20 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_21'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_21 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_22'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_22 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_23'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_23 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_24'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_24 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_25'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_25 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_26'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_26 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_degraded__mutmut['xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_27'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_degraded__mutmut_27 # type: ignore # mutmut generated

mutants_xǁMcpServerHealthRegistryǁget_degraded_reason__mutmut['_mutmut_orig'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁget_degraded_reason__mutmut_orig # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁget_degraded_reason__mutmut['xǁMcpServerHealthRegistryǁget_degraded_reason__mutmut_1'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁget_degraded_reason__mutmut_1 # type: ignore # mutmut generated

mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['_mutmut_orig'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_orig # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_1'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_1 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_2'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_2 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_3'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_3 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_4'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_4 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_5'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_5 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_6'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_6 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_7'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_7 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_8'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_8 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_9'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_9 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_10'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_10 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_11'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_11 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_12'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_12 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_13'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_13 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_14'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_14 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_15'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_15 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_16'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_16 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_17'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_17 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_18'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_18 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁrecord_success__mutmut['xǁMcpServerHealthRegistryǁrecord_success__mutmut_19'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁrecord_success__mutmut_19 # type: ignore # mutmut generated

mutants_xǁMcpServerHealthRegistryǁget_state__mutmut['_mutmut_orig'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁget_state__mutmut_orig # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁget_state__mutmut['xǁMcpServerHealthRegistryǁget_state__mutmut_1'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁget_state__mutmut_1 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁget_state__mutmut['xǁMcpServerHealthRegistryǁget_state__mutmut_2'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁget_state__mutmut_2 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁget_state__mutmut['xǁMcpServerHealthRegistryǁget_state__mutmut_3'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁget_state__mutmut_3 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁget_state__mutmut['xǁMcpServerHealthRegistryǁget_state__mutmut_4'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁget_state__mutmut_4 # type: ignore # mutmut generated

mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['_mutmut_orig'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_orig # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_1'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_1 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_2'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_2 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_3'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_3 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_4'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_4 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_5'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_5 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_6'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_6 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_7'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_7 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_8'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_8 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_9'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_9 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_10'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_10 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_11'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_11 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_12'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_12 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_13'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_13 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_14'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_14 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_15'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_15 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_16'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_16 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_17'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_17 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_18'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_18 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_19'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_19 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_20'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_20 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_21'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_21 # type: ignore # mutmut generated
mutants_xǁMcpServerHealthRegistryǁis_unavailable__mutmut['xǁMcpServerHealthRegistryǁis_unavailable__mutmut_22'] = McpServerHealthRegistry.xǁMcpServerHealthRegistryǁis_unavailable__mutmut_22 # type: ignore # mutmut generated
