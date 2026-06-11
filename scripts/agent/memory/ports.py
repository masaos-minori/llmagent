"""agent/memory/ports.py
Output port Protocol for the persistent memory layer.
"""

from __future__ import annotations

from typing import Protocol


class MemoryOutputPort(Protocol):
    def emit_persist(self, memory_id: str, memory_type: str) -> None: ...
    def emit_skip_dedup(self, memory_id: str) -> None: ...
