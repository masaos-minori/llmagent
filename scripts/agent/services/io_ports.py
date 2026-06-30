"""agent/services/io_ports.py
I/O port Protocols for the agent/services subsystem.

No agent/* imports to prevent circular dependencies.
"""

from __future__ import annotations

from typing import Protocol


class ExportOutputPort(Protocol):
    """Output abstraction for conversation export operations."""

    def write(self, content: str) -> None: ...

    def write_file(self, content: str, path: str, n_messages: int) -> None: ...
