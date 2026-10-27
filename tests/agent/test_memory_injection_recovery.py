"""tests/agent/test_memory_injection_recovery.py

Regression tests for the per-turn memory-injection degraded-state transitions
in agent/conversation_state_manager.py (handle_memory_injection):

- AC-001: a failed injection sets ``memory_disabled``; a later successful
  attempt clears it.
- AC-002: recovery resets ``memory_warning_shown``, so a later degradation
  period warns once again.
- AC-003: persistent failures emit exactly one warning-level log; the repeat
  failures log at debug and no exception escapes the method.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import agent.conversation_state_manager as csm_module
import pytest
from agent.context import ConversationState
from agent.conversation_state_manager import ConversationStateManager

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_manager() -> tuple[ConversationStateManager, MagicMock, MagicMock]:
    """Return a ConversationStateManager with mocked ctx and a fake memory service."""
    ctx = MagicMock()
    ctx.conv = ConversationState()
    ctx.session.session_id = "test-session"
    mem = MagicMock()
    mem.on_user_prompt = AsyncMock(return_value=[])
    ctx.services_required.memory = mem
    manager = ConversationStateManager(ctx, tasks=set(), on_discard=lambda task: None)
    return manager, ctx, mem


def _fail(mem: MagicMock) -> None:
    """Make the fake memory service raise on the next call."""
    mem.on_user_prompt.side_effect = RuntimeError("memory injection failure")


def _succeed(mem: MagicMock) -> None:
    """Make the fake memory service return an empty snippet list."""
    mem.on_user_prompt.side_effect = None
    mem.on_user_prompt.return_value = []


class TestMemoryInjectionRecovery:
    """Flag and logging transitions across failing and succeeding turns."""

    @pytest.mark.asyncio
    async def test_failure_then_success_clears_flag(self) -> None:
        """AC-001: a failure sets memory_disabled, the next success clears it."""
        manager, ctx, mem = _make_manager()

        _fail(mem)
        await manager.handle_memory_injection("hello")
        assert ctx.conv.memory_disabled is True

        _succeed(mem)
        await manager.handle_memory_injection("hello")
        assert ctx.conv.memory_disabled is False

    @pytest.mark.asyncio
    async def test_recovery_rearms_warning_flag(self) -> None:
        """AC-002: recovery resets memory_warning_shown and a later failure re-warns."""
        manager, ctx, mem = _make_manager()

        _fail(mem)
        await manager.handle_memory_injection("hello")
        assert ctx.conv.memory_disabled is True
        assert ctx.conv.memory_warning_shown is True

        _succeed(mem)
        await manager.handle_memory_injection("hello")
        assert ctx.conv.memory_disabled is False
        assert ctx.conv.memory_warning_shown is False

        _fail(mem)
        await manager.handle_memory_injection("hello")
        assert ctx.conv.memory_warning_shown is True

    @pytest.mark.asyncio
    async def test_persistent_failure_warns_once(self) -> None:
        """AC-003: N consecutive failures emit one warning and debug for the repeats."""

        manager, ctx, mem = _make_manager()
        _fail(mem)

        with (
            patch.object(csm_module.logger, "warning") as warn,
            patch.object(csm_module.logger, "debug") as debug,
        ):
            await manager.handle_memory_injection("hello")
            await manager.handle_memory_injection("hello")
            await manager.handle_memory_injection("hello")

        assert warn.call_count == 1
        assert debug.call_count >= 2
        assert ctx.conv.memory_disabled is True
