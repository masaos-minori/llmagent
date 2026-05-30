#!/usr/bin/env python3
"""
shared/mcp_config.py
Transport configuration for MCP servers.
Placed in shared/ so tool_executor.py can reference it without depending on agent/.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class McpServerConfig:
    """Transport configuration for one MCP server; transport/startup_mode/healthcheck_mode govern lifecycle; tool_names enables config-driven routing."""

    transport: str  # "http" | "stdio"
    url: str  # base URL (transport="http")
    cmd: list[str]  # command argv (transport="stdio")
    openrc_service: str  # e.g. "file-mcp"  (transport="http", watchdog restart)
    startup_mode: str = "persistent"  # "persistent" | "ondemand"
    healthcheck_mode: str = (
        ""  # "http" | "process" | "ping_tool"; auto-inferred when ""
    )
    idle_timeout_sec: int = 0  # ondemand auto-stop delay in seconds; 0 = disabled
    working_dir: str = ""  # stdio subprocess working directory; "" = inherit
    env: dict[str, str] = field(default_factory=dict)  # env vars for stdio subprocess
    tool_names: list[str] = field(
        default_factory=list
    )  # explicit tool routing; [] = static fallback

    def __post_init__(self) -> None:
        if self.transport not in ("http", "stdio"):
            raise ValueError(
                f"McpServerConfig.transport must be 'http' or 'stdio', got {self.transport!r}"
            )
        if self.transport == "http" and not self.url:
            raise ValueError(
                "McpServerConfig: url must not be empty when transport='http'"
            )
        if self.transport == "stdio" and not self.cmd:
            raise ValueError(
                "McpServerConfig: cmd must not be empty when transport='stdio'"
            )
        if self.startup_mode not in ("persistent", "ondemand"):
            raise ValueError(
                f"McpServerConfig.startup_mode must be 'persistent' or 'ondemand',"
                f" got {self.startup_mode!r}"
            )
        # Auto-infer healthcheck_mode from transport when not explicitly set
        if not self.healthcheck_mode:
            self.healthcheck_mode = "http" if self.transport == "http" else "process"
        if self.healthcheck_mode not in ("http", "process", "ping_tool"):
            raise ValueError(
                f"McpServerConfig.healthcheck_mode must be 'http', 'process', or"
                f" 'ping_tool', got {self.healthcheck_mode!r}"
            )


def _build_mcp_servers(cfg: dict[str, Any]) -> dict[str, McpServerConfig]:
    """Build per-server transport config from agent.toml; uses mcp_servers section when present, falls back to legacy URL constants."""
    raw: dict[str, Any] = cfg.get("mcp_servers", {})
    if raw:
        return {
            key: McpServerConfig(
                transport=v.get("transport", "http"),
                url=v.get("url", ""),
                cmd=list(v.get("cmd", [])),
                openrc_service=v.get("openrc_service", ""),
                startup_mode=v.get("startup_mode", "persistent"),
                healthcheck_mode=v.get("healthcheck_mode", ""),
                idle_timeout_sec=int(v.get("idle_timeout_sec", 0)),
                working_dir=v.get("working_dir", ""),
                env=dict(v.get("env", {})),
                tool_names=list(v.get("tool_names", [])),
            )
            for key, v in raw.items()
        }
    # Backwards compat: derive from legacy URL constants
    return {
        "web_search": McpServerConfig(
            "http", cfg.get("web_search_url", ""), [], "web-search-mcp"
        ),
        "github": McpServerConfig(
            "http",
            cfg.get("github_server_url", "http://127.0.0.1:8006"),
            [],
            "github-mcp",
        ),
    }
