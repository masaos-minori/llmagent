#!/usr/bin/env python3
"""scripts/shared/tool_lifecycle.py — MCP server lifecycle protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


class ServerCooldownError(RuntimeError):
    """Raised when a tool call is attempted while an MCP server is in cooldown."""


@runtime_checkable
class LifecycleProtocol(Protocol):
    """Protocol for MCP server lifecycle managers injected into ToolExecutor."""

    async def ensure_ready(self, server_key: str) -> None:
        """Ensure the MCP server identified by server_key is ready to accept calls."""
        ...
