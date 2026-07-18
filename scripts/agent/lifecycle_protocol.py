"""agent/lifecycle_protocol.py

LifecycleManager protocol types for structural subtyping.

Two protocols:
  LifecycleManagerProtocol — shared methods implemented by HTTP lifecycle manager
  HttpLifecycleProtocol    — HTTP-only: start_http_subprocess
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from shared.mcp_config import McpServerConfig

from agent.lifecycle import LifecycleState


@runtime_checkable
class LifecycleManagerProtocol(Protocol):
    """Protocol for MCP server lifecycle managers.

    _ServerLifecycleRouter in factory.py is the production implementation.
    HttpServerLifecycleManager is the low-level subprocess manager it delegates to.
    """

    async def ensure_ready(self, server_key: str) -> None:
        """Ensure the named MCP server is running; start it if needed."""
        ...

    async def shutdown_all(self) -> None:
        """Shut down all managed MCP servers."""
        ...

    async def restart(self, server_key: str) -> None:
        """Restart a single MCP server."""
        ...

    async def shutdown_idle(self) -> None:
        """Shutdown idle MCP servers (stdio mode)."""
        ...

    def get_transport_state(self, server_key: str) -> LifecycleState:
        """Return the current lifecycle state for a server."""
        ...

    async def start_http_subprocess(
        self, server_key: str, cfg: McpServerConfig
    ) -> None:
        """Start a single HTTP subprocess MCP server."""
        ...

    def get_process_snapshot(self, server_key: str) -> dict | None:
        """Return process snapshot dict for a managed subprocess server, or None."""
        ...
