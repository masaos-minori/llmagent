"""tests/test_conversation_service.py
Unit tests for agent/services/conversation_service.py:
await clear_conversation().
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.fixture
def patched_service() -> Iterator[MagicMock]:
    service = MagicMock()
    service.clear_new = AsyncMock(return_value=5)
    with patch(
        "agent.services.conversation_service.SessionTransitionService.for_context",
        return_value=service,
    ):
        yield service


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

    async def test_new_session_goes_through_the_transition_service(self) -> None:
        ctx = _make_ctx()
        service = MagicMock()
        service.clear_new = AsyncMock(return_value=5)
        with patch(
            "agent.services.conversation_service.SessionTransitionService.for_context",
            return_value=service,
        ) as for_context:
            result = await clear_conversation(ctx, new_session=True)
        for_context.assert_called_once_with(ctx)
        service.clear_new.assert_awaited_once_with()
        ctx.session.set_title.assert_called_once_with("(New Session)")
        ctx.session.start.assert_not_called()
        assert result.action == ConversationActionType.CLEAR

    async def test_new_session_failure_propagates_and_sets_no_title(self) -> None:
        ctx = _make_ctx()
        service = MagicMock()
        service.clear_new = AsyncMock(side_effect=RuntimeError("commit failed"))
        with (
            patch(
                "agent.services.conversation_service.SessionTransitionService.for_context",
                return_value=service,
            ),
            pytest.raises(RuntimeError, match="commit failed"),
        ):
            await clear_conversation(ctx, new_session=True)
        ctx.session.set_title.assert_not_called()

    async def test_new_session_message_mentions_new_session(
        self, patched_service: MagicMock
    ) -> None:
        result = await clear_conversation(_make_ctx(), new_session=True)
        assert "New session" in result.message

    async def test_messages_name_the_in_memory_reset_and_surviving_rows(
        self, patched_service: MagicMock
    ) -> None:
        plain = (await clear_conversation(_make_ctx())).message
        new = (await clear_conversation(_make_ctx(), new_session=True)).message
        assert plain.startswith("In-memory conversation history cleared")
        assert "Saved messages and long-term Memory are unchanged" in plain
        assert new.startswith("In-memory conversation history cleared")
        assert "finalized" in new
        assert "saved messages remain in the database" in new

    async def test_clear_never_deletes_persisted_rows_or_touches_memory(
        self, patched_service: MagicMock
    ) -> None:
        ctx = _make_ctx()
        await clear_conversation(ctx)
        await clear_conversation(ctx, new_session=True)
        ctx.session.delete_session.assert_not_called()
        ctx.session.replace_messages.assert_not_called()
        ctx.session.save.assert_not_called()
        ctx.services_required.memory.assert_not_called()

    async def test_no_new_session_does_not_call_session_start(self) -> None:
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


# ── /clear new through the real transition service ───────────────────────────

from tests.agent.services import test_session_transition as _transition

# Fixtures reused from the service tests under distinct names (conn is the ctx dependency).
conn = _transition.conn
real_ctx = _transition.ctx


class TestClearNewFinalizesAndRollsBack:
    @staticmethod
    def _wire(real_ctx, order: list[str]):  # noqa: ANN001, ANN205 — SimpleNamespace stand-in real_ctx
        from types import SimpleNamespace

        real_ctx.cfg = SimpleNamespace(diagnostics=None, db=None)
        persister = MagicMock()
        persister.capture_snapshot.side_effect = lambda: order.append(
            f"capture:{real_ctx.session.session_id}"
        )
        persister.persist_session_memories = AsyncMock(
            side_effect=lambda snap: order.append(
                f"memories:{real_ctx.session.session_id}"
            )
        )
        persister.persist_session_diagnostics = AsyncMock(
            side_effect=lambda snap: order.append(
                f"diagnostics:{real_ctx.session.session_id}"
            )
        )
        from agent.services.session_transition import SessionTransitionService

        return patch(
            "agent.services.conversation_service.SessionTransitionService.for_context",
            return_value=SessionTransitionService(real_ctx, persister),
        )

    async def test_old_session_is_finalized_before_the_switch(self, real_ctx) -> None:
        old_id = real_ctx.session.session_id
        order: list[str] = []
        with self._wire(real_ctx, order):
            result = await clear_conversation(real_ctx, new_session=True)

        assert order == [
            f"capture:{old_id}",
            f"memories:{old_id}",
            f"diagnostics:{old_id}",
        ]
        assert real_ctx.session.session_id != old_id
        assert real_ctx.conv.history == [real_ctx.conv.history[0]]
        assert result.action == ConversationActionType.CLEAR

    async def test_failed_switch_leaves_the_old_session_and_sets_no_title(
        self,
        real_ctx,
    ) -> None:
        old_id = real_ctx.session.session_id
        history = [dict(m) for m in real_ctx.conv.history]
        with (
            self._wire(real_ctx, []),
            patch(
                "agent.services.session_transition.reset_session_stats",
                side_effect=RuntimeError("boom"),
            ),
            patch.object(real_ctx.session, "set_title") as set_title,
            pytest.raises(RuntimeError, match="boom"),
        ):
            await clear_conversation(real_ctx, new_session=True)

        assert real_ctx.session.session_id == old_id
        assert real_ctx.conv.history == history
        set_title.assert_not_called()

    async def test_clear_new_is_refused_while_a_turn_runs(self, real_ctx) -> None:
        from agent.services.session_transition import SessionTransitionRefusedError

        real_ctx.turn.current_turn_id = "t-1"
        with self._wire(real_ctx, []), pytest.raises(SessionTransitionRefusedError):
            await clear_conversation(real_ctx, new_session=True)
