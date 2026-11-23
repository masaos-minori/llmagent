"""tests/agent/services/test_session_transition.py

SessionTransitionService: atomic ``/clear new`` and ``/session load``.

The context is a real ``AgentSession`` on a shared in-memory DB plus the real
conversation, turn, and statistics state, so rollback completeness is asserted
against actual field values rather than mock bookkeeping.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable, Generator
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.context import ConversationState, RuntimeStats, TurnState
from agent.services.exceptions import SessionNotFoundError
from agent.services.session_transition import (
    SessionTransitionRefusedError,
    SessionTransitionService,
)
from agent.session import AgentSession
from agent.session_persister import SessionPersister

from tests.agent._config_test_defaults import MIN_DB_CONFIG
from tests.agent.test_session_restore import _SCHEMA_SQL, _FakeSQLiteHelper

SYSTEM = {"role": "system", "content": "Canonical prompt."}
OLD_HISTORY = [
    SYSTEM,
    {"role": "user", "content": "old question"},
    {"role": "assistant", "content": "old answer"},
]


@pytest.fixture
def conn() -> Generator[sqlite3.Connection]:
    c = sqlite3.connect(":memory:")
    c.executescript(_SCHEMA_SQL)
    # Target session 200 to load.
    c.execute("INSERT INTO sessions (session_id) VALUES (200)")
    c.executemany(
        "INSERT INTO messages (session_id, role, content) VALUES (200, ?, ?)",
        [("user", "stored question"), ("assistant", "stored answer")],
    )
    c.commit()
    yield c


@pytest.fixture
def ctx(conn: sqlite3.Connection) -> Generator[SimpleNamespace]:
    def _make(target: str = "session", db_config=None) -> _FakeSQLiteHelper:  # noqa: ARG001 — factory-signature parity, unused
        return _FakeSQLiteHelper(conn)

    with (
        patch("agent.session.SQLiteHelper", side_effect=_make),
        patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
    ):
        session = AgentSession(db_config=MIN_DB_CONFIG)
        session.start()
        conv = ConversationState()
        conv.system_prompt_content = SYSTEM["content"]
        conv.history = [dict(m) for m in OLD_HISTORY]
        conv.undo_floor = 2
        stats = RuntimeStats(
            stat_turns=4, stat_tool_calls=2, stat_latency={"llm": [1.0]}
        )
        tools = MagicMock()
        yield SimpleNamespace(
            session=session,
            conv=conv,
            turn=TurnState(),
            stats=stats,
            workflow=SimpleNamespace(active=False),
            services=SimpleNamespace(tools=tools),
            services_required=SimpleNamespace(tools=tools),
            diagnostics=None,
        )


def _persister(order: list[str], ctx: SimpleNamespace) -> MagicMock:
    """A persister double that records the live session id each step observes."""
    p = MagicMock()
    p.capture_snapshot.side_effect = lambda: order.append(
        f"capture:{ctx.session.session_id}"
    )
    p.persist_session_memories = AsyncMock(
        side_effect=lambda snap: order.append(f"memories:{ctx.session.session_id}")
    )
    p.persist_session_diagnostics = AsyncMock(
        side_effect=lambda snap: order.append(f"diagnostics:{ctx.session.session_id}")
    )
    return p


def _state_of(ctx: SimpleNamespace) -> tuple:
    return (
        ctx.session.session_id,
        ctx.session.generation,
        [dict(m) for m in ctx.conv.history],
        ctx.conv.undo_floor,
        ctx.stats.stat_turns,
        ctx.stats.stat_tool_calls,
        {k: list(v) for k, v in ctx.stats.stat_latency.items()},
    )


def _service(ctx: SimpleNamespace, order: list[str] | None = None):
    order = [] if order is None else order
    persister = _persister(order, ctx)
    return SessionTransitionService(ctx, persister), persister, order  # type: ignore[arg-type] — SimpleNamespace stands in for AgentContext


class TestLoad:
    async def test_commits_every_field_together(self, ctx: SimpleNamespace) -> None:
        old_gen = ctx.session.generation
        service, _, _ = _service(ctx)

        result = await service.load(200)

        assert result.session_id == 200
        assert (result.fetched, result.synthesized, result.dropped) == (2, 0, 0)
        assert ctx.session.session_id == 200
        assert ctx.session.generation > old_gen
        assert [m["content"] for m in ctx.conv.history] == [
            "Canonical prompt.",
            "stored question",
            "stored answer",
        ]
        assert ctx.conv.undo_floor == 0
        assert ctx.stats.stat_turns == 0
        assert ctx.stats.stat_tool_calls == 0
        assert ctx.stats.stat_latency == {}
        ctx.services.tools.set_session_id.assert_called_once_with("200")

    async def test_old_session_is_finalized_before_the_switch(
        self, ctx: SimpleNamespace
    ) -> None:
        old_id = ctx.session.session_id
        service, _, order = _service(ctx)

        await service.load(200)

        assert order == [
            f"capture:{old_id}",
            f"memories:{old_id}",
            f"diagnostics:{old_id}",
        ]

    async def test_same_snapshot_feeds_both_finalization_steps(
        self, ctx: SimpleNamespace
    ) -> None:
        service, persister, _ = _service(ctx)
        persister.capture_snapshot.side_effect = None
        persister.capture_snapshot.return_value = "one-snapshot"

        await service.load(200)

        persister.capture_snapshot.assert_called_once_with()
        persister.persist_session_memories.assert_awaited_once_with("one-snapshot")
        persister.persist_session_diagnostics.assert_awaited_once_with("one-snapshot")

    async def test_unknown_session_leaves_everything_and_skips_finalization(
        self, ctx: SimpleNamespace
    ) -> None:
        before = _state_of(ctx)
        service, persister, _ = _service(ctx)

        with pytest.raises(SessionNotFoundError):
            await service.load(999)

        assert _state_of(ctx) == before
        persister.persist_session_memories.assert_not_called()

    async def test_build_failure_leaves_the_old_session_unchanged(
        self, ctx: SimpleNamespace
    ) -> None:
        before = _state_of(ctx)
        service, persister, _ = _service(ctx)

        with (
            patch.object(
                ctx.session, "fetch_messages", side_effect=sqlite3.OperationalError("x")
            ),
            pytest.raises(sqlite3.OperationalError),
        ):
            await service.load(200)

        assert _state_of(ctx) == before
        persister.persist_session_memories.assert_not_called()

    async def test_finalization_failure_only_warns_and_the_load_completes(
        self, ctx: SimpleNamespace, caplog: pytest.LogCaptureFixture
    ) -> None:
        service, persister, _ = _service(ctx)
        persister.persist_session_memories.side_effect = RuntimeError("memory down")

        with caplog.at_level(logging.WARNING):
            result = await service.load(200)

        assert result.session_id == 200
        assert ctx.session.session_id == 200
        assert "finalization failed (RuntimeError)" in caplog.text
        assert "memory down" not in caplog.text

    @pytest.mark.parametrize(
        "failing_step",
        ["switch_session", "restore_messages", "reset_stats", "correlation"],
    )
    async def test_commit_failure_restores_the_old_session_completely(
        self, ctx: SimpleNamespace, failing_step: str
    ) -> None:
        before = _state_of(ctx)
        service, _, _ = _service(ctx)
        boom = RuntimeError(f"{failing_step} failed")

        def fail_once(real: Callable) -> Callable:
            calls = {"n": 0}

            async def wrapper(*args, **kwargs):  # noqa: ANN002, ANN003 — generic passthrough
                calls["n"] += 1
                if calls["n"] == 1:
                    raise boom
                return await real(*args, **kwargs)

            return wrapper

        patches = {
            "switch_session": patch.object(
                ctx.session, "switch_session", side_effect=boom
            ),
            "restore_messages": patch.object(
                ctx.conv,
                "restore_messages",
                side_effect=fail_once(ctx.conv.restore_messages),
            ),
            "reset_stats": patch(
                "agent.services.session_transition.reset_session_stats",
                side_effect=boom,
            ),
            "correlation": patch(
                "agent.services.session_transition.refresh_session_correlation",
                side_effect=[boom, None],
            ),
        }
        with patches[failing_step], pytest.raises(RuntimeError) as excinfo:
            await service.load(200)

        assert excinfo.value is boom
        assert _state_of(ctx) == before
        # The correlation id may have moved during the commit; rollback must have
        # pointed it back at the old session as its last act.
        set_calls = ctx.services.tools.set_session_id.call_args_list
        if set_calls:
            assert set_calls[-1].args == (str(before[0]),)

    async def test_rollback_failure_does_not_mask_the_original_error(
        self, ctx: SimpleNamespace
    ) -> None:
        service, _, _ = _service(ctx)
        original = RuntimeError("commit failed")
        with (
            patch.object(ctx.session, "switch_session", side_effect=original),
            patch.object(
                ctx.session, "restore_identity", side_effect=ValueError("rollback")
            ),
            pytest.raises(RuntimeError) as excinfo,
        ):
            await service.load(200)

        assert excinfo.value is original


class TestIdleCheck:
    @pytest.mark.parametrize("operation", ["load", "clear_new"])
    async def test_active_turn_is_refused_without_any_change(
        self, ctx: SimpleNamespace, operation: str
    ) -> None:
        ctx.turn.current_turn_id = "turn-1"
        before = _state_of(ctx)
        service, persister, _ = _service(ctx)

        with pytest.raises(
            SessionTransitionRefusedError, match="turn is still running"
        ):
            await (service.load(200) if operation == "load" else service.clear_new())

        assert _state_of(ctx) == before
        persister.persist_session_memories.assert_not_called()

    async def test_running_workflow_is_refused(self, ctx: SimpleNamespace) -> None:
        ctx.workflow.active = True
        service, _, _ = _service(ctx)

        with pytest.raises(SessionTransitionRefusedError):
            await service.load(200)

    async def test_a_stale_persistence_boundary_does_not_block(
        self, ctx: SimpleNamespace
    ) -> None:
        """UNK-01: the boundary is never cleared after a turn, so it is not the flag."""
        ctx.turn.persistence_boundary = MagicMock()
        service, _, _ = _service(ctx)

        result = await service.load(200)

        assert result.session_id == 200


class TestClearNew:
    async def test_finalizes_the_old_session_then_switches(
        self, ctx: SimpleNamespace
    ) -> None:
        old_id = ctx.session.session_id
        old_gen = ctx.session.generation
        service, _, order = _service(ctx)

        new_id = await service.clear_new()

        assert order == [
            f"capture:{old_id}",
            f"memories:{old_id}",
            f"diagnostics:{old_id}",
        ]
        assert new_id == ctx.session.session_id
        assert new_id != old_id
        assert ctx.session.generation > old_gen
        assert ctx.conv.history == [SYSTEM]
        assert ctx.conv.undo_floor == 0
        assert ctx.stats.stat_turns == 0
        ctx.services.tools.set_session_id.assert_called_once_with(str(new_id))

    async def test_failure_restores_the_old_session_and_removes_the_new_row(
        self, ctx: SimpleNamespace, conn: sqlite3.Connection
    ) -> None:
        before = _state_of(ctx)
        rows_before = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        service, _, _ = _service(ctx)

        with (
            patch(
                "agent.services.session_transition.reset_session_stats",
                side_effect=RuntimeError("stats"),
            ),
            pytest.raises(RuntimeError),
        ):
            await service.clear_new()

        assert _state_of(ctx) == before
        assert (
            conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == rows_before
        )

    async def test_start_failure_leaves_the_old_session_unchanged(
        self, ctx: SimpleNamespace
    ) -> None:
        before = _state_of(ctx)
        service, _, _ = _service(ctx)

        with (
            patch.object(
                ctx.session, "start", side_effect=sqlite3.OperationalError("x")
            ),
            pytest.raises(sqlite3.OperationalError),
        ):
            await service.clear_new()

        assert _state_of(ctx) == before


class TestFinalizationIsNotRepeated:
    """UNK-03: Memory extraction is not idempotent, so a finalized session is marked."""

    async def test_exit_after_a_transition_does_not_finalize_the_same_history_again(
        self, ctx: SimpleNamespace
    ) -> None:
        ctx.cfg = SimpleNamespace(db=MIN_DB_CONFIG)
        ctx.services = SimpleNamespace(
            tools=ctx.services.tools,
            memory=MagicMock(on_session_stop=AsyncMock()),
            llm=None,
            hist_mgr=None,
        )
        persister = SessionPersister(ctx, MagicMock(), MagicMock())  # type: ignore[arg-type] — SimpleNamespace stands in for AgentContext
        service = SessionTransitionService(ctx, persister)  # type: ignore[arg-type] — SimpleNamespace stands in for AgentContext
        old_id = ctx.session.session_id

        await service.load(200)
        ctx.session.restore_identity(
            old_id, ctx.session.generation
        )  # back on the old id
        ctx.conv.history = [dict(m) for m in OLD_HISTORY]
        await persister.persist_session_memories()

        assert ctx.services.memory.on_session_stop.await_count == 1
