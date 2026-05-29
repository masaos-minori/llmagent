#!/usr/bin/env python3
"""
shared/mcp_config.py
Transport configuration for MCP servers.
Placed in shared/ so tool_executor.py can reference it without depending on agent/.
"""

from dataclasses import dataclass


@dataclass
class McpServerConfig:
    """Transport configuration for one MCP server.

    transport: "http" uses url + httpx; "stdio" spawns cmd as a subprocess.
    openrc_service: OpenRC service name used by the watchdog to restart HTTP servers.
    """

    transport: str  # "http" | "stdio"
    url: str  # base URL (transport="http")
    cmd: list[str]  # command argv (transport="stdio")
    openrc_service: str  # e.g. "file-mcp"  (transport="http", watchdog restart)

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


def _build_mcp_servers(cfg: dict) -> dict[str, McpServerConfig]:
    """Build per-server transport config from agent.toml.

    If 'mcp_servers' is present, use it directly.
    Otherwise fall back to legacy url keys (web_search_url, github_server_url, etc.).
    """
    raw: dict = cfg.get("mcp_servers", {})
    if raw:
        return {
            key: McpServerConfig(
                transport=v.get("transport", "http"),
                url=v.get("url", ""),
                cmd=list(v.get("cmd", [])),
                openrc_service=v.get("openrc_service", ""),
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
