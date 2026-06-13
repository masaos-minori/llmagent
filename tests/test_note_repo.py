"""
tests/test_note_repo.py
Behavior-lock tests for NoteRepository.

SQLiteHelper is replaced with an in-memory SQLite connection so no
real DB file is required.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import patch

import pytest
from agent.note_repo import NoteRepository

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS notes (
    note_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    content    TEXT    NOT NULL,
    pinned     INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
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

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

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


@pytest.fixture
def repo() -> Generator[NoteRepository]:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()

    def _make(target: str = "session") -> _FakeSQLiteHelper:
        return _FakeSQLiteHelper(conn)

    with patch("agent.note_repo.SQLiteHelper", side_effect=_make):
        yield NoteRepository()


# ── add_note() ─────────────────────────────────────────────────────────────────


class TestAddNote:
    def test_returns_note_id(self, repo: NoteRepository) -> None:
        note_id = repo.add_note("test content")
        assert isinstance(note_id, int)
        assert note_id > 0

    def test_inserts_into_db(self, repo: NoteRepository) -> None:
        repo.add_note("content A")
        repo.add_note("content B")
        notes = repo.list_notes()
        assert len(notes) == 2

    def test_db_error_raises(self, repo: NoteRepository) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.commit()

        fake = _FakeSQLiteHelper(conn)

        def broken_execute(sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
            raise sqlite3.OperationalError("DB error")

        fake.execute = broken_execute

        def _make(target: str = "session") -> _FakeSQLiteHelper:
            return fake

        with patch("agent.note_repo.SQLiteHelper", side_effect=_make):
            with pytest.raises(sqlite3.OperationalError):
                NoteRepository().add_note("test")


# ── list_notes() ───────────────────────────────────────────────────────────────


class TestListNotes:
    def test_empty_db_returns_empty_list(self, repo: NoteRepository) -> None:
        assert repo.list_notes() == []

    def test_returns_all_notes(self, repo: NoteRepository) -> None:
        repo.add_note("first")
        repo.add_note("second")
        notes = repo.list_notes()
        assert len(notes) == 2
        assert notes[0]["content"] == "first"
        assert notes[1]["content"] == "second"

    def test_returns_correct_keys(self, repo: NoteRepository) -> None:
        repo.add_note("content")
        notes = repo.list_notes()
        assert len(notes) == 1
        assert set(notes[0].keys()) == {"note_id", "content", "pinned", "created_at"}

    def test_ordered_by_note_id_ascending(self, repo: NoteRepository) -> None:
        repo.add_note("A")
        repo.add_note("B")
        repo.add_note("C")
        notes = repo.list_notes()
        ids = [n["note_id"] for n in notes]
        assert ids == sorted(ids)

    def test_db_error_raises(self, repo: NoteRepository) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.commit()

        fake = _FakeSQLiteHelper(conn)
        fake.fetchall = lambda sql, params=None: (_ for _ in ()).throw(
            sqlite3.OperationalError("DB error")
        )

        def _make(target: str = "session") -> _FakeSQLiteHelper:
            return fake

        with patch("agent.note_repo.SQLiteHelper", side_effect=_make):
            with pytest.raises(sqlite3.OperationalError):
                NoteRepository().list_notes()


# ── delete_note() ──────────────────────────────────────────────────────────────


class TestDeleteNote:
    def test_not_found_returns_false(self, repo: NoteRepository) -> None:
        assert repo.delete_note(999) is False

    def test_found_deletes_and_returns_true(self, repo: NoteRepository) -> None:
        note_id = repo.add_note("to delete")
        assert note_id is not None
        result = repo.delete_note(note_id)
        assert result is True
        assert repo.list_notes() == []

    def test_db_error_on_select_raises(self, repo: NoteRepository) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.execute("INSERT INTO notes (content) VALUES (?)", ("test",))
        conn.commit()

        fake = _FakeSQLiteHelper(conn)
        real_execute = fake.execute

        def broken_execute(sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
            if "SELECT note_id FROM notes" in sql and "DELETE" not in sql:
                raise sqlite3.OperationalError("DB error")
            return real_execute(sql, params)

        fake.execute = broken_execute

        def _make(target: str = "session") -> _FakeSQLiteHelper:
            return fake

        with patch("agent.note_repo.SQLiteHelper", side_effect=_make):
            with pytest.raises(sqlite3.OperationalError):
                NoteRepository().delete_note(1)


# ── get_all_note_contents() ────────────────────────────────────────────────────


class TestGetAllNoteContents:
    def test_empty_db_returns_empty_list(self, repo: NoteRepository) -> None:
        assert repo.get_all_note_contents() == []

    def test_returns_contents_in_order(self, repo: NoteRepository) -> None:
        repo.add_note("content C")
        repo.add_note("content A")
        repo.add_note("content B")
        contents = repo.get_all_note_contents()
        assert contents == ["content C", "content A", "content B"]

    def test_db_error_raises(self, repo: NoteRepository) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.commit()

        fake = _FakeSQLiteHelper(conn)
        fake.fetchall = lambda sql, params=None: (_ for _ in ()).throw(
            sqlite3.OperationalError("DB error")
        )

        def _make(target: str = "session") -> _FakeSQLiteHelper:
            return fake

        with patch("agent.note_repo.SQLiteHelper", side_effect=_make):
            with pytest.raises(sqlite3.OperationalError):
                NoteRepository().get_all_note_contents()


# ── pin_note() / unpin_note() ──────────────────────────────────────────────────


class TestPinNote:
    def test_pin_returns_true_when_found(self, repo: NoteRepository) -> None:
        note_id = repo.add_note("pinnable")
        assert repo.pin_note(note_id) is True

    def test_pin_sets_pinned_flag(self, repo: NoteRepository) -> None:
        note_id = repo.add_note("pinnable")
        repo.pin_note(note_id)
        notes = repo.list_notes()
        assert notes[0]["pinned"] == 1

    def test_pin_returns_false_for_unknown_id(self, repo: NoteRepository) -> None:
        assert repo.pin_note(9999) is False


class TestUnpinNote:
    def test_unpin_returns_true_when_found(self, repo: NoteRepository) -> None:
        note_id = repo.add_note("pinnable")
        repo.pin_note(note_id)
        assert repo.unpin_note(note_id) is True

    def test_unpin_clears_pinned_flag(self, repo: NoteRepository) -> None:
        note_id = repo.add_note("pinnable")
        repo.pin_note(note_id)
        repo.unpin_note(note_id)
        notes = repo.list_notes()
        assert notes[0]["pinned"] == 0

    def test_unpin_returns_false_for_unknown_id(self, repo: NoteRepository) -> None:
        assert repo.unpin_note(9999) is False


# ── get_pinned_notes() ────────────────────────────────────────────────────────


class TestGetPinnedNotes:
    def test_empty_returns_empty(self, repo: NoteRepository) -> None:
        repo.add_note("not pinned")
        assert repo.get_pinned_notes() == []

    def test_returns_only_pinned(self, repo: NoteRepository) -> None:
        nid1 = repo.add_note("pinned note")
        repo.add_note("not pinned")
        repo.pin_note(nid1)
        pinned = repo.get_pinned_notes()
        assert len(pinned) == 1
        assert pinned[0]["note_id"] == nid1
        assert pinned[0]["pinned"] == 1

    def test_result_has_correct_keys(self, repo: NoteRepository) -> None:
        nid = repo.add_note("content")
        repo.pin_note(nid)
        pinned = repo.get_pinned_notes()
        assert set(pinned[0].keys()) == {"note_id", "content", "pinned", "created_at"}


# ── search_notes() ────────────────────────────────────────────────────────────


class TestSearchNotes:
    def test_returns_matching_notes(self, repo: NoteRepository) -> None:
        repo.add_note("Python tips")
        repo.add_note("Java guide")
        results = repo.search_notes("Python")
        assert len(results) == 1
        assert results[0]["content"] == "Python tips"

    def test_empty_when_no_match(self, repo: NoteRepository) -> None:
        repo.add_note("Python tips")
        assert repo.search_notes("Rust") == []

    def test_limit_respected(self, repo: NoteRepository) -> None:
        for i in range(10):
            repo.add_note(f"note {i}")
        results = repo.search_notes("note", limit=3)
        assert len(results) == 3

    def test_escapes_like_metacharacters(self, repo: NoteRepository) -> None:
        repo.add_note("50% discount")
        repo.add_note("other note")
        results = repo.search_notes("50%")
        assert len(results) == 1
        assert results[0]["content"] == "50% discount"
