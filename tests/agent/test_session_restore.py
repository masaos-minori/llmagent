"""
tests/test_session_restore.py
Unit tests for agent/services/session_restore.py.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, patch

import pytest
from agent.context import ConversationState
from agent.services.exceptions import SessionNoMessagesError
from agent.services.session_restore import _boundary_to_index, restore_session


def _make_ctx(
    messages: list[dict] | None = None,
    system_prompt_content: str = "",
    extra_history: list[dict] | None = None,
    session_found: bool = True,
    undo_floor_id: int = 0,
) -> MagicMock:
    """Build a minimal AgentContext mock.

    ``fetch_messages`` returns the 3-tuple ``(messages, found, undo_floor_id)``
    that the restored service unpacks (rows 02/03). ``undo_floor_id`` defaults
    to 0 (no boundary); set it non-zero to exercise the boundary conversion.
    """
    ctx = MagicMock()
    ctx.session.fetch_messages.return_value = (
        messages or [],
        session_found,
        undo_floor_id,
    )
    ctx.conv = ConversationState()
    ctx.conv.system_prompt_content = system_prompt_content
    ctx.conv.undo_floor = 0
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

    async def test_undo_floor_zero_when_no_boundary(self) -> None:
        msgs = [{"role": "user", "content": "hi"}]
        ctx = _make_ctx(messages=msgs, system_prompt_content="Canonical.")
        await restore_session(ctx, session_id=6)
        assert ctx.conv.undo_floor == 0

    async def test_undo_floor_converts_boundary_to_index(self) -> None:
        # Snapshot = first 2 rows (system summary + user); post-compression =
        # the remaining assistant + user rows. system_prompt is set, so the
        # rebuilt history is [canonical SYS] + non-system rows.
        messages = [
            {"role": "system", "content": "[summary]"},
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
        ]
        ctx = _make_ctx(
            messages=messages, system_prompt_content="Canonical.", undo_floor_id=2
        )
        ctx.session.count_messages_up_to.return_value = 2  # n_snapshot
        await restore_session(ctx, session_id=42)
        # 1 + n_snapshot - system_count = 1 + 2 - 1 = 2 -> first post-compression
        # turn (a1) is the first undoable index; snapshot turns stay blocked.
        assert ctx.conv.undo_floor == 2
        assert ctx.conv.history[0]["role"] == "system"
        assert ctx.conv.history[0]["content"] == "Canonical."
        # index 1 (q1, last snapshot user) is below the floor; index 2 (a1) above.
        assert ctx.conv.history[1]["content"] == "q1"

    async def test_raise_in_count_messages_up_to_leaves_state_unmutated(self):
        """A raise in count_messages_up_to propagates before any session-state
        mutation (session_id unchanged, reset_session_stats not called); AC-1."""
        msgs = [{"role": "user", "content": "hi"}]
        ctx = _make_ctx(
            messages=msgs, system_prompt_content="Canonical.", undo_floor_id=1
        )
        ctx.session.count_messages_up_to.side_effect = sqlite3.Error("db down")
        with patch("agent.services.session_restore.reset_session_stats") as mock_reset:
            with pytest.raises(sqlite3.Error):
                await restore_session(ctx, session_id=42)
            mock_reset.assert_not_called()
        # session_id was not reassigned before the raise; still its _make_ctx default.
        assert ctx.session.session_id == 0

    async def test_undo_floor_anchors_to_rebuilt_history_after_dropped_row(self):
        """A content-less restored row is dropped by replace_history(); the undo
        boundary anchors to the shorter rebuilt history, not the pre-sanitization
        row count; AC-2."""
        messages = [
            {"role": "user"},  # missing content -> dropped by replace_history()
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
        ]
        ctx = _make_ctx(
            messages=messages, system_prompt_content="Canonical.", undo_floor_id=1
        )
        ctx.session.count_messages_up_to.return_value = 1  # n_snapshot
        await restore_session(ctx, session_id=7)
        # The content-less row is dropped; rebuilt history is [canonical sys, q1, a1].
        assert len(ctx.conv.history) == 3
        assert all(m.get("content") for m in ctx.conv.history)
        # Anchored to the rebuilt history, not the 4-row pre-sanitization list.
        expected = _boundary_to_index(
            1, ctx.conv.history, system_prompt_set=bool(ctx.conv.system_prompt_content)
        )
        assert ctx.conv.undo_floor == expected == 1
        # Sanity: the pre-sanitization anchor would over-index to 2.
        stale = _boundary_to_index(
            1, messages, system_prompt_set=bool(ctx.conv.system_prompt_content)
        )
        assert ctx.conv.undo_floor != stale
        # The computed index stays within the live history length.
        assert 0 <= ctx.conv.undo_floor <= len(ctx.conv.history)
