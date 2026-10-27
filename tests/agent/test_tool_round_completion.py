"""tests/agent/test_tool_round_completion.py

Batch-ordering pure-function tests plus round-completion persistence tests.

The persistence cases build a real ``AgentSession`` bound to an in-memory SQLite
DB (via a ``_FakeSQLiteHelper`` stand-in for ``SQLiteHelper``) and assert that
``complete_round`` routes its tool-result insert through the turn boundary's
``save_phase_grouped`` variant, and that a single injected failure leaves the
turn clean (all-or-none, AC-005).

Mutation note (T-6): restoring ``tc["id"]`` in ``complete_round()`` (or wrapping the merge
in ``try/except KeyError``) makes the id-less cases below fail, so strict indexing cannot
come back silently.
"""

from __future__ import annotations

import contextlib
import sqlite3
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.context import ConversationState
from agent.session import AgentSession
from agent.session_message_repo import SessionMessageRepository
from agent.tool_enums import ToolCallStopReason
from agent.tool_round_completion import (
    RoundState,
    _merge_in_declared_order,
    complete_round,
)
from agent.turn_persistence import ConversationPersistenceError
from shared.types import LLMMessage


def _row(call_id: str, tag: str = "") -> tuple:
    return (call_id, "tool", {}, tag or call_id, False, "")


class TestMergeInDeclaredOrder:
    def test_entry_without_id_key_takes_the_empty_id_result(self) -> None:
        failure = _row("", "failure")

        merged = _merge_in_declared_order([{"function": {"name": "t"}}], [failure])

        assert merged == [failure]

    def test_id_less_entries_keep_distinct_batch_positions(self) -> None:
        tool_calls = [{}, {"id": "call_b"}, {"id": ""}]
        first, second = _row("", "first"), _row("", "second")
        b = _row("call_b")

        merged = _merge_in_declared_order(tool_calls, [b, first, second])

        assert merged == [first, b, second]

    def test_repeated_real_id_has_one_result_row(self) -> None:
        # Upstream collapses a repeated real id to one collected row (D-3), so only one
        # "x" result can exist for the three declared entries.
        x, y = _row("x"), _row("y")

        merged = _merge_in_declared_order(
            [{"id": "x"}, {"id": "y"}, {"id": "x"}], [x, y]
        )

        assert merged == [x, y]

    def test_unmatched_results_are_appended_last_and_kept(self) -> None:
        zz, a = _row("zz"), _row("a")

        merged = _merge_in_declared_order([{"id": "a"}], [zz, a])

        assert merged == [a, zz]

    def test_valid_unique_id_batches_follow_declared_order(self) -> None:
        a, b, c = _row("a"), _row("b"), _row("c")
        declared = [{"id": "a"}, {"id": "b"}, {"id": "c"}]

        assert _merge_in_declared_order(declared, [a, b, c]) == [a, b, c]
        assert _merge_in_declared_order(declared, [c, a, b]) == [a, b, c]


class TestCompleteRoundPersistence:
    """complete_round routes the round's tool-result persist through the turn
    boundary's grouped variant instead of a standalone save_many (SEQ-08)."""

    @staticmethod
    def _make_ctx() -> MagicMock:
        ctx = MagicMock()
        # Memory advance stays a real append; the DB persist now flows through
        # the turn boundary's begin_immediate transaction (SEQ-08).
        ctx.conv.extend_messages = AsyncMock(return_value=None)
        ctx.turn.persistence_boundary.save_phase_grouped = AsyncMock(return_value=None)
        return ctx

    @staticmethod
    def _state() -> RoundState:
        # One executed call with a real result; declared order is preserved.
        return RoundState(
            declared_ids=["c1"],
            collected={"c1": ("c1", "t", "{}", "r", False, "r")},
        )

    async def test_persists_tool_results_through_boundary(self) -> None:
        ctx = self._make_ctx()

        await complete_round(
            ctx,
            self._state(),
            [{"id": "c1"}],
            0,
            None,
            ToolCallStopReason.GUARD_STOP,
            AsyncMock(return_value=[("tool", "r", None, "c1")]),
        )

        # Memory append is preserved; the DB persist goes through the boundary.
        ctx.conv.extend_messages.assert_awaited_once()
        ctx.turn.persistence_boundary.save_phase_grouped.assert_awaited_once_with(
            [("tool", "r", None, "c1")]
        )

    async def test_no_standalone_save_many_commit(self) -> None:
        ctx = self._make_ctx()

        await complete_round(
            ctx,
            self._state(),
            [{"id": "c1"}],
            0,
            None,
            ToolCallStopReason.GUARD_STOP,
            AsyncMock(return_value=[("tool", "r", None, "c1")]),
        )

        # AC-001: no direct session writes remain in the round path.
        ctx.session.save_many.assert_not_called()
        ctx.session.save.assert_not_called()


# ── Round atomicity (AC-005) ────────────────────────────────────────────────

_ROUND_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT,
    undo_floor_message_id INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    tool_calls TEXT,
    tool_call_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class _FakeSQLiteHelper:
    """Minimal SQLiteHelper stand-in bound to an in-memory connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    @contextlib.contextmanager
    def begin_immediate(self):
        """BEGIN IMMEDIATE ... COMMIT; ROLLBACK and re-raise on exception."""
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def executemany(self, sql: str, params_seq: list) -> sqlite3.Cursor:
        return self._conn.executemany(sql, params_seq)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        pass

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


class TestCompleteRoundRoundAtomicity:
    """A persistence failure in a later round rolls back every earlier round's
    committed rows through the turn boundary, leaving the turn clean (AC-005)."""

    @staticmethod
    def _guarded_ctx(boundary) -> MagicMock:
        ctx = MagicMock()
        ctx.conv.extend_messages = AsyncMock(return_value=None)
        ctx.turn.persistence_boundary = boundary
        return ctx

    @pytest.mark.asyncio
    async def test_later_failure_leaves_no_partial_rows(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(_ROUND_SCHEMA_SQL)
        conn.execute("INSERT INTO sessions (session_id) VALUES (1)")
        conn.commit()
        fake = _FakeSQLiteHelper(conn)
        with (
            patch("agent.session.SQLiteHelper", return_value=fake),
            patch("agent.session_message_repo.SQLiteHelper", return_value=fake),
        ):
            session = AgentSession()
            session.session_id = 1
            session._message_repo = SessionMessageRepository(session_id=1)

            # Pre-turn user row (id 1); the boundary marker is captured after it.
            user_msg: LLMMessage = {"role": "user", "content": "q"}
            session.save(user_msg["role"], user_msg["content"])
            conv = ConversationState()
            conv.history = [user_msg]
            boundary = await session.turn_boundary(conv)

            ctx = self._guarded_ctx(boundary)

            real_spg = session._message_repo.save_phase_grouped  # bound method
            calls = {"n": 0}

            def _counting_spg(messages) -> None:
                # Round 1 (call 1) persists; round 2 (call 2) fails and the
                # boundary compensates every row after the turn-start marker.
                calls["n"] += 1
                if calls["n"] >= 2:
                    raise sqlite3.OperationalError("injected disk failure")
                return real_spg(messages)

            # Both rounds run under the injected-failure wrapper: round 1 commits
            # its tool row (id 2); round 2 fails inside save_phase_grouped and the
            # boundary compensates every row after the turn-start marker.
            with patch.object(
                SessionMessageRepository,
                "save_phase_grouped",
                side_effect=_counting_spg,
            ):
                await complete_round(
                    ctx,
                    RoundState(
                        declared_ids=["c1"],
                        collected={"c1": ("c1", "t", "{}", "r", False, "r")},
                    ),
                    [{"id": "c1"}],
                    0,
                    None,
                    ToolCallStopReason.GUARD_STOP,
                    AsyncMock(return_value=[("tool", "r1", None, "c1")]),
                )

                with pytest.raises(ConversationPersistenceError):
                    await complete_round(
                        ctx,
                        RoundState(
                            declared_ids=["c2"],
                            collected={"c2": ("c2", "t", "{}", "r", False, "r")},
                        ),
                        [{"id": "c2"}],
                        1,
                        None,
                        ToolCallStopReason.GUARD_STOP,
                        AsyncMock(return_value=[("tool", "r2", None, "c2")]),
                    )

            # Round 2's failure compensated round 1's committed row; only the
            # pre-turn user row remains. No partial round rows survive (AC-005).
            rows = conn.execute(
                "SELECT role FROM messages WHERE session_id = 1 ORDER BY message_id"
            ).fetchall()
            assert [r[0] for r in rows] == ["user"]
