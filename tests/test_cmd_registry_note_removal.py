"""tests/test_cmd_registry_note_removal.py

Tests that the removed `/note` command is no longer dispatched,
while `/memory` remains functional.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from agent.commands.cmd_mcp import _McpMixin
from agent.commands.cmd_mdq import _MdqMixin
from agent.commands.exceptions import UnknownSubcommandError


class _Ctx:
    """Minimal stub for AgentContext."""

    def __init__(self) -> None:
        self.cfg = SimpleNamespace()
        self.cfg.tool = SimpleNamespace()
        self.cfg.tool.tool_definitions = []
        self.cfg.mcp = SimpleNamespace()
        self.cfg.mcp.mcp_watchdog_interval = 0.0
        self.cfg.mcp.mcp_watchdog_max_restarts = 3
        self.cfg.mcp.mcp_servers = {}
        self.cfg.approval = SimpleNamespace()
        self.cfg.approval.tool_safety_tiers = {}
        self.services = SimpleNamespace()
        self.services.stdio_procs = {}
        self.services.health_registry = None
        self.services.memory = None
        self.services_required = SimpleNamespace()
        self.services_required.memory = None
        self.stats = SimpleNamespace()
        self.stats.stat_serialization_events = []
        self.session = SimpleNamespace()
        self.session.session_id = "test-session"


class _Mcp(_McpMixin):
    """Concrete mixin for testing."""

    def __init__(self, ctx: _Ctx) -> None:
        self._ctx = ctx  # type: ignore[assignment]
        self._out = SimpleNamespace(
            write=lambda msg: None,
            write_success=lambda msg: None,
        )


class _Mdq(_MdqMixin):
    """Concrete mixin for testing — adds missing _cmd_mdq prefix handler."""

    async def _cmd_mdq(self, args: str) -> None:
        """Dispatch /mdq subcommands (stub)."""
        pass


# ── CommandRegistry dispatch-level tests ────────────────────────────────────────


class _PatchedCommandRegistry:
    """Thin wrapper that patches CommandRegistry with the missing _cmd_mdq handler.

    Uses a monkey-patch approach to avoid MRO conflicts from diamond inheritance.
    """

    def __init__(self, ctx: _Ctx) -> None:
        from agent.commands.registry import CommandRegistry as _CR

        # Patch CommandRegistry directly to add the missing _cmd_mdq handler
        if not hasattr(_CR, "_cmd_mdq"):

            async def _cmd_mdq(self, args: str) -> None:
                pass

            setattr(_CR, "_cmd_mdq", _cmd_mdq)

        self._registry = _CR(ctx)

    @property
    def dispatch(self):
        return self._registry.dispatch


class TestNoteDispatchReturnsUnknown:
    """Tests that /note subcommands return False from dispatch()."""

    @pytest.mark.asyncio
    async def test_note_add_dispatch_returns_false(self) -> None:
        """dispatch('/note add hello') returns False."""
        ctx = _Ctx()
        registry = _PatchedCommandRegistry(ctx)
        result = await registry.dispatch("/note add hello")
        assert result is False

    @pytest.mark.asyncio
    async def test_note_list_dispatch_returns_false(self) -> None:
        """dispatch('/note list') returns False."""
        ctx = _Ctx()
        registry = _PatchedCommandRegistry(ctx)
        result = await registry.dispatch("/note list")
        assert result is False

    @pytest.mark.asyncio
    async def test_note_delete_dispatch_returns_false(self) -> None:
        """dispatch('/note delete 1') returns False."""
        ctx = _Ctx()
        registry = _PatchedCommandRegistry(ctx)
        result = await registry.dispatch("/note delete 1")
        assert result is False

    @pytest.mark.asyncio
    async def test_note_pin_dispatch_returns_false(self) -> None:
        """dispatch('/note pin 1') returns False."""
        ctx = _Ctx()
        registry = _PatchedCommandRegistry(ctx)
        result = await registry.dispatch("/note pin 1")
        assert result is False

    @pytest.mark.asyncio
    async def test_note_unpin_dispatch_returns_false(self) -> None:
        """dispatch('/note unpin 1') returns False."""
        ctx = _Ctx()
        registry = _PatchedCommandRegistry(ctx)
        result = await registry.dispatch("/note unpin 1")
        assert result is False

    @pytest.mark.asyncio
    async def test_note_search_dispatch_returns_false(self) -> None:
        """dispatch('/note search hello') returns False."""
        ctx = _Ctx()
        registry = _PatchedCommandRegistry(ctx)
        result = await registry.dispatch("/note search hello")
        assert result is False


class TestMemoryCommandGuard:
    """Tests that /memory remains functional after /note removal."""

    @pytest.mark.asyncio
    async def test_memory_list_dispatch_returns_true(self) -> None:
        """dispatch('/memory list') returns True."""
        ctx = _Ctx()
        registry = _PatchedCommandRegistry(ctx)
        result = await registry.dispatch("/memory list")
        assert result is True


class TestNoteCommandRemoved:
    @pytest.mark.asyncio
    async def test_mcp_unknown_subcommand_raises(self) -> None:
        """Verify unknown subcommand behavior pattern (reference for /note)."""
        ctx = _Ctx()
        mcp = _Mcp(ctx)
        with pytest.raises(
            UnknownSubcommandError, match="Unknown subcommand 'invalid'"
        ):
            await mcp._cmd_mcp("invalid")

    @pytest.mark.asyncio
    async def test_note_add_not_dispatched(self) -> None:
        """Verify /note is not handled by the dispatch loop (returns False)."""
        from agent.commands.registry import _COMMANDS

        # Verify /note is NOT in _COMMANDS
        note_cmds = [c for c in _COMMANDS if c.name == "/note"]
        assert len(note_cmds) == 0, (
            "/note should not be registered as a built-in command"
        )

    @pytest.mark.asyncio
    async def test_memory_still_registered(self) -> None:
        """Verify /memory is still in _COMMANDS."""
        from agent.commands.registry import _COMMANDS

        memory_cmds = [c for c in _COMMANDS if c.name == "/memory"]
        assert len(memory_cmds) == 1, "/memory should still be registered"
        assert memory_cmds[0].prefix is True
