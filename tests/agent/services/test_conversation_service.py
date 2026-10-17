"""tests/test_conversation_service.py
Unit tests for agent/services/conversation_service.py:
clear_conversation().
"""

from __future__ import annotations

from unittest.mock import MagicMock

from agent.services.conversation_service import clear_conversation
from agent.services.enums import ConversationActionType


def _make_ctx(
    history: list | None = None,
    system_prompts: dict | None = None,
) -> MagicMock:
    ctx = MagicMock()
    ctx.conv.history = (
        history
        if history is not None
        else [{"role": "system", "content": "You are helpful."}]
    )
    ctx.conv.system_prompt_name = "default"
    ctx.conv.system_prompt_content = "You are helpful."
    ctx.cfg.tool.system_prompts = system_prompts or {
        "default": "You are helpful.",
        "coding": "You code well.",
    }
    ctx.stats.stat_turns = 5
    ctx.stats.stat_tool_calls = 3
    ctx.stats.stat_tool_errors = 1
    ctx.stats.stat_latency = {"llm": [0.1, 0.2]}
    ctx.services_required.llm = None
    return ctx


# ── clear_conversation ────────────────────────────────────────────────────────


class TestClearConversation:
    def test_trims_history_to_first_message_only(self) -> None:
        ctx = _make_ctx(
            history=[
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ]
        )
        clear_conversation(ctx)
        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[0]["role"] == "system"

    def test_returns_clear_action_result(self) -> None:
        ctx = _make_ctx()
        result = clear_conversation(ctx)
        assert result.action == ConversationActionType.CLEAR

    def test_resets_stat_turns_to_zero(self) -> None:
        ctx = _make_ctx()
        clear_conversation(ctx)
        assert ctx.stats.stat_turns == 0

    def test_resets_stat_tool_calls_to_zero(self) -> None:
        ctx = _make_ctx()
        clear_conversation(ctx)
        assert ctx.stats.stat_tool_calls == 0

    def test_resets_stat_tool_errors_to_zero(self) -> None:
        ctx = _make_ctx()
        clear_conversation(ctx)
        assert ctx.stats.stat_tool_errors == 0

    def test_resets_stat_latency_to_empty_dict(self) -> None:
        ctx = _make_ctx()
        clear_conversation(ctx)
        assert ctx.stats.stat_latency == {}

    def test_new_session_starts_session(self) -> None:
        ctx = _make_ctx()
        result = clear_conversation(ctx, new_session=True)
        ctx.session.start.assert_called_once()
        ctx.session.set_title.assert_called_once()
        assert result.action == ConversationActionType.CLEAR

    def test_new_session_message_mentions_new_session(self) -> None:
        ctx = _make_ctx()
        result = clear_conversation(ctx, new_session=True)
        assert "New session" in result.message

    def test_no_new_session_does_not_call_session_start(self) -> None:
        ctx = _make_ctx()
        clear_conversation(ctx, new_session=False)
        ctx.session.start.assert_not_called()

    def test_history_with_only_system_prompt_stays_unchanged(self) -> None:
        ctx = _make_ctx(history=[{"role": "system", "content": "sys"}])
        clear_conversation(ctx)
        assert len(ctx.conv.history) == 1

    def test_empty_history_stays_empty(self) -> None:
        ctx = _make_ctx(history=[])
        clear_conversation(ctx)
        assert ctx.conv.history == []
