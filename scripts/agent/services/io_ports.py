"""agent/services/io_ports.py
I/O port Protocols for the agent/services subsystem.

No agent/* imports to prevent circular dependencies.
"""

from __future__ import annotations

from typing import Protocol


class InstallIOPort(Protocol):
    """I/O abstraction for the MCP server install wizard."""

    async def ask_port(self, default: int) -> int: ...

    async def ask_role(self) -> str: ...

    async def ask_confd(self) -> bool: ...


class ExportOutputPort(Protocol):
    """Output abstraction for conversation export operations."""

    def write(self, content: str) -> None: ...

    def write_file(self, content: str, path: str, n_messages: int) -> None: ...


class StatusRenderPort(Protocol):
    """Rendering abstraction for post-install status display."""

    def render_next_steps(self, result: object) -> str: ...
