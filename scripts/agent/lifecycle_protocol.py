"""agent/lifecycle_protocol.py

LifecycleManager protocol types for structural subtyping.

Two protocols:
  LifecycleManagerProtocol — shared methods implemented by HTTP lifecycle manager
  HttpLifecycleProtocol    — HTTP-only: start_http_subprocess
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from agent.lifecycle import LifecycleState
from shared.mcp_config import McpServerConfig


@runtime_checkable
class LifecycleManagerProtocol(Protocol):
    """Protocol for MCP server lifecycle managers.

    _ServerLifecycleRouter in factory.py is the production implementation.
    HttpServerLifecycleManager is the low-level subprocess manager it delegates to.
    """

    async def ensure_ready(self, server_key: str) -> None: ...
    async def shutdown_all(self) -> None: ...
    async def restart(self, server_key: str) -> None: ...
    async def shutdown_idle(self) -> None: ...
    def get_transport_state(self, server_key: str) -> LifecycleState: ...
    async def start_http_subprocess(
        self, server_key: str, cfg: McpServerConfig
    ) -> None: ...
    def get_process_snapshot(self, server_key: str) -> dict | None: ...
