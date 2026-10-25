"""
tests/agent/test_session_correlation_refresh.py
Spy-based coverage for the MCP correlation session-id refresh invariant.

Covers: helper guards and single str call, restore-flow refresh, clear-flow
refresh. No DB, network, or config access — MagicMock ctx + real ConversationState.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from agent.commands.mixin_base import refresh_session_correlation
from agent.context import ConversationState
from agent.services.conversation_service import clear_conversation
from agent.services.session_restore import restore_session


def _make_corr_ctx(session_id: int | None = 1) -> MagicMock:
    """Minimal MagicMock ctx: only attributes the three flows touch."""
    ctx = MagicMock()
    ctx.session.session_id = session_id
    ctx.session.fetch_messages.return_value = ([], True, 0)
    ctx.conv = ConversationState()
    ctx.services_required.tools = MagicMock()
    return ctx


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
        await restore_session(ctx, 7)
        tools.set_session_id.assert_called_once_with("7")

    def test_clear_flow_refreshes_correlation(self) -> None:
        ctx = _make_corr_ctx(session_id=1)

        def _start() -> None:
            ctx.session.session_id = 8

        ctx.session.start.side_effect = _start
        tools = ctx.services_required.tools
        clear_conversation(ctx, new_session=True)
        tools.set_session_id.assert_called_once_with("8")
