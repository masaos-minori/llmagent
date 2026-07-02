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

    HttpServerLifecycleManager satisfies this protocol structurally.
    """

    async def ensure_ready(self, server_key: str) -> None: ...
    async def shutdown_all(self) -> None: ...
    async def restart(self, server_key: str) -> None: ...
    async def shutdown_idle(self) -> None: ...
    def get_transport_state(self, server_key: str) -> LifecycleState: ...
    async def start_http_subprocess(
        self, server_key: str, cfg: McpServerConfig
    ) -> None: ...
