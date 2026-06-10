#!/usr/bin/env python3
"""shared/mcp_config.py
Transport configuration for MCP servers.
Placed in shared/ so tool_executor.py can reference it without depending on agent/.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass
class McpServerConfig:
    """Transport configuration for one MCP server."""

    transport: str  # "http" | "stdio"
    url: str  # base URL (transport="http")
    cmd: list[str]  # command argv (transport="stdio")
    openrc_service: str  # e.g. "file-mcp"  (transport="http", watchdog restart)
    startup_mode: str = "persistent"  # "persistent" | "ondemand" | "subprocess"
    healthcheck_mode: str = ""  # "http" | "process" | "ping_tool" | ""
    idle_timeout_sec: int = 0  # ondemand auto-stop delay in seconds
    startup_timeout_sec: int = 30  # subprocess startup health-poll timeout in seconds
    working_dir: str = ""  # stdio subprocess working directory; "" = inherit
    env: dict[str, str] = field(default_factory=dict)
    tool_names: list[str] = field(default_factory=list)
    auth_token: str = ""  # Bearer token sent by ToolExecutor
    role: str = ""  # human-readable role label

    def __post_init__(self) -> None:
        self._validate_transport()
        self._validate_startup_mode()
        if not self.healthcheck_mode:
            self.healthcheck_mode = "http" if self.transport == "http" else "process"
        if self.healthcheck_mode not in ("http", "process", "ping_tool"):
            raise ValueError(
                f"McpServerConfig.healthcheck_mode must be 'http', 'process', or "
                f"'ping_tool', got {self.healthcheck_mode!r}"
            )

    def _validate_transport(self) -> None:
        if self.transport not in ("http", "stdio"):
            raise ValueError(
                f"McpServerConfig.transport must be 'http' or 'stdio', got {self.transport!r}"
            )
        if self.transport == "http" and not self.url:
            raise ValueError("McpServerConfig: url must not be empty when transport='http'")
        if self.transport == "stdio" and not self.cmd:
            raise ValueError("McpServerConfig: cmd must not be empty when transport='stdio'")

    def _validate_startup_mode(self) -> None:
        if self.startup_mode not in ("persistent", "ondemand", "subprocess"):
            raise ValueError(
                f"McpServerConfig.startup_mode must be 'persistent', 'ondemand', or "
                f"'subprocess', got {self.startup_mode!r}"
            )
        if self.startup_mode == "subprocess" and self.transport == "stdio":
            raise ValueError(
                "startup_mode='subprocess' is only valid for transport='http'; "
                "stdio servers use 'persistent' or 'ondemand'"
            )


class McpServerHealthState(Enum):
    """Represents the health status of an MCP server."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"  # failing but not yet unavailable
    UNAVAILABLE = "unavailable"


class McpServerHealthRegistry:
    """Tracks per-server health states for ToolExecutor dispatch gating."""

    def __init__(self, failure_threshold: int = 3) -> None:
        self._states: dict[str, McpServerHealthState] = {}
        self._failure_counts: dict[str, int] = {}
        self._failure_threshold = failure_threshold

    def record_failure(self, server_key: str) -> McpServerHealthState:
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        state = McpServerHealthState.UNAVAILABLE if count >= self._failure_threshold else McpServerHealthState.DEGRADED
        self._states[server_key] = state
        return state

    def record_success(self, server_key: str) -> None:
        self._states[server_key] = McpServerHealthState.HEALTHY
        self._failure_counts[server_key] = 0

    def get_state(self, server_key: str) -> McpServerHealthState:
        return self._states.get(server_key, McpServerHealthState.HEALTHY)

    def is_unavailable(self, server_key: str) -> bool:
        return self.get_state(server_key) == McpServerHealthState.UNAVAILABLE


def _build_mcp_servers(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from agent.toml; uses mcp_servers section when present, falls back to legacy URL constants."""
    raw: dict[str, Any] = cfg.get("mcp_servers", {})
    if raw:
        return {key: _build_single_server(key, v) for key, v in raw.items()}

    warnings.warn(
        "mcp_servers config section missing; falling back to legacy URL constants. "
        "Add [mcp_servers] to config/mcp_servers.toml.",
        DeprecationWarning,
        stacklevel=2,
    )
    return {
        "web_search": _build_single_server("web_search", cfg),
        "github": McpServerConfig(
            transport="http",
            url=cfg.get("github_server_url", "http://127.0.0.1:8006"),
            cmd=[],
            openrc_service="github-mcp",
        ),
    }


def _build_single_server(key: str, v: Any) -> McpServerConfig:
    """Construct McpServerConfig from a raw dict, applying defaults."""
    return McpServerConfig(
        transport=v.get("transport", "http"),
        url=v.get("url", ""),
        cmd=list(v.get("cmd", [])),
        openrc_service=v.get("openrc_service", ""),
        startup_mode=v.get("startup_mode", "persistent"),
        healthcheck_mode=v.get("healthcheck_mode", ""),
        idle_timeout_sec=int(v.get("idle_timeout_sec", 0)),
        startup_timeout_sec=int(v.get("startup_timeout_sec", 30)),
        working_dir=v.get("working_dir", ""),
        env=dict(v.get("env", {})),
        tool_names=list(v.get("tool_names", [])),
        auth_token=v.get("auth_token", ""),
        role=v.get("role", ""),
    )
