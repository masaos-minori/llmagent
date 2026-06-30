"""tests/test_db_store_impl.py
Unit tests for db/store_impl.py:
SQLiteDocumentStore, SQLiteSessionStore, SQLiteVectorStore, SQLiteMemoryDeleteStore.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, patch

import pytest
from db.store_impl import (
    SQLiteDocumentStore,
    SQLiteMemoryDeleteStore,
    SQLiteSessionStore,
    SQLiteVectorStore,
)

# ── In-memory DB helper ───────────────────────────────────────────────────────

_DOCUMENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    url          TEXT NOT NULL UNIQUE,
    title        TEXT,
    lang         TEXT NOT NULL,
    etag         TEXT,
    last_modified TEXT,
    fetched_at   TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id             INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    chunk_index        INTEGER,
    content            TEXT NOT NULL,
    normalized_content TEXT
);
"""

_SESSION_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title      TEXT
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


class _FakeDB:
    """Minimal SQLiteHelper drop-in backed by an in-memory SQLite connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        return self.conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self.conn.commit()


def _make_doc_db() -> _FakeDB:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_DOCUMENT_SCHEMA)
    return _FakeDB(conn)


def _make_session_db() -> _FakeDB:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SESSION_SCHEMA)
    return _FakeDB(conn)


# ── SQLiteDocumentStore ───────────────────────────────────────────────────────


class TestSQLiteDocumentStore:
    def test_doc_get_returns_none_for_nonexistent_url(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        result = store.doc_get("http://nonexistent.example.com")
        assert result is None

    def test_doc_upsert_new_url_returns_positive_id(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        doc_id = store.doc_upsert("http://example.com", "Title", "en", None, None)
        assert isinstance(doc_id, int)
        assert doc_id >= 1

    def test_doc_upsert_and_get_roundtrip(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert("http://example.com", "My Title", "ja", "etag1", None)
        result = store.doc_get("http://example.com")
        assert result is not None
        assert result.url == "http://example.com"
        assert result.title == "My Title"
        assert result.lang == "ja"
        assert isinstance(result.lang, str)

    def test_doc_get_returns_lang_as_str(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert("http://example.com", "My Title", "en", "etag1", None)
        result = store.doc_get("http://example.com")
        assert isinstance(result.lang, str)

    def test_chunk_count_starts_at_zero(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        assert store.chunk_count() == 0

    def test_chunk_insert_increments_count(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        doc_id = store.doc_upsert("http://example.com", None, "en", None, None)
        store.chunk_insert(doc_id, 0, "first chunk content", None)
        assert store.chunk_count() == 1
        store.chunk_insert(doc_id, 1, "second chunk content", "normalized")
        assert store.chunk_count() == 2

    def test_doc_delete_removes_document_and_returns_true(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert("http://example.com", "Title", "en", None, None)
        deleted = store.doc_delete("http://example.com")
        assert deleted is True
        assert store.doc_get("http://example.com") is None

    def test_doc_delete_nonexistent_returns_false(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        deleted = store.doc_delete("http://nowhere.example.com")
        assert deleted is False

    def test_doc_list_returns_inserted_documents(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert("http://a.com", "A", "en", None, None)
        store.doc_upsert("http://b.com", "B", "ja", None, None)
        rows = store.doc_list(lang=None, limit=10)
        assert len(rows) == 2
        urls = {r.url for r in rows}
        assert "http://a.com" in urls
        assert "http://b.com" in urls

    def test_doc_list_filtered_by_lang(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert("http://a.com", "A", "en", None, None)
        store.doc_upsert("http://b.com", "B", "ja", None, None)
        rows = store.doc_list(lang="ja", limit=10)
        assert len(rows) == 1
        assert rows[0].url == "http://b.com"

    def test_doc_list_returns_lang_as_str(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert("http://a.com", "A", "en", None, None)
        store.doc_upsert("http://b.com", "B", "ja", None, None)
        rows = store.doc_list(lang=None, limit=10)
        assert all(isinstance(r.lang, str) for r in rows)


# ── SQLiteSessionStore ────────────────────────────────────────────────────────


class TestSQLiteSessionStore:
    def test_session_create_returns_positive_int(self) -> None:
        store = SQLiteSessionStore(_make_session_db())  # type: ignore[arg-type]
        sid = store.session_create()
        assert isinstance(sid, int)
        assert sid >= 1

    def test_session_create_increments(self) -> None:
        store = SQLiteSessionStore(_make_session_db())  # type: ignore[arg-type]
        sid1 = store.session_create()
        sid2 = store.session_create()
        assert sid2 > sid1

    def test_session_list_shows_created_session(self) -> None:
        store = SQLiteSessionStore(_make_session_db())  # type: ignore[arg-type]
        store.session_create()
        rows = store.session_list(limit=10)
        assert len(rows) == 1
        assert rows[0].session_id >= 1

    def test_message_save_and_list(self) -> None:
        store = SQLiteSessionStore(_make_session_db())  # type: ignore[arg-type]
        sid = store.session_create()
        store.message_save(sid, "user", "hello", None)
        store.message_save(sid, "assistant", "world", None)
        msgs = store.message_list(sid)
        assert len(msgs) == 2
        assert msgs[0].role == "user"
        assert msgs[0].content == "hello"
        assert msgs[1].role == "assistant"

    def test_session_rename_updates_title(self) -> None:
        store = SQLiteSessionStore(_make_session_db())  # type: ignore[arg-type]
        sid = store.session_create()
        store.session_rename(sid, "My Session")
        rows = store.session_list(limit=10)
        assert rows[0].title == "My Session"

    def test_session_delete_removes_session(self) -> None:
        store = SQLiteSessionStore(_make_session_db())  # type: ignore[arg-type]
        sid = store.session_create()
        store.session_delete(sid)
        rows = store.session_list(limit=10)
        assert len(rows) == 0

    def test_message_list_empty_for_unknown_session(self) -> None:
        store = SQLiteSessionStore(_make_session_db())  # type: ignore[arg-type]
        msgs = store.message_list(99999)
        assert msgs == []

    def test_message_save_with_tool_call_id_round_trips(self) -> None:
        store = SQLiteSessionStore(_make_session_db())  # type: ignore[arg-type]
        sid = store.session_create()
        store.message_save(sid, "tool", "", None, tool_call_id="call_abc123")
        msgs = store.message_list(sid)
        assert len(msgs) == 1
        assert msgs[0].tool_call_id == "call_abc123"

    def test_message_save_default_tool_call_id_is_none(self) -> None:
        store = SQLiteSessionStore(_make_session_db())  # type: ignore[arg-type]
        sid = store.session_create()
        store.message_save(sid, "user", "hello", None)
        msgs = store.message_list(sid)
        assert len(msgs) == 1
        assert msgs[0].tool_call_id is None


# ── SQLiteVectorStore ─────────────────────────────────────────────────────────


class TestSQLiteVectorStore:
    def test_vec_count_delegates_to_db(self) -> None:
        mock_db = MagicMock()
        mock_db.fetchall.return_value = [(7,)]
        store = SQLiteVectorStore(mock_db)
        assert store.vec_count() == 7

    def test_vec_count_empty_result_returns_zero(self) -> None:
        mock_db = MagicMock()
        mock_db.fetchall.return_value = []
        store = SQLiteVectorStore(mock_db)
        assert store.vec_count() == 0

    def test_vec_delete_calls_execute_with_chunk_id(self) -> None:
        mock_db = MagicMock()
        store = SQLiteVectorStore(mock_db)
        store.vec_delete(42)
        mock_db.execute.assert_called_once_with(
            "DELETE FROM chunks_vec WHERE chunk_id = ?", (42,)
        )

    def test_vec_insert_raises_type_error_for_non_bytes(self) -> None:
        mock_db = MagicMock()
        store = SQLiteVectorStore(mock_db)
        with pytest.raises(TypeError):
            store.vec_insert(1, "not bytes")  # type: ignore[arg-type]

    def test_vec_insert_with_valid_blob_delegates_to_execute(self) -> None:
        mock_db = MagicMock()
        store = SQLiteVectorStore(mock_db)
        blob = b"\x00" * (384 * 4)
        with patch("db.store_impl.validate_embedding_blob"):
            store.vec_insert(1, blob)
        mock_db.execute.assert_called_once()

    def test_vec_search_with_valid_blob_returns_pairs(self) -> None:
        mock_db = MagicMock()
        mock_db.fetchall.return_value = [(1, 0.5), (2, 0.8)]
        store = SQLiteVectorStore(mock_db)
        blob = b"\x00" * (384 * 4)
        with patch("db.store_impl.validate_embedding_blob"):
            results = store.vec_search(blob, k=5)
        assert results == [(1, 0.5), (2, 0.8)]

    def test_vec_search_raises_type_error_for_non_bytes(self) -> None:
        mock_db = MagicMock()
        store = SQLiteVectorStore(mock_db)
        with pytest.raises(TypeError):
            store.vec_search("not bytes", k=5)  # type: ignore[arg-type]

    def test_vec_search_k_zero_returns_empty(self) -> None:
        mock_db = MagicMock()
        store = SQLiteVectorStore(mock_db)
        blob = b"\x00" * (384 * 4)
        with patch("db.store_impl.validate_embedding_blob"):
            results = store.vec_search(blob, k=0)
        assert results == []
        mock_db.fetchall.assert_not_called()

    def test_vec_search_k_negative_returns_empty(self) -> None:
        mock_db = MagicMock()
        store = SQLiteVectorStore(mock_db)
        blob = b"\x00" * (384 * 4)
        with patch("db.store_impl.validate_embedding_blob"):
            results = store.vec_search(blob, k=-1)
        assert results == []
        mock_db.fetchall.assert_not_called()

    def test_vec_search_valid_k_delegates_to_db(self) -> None:
        mock_db = MagicMock()
        mock_db.fetchall.return_value = [(3, 0.3)]
        store = SQLiteVectorStore(mock_db)
        blob = b"\x00" * (384 * 4)
        with patch("db.store_impl.validate_embedding_blob"):
            results = store.vec_search(blob, k=1)
        assert results == [(3, 0.3)]
        mock_db.fetchall.assert_called_once()


# ── SQLiteMemoryDeleteStore ───────────────────────────────────────────────────


class TestSQLiteMemoryDeleteStore:
    def test_no_old_entries_returns_deleted_zero(self) -> None:
        mock_db = MagicMock()
        mock_db.fetchall.return_value = []
        store = SQLiteMemoryDeleteStore(mock_db)
        result = store.delete_memories_before(30)
        assert result.deleted == 0
        mock_db.execute.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_old_entries_trigger_delete_and_commit(self) -> None:
        mock_db = MagicMock()
        mock_cur = MagicMock()
        mock_cur.rowcount = 2
        mock_db.fetchall.return_value = [("uuid-1",), ("uuid-2",)]
        mock_db.execute.return_value = mock_cur
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_cm)
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_db.begin_immediate.return_value = mock_cm
        store = SQLiteMemoryDeleteStore(mock_db)
        result = store.delete_memories_before(30)
        assert result.deleted == 2
        mock_db.begin_immediate.assert_called_once()

    def test_fts_and_vec_cleanup_called_per_deleted_entry(self) -> None:
        mock_db = MagicMock()
        mock_cur = MagicMock()
        mock_cur.rowcount = 1
        mock_db.fetchall.return_value = [("uuid-abc",)]
        mock_db.execute.return_value = mock_cur
        store = SQLiteMemoryDeleteStore(mock_db)
        store.delete_memories_before(7)
        calls = [str(c) for c in mock_db.execute.call_args_list]
        assert any("DELETE FROM memories WHERE" in c for c in calls)
        assert any("memories_fts" in c for c in calls)
        assert any("memories_vec" in c for c in calls)
