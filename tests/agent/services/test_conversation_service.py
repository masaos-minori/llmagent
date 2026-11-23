"""tests/test_conversation_service.py
Unit tests for agent/services/conversation_service.py:
clear_conversation().

new_session=True delegates the whole switch to SessionTransitionService
(REQ-002); both result messages name the in-memory history and state that
persisted rows survive (REQ-007).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.services.conversation_service import clear_conversation
from agent.services.enums import ConversationActionType


def _make_ctx(
    history: list | None = None,
) -> MagicMock:
    ctx = MagicMock()
    ctx.conv.history = (
        history
        if history is not None
        else [{"role": "system", "content": "You are helpful."}]
    )
    ctx.conv.system_prompt_name = "default"
    ctx.conv.system_prompt_content = "You are helpful."
    ctx.stats.stat_turns = 5
    ctx.stats.stat_tool_calls = 3
    ctx.stats.stat_tool_errors = 1
    ctx.stats.stat_latency = {"llm": [0.1, 0.2]}
    ctx.services_required.llm = None
    return ctx


def _make_service() -> MagicMock:
    service = MagicMock()
    service.clear_new = AsyncMock()
    return service


# ── clear_conversation ────────────────────────────────────────────────────────


class TestClearConversation:
    async def test_trims_history_to_first_message_only(self) -> None:
        ctx = _make_ctx(
            history=[
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ]
        )
        await clear_conversation(ctx)
        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[0]["role"] == "system"

    async def test_returns_clear_action_result(self) -> None:
        ctx = _make_ctx()
        result = await clear_conversation(ctx)
        assert result.action == ConversationActionType.CLEAR

    async def test_resets_stat_turns_to_zero(self) -> None:
        ctx = _make_ctx()
        await clear_conversation(ctx)
        assert ctx.stats.stat_turns == 0

    async def test_resets_stat_tool_calls_to_zero(self) -> None:
        ctx = _make_ctx()
        await clear_conversation(ctx)
        assert ctx.stats.stat_tool_calls == 0

    async def test_resets_stat_tool_errors_to_zero(self) -> None:
        ctx = _make_ctx()
        await clear_conversation(ctx)
        assert ctx.stats.stat_tool_errors == 0

    async def test_resets_stat_latency_to_empty_dict(self) -> None:
        ctx = _make_ctx()
        await clear_conversation(ctx)
        assert ctx.stats.stat_latency == {}

    async def test_new_session_delegates_to_transition_service(self) -> None:
        ctx = _make_ctx()
        service = _make_service()
        result = await clear_conversation(
            ctx, new_session=True, transition_service=service
        )
        # REQ-002: the service owns finalize/start/commit; the function does
        # not call session.start or correlation refresh itself.
        service.clear_new.assert_awaited_once()
        ctx.session.start.assert_not_called()
        ctx.session.set_title.assert_called_once_with("(New Session)")
        assert result.action == ConversationActionType.CLEAR

    async def test_new_session_message_mentions_new_session(self) -> None:
        ctx = _make_ctx()
        result = await clear_conversation(
            ctx, new_session=True, transition_service=_make_service()
        )
        assert "New session" in result.message

    async def test_new_session_requires_transition_service(self) -> None:
        ctx = _make_ctx()
        with pytest.raises(ValueError, match="SessionTransitionService"):
            await clear_conversation(ctx, new_session=True)
        ctx.session.start.assert_not_called()

    async def test_both_messages_name_in_memory_history_and_persisted_rows(
        self,
    ) -> None:
        # REQ-007 wording: in-memory reset explicit, persisted rows survive.
        ctx = _make_ctx()
        plain = await clear_conversation(ctx)
        fresh = await clear_conversation(
            ctx, new_session=True, transition_service=_make_service()
        )
        for message in (plain.message, fresh.message):
            assert "In-memory conversation history cleared" in message
            assert "Persisted messages remain" in message

    async def test_no_new_session_does_not_call_service_or_session_start(self) -> None:
        ctx = _make_ctx()
        await clear_conversation(ctx, new_session=False)
        ctx.session.start.assert_not_called()

    async def test_history_with_only_system_prompt_stays_unchanged(self) -> None:
        ctx = _make_ctx(history=[{"role": "system", "content": "sys"}])
        await clear_conversation(ctx)
        assert len(ctx.conv.history) == 1

    async def test_empty_history_stays_empty(self) -> None:
        ctx = _make_ctx(history=[])
        await clear_conversation(ctx)
        assert ctx.conv.history == []
