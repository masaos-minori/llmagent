"""
tests/test_session_restore.py
Unit tests for agent/services/session_restore.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from agent.services.exceptions import SessionNotFoundError
from agent.services.session_restore import restore_session


def _make_ctx(
    messages: list[dict] | None = None,
    system_prompt_content: str = "",
    extra_history: list[dict] | None = None,
) -> MagicMock:
    """Build a minimal AgentContext mock."""
    ctx = MagicMock()
    ctx.session.fetch_messages.return_value = messages or []
    ctx.conv.system_prompt_content = system_prompt_content
    ctx.conv.history = list(extra_history or [])
    ctx.session.session_id = 0
    return ctx


class TestRestoreSession:
    def test_successful_restore(self) -> None:
        msgs = [{"role": "user", "content": "hello"}]
        ctx = _make_ctx(messages=msgs)
        result = restore_session(ctx, session_id=5)
        assert result.session_id == 5
        assert result.n_messages == 1

    def test_session_id_updated_on_ctx(self) -> None:
        msgs = [{"role": "user", "content": "hi"}]
        ctx = _make_ctx(messages=msgs)
        restore_session(ctx, session_id=99)
        assert ctx.session.session_id == 99

    def test_history_rebuilt_with_canonical_system_prefix(self) -> None:
        user_msg = {"role": "user", "content": "hello"}
        ctx = _make_ctx(
            messages=[user_msg],
            system_prompt_content="You are a helpful assistant.",
        )
        restore_session(ctx, session_id=3)
        assert ctx.conv.history[0]["role"] == "system"
        assert ctx.conv.history[0]["content"] == "You are a helpful assistant."
        assert ctx.conv.history[1]["role"] == "user"

    def test_system_message_appears_exactly_once_when_db_also_has_system(self) -> None:
        db_sys = {"role": "system", "content": "old system from DB"}
        user_msg = {"role": "user", "content": "hello"}
        ctx = _make_ctx(
            messages=[db_sys, user_msg],
            system_prompt_content="Current canonical prompt.",
        )
        restore_session(ctx, session_id=3)
        system_count = sum(1 for m in ctx.conv.history if m["role"] == "system")
        assert system_count == 1
        assert ctx.conv.history[0]["content"] == "Current canonical prompt."

    def test_memory_injected_messages_not_carried_into_restored_history(self) -> None:
        user_msg = {"role": "user", "content": "hello"}
        ctx = _make_ctx(
            messages=[user_msg],
            system_prompt_content="Canonical prompt.",
            extra_history=[
                {"role": "system", "content": "mem", "_memory_injected": True}
            ],
        )
        restore_session(ctx, session_id=4)
        assert all(not m.get("_memory_injected") for m in ctx.conv.history)

    def test_no_system_prompt_content_uses_db_messages_as_is(self) -> None:
        db_sys = {"role": "system", "content": "system from db"}
        user_msg = {"role": "user", "content": "hi"}
        ctx = _make_ctx(
            messages=[db_sys, user_msg],
            system_prompt_content="",
        )
        restore_session(ctx, session_id=5)
        assert ctx.conv.history == [db_sys, user_msg]

    def test_non_system_extra_history_discarded(self) -> None:
        old_user = {"role": "user", "content": "old message"}
        new_msg = {"role": "user", "content": "restored message"}
        ctx = _make_ctx(
            messages=[new_msg],
            system_prompt_content="",
            extra_history=[old_user],
        )
        restore_session(ctx, session_id=2)
        assert all(m["content"] != "old message" for m in ctx.conv.history)

    def test_empty_messages_raises_not_found(self) -> None:
        ctx = _make_ctx(messages=[])
        with pytest.raises(SessionNotFoundError):
            restore_session(ctx, session_id=1)

    def test_n_messages_reflects_fetched_count(self) -> None:
        msgs = [{"role": "user", "content": str(i)} for i in range(5)]
        ctx = _make_ctx(messages=msgs)
        result = restore_session(ctx, session_id=10)
        assert result.n_messages == 5

    def test_reset_session_stats_called(self) -> None:
        msgs = [{"role": "user", "content": "hi"}]
        ctx = _make_ctx(messages=msgs)
        with __import__("unittest.mock", fromlist=["patch"]).patch(
            "agent.services.session_restore.reset_session_stats"
        ) as mock_reset:
            restore_session(ctx, session_id=4)
            mock_reset.assert_called_once_with(ctx)
