"""tests/test_undo_artifact_consistency.py
Regression tests for undo turn -> inspect tool results consistency.

Verifies that tool_result artifacts are marked undone (not deleted) when
undo_last_turn() is called, and remain retrievable via ToolResultStore.get().
"""

from __future__ import annotations

import sqlite3
from types import SimpleNamespace

from agent.services.undo_service import undo_last_turn
from db.tool_results import ToolResultStore

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tool_results (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    turn       INTEGER NOT NULL,
    tool_name  TEXT    NOT NULL,
    args_masked  TEXT,
    full_text  TEXT    NOT NULL,
    summary    TEXT,
    is_error   INTEGER NOT NULL DEFAULT 0,
    undone     INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
"""


class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        pass

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


def _make_store() -> tuple[ToolResultStore, sqlite3.Connection]:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()

    def _make(
        *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:  # noqa: ARG001
        conn.row_factory = sqlite3.Row if row_factory else None
        return _FakeSQLiteHelper(conn)

    store = ToolResultStore()
    store._make_helper = _make  # type: ignore[method-assign]
    return store, conn


def _make_ctx(stat_turns: int = 5, session_id: int = 1) -> SimpleNamespace:
    """Minimal AgentContext with user+assistant history for undo_last_turn."""
    history = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    conv = SimpleNamespace(history=history)
    stats = SimpleNamespace(stat_turns=stat_turns)
    session = SimpleNamespace(session_id=session_id, undo_last_turn=lambda: None)
    return SimpleNamespace(
        conv=conv, stats=stats, session=session, tool_result_store=None
    )


class TestUndoArtifactConsistency:
    def test_undo_marks_tool_result_as_undone(self) -> None:
        """undo_last_turn marks tool_results for the undone turn."""
        store, _ = _make_store()
        row_id = store.store(1, 5, "bash", "{}", "output", "summary", False)

        ctx = _make_ctx(stat_turns=5, session_id=1)
        ctx.tool_result_store = store

        result = undo_last_turn(ctx)
        assert result.n_artifacts_marked == 1
        row = store.get(row_id)
        assert row is not None
        assert row.undone is True

    def test_undo_marks_partial_completion_artifact(self) -> None:
        """Partial-completion artifacts are also marked undone on undo."""
        store, _ = _make_store()
        row_id = store.store(
            1, 5, "llm_partial_completion", "{}", "partial", None, False
        )

        ctx = _make_ctx(stat_turns=5, session_id=1)
        ctx.tool_result_store = store

        result = undo_last_turn(ctx)
        assert result.n_artifacts_marked == 1
        row = store.get(row_id)
        assert row is not None
        assert row.undone is True

    def test_undo_without_tool_calls_marks_zero(self) -> None:
        """Undo with no tool results for that turn returns n_artifacts_marked=0."""
        store, _ = _make_store()
        ctx = _make_ctx(stat_turns=5, session_id=1)
        ctx.tool_result_store = store

        result = undo_last_turn(ctx)
        assert result.n_artifacts_marked == 0

    def test_undo_with_none_store_marks_zero(self) -> None:
        """Undo when tool_result_store is None returns n_artifacts_marked=0."""
        ctx = _make_ctx(stat_turns=5, session_id=1)
        ctx.tool_result_store = None

        result = undo_last_turn(ctx)
        assert result.n_artifacts_marked == 0

    def test_undo_does_not_delete_artifacts(self) -> None:
        """Undone artifacts remain retrievable after undo."""
        store, _ = _make_store()
        row_id = store.store(1, 5, "bash", "{}", "output", "summary", False)

        ctx = _make_ctx(stat_turns=5, session_id=1)
        ctx.tool_result_store = store

        undo_last_turn(ctx)
        row = store.get(row_id)
        assert row is not None
        assert row.tool_name == "bash"

    def test_double_undo_marks_both_turns(self) -> None:
        """Two consecutive undos each mark their respective turn's artifacts."""
        store, _ = _make_store()
        id1 = store.store(1, 5, "tool_a", "{}", "out_a", None, False)
        id2 = store.store(1, 6, "tool_b", "{}", "out_b", None, False)

        history = [
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "rsp1"},
            {"role": "user", "content": "msg2"},
            {"role": "assistant", "content": "rsp2"},
        ]
        conv = SimpleNamespace(history=history)
        stats = SimpleNamespace(stat_turns=6)
        session = SimpleNamespace(session_id=1, undo_last_turn=lambda: None)
        ctx = SimpleNamespace(
            conv=conv, stats=stats, session=session, tool_result_store=store
        )

        undo_last_turn(ctx)
        assert ctx.stats.stat_turns == 5
        undo_last_turn(ctx)
        assert ctx.stats.stat_turns == 4

        assert store.get(id1) is not None and store.get(id1).undone is True  # type: ignore[union-attr]
        assert store.get(id2) is not None and store.get(id2).undone is True  # type: ignore[union-attr]
