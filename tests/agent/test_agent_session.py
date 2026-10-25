"""
tests/test_agent_session.py
Behavior-lock tests for AgentSession.

Covers: start, save, save_many, fetch_messages, set_title,
        list_sessions, delete_session.
SQLiteHelper is replaced with an in-memory SQLite connection so no
real DB file or sqlite-vec extension is required.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from unittest.mock import patch

import pytest
from agent.session import AgentSession, SchemaMissingError


def _msgs(result):
    """Unwrap (messages, session_found) tuple returned by fetch_messages."""
    if isinstance(result, tuple):
        return result[0]
    return result


# ── In-memory SQLiteHelper replacement ───────────────────────────────────────

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT,
    undo_floor_message_id INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    tool_calls TEXT,
    tool_call_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_write_lock = Lock()


class _FakeSQLiteHelper:
    """Minimal SQLiteHelper drop-in backed by a real in-memory SQLite connection."""

    _initialized_conns: set[int] = set()

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        conn_id = id(self._conn)
        if conn_id not in _FakeSQLiteHelper._initialized_conns:
            with _write_lock:
                if conn_id not in _FakeSQLiteHelper._initialized_conns:
                    self._conn.executescript(_SCHEMA_SQL)
                    _FakeSQLiteHelper._initialized_conns.add(conn_id)
        return self._conn.execute(sql, params)

    @classmethod
    def reset(cls) -> None:
        cls._initialized_conns.clear()

    def executemany(self, sql: str, params_seq: list) -> sqlite3.Cursor:
        return self._conn.executemany(sql, params_seq)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    @contextmanager
    def write_transaction(
        self, sql: str, params: tuple = ()
    ) -> Generator[sqlite3.Cursor]:
        with _write_lock:
            cur = self._conn.execute(sql, params)
            yield cur
            self._conn.commit()

    def commit(self) -> None:
        with _write_lock:
            self._conn.commit()

    def close(self) -> None:
        pass  # keep alive for the test lifetime

    @contextmanager
    def begin_immediate(self) -> Generator[None]:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._conn.execute("COMMIT")
        except Exception:
            try:
                self._conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


@pytest.fixture(autouse=True)
def reset_fake_helper() -> Generator[None]:
    """Reset class-level state before each test."""
    _FakeSQLiteHelper.reset()
    yield


@pytest.fixture
def session() -> Generator[AgentSession]:
    """AgentSession wired to a fresh in-memory SQLite DB."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")  # enable cascade deletes
    conn.executescript(_SCHEMA_SQL)
    conn.execute("INSERT INTO sessions (session_id) VALUES (1)")
    conn.commit()

    def _make(target: str = "rag") -> _FakeSQLiteHelper:  # noqa: ARG001
        return _FakeSQLiteHelper(conn)

    with (
        patch("agent.session.SQLiteHelper", side_effect=_make),
        patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
    ):
        yield AgentSession()


# ── start() ───────────────────────────────────────────────────────────────────


class TestStart:
    def test_sets_session_id(self, session: AgentSession) -> None:
        assert session.session_id is None
        session.start()
        assert session.session_id is not None
        assert isinstance(session.session_id, int)

    def test_inserts_row_in_sessions(self, session: AgentSession) -> None:
        session.start()
        # Verify via list_sessions: doesn't raise
        session.list_sessions()

    def test_multiple_starts_increment_id(self, session: AgentSession) -> None:
        session.start()
        first_id = session.session_id
        session.start()
        assert session.session_id != first_id


# ── save() ────────────────────────────────────────────────────────────────────


class TestStartSchemaMissingFallback:
    """Regression coverage for start()'s OperationalError fallback."""

    @staticmethod
    def _real_no_such_table_error() -> sqlite3.OperationalError:
        conn = sqlite3.connect(":memory:")
        try:
            conn.execute("INSERT INTO sessions (title) VALUES (NULL)")
        except sqlite3.OperationalError as err:
            return err  # genuine object: carries sqlite_errorcode / sqlite_errorname
        finally:
            conn.close()
        raise AssertionError("expected OperationalError was not raised")

    class _ExplodingHelper(_FakeSQLiteHelper):
        """Fake helper whose sessions INSERT raises a stored error."""

        injected: sqlite3.OperationalError

        def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
            if "INSERT INTO sessions" in sql:
                raise self.injected
            return super().execute(sql, params)

    def _make_exploding(self, error: sqlite3.OperationalError):
        conn = sqlite3.connect(":memory:")

        def _make(name: str = "session") -> TestStartSchemaMissingFallback._ExplodingHelper:
            helper = TestStartSchemaMissingFallback._ExplodingHelper(conn)
            helper.injected = error
            return helper

        return _make

    def test_fallback_converts_schema_error_after_preflight(self) -> None:
        with patch(
            "agent.session.SQLiteHelper",
            side_effect=self._make_exploding(self._real_no_such_table_error()),
        ):
            s = AgentSession()
            with pytest.raises(SchemaMissingError, match="Session schema missing"):
                s.start()

    def test_non_schema_operational_error_propagates(self) -> None:
        with patch(
            "agent.session.SQLiteHelper",
            side_effect=self._make_exploding(
                sqlite3.OperationalError("table sessions is locked")
            ),
        ):
            s = AgentSession()
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                s.start()

    def test_real_db_missing_schema_raises_schema_missing(self, tmp_path: Path) -> None:
        from db.helper import SQLiteHelper

        with patch(
            "agent.session.SQLiteHelper",
            side_effect=lambda _name: SQLiteHelper(
                "session", db_path=str(tmp_path / "unseeded.db")
            ),
        ):
            s = AgentSession()
            with pytest.raises(SchemaMissingError, match="Session schema missing"):
                s.start()


class TestSave:
    def test_saves_user_message(self, session: AgentSession) -> None:
        session.start()
        session.save("user", "hello")
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "hello"

    def test_saves_assistant_message(self, session: AgentSession) -> None:
        session.start()
        session.save("assistant", "world")
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert msgs[0]["role"] == "assistant"

    def test_saves_tool_calls_json(self, session: AgentSession) -> None:
        session.start()
        tcs = [
            {
                "id": "tc1",
                "type": "function",
                "function": {"name": "f", "arguments": "{}"},
            }
        ]
        session.save("assistant", "", tool_calls=tcs)
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert msgs[0].get("tool_calls") == tcs

    def test_saves_tool_call_id(self, session: AgentSession) -> None:
        session.start()
        session.save("tool", "result text", tool_call_id="tc1")
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert msgs[0]["role"] == "tool"
        assert msgs[0].get("tool_call_id") == "tc1"

    def test_no_op_when_session_id_none(self, session: AgentSession) -> None:
        # No start() called — session_id is None
        session.save("user", "orphan")
        # No error; nothing written (session_id is None → early return)
        assert session.skipped_no_session_count == 1

    def test_invalid_role_is_skipped(self, session: AgentSession) -> None:
        session.start()
        session.save("invalid_role", "content")
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is None or len(msgs) == 0
        assert session.skipped_invalid_role_count == 1


# ── save_many() ───────────────────────────────────────────────────────────────


class TestSaveMany:
    def test_saves_multiple_messages(self, session: AgentSession) -> None:
        session.start()
        rows: list[tuple[str, str | None, list[dict] | None, str | None]] = [
            ("tool", "result A", None, "tc1"),
            ("tool", "result B", None, "tc2"),
        ]
        session.save_many(rows)
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert len(msgs) == 2
        assert msgs[0]["content"] == "result A"
        assert msgs[0].get("tool_call_id") == "tc1"
        assert msgs[1].get("tool_call_id") == "tc2"

    def test_no_op_when_empty(self, session: AgentSession) -> None:
        session.start()
        session.save_many([])  # should not raise

    def test_no_op_when_session_id_none(self, session: AgentSession) -> None:
        session.save_many([("user", "orphan", None, None)])  # no error

    def test_filters_invalid_roles(self, session: AgentSession) -> None:
        session.start()
        rows: list[tuple[str, str | None, list[dict] | None, str | None]] = [
            ("user", "valid", None, None),
            ("bad_role", "invalid", None, None),
        ]
        session.save_many(rows)
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"


# ── fetch_messages() ──────────────────────────────────────────────────────────


class TestFetchMessages:
    def test_returns_messages_in_order(self, session: AgentSession) -> None:
        session.start()
        session.save("user", "first")
        session.save("assistant", "second")
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_returns_empty_for_unknown_session(self, session: AgentSession) -> None:
        result = _msgs(session.fetch_messages(99999))
        assert result == []

    def test_tool_call_id_restored(self, session: AgentSession) -> None:
        session.start()
        session.save("tool", "content", tool_call_id="abc-123")
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert msgs[0].get("tool_call_id") == "abc-123"

    def test_tool_call_id_absent_when_null(self, session: AgentSession) -> None:
        session.start()
        session.save("user", "no tool_call_id")
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert "tool_call_id" not in msgs[0]

    def test_tool_calls_json_roundtrip(self, session: AgentSession) -> None:
        session.start()
        tcs = [
            {
                "id": "x",
                "type": "function",
                "function": {"name": "g", "arguments": "{}"},
            }
        ]
        session.save("assistant", "ok", tool_calls=tcs)
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert msgs[0]["tool_calls"] == tcs

    def test_invalid_tool_calls_json_skipped(self, session: AgentSession) -> None:
        # Directly insert a corrupted tool_calls value
        session.start()
        session.save("assistant", "text")
        # Corrupt the tool_calls column post-insert
        with patch("agent.session.SQLiteHelper") as mock_cls:
            conn = sqlite3.connect(":memory:")
            conn.executescript(_SCHEMA_SQL)
            conn.commit()
            conn.execute("INSERT INTO sessions DEFAULT VALUES")
            conn.commit()
            sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls)"
                " VALUES (?, 'assistant', 'bad', 'NOT_JSON')",
                (sid,),
            )
            conn.commit()
            mock_cls.side_effect = lambda target="rag": _FakeSQLiteHelper(conn)  # noqa: ARG005
            s2 = AgentSession()
            s2.session_id = sid
            msgs = _msgs(s2.fetch_messages(sid))
        # Corrupted row should still return without KeyError; tool_calls absent
        assert msgs is not None
        assert "tool_calls" not in (msgs[0] if msgs else {})

    def test_returns_three_tuple_with_boundary(self, session: AgentSession) -> None:
        session.start()
        session.save("user", "q1")
        messages, found, floor = session.fetch_messages(
            session.session_id  # type: ignore[arg-type]
        )
        assert found is True
        assert isinstance(floor, int)
        assert len(messages) == 1


# ── set_title() ───────────────────────────────────────────────────────────────


class TestSetTitle:
    def test_updates_title(self, session: AgentSession) -> None:
        session.start()
        session.set_title("My Session")
        rows = session.list_sessions()
        assert any(r["title"] == "My Session" for r in rows)

    def test_stores_at_max_chars(self, session: AgentSession) -> None:
        session.start()
        session.set_title("A" * 100)
        rows = session.list_sessions()
        # title is stored at the canonical max (32) chars
        assert any(len(r["title"] or "") == 32 for r in rows)
        stored = next(r["title"] for r in rows if r["title"])
        assert len(stored) == 32

    def test_no_op_when_session_id_none(self, session: AgentSession) -> None:
        session.set_title("ghost")  # should not raise


# ── list_sessions() ───────────────────────────────────────────────────────────


class TestListSessions:
    def test_returns_sessions_when_exist(self, session: AgentSession) -> None:
        session.start()
        rows = session.list_sessions()
        assert len(rows) > 0
        assert "session_id" in rows[0]

    def test_returns_empty_list_when_no_sessions(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(_SCHEMA_SQL)
        conn.commit()

        def _make(target: str = "rag") -> _FakeSQLiteHelper:  # noqa: ARG001
            return _FakeSQLiteHelper(conn)

        with (
            patch("agent.session.SQLiteHelper", side_effect=_make),
            patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
        ):
            s = AgentSession()
            rows = s.list_sessions()
            assert rows == []

    def test_marks_current_session(self, session: AgentSession) -> None:
        session.start()
        rows = session.list_sessions()
        assert any(r["is_current"] for r in rows)

    def test_message_count_counts_messages_per_session(
        self, session: AgentSession
    ) -> None:
        session.start()
        session.save("user", "a")
        session.save("user", "b")
        rows = {r["session_id"]: r for r in session.list_sessions()}
        sid = session.session_id
        assert sid is not None
        assert rows[sid]["message_count"] == 2
        assert rows[1]["message_count"] == 0


# ── delete_session() ─────────────────────────────────────────────────────────


class TestDeleteSession:
    def test_returns_true_on_success(self, session: AgentSession) -> None:
        session.start()
        sid = session.session_id
        result = session.delete_session(sid)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert result is True

    def test_returns_false_for_unknown_id(self, session: AgentSession) -> None:
        result = session.delete_session(99999)
        assert result is False

    def test_cascades_to_messages(self, session: AgentSession) -> None:
        session.start()
        sid = session.session_id
        session.save("user", "to be deleted")
        session.delete_session(sid)  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        # After deletion, fetch_messages returns [] (no messages in DB)
        msgs = _msgs(session.fetch_messages(sid))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs == []


# ── TestSessionIdConcurrency ──────────────────────────────────────────────────


class TestSessionIdConcurrency:
    """Tests for concurrent session_id generation via AgentSession.start()."""

    def test_concurrent_starts_produce_unique_ids(self, tmp_path: Path) -> None:
        db_path = tmp_path / "sessions.db"

        with (
            patch(
                "agent.session.SQLiteHelper",
                side_effect=lambda target: _FakeSQLiteHelper(
                    sqlite3.connect(str(db_path), check_same_thread=False, timeout=5)
                ),
            ),
            patch(
                "agent.session_message_repo.SQLiteHelper",
                side_effect=lambda target: _FakeSQLiteHelper(
                    sqlite3.connect(str(db_path), check_same_thread=False, timeout=5)
                ),
            ),
        ):
            from concurrent.futures import ThreadPoolExecutor

            def _make_and_start(_: int = 0) -> AgentSession:
                s = AgentSession()
                s.start()
                return s

            with ThreadPoolExecutor(max_workers=4) as executor:
                sessions = list(executor.map(_make_and_start, range(8)))

        ids = [s.session_id for s in sessions]
        assert all(isinstance(sid, int) for sid in ids)
        assert len(set(ids)) == 8

    def test_concurrent_starts_all_persisted(self, tmp_path: Path) -> None:
        db_path = tmp_path / "sessions.db"

        with (
            patch(
                "agent.session.SQLiteHelper",
                side_effect=lambda target: _FakeSQLiteHelper(
                    sqlite3.connect(str(db_path), check_same_thread=False, timeout=5)
                ),
            ),
            patch(
                "agent.session_message_repo.SQLiteHelper",
                side_effect=lambda target: _FakeSQLiteHelper(
                    sqlite3.connect(str(db_path), check_same_thread=False, timeout=5)
                ),
            ),
        ):
            from concurrent.futures import ThreadPoolExecutor

            def _make_and_start(_: int = 0) -> AgentSession:
                s = AgentSession()
                s.start()
                return s

            with ThreadPoolExecutor(max_workers=4) as executor:
                list(executor.map(_make_and_start, range(8)))

        conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=5)
        count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        assert count == 8


# ── undo_last_turn() ──────────────────────────────────────────────────────────


class TestUndoLastTurn:
    def test_removes_from_last_user_message(self, session: AgentSession) -> None:
        session.start()
        session.save("user", "q1")
        session.save("assistant", "a1")
        session.save("user", "q2")
        session.save("assistant", "a2")
        deleted = session.undo_last_turn()
        assert deleted == 2
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert len(msgs) == 2
        assert msgs[0]["content"] == "q1"
        assert msgs[1]["content"] == "a1"

    def test_with_tool_result_messages(self, session: AgentSession) -> None:
        session.start()
        session.save("user", "q1")
        session.save("assistant", "a1")
        session.save("tool", "result1", tool_call_id="tc1")
        session.save("user", "q2")
        deleted = session.undo_last_turn()
        assert deleted == 1
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs is not None
        assert len(msgs) == 3

    def test_no_op_when_no_user_message(self, session: AgentSession) -> None:
        session.start()
        session.save("assistant", "a1")
        deleted = session.undo_last_turn()
        assert deleted == 0

    def test_no_op_when_session_id_none(self, session: AgentSession) -> None:
        deleted = session.undo_last_turn()
        assert deleted == 0

    def test_no_op_when_empty_history(self, session: AgentSession) -> None:
        session.start()
        deleted = session.undo_last_turn()
        assert deleted == 0


class TestReplaceMessages:
    def test_returns_none_before_start(self) -> None:
        session = AgentSession()
        assert session.replace_messages([{"role": "user", "content": "x"}]) is None

    def test_returns_boundary_after_rewrite(self, session: AgentSession) -> None:
        session.start()
        boundary = session.replace_messages([{"role": "user", "content": "hi"}])
        assert isinstance(boundary, int)
        assert boundary >= 1


class TestUndoLastTurnBoundary:
    """DB-boundary gate for undo_last_turn (rows 02/03)."""

    def test_blocks_when_last_user_at_or_before_boundary(self) -> None:
        import sqlite3
        from unittest.mock import patch

        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.commit()

        def _make(target: str = "session") -> _FakeSQLiteHelper:
            return _FakeSQLiteHelper(conn)

        with (
            patch("agent.session.SQLiteHelper", side_effect=_make),
            patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
        ):
            session = AgentSession()
            session.start()
            sid = session.session_id
            session.save("user", "q1")
            session.save("assistant", "a1")
            session.save("user", "q2")
            session.save("assistant", "a2")
            conn.execute(
                "UPDATE sessions SET undo_floor_message_id = ? WHERE session_id = ?",
                (3, sid),
            )
            conn.commit()
            # q2 lives at message_id 3 == boundary: nothing undoable
            assert session.undo_last_turn() == 0
            rows = _msgs(session.fetch_messages(sid))  # type: ignore[arg-type]
            assert rows is not None
            assert len(rows) == 4

    def test_deletes_only_last_turn_beyond_boundary(self) -> None:
        import sqlite3
        from unittest.mock import patch

        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.commit()

        def _make(target: str = "session") -> _FakeSQLiteHelper:
            return _FakeSQLiteHelper(conn)

        with (
            patch("agent.session.SQLiteHelper", side_effect=_make),
            patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
        ):
            session = AgentSession()
            session.start()
            sid = session.session_id
            session.save("user", "q1")
            session.save("assistant", "a1")
            session.save("user", "q2")
            session.save("assistant", "a2")
            conn.execute(
                "UPDATE sessions SET undo_floor_message_id = ? WHERE session_id = ?",
                (1, sid),
            )
            conn.commit()
            # boundary at id 1: only q2(3)/a2(4) are undoable
            assert session.undo_last_turn() == 2
            rows = _msgs(session.fetch_messages(sid))  # type: ignore[arg-type]
            assert rows is not None
            assert [m["content"] for m in rows] == ["q1", "a1"]


# ── TestAgentSessionRagBoundary ────────────────────────────────────────────────


class TestAgentSessionRagBoundary:
    """Confirm AgentSession has zero RAG-layer imports."""

    def test_session_has_no_rag_imports(self) -> None:
        import ast
        import pathlib

        src = pathlib.Path(__file__).parent.parent.parent / "scripts/agent/session.py"
        tree = ast.parse(src.read_text())
        rag_imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            and any(
                (alias.name or "").startswith("rag")
                or getattr(node, "module", "").startswith("rag")
                for alias in getattr(node, "names", [])
            )
        ]
        assert not rag_imports, (
            f"AgentSession must not import from rag.*; found: {rag_imports}"
        )

    def test_delete_last_turn_absent_from_facade(self) -> None:
        # Row 03 removed AgentSession.delete_last_turn; no such attribute remains.
        assert not hasattr(AgentSession, "delete_last_turn")


class TestSaveDiagnosticIsolation:
    """Tests verifying that save_diagnostic() writes to DiagnosticStore, not messages."""

    def test_save_diagnostic_does_not_write_to_messages(
        self, session: AgentSession
    ) -> None:
        from unittest.mock import MagicMock

        session.start()
        diag_mock = MagicMock()
        session._diagnostic_store = diag_mock
        session.save_diagnostic("test diagnostic content")
        diag_mock.save.assert_called_once()
        # Verify messages table is not touched
        msgs = _msgs(session.fetch_messages(session.session_id))  # type: ignore[arg-type]  # session_id narrowed by start() but typed int | None
        assert msgs == []

    def test_save_diagnostic_calls_diagnostic_store_with_kind(
        self, session: AgentSession
    ) -> None:
        from unittest.mock import MagicMock

        session.start()
        diag_mock = MagicMock()
        session._diagnostic_store = diag_mock
        session.save_diagnostic("error detail")
        call_kwargs = diag_mock.save.call_args
        assert call_kwargs is not None
        # kind should be "llm_transport_error"
        args, kwargs = call_kwargs
        assert (
            "llm_transport_error" in args or kwargs.get("kind") == "llm_transport_error"
        )
