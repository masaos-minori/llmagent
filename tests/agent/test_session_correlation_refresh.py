"""
tests/agent/test_session_correlation_refresh.py
Spy-based coverage for the MCP correlation session-id refresh invariant.

Covers: helper guards and single str call, restore-flow refresh, clear-flow
refresh. No DB, network, or config access — MagicMock ctx + real ConversationState.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from agent.commands.mixin_base import refresh_session_correlation
from agent.context import ConversationState
from agent.services.conversation_service import clear_conversation
from agent.services.session_transition import SessionTransitionService


def _make_corr_ctx(session_id: int | None = 1) -> MagicMock:
    """Minimal MagicMock ctx: only attributes the three flows touch."""
    ctx = MagicMock()
    ctx.session.session_id = session_id
    ctx.session.fetch_messages.return_value = ([], True, 0)
    ctx.conv = ConversationState()
    ctx.turn.current_turn_id = None  # idle: the transition guard must pass
    ctx.services_required.tools = MagicMock()
    return ctx


def _make_persister() -> MagicMock:
    persister = MagicMock()
    persister.persist_session_memories = AsyncMock()
    persister.persist_session_diagnostics = AsyncMock()
    return persister


class TestHelperGuards:
    def test_helper_sets_str_id(self) -> None:
        ctx = _make_corr_ctx(session_id=42)
        tools = ctx.services_required.tools
        refresh_session_correlation(ctx)
        tools.set_session_id.assert_called_once_with("42")

    def test_helper_noop_when_tools_none(self) -> None:
        ctx = _make_corr_ctx(session_id=42)
        ctx.services_required.tools = None
        refresh_session_correlation(ctx)  # must not raise

    def test_helper_noop_when_session_id_none(self) -> None:
        ctx = _make_corr_ctx(session_id=None)
        tools = ctx.services_required.tools
        refresh_session_correlation(ctx)
        tools.set_session_id.assert_not_called()


class TestFlowRefresh:
    async def test_restore_flow_refreshes_correlation(self) -> None:
        ctx = _make_corr_ctx(session_id=1)
        ctx.session.fetch_messages.return_value = (
            [{"role": "user", "content": "hello"}],
            True,
            0,
        )
        tools = ctx.services_required.tools
        await SessionTransitionService(ctx, _make_persister()).load(7)
        tools.set_session_id.assert_called_once_with("7")

    async def test_clear_flow_refreshes_correlation(self) -> None:
        ctx = _make_corr_ctx(session_id=1)

        def _start() -> None:
            ctx.session.session_id = 8

        ctx.session.start.side_effect = _start
        tools = ctx.services_required.tools
        await clear_conversation(
            ctx,
            new_session=True,
            transition_service=SessionTransitionService(ctx, _make_persister()),
        )
        tools.set_session_id.assert_called_once_with("8")
