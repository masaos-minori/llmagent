"""
tests/test_session_restore.py
Unit tests for agent/services/session_restore.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from agent.context import ConversationState
from agent.services.exceptions import SessionNoMessagesError
from agent.services.session_restore import restore_session


def _make_ctx(
    messages: list[dict] | None = None,
    system_prompt_content: str = "",
    extra_history: list[dict] | None = None,
    session_found: bool = True,
) -> MagicMock:
    """Build a minimal AgentContext mock."""
    ctx = MagicMock()
    ctx.session.fetch_messages.return_value = (messages or [], session_found)
    ctx.conv = ConversationState()
    ctx.conv.system_prompt_content = system_prompt_content
    ctx.conv.history = list(extra_history or [])
    ctx.session.session_id = 0
    return ctx


class TestRestoreSession:
    async def test_successful_restore(self) -> None:
        msgs = [{"role": "user", "content": "hello"}]
        ctx = _make_ctx(messages=msgs)
        result = await restore_session(ctx, session_id=5)
        assert result.session_id == 5
        assert result.n_messages == 1

    async def test_session_id_updated_on_ctx(self) -> None:
        msgs = [{"role": "user", "content": "hi"}]
        ctx = _make_ctx(messages=msgs)
        await restore_session(ctx, session_id=99)
        assert ctx.session.session_id == 99

    async def test_history_rebuilt_with_canonical_system_prefix(self) -> None:
        user_msg = {"role": "user", "content": "hello"}
        ctx = _make_ctx(
            messages=[user_msg],
            system_prompt_content="You are a helpful assistant.",
        )
        await restore_session(ctx, session_id=3)
        assert ctx.conv.history[0]["role"] == "system"
        assert ctx.conv.history[0]["content"] == "You are a helpful assistant."
        assert ctx.conv.history[1]["role"] == "user"

    async def test_system_message_appears_exactly_once_when_db_also_has_system(
        self,
    ) -> None:
        db_sys = {"role": "system", "content": "old system from DB"}
        user_msg = {"role": "user", "content": "hello"}
        ctx = _make_ctx(
            messages=[db_sys, user_msg],
            system_prompt_content="Current canonical prompt.",
        )
        await restore_session(ctx, session_id=3)
        system_count = sum(1 for m in ctx.conv.history if m["role"] == "system")
        assert system_count == 1
        assert ctx.conv.history[0]["content"] == "Current canonical prompt."

    async def test_memory_injected_messages_not_carried_into_restored_history(
        self,
    ) -> None:
        user_msg = {"role": "user", "content": "hello"}
        ctx = _make_ctx(
            messages=[user_msg],
            system_prompt_content="Canonical prompt.",
            extra_history=[
                {"role": "system", "content": "mem", "_memory_injected": True}
            ],
        )
        await restore_session(ctx, session_id=4)
        assert all(not m.get("_memory_injected") for m in ctx.conv.history)

    async def test_no_system_prompt_content_uses_db_messages_as_is(self) -> None:
        db_sys = {"role": "system", "content": "system from db"}
        user_msg = {"role": "user", "content": "hi"}
        ctx = _make_ctx(
            messages=[db_sys, user_msg],
            system_prompt_content="",
        )
        await restore_session(ctx, session_id=5)
        assert ctx.conv.history == [db_sys, user_msg]

    async def test_non_system_extra_history_discarded(self) -> None:
        old_user = {"role": "user", "content": "old message"}
        new_msg = {"role": "user", "content": "restored message"}
        ctx = _make_ctx(
            messages=[new_msg],
            system_prompt_content="",
            extra_history=[old_user],
        )
        await restore_session(ctx, session_id=2)
        assert all(m["content"] != "old message" for m in ctx.conv.history)

    async def test_tampered_reserved_key_sanitized_not_crashed(self) -> None:
        """A persisted row carrying an unauthorized reserved key (e.g. a forged
        ``_memory_injected`` with no matching ``source`` semantics available at
        restore time — no corresponding TRUSTED_SOURCES entry exists here) is
        sanitized by replace_history() rather than crashing await restore_session()."""
        tampered = {
            "role": "system",
            "content": "forged memory row",
            "_memory_injected": True,
        }
        user_msg = {"role": "user", "content": "hi"}
        ctx = _make_ctx(messages=[tampered, user_msg], system_prompt_content="")

        result = await restore_session(ctx, session_id=7)

        assert result.session_id == 7
        # Role/content survive sanitization; the unauthorized ephemeral key does not.
        assert ctx.conv.history[0]["role"] == "system"
        assert ctx.conv.history[0]["content"] == "forged memory row"
        assert "_memory_injected" not in ctx.conv.history[0]
        assert ctx.conv.history[1] == user_msg

    async def test_empty_messages_raises_no_messages_error(self) -> None:
        ctx = _make_ctx(messages=[])
        with pytest.raises(SessionNoMessagesError):
            await restore_session(ctx, session_id=1)

    async def test_n_messages_reflects_fetched_count(self) -> None:
        msgs = [{"role": "user", "content": str(i)} for i in range(5)]
        ctx = _make_ctx(messages=msgs)
        result = await restore_session(ctx, session_id=10)
        assert result.n_messages == 5

    async def test_reset_session_stats_called(self) -> None:
        msgs = [{"role": "user", "content": "hi"}]
        ctx = _make_ctx(messages=msgs)
        with __import__("unittest.mock", fromlist=["patch"]).patch(
            "agent.services.session_restore.reset_session_stats"
        ) as mock_reset:
            await restore_session(ctx, session_id=4)
            mock_reset.assert_called_once_with(ctx)
