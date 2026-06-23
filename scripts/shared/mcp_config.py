#!/usr/bin/env python3
"""shared/mcp_config.py
Transport configuration for MCP servers.
Placed in shared/ so tool_executor.py can reference it without depending on agent/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, StrEnum
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class TransportType(StrEnum):
    """MCP server transport protocol."""

    HTTP = "http"
    STDIO = "stdio"


class StartupMode(StrEnum):
    """MCP server startup lifecycle mode."""

    PERSISTENT = "persistent"
    ONDEMAND = "ondemand"
    SUBPROCESS = "subprocess"


class HealthcheckMode(StrEnum):
    """MCP server health-check strategy."""

    HTTP = "http"
    PROCESS = "process"
    PING_TOOL = "ping_tool"


class SecurityProfile(StrEnum):
    """Deployment security profile for MCP auth enforcement."""

    LOCAL = "local"
    PRODUCTION = "production"


@dataclass
class McpServerConfig:
    """Transport configuration for one MCP server."""

    transport: TransportType
    url: str  # base URL (transport=HTTP)
    cmd: list[str]  # command argv (transport=STDIO)
    startup_mode: StartupMode = StartupMode.PERSISTENT
    healthcheck_mode: HealthcheckMode = (
        HealthcheckMode.HTTP
    )  # resolved in __post_init__
    idle_timeout_sec: int = 0  # ondemand auto-stop delay in seconds
    startup_timeout_sec: int = 30  # subprocess startup health-poll timeout in seconds
    working_dir: str = ""  # stdio subprocess working directory; "" = inherit
    env: dict[str, str] = field(default_factory=dict)
    tool_names: list[str] = field(default_factory=list)
    auth_token: str = ""  # Bearer token sent by ToolExecutor
    role: str = ""  # human-readable role label

    def __post_init__(self) -> None:
        # Cast str inputs from config files to enum types; invalid values raise ValueError.
        if not isinstance(self.transport, TransportType):
            self.transport = TransportType(self.transport)
        if not isinstance(self.startup_mode, StartupMode):
            self.startup_mode = StartupMode(self.startup_mode)
        if not isinstance(self.healthcheck_mode, HealthcheckMode):
            if not self.healthcheck_mode:
                self.healthcheck_mode = (
                    HealthcheckMode.HTTP
                    if self.transport == TransportType.HTTP
                    else HealthcheckMode.PROCESS
                )
            else:
                self.healthcheck_mode = HealthcheckMode(self.healthcheck_mode)
        self._validate_cross_fields()

    def _validate_cross_fields(self) -> None:
        if self.transport == TransportType.HTTP and not self.url:
            raise ValueError(
                "McpServerConfig: url must not be empty when transport='http'"
            )
        if self.transport == TransportType.STDIO and not self.cmd:
            raise ValueError(
                "McpServerConfig: cmd must not be empty when transport='stdio'"
            )
        if (
            self.startup_mode == StartupMode.SUBPROCESS
            and self.transport == TransportType.STDIO
        ):
            raise ValueError(
                "startup_mode='subprocess' is only valid for transport='http'; "
                "stdio servers use 'persistent' or 'ondemand'"
            )


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


def _build_mcp_servers(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from mcp_servers.toml [mcp_servers] section."""
    raw = cfg.get("mcp_servers")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "mcp_servers config section is missing or empty. "
            "Add [mcp_servers] to config/mcp_servers.toml."
        )
    return {key: _build_single_server(key, v) for key, v in raw.items()}


def _build_single_server(key: str, v: dict[str, Any]) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults."""
    if not isinstance(v, dict):
        raise ValueError(f"mcp_servers[{key!r}] must be a dict, got {type(v).__name__}")
    transport = v.get("transport", "http")
    if not isinstance(transport, str):
        raise ValueError(
            f"mcp_servers[{key!r}].transport must be str, got {type(transport).__name__}"
        )
    return McpServerConfig(
        transport=TransportType(transport),
        url=v.get("url", ""),
        cmd=list(v.get("cmd", [])),
        startup_mode=StartupMode(v.get("startup_mode", "persistent")),
        healthcheck_mode=HealthcheckMode(v.get("healthcheck_mode", ""))
        if v.get("healthcheck_mode")
        else HealthcheckMode.HTTP,
        idle_timeout_sec=int(v.get("idle_timeout_sec", 0)),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        working_dir=v.get("working_dir", ""),
        env=dict(v.get("env", {})),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        role=v.get("role", ""),
    )
