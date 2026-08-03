"""tests/test_conversation_service.py
Unit tests for agent/services/conversation_service.py:
clear_conversation() and switch_system_prompt().
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from agent.services.conversation_service import clear_conversation, switch_system_prompt
from agent.services.enums import ConversationActionType
from agent.services.exceptions import ConversationStateError


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
    ctx.stats.stat_semantic_cache_hits = 2
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

    def test_resets_semantic_cache_hits_to_zero(self) -> None:
        ctx = _make_ctx()
        clear_conversation(ctx)
        assert ctx.stats.stat_semantic_cache_hits == 0

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


# ── switch_system_prompt ──────────────────────────────────────────────────────


class TestSwitchSystemPrompt:
    def test_updates_system_prompt_name(self) -> None:
        ctx = _make_ctx()
        switch_system_prompt(ctx, "coding")
        assert ctx.conv.system_prompt_name == "coding"

    def test_updates_system_prompt_content(self) -> None:
        ctx = _make_ctx()
        switch_system_prompt(ctx, "coding")
        assert ctx.conv.system_prompt_content == "You code well."

    def test_replaces_existing_system_message_in_history(self) -> None:
        ctx = _make_ctx(history=[{"role": "system", "content": "old prompt"}])
        switch_system_prompt(ctx, "coding")
        assert ctx.conv.history[0]["content"] == "You code well."

    def test_returns_switch_prompt_action(self) -> None:
        ctx = _make_ctx()
        result = switch_system_prompt(ctx, "coding")
        assert result.action == ConversationActionType.SWITCH_PROMPT

    def test_result_message_contains_preset_name(self) -> None:
        ctx = _make_ctx()
        result = switch_system_prompt(ctx, "coding")
        assert "coding" in result.message

    def test_unknown_preset_raises_conversation_state_error(self) -> None:
        ctx = _make_ctx()
        with pytest.raises(ConversationStateError, match="Unknown preset"):
            switch_system_prompt(ctx, "nonexistent")

    def test_error_message_lists_available_presets(self) -> None:
        ctx = _make_ctx()
        with pytest.raises(ConversationStateError, match="default"):
            switch_system_prompt(ctx, "nonexistent")

    def test_inserts_system_message_when_history_empty(self) -> None:
        ctx = _make_ctx(history=[])
        switch_system_prompt(ctx, "coding")
        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[0]["role"] == "system"
        assert ctx.conv.history[0]["content"] == "You code well."

    def test_does_not_insert_when_content_is_empty(self) -> None:
        ctx = _make_ctx(
            history=[],
            system_prompts={"default": "You are helpful.", "empty": ""},
        )
        switch_system_prompt(ctx, "empty")
        assert len(ctx.conv.history) == 0

    def test_history_without_leading_system_message_inserts_new(self) -> None:
        ctx = _make_ctx(history=[{"role": "user", "content": "hi"}])
        switch_system_prompt(ctx, "coding")
        assert ctx.conv.history[0]["role"] == "system"
        assert ctx.conv.history[0]["content"] == "You code well."
