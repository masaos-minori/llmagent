"""scripts/agent/lifecycle_protocol.py

LifecycleManager protocol types for structural subtyping.

Two protocols:
  LifecycleManagerProtocol — shared methods implemented by HTTP lifecycle managers
    Implementations: _ServerLifecycleRouter (coordinator), _SubprocessLifecycleManager (subprocess operations)
  HttpLifecycleProtocol    — HTTP-only: start_http_subprocess
"""

from __future__ import annotations

import asyncio
import subprocess
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from shared.mcp_config import McpServerConfig

from agent.http_lifecycle_errors import TerminationOutcome
from agent.lifecycle import LifecycleState

if TYPE_CHECKING:
    from agent.shutdown_budget import ShutdownBudget


@runtime_checkable
class LifecycleManagerProtocol(Protocol):
    """Protocol for MCP server lifecycle managers.

    _ServerLifecycleRouter in lifecycle_router.py is the coordinator implementation.
    _SubprocessLifecycleManager in lifecycle_router.py is the subprocess operations implementation.
    HttpServerLifecycleManager is the low-level subprocess manager they delegate to.
    """

    async def ensure_ready(self, server_key: str) -> None:
        """Ensure the named MCP server is running; start it if needed.

        Raises:
            EnsureSuppressedError: When the call is refused because shutdown has
                begun; the call never returns silently during shutdown (REQ-008).
        """
        ...

    async def shutdown_all(
        self, *, budget: ShutdownBudget | None = None
    ) -> list[tuple[str, TerminationOutcome]]:
        """Shut down all managed MCP servers.

        Args:
            budget: The time left in the shutdown sequence. An implementation must not
                wait longer than ``budget.remaining()`` for an exit, and must stop
                waiting once the budget's interrupt is requested; the termination
                signals themselves are not skipped for a short budget. None means no
                deadline was supplied and the implementation uses its own default.

        Returns:
            One ``(server_key, outcome)`` pair per server whose exit was not
            confirmed; an empty list means every started server was confirmed gone.

        A server whose exit was not confirmed keeps its process record in the
        manager until a later shutdown confirms the exit (REQ-002, REQ-003); its
        lifecycle state becomes ``EXIT_UNCONFIRMED`` or ``SIGNAL_NOT_DELIVERED``,
        never ``STOPPED`` (REQ-006).
        """
        ...

    async def restart(self, server_key: str) -> None:
        """Restart a single MCP server.

        Raises:
            RestartSuppressedError: When the call is refused because shutdown has
                begun; the call never returns silently during shutdown (REQ-008).
            RestartBlockedError: When the old process exit could not be confirmed;
                the record is retained and no replacement process is started.
        """
        ...

    async def shutdown_idle(self) -> None:
        """Shutdown idle MCP servers (stdio mode)."""
        ...

    def get_transport_state(self, server_key: str) -> LifecycleState:
        """Return the current lifecycle state for a server.

        After a shutdown the state is per-server and outcome-driven: ``STOPPED``
        only for servers whose exit was confirmed, ``EXIT_UNCONFIRMED`` or
        ``SIGNAL_NOT_DELIVERED`` for retained ones (REQ-006).
        """
        ...

    async def start_http_subprocess(
        self,
        server_key: str,
        cfg: McpServerConfig,
        shutdown_event: asyncio.Event | None = None,
    ) -> subprocess.Popen[bytes] | None:
        """Start a single HTTP subprocess MCP server and return its Popen object.

        None means only that no process was recorded. A manager that refuses a start
        because shutdown has begun raises a typed error instead of returning None.
        """
        ...

    def get_process_snapshot(self, server_key: str) -> dict | None:
        """Return process snapshot dict for a managed subprocess server, or None."""
        ...

    def cleanup_server_resources(self, server_key: str) -> str:
        """Clean up resources for a removed MCP server. Returns stderr or empty string."""
        ...
