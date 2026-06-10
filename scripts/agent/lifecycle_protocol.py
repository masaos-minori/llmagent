"""agent/lifecycle_protocol.py
LifecycleManager protocol types for structural subtyping.

Three narrow protocols:
  LifecycleManagerProtocol — shared methods implemented by both HTTP and stdio managers
  HttpLifecycleProtocol    — HTTP-only: start_http_subprocess
  StdioLifecycleProtocol   — stdio-only: restart_stdio
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from shared.mcp_config import McpServerConfig

from agent.lifecycle import LifecycleState


@runtime_checkable
class LifecycleManagerProtocol(Protocol):
    """Protocol for MCP server lifecycle managers.

    Both HttpServerLifecycleManager and StdioServerLifecycleManager
    satisfy this protocol structurally.
    """

    async def ensure_ready(self, server_key: str) -> None: ...
    async def shutdown_all(self) -> None: ...
    async def restart(self, server_key: str) -> None: ...
    async def shutdown_idle(self) -> None: ...
    def get_transport_state(self, server_key: str) -> LifecycleState: ...


@runtime_checkable
class HttpLifecycleProtocol(Protocol):
    """Protocol for HTTP subprocess lifecycle management."""

    async def start_http_subprocess(
        self, server_key: str, cfg: McpServerConfig
    ) -> None: ...


@runtime_checkable
class StdioLifecycleProtocol(Protocol):
    """Protocol for stdio server lifecycle management."""

    async def restart_stdio(self, server_key: str) -> None: ...
