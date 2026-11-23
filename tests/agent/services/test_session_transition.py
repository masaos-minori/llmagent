"""
tests/agent/services/test_session_transition.py
Unit tests for agent/services/session_transition.py.

Pipeline-level coverage per the seq 02 companion procedure: refusal while a
turn is active, finalization ordering and warn-continue behavior, atomic
commit, and rollback completeness at every failure point (AC-1).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.context import ConversationState, RuntimeStats, TurnState
from agent.services.exceptions import SessionNotFoundError
from agent.services.models import SessionRestoreResult
from agent.services.session_restore import RestoredSessionState
from agent.services.session_transition import (
    SessionTransitionRefusedError,
    SessionTransitionService,
)


def _make_session(session_id: int | None = 1, generation: int = 1) -> MagicMock:
    """Session double whose start()/bump_generation() mirror AgentSession behavior."""
    session = MagicMock()
    session.session_id = session_id
    session.generation = generation

    def _bump() -> int:
        session.generation += 1
        return session.generation

    def _start() -> None:
        session.session_id = 999
        session.generation += 1

    session.bump_generation.side_effect = _bump
    session.start.side_effect = _start
    return session


def _make_ctx(
    *,
    session_id: int | None = 1,
    generation: int = 1,
    system_prompt: str = "SYS",
    history: list[dict] | None = None,
) -> MagicMock:
    """Context double with real ConversationState/TurnState/RuntimeStats."""
    ctx = MagicMock()
    ctx.conv = ConversationState(system_prompt_content=system_prompt)
    ctx.conv.history = history or [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "keep me"},
    ]
    ctx.conv.undo_floor = 0
    ctx.conv.is_processing = False
    ctx.turn = TurnState()
    ctx.stats = RuntimeStats()
    ctx.stats.stat_turns = 7
    ctx.session = _make_session(session_id, generation)
    return ctx


def _make_persister(events: list[str]) -> MagicMock:
    persister = MagicMock()
    persister.capture_snapshot.return_value = MagicMock()
    persister.persist_session_memories = AsyncMock(
        side_effect=lambda *_: events.append("finalize")
    )
    persister.persist_session_diagnostics = AsyncMock()
    return persister


def _built_state(session_id: int = 42) -> RestoredSessionState:
    return RestoredSessionState(
        history=[
            {"role": "system", "content": "SYS"},
            {"role": "user", "content": "restored"},
        ],
        undo_floor=1,
        result=SessionRestoreResult(
            session_id=session_id,
            n_messages=5,
            fetched=5,
            synthesized=1,
            dropped=2,
            restored=2,
        ),
    )


@pytest.fixture
def events() -> list[str]:
    return []


class TestIdleRefusal:
    @pytest.mark.asyncio
    async def test_refused_while_processing(self, events: list[str]) -> None:
        ctx = _make_ctx()
        ctx.conv.is_processing = True
        service = SessionTransitionService(ctx, _make_persister(events))
        with pytest.raises(SessionTransitionRefusedError, match="in progress"):
            await service.load(42)
        assert events == []  # no finalization ran
        assert ctx.session.session_id == 1

    @pytest.mark.asyncio
    async def test_refused_while_turn_active(self, events: list[str]) -> None:
        ctx = _make_ctx()
        ctx.turn.current_turn_id = "turn-1"
        service = SessionTransitionService(ctx, _make_persister(events))
        with pytest.raises(SessionTransitionRefusedError):
            await service.clear_new()
        assert events == []
        assert ctx.session.session_id == 1


class TestLoadCommit:
    @pytest.mark.asyncio
    async def test_load_commits_builder_state_and_returns_counts(
        self, events: list[str]
    ) -> None:
        ctx = _make_ctx()
        persister = _make_persister(events)
        service = SessionTransitionService(ctx, persister)

        async def _build(*_args: object) -> RestoredSessionState:
            events.append("build")
            return _built_state()

        with patch(
            "agent.services.session_transition.restore_session",
            new=AsyncMock(side_effect=_build),
        ):
            result = await service.load(42)

        assert (result.fetched, result.synthesized, result.dropped) == (5, 1, 2)
        assert result.restored == 2
        assert ctx.conv.history == _built_state().history
        assert ctx.conv.undo_floor == 1
        assert ctx.session.session_id == 42
        assert ctx.session.generation == 2  # bumped once on commit (REQ-001)
        assert ctx.stats.stat_turns == 0
        # finalize runs before the build; the commit is only reached after both
        assert events == ["finalize", "build"]

    @pytest.mark.asyncio
    async def test_finalize_uses_one_persistence_snapshot(self) -> None:
        ctx = _make_ctx()
        persister = _make_persister([])
        service = SessionTransitionService(ctx, persister)
        with patch(
            "agent.services.session_transition.restore_session",
            new=AsyncMock(return_value=_built_state()),
        ):
            await service.load(42)
        persister.capture_snapshot.assert_called_once_with()
        snapshot = persister.capture_snapshot.return_value
        persister.persist_session_memories.assert_awaited_once_with(snapshot)
        persister.persist_session_diagnostics.assert_awaited_once_with(snapshot)

    @pytest.mark.asyncio
    async def test_finalize_failure_warns_and_continues(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        ctx = _make_ctx()
        persister = _make_persister([])
        persister.persist_session_memories = AsyncMock(
            side_effect=RuntimeError("db locked")
        )
        service = SessionTransitionService(ctx, persister)
        with patch(
            "agent.services.session_transition.restore_session",
            new=AsyncMock(return_value=_built_state()),
        ):
            result = await service.load(42)
        assert result.session_id == 42
        assert any("finalization failed" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_same_session_finalized_only_once(self) -> None:
        ctx = _make_ctx()
        persister = _make_persister([])
        service = SessionTransitionService(ctx, persister)
        failing = AsyncMock(side_effect=SessionNotFoundError("42 not found."))
        with patch("agent.services.session_transition.restore_session", new=failing):
            for _ in range(2):
                with pytest.raises(SessionNotFoundError):
                    await service.load(42)
        # UNK-03 guard: old session 1 is finalized once, not per attempt
        assert persister.persist_session_memories.await_count == 1

    @pytest.mark.asyncio
    async def test_no_active_session_skips_finalize(self, events: list[str]) -> None:
        ctx = _make_ctx(session_id=None)
        service = SessionTransitionService(ctx, _make_persister(events))
        with patch(
            "agent.services.session_transition.restore_session",
            new=AsyncMock(return_value=_built_state()),
        ):
            await service.load(42)
        assert events == []


class TestRollback:
    @pytest.mark.asyncio
    async def test_build_failure_leaves_previous_session_intact(self) -> None:
        ctx = _make_ctx()
        original_history = list(ctx.conv.history)
        service = SessionTransitionService(ctx, _make_persister([]))
        with patch(
            "agent.services.session_transition.restore_session",
            new=AsyncMock(side_effect=SessionNotFoundError("42 not found.")),
        ):
            with pytest.raises(SessionNotFoundError):
                await service.load(42)
        assert ctx.conv.history == original_history
        assert ctx.conv.undo_floor == 0
        assert ctx.session.session_id == 1
        assert ctx.session.generation == 1
        assert ctx.stats.stat_turns == 7

    @pytest.mark.asyncio
    async def test_commit_failure_restores_every_field(self) -> None:
        ctx = _make_ctx()
        original_history = list(ctx.conv.history)
        ctx.conv.undo_floor = 3
        service = SessionTransitionService(ctx, _make_persister([]))

        def _flaky_correlation(target_ctx: MagicMock) -> None:
            # Fail only for the newly committed session id, succeed on rollback.
            if target_ctx.session.session_id == 42:
                raise RuntimeError("commit boom")

        with (
            patch(
                "agent.services.session_transition.restore_session",
                new=AsyncMock(return_value=_built_state()),
            ),
            patch(
                "agent.services.session_transition.refresh_session_correlation",
                side_effect=_flaky_correlation,
            ),
        ):
            with pytest.raises(RuntimeError, match="commit boom"):
                await service.load(42)
        assert ctx.conv.history == original_history
        assert ctx.conv.undo_floor == 3
        assert ctx.session.session_id == 1
        assert ctx.session.generation == 1
        assert ctx.stats.stat_turns == 7


class TestClearNew:
    @pytest.mark.asyncio
    async def test_clear_new_finalizes_then_starts_fresh(
        self, events: list[str]
    ) -> None:
        ctx = _make_ctx(generation=4)
        ctx.conv.undo_floor = 2

        def _start_with_event() -> None:
            events.append("start")
            ctx.session.session_id = 999
            ctx.session.generation += 1

        ctx.session.start.side_effect = _start_with_event
        service = SessionTransitionService(ctx, _make_persister(events))
        await service.clear_new()
        assert events == ["finalize", "start"]
        assert ctx.session.session_id == 999
        assert ctx.session.generation == 5  # bumped by start(), not again by commit
        assert ctx.conv.history == [{"role": "system", "content": "SYS"}]
        assert ctx.conv.undo_floor == 0
        assert ctx.stats.stat_turns == 0

    @pytest.mark.asyncio
    async def test_clear_new_without_system_prompt_has_empty_history(self) -> None:
        ctx = _make_ctx(system_prompt="")
        service = SessionTransitionService(ctx, _make_persister([]))
        await service.clear_new()
        assert ctx.conv.history == []

    @pytest.mark.asyncio
    async def test_clear_new_start_failure_rolls_back(self) -> None:
        ctx = _make_ctx()
        original_history = list(ctx.conv.history)
        ctx.session.start.side_effect = RuntimeError("db write failed")
        service = SessionTransitionService(ctx, _make_persister([]))
        with pytest.raises(RuntimeError, match="db write failed"):
            await service.clear_new()
        assert ctx.conv.history == original_history
        assert ctx.session.session_id == 1
        assert ctx.session.generation == 1
        assert ctx.stats.stat_turns == 7
