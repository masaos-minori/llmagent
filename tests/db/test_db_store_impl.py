"""tests/test_db_store_impl.py
Unit tests for db/store_impl.py:
SQLiteDocumentStore, SQLiteVectorStore, SQLiteMemoryDeleteStore.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from db.store_impl import (
    SQLiteDocumentStore,
    SQLiteMemoryDeleteStore,
    SQLiteVectorStore,
)

# ── Constants ───────────────────────────────────────────────────────────────

_CHUNKING_STRATEGY = "text"
_CHUNKING_STRATEGY_UPDATED = "semantic"

# ── In-memory DB helper ───────────────────────────────────────────────────────

_DOCUMENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    url           TEXT NOT NULL UNIQUE,
    title         TEXT,
    lang          TEXT NOT NULL,
    etag          TEXT,
    last_modified TEXT,
    fetched_at    TEXT NOT NULL,
    chunking_strategy TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
     chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
     doc_id             INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
     chunk_index        INTEGER,
     content            TEXT NOT NULL,
     normalized_content TEXT,
     chunk_type         TEXT NOT NULL,
     source_file        TEXT NOT NULL
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


# ── SQLiteDocumentStore ───────────────────────────────────────────────────────


class TestSQLiteDocumentStore:
    def test_doc_get_returns_none_for_nonexistent_url(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        result = store.doc_get("http://nonexistent.example.com")
        assert result is None

    def test_doc_upsert_new_url_returns_positive_id(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        doc_id = store.doc_upsert(
            "http://example.com",
            "Title",
            "en",
            None,
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY,
        )
        assert isinstance(doc_id, int)
        assert doc_id >= 1

    def test_doc_upsert_and_get_roundtrip(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert(
            "http://example.com",
            "My Title",
            "ja",
            "etag1",
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY,
        )
        result = store.doc_get("http://example.com")
        assert result is not None
        assert result.url == "http://example.com"
        assert result.title == "My Title"
        assert result.lang == "ja"
        assert isinstance(result.lang, str)

    def test_doc_get_returns_lang_as_str(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert(
            "http://example.com",
            "My Title",
            "en",
            "etag1",
            None,
            "2024-01-01T00:00:00Z",
            "text",
        )
        result = store.doc_get("http://example.com")
        assert isinstance(result.lang, str)  # type: ignore[union-attr]

    def test_chunk_count_starts_at_zero(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        assert store.chunk_count() == 0

    def test_chunk_insert_increments_count(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        doc_id = store.doc_upsert(
            "http://example.com",
            None,
            "en",
            None,
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY,
        )
        store.chunk_insert(doc_id, 0, "first chunk content", "", "")
        assert store.chunk_count() == 1
        store.chunk_insert(
            doc_id, 1, "second chunk content", "", "", normalized="normalized"
        )
        assert store.chunk_count() == 2

    def test_chunk_insert_stores_chunk_type_and_source_file(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        doc_id = store.doc_upsert(
            "http://example.com",
            None,
            "en",
            None,
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY,
        )
        chunk_id = store.chunk_insert(
            doc_id, 0, "content", "code", "foo.py", normalized=None
        )
        row = store._db.execute(
            "SELECT chunk_type, source_file FROM chunks WHERE chunk_id = ?", (chunk_id,)
        ).fetchone()
        assert row is not None
        assert row[0] == "code"
        assert row[1] == "foo.py"

    def test_chunk_insert_requires_chunk_type_and_source_file(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        doc_id = store.doc_upsert(
            "http://example.com",
            None,
            "en",
            None,
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY,
        )
        with pytest.raises(TypeError):
            store.chunk_insert(doc_id, 0, "content")  # type: ignore[call-arg]

    def test_doc_delete_removes_document_and_returns_true(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert(
            "http://example.com",
            "Title",
            "en",
            None,
            None,
            "2024-01-01T00:00:00Z",
            "text",
        )
        deleted = store.doc_delete("http://example.com")
        assert deleted is True
        assert store.doc_get("http://example.com") is None

    def test_doc_delete_nonexistent_returns_false(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        deleted = store.doc_delete("http://nowhere.example.com")
        assert deleted is False

    def test_doc_list_returns_inserted_documents(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert(
            "http://a.com",
            "A",
            "en",
            None,
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY,
        )
        store.doc_upsert(
            "http://b.com",
            "B",
            "ja",
            None,
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY,
        )
        rows = store.doc_list(lang=None, limit=10)
        assert len(rows) == 2
        urls = {r.url for r in rows}
        assert "http://a.com" in urls
        assert "http://b.com" in urls

    def test_doc_list_filtered_by_lang(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert(
            "http://a.com",
            "A",
            "en",
            None,
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY,
        )
        store.doc_upsert(
            "http://b.com",
            "B",
            "ja",
            None,
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY,
        )
        rows = store.doc_list(lang="ja", limit=10)
        assert len(rows) == 1
        assert rows[0].url == "http://b.com"

    def test_doc_list_returns_lang_as_str(self) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert(
            "http://a.com",
            "A",
            "en",
            None,
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY,
        )
        store.doc_upsert(
            "http://b.com",
            "B",
            "ja",
            None,
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY,
        )
        rows = store.doc_list(lang=None, limit=10)
        assert all(isinstance(r.lang, str) for r in rows)

    def test_doc_upsert_conflict_updates_chunking_strategy_to_supplied_value(
        self,
    ) -> None:
        store = SQLiteDocumentStore(_make_doc_db())  # type: ignore[arg-type]
        store.doc_upsert(
            "http://example.com",
            "Title",
            "en",
            None,
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY,
        )
        row = store._db.execute(
            "SELECT chunking_strategy FROM documents WHERE url = ?",
            ("http://example.com",),
        ).fetchone()
        assert row is not None
        assert row[0] == _CHUNKING_STRATEGY
        store.doc_upsert(
            "http://example.com",
            "Updated Title",
            "en",
            None,
            None,
            "2024-01-01T00:00:00Z",
            _CHUNKING_STRATEGY_UPDATED,
        )
        row = store._db.execute(
            "SELECT chunking_strategy FROM documents WHERE url = ?",
            ("http://example.com",),
        ).fetchone()
        assert row is not None
        assert row[0] == _CHUNKING_STRATEGY_UPDATED


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
        mock_cur.fetchall.return_value = [("uuid-1",), ("uuid-2",)]
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
        mock_cur.fetchall.return_value = [("uuid-abc",)]
        mock_db.fetchall.return_value = [("uuid-abc",)]
        mock_db.execute.return_value = mock_cur
        store = SQLiteMemoryDeleteStore(mock_db)
        store.delete_memories_before(7)
        calls = [str(c) for c in mock_db.execute.call_args_list]
        assert any("DELETE FROM memories WHERE" in c for c in calls)
        assert any("memories_fts" in c for c in calls)
        assert any("memories_vec" in c for c in calls)
        assert any("memory_links" in c for c in calls)

    def test_delete_statement_reapplies_guards_and_returns_ids(self) -> None:
        mock_db = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [("uuid-1",)]
        mock_db.fetchall.return_value = [("uuid-1",)]
        mock_db.execute.return_value = mock_cur
        store = SQLiteMemoryDeleteStore(mock_db)
        result = store.delete_memories_before(30)
        sql, params = mock_db.execute.call_args_list[0][0]
        assert "DELETE FROM memories" in sql
        assert "updated_at < datetime('now', ?)" in sql
        assert "pinned = 0" in sql
        assert "RETURNING memory_id" in sql
        assert params == ("-30 days",)
        assert result.deleted == 1

    def test_collect_prunable_ids_filters_pinned(self) -> None:
        mock_db = MagicMock()
        mock_db.fetchall.return_value = [
            ("old-1",),
            ("old-2",),
        ]
        store = SQLiteMemoryDeleteStore(mock_db)
        ids = store.collect_prunable_ids(30)
        assert ids == ["old-1", "old-2"]
        sql, args = mock_db.fetchall.call_args[0]
        assert "pinned = 0" in sql
        assert args == ("-30 days",)

    def test_collect_prunable_ids_empty(self) -> None:
        mock_db = MagicMock()
        mock_db.fetchall.return_value = []
        store = SQLiteMemoryDeleteStore(mock_db)
        assert store.collect_prunable_ids(30) == []

    def test_collect_prunable_ids_uses_updated_at(self) -> None:
        mock_db = MagicMock()
        mock_db.fetchall.return_value = []
        store = SQLiteMemoryDeleteStore(mock_db)
        store.collect_prunable_ids(30)
        sql, args = mock_db.fetchall.call_args[0]
        assert "updated_at < datetime('now', ?)" in sql
        assert "pinned = 0" in sql
        assert "created_at" not in sql
        assert args == ("-30 days",)

    def test_delete_memories_before_selects_by_updated_at(self) -> None:
        mock_db = MagicMock()
        mock_db.fetchall.return_value = []
        store = SQLiteMemoryDeleteStore(mock_db)
        store.delete_memories_before(30)
        sql, args = mock_db.fetchall.call_args[0]
        assert "updated_at < datetime('now', ?)" in sql
        assert "pinned = 0" in sql
        assert "created_at" not in sql
        assert args == ("-30 days",)


class _RealDeleteDB(_FakeDB):
    """_FakeDB plus the ``begin_immediate`` context manager the delete store uses."""

    @contextmanager
    def begin_immediate(self):
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield self.conn
        except BaseException:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()


class _RaceDeleteDB(_RealDeleteDB):
    """Runs an injected committed mutation right after the fast-path selection."""

    def __init__(self, conn: sqlite3.Connection, inject: Callable[[], None]) -> None:
        super().__init__(conn)
        self._inject = inject
        self._armed = True

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        rows = super().fetchall(sql, params)
        if self._armed and sql.startswith("SELECT memory_id FROM memories"):
            self._armed = False
            self._inject()
            self.conn.commit()
        return rows


def _seed_delete_tables(conn: sqlite3.Connection) -> None:
    """Create the minimal memory tables and seed m1..m4 with auxiliary rows."""
    conn.executescript(
        """
        CREATE TABLE memories (
            memory_id  TEXT PRIMARY KEY,
            created_at TEXT,
            updated_at TEXT,
            pinned     INTEGER DEFAULT 0
        );
        CREATE TABLE memories_fts (memory_id TEXT);
        CREATE TABLE memories_vec (memory_id TEXT);
        CREATE TABLE memory_links (src_id TEXT, dst_id TEXT);
        """
    )

    def _iso(days_ago: int) -> str:
        return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")

    conn.executemany(
        "INSERT INTO memories VALUES (?, ?, ?, ?)",
        [
            ("m1", _iso(90), _iso(90), 0),  # old update + old create -> prune
            ("m2", _iso(90), _iso(1), 0),  # old create, recent update -> keep
            ("m3", _iso(90), _iso(90), 1),  # old but pinned -> keep
            ("m4", _iso(1), _iso(1), 0),  # recent -> keep
        ],
    )
    conn.commit()
    conn.executemany("INSERT INTO memories_fts VALUES (?)", [("m1",), ("m2",)])
    conn.executemany("INSERT INTO memories_vec VALUES (?)", [("m1",), ("m2",)])
    conn.executemany(
        "INSERT INTO memory_links VALUES (?, ?)", [("m1", "x"), ("y", "m1")]
    )
    conn.commit()


class TestMemoryDeleteStoreRealSqlite:
    def test_prunes_only_old_unpinned_by_updated_at(self) -> None:
        conn = sqlite3.connect(":memory:")
        _seed_delete_tables(conn)

        store = SQLiteMemoryDeleteStore(_RealDeleteDB(conn))  # type: ignore[arg-type]
        ids = store.collect_prunable_ids(30)
        result = store.delete_memories_before(30)

        assert ids == ["m1"]
        assert result.deleted == 1

        remaining = {row[0] for row in conn.execute("SELECT memory_id FROM memories")}
        assert remaining == {"m2", "m3", "m4"}

        assert conn.execute("SELECT memory_id FROM memories_fts").fetchall() == [
            ("m2",)
        ]
        assert conn.execute("SELECT memory_id FROM memories_vec").fetchall() == [
            ("m2",)
        ]
        link_rows = conn.execute(
            "SELECT * FROM memory_links WHERE src_id = ? OR dst_id = ?",
            ("m1", "m1"),
        ).fetchall()
        assert link_rows == []

    def test_repin_between_selection_and_delete_is_retained(self) -> None:
        conn = sqlite3.connect(":memory:")
        _seed_delete_tables(conn)

        def _inject() -> None:
            conn.execute("UPDATE memories SET pinned = 1 WHERE memory_id = 'm1'")

        store = SQLiteMemoryDeleteStore(_RaceDeleteDB(conn, _inject))  # type: ignore[arg-type]
        result = store.delete_memories_before(30)

        assert result.deleted == 0
        assert conn.execute(
            "SELECT pinned FROM memories WHERE memory_id = 'm1'"
        ).fetchone() == (1,)
        assert conn.execute(
            "SELECT memory_id FROM memories_fts WHERE memory_id='m1'"
        ).fetchall() == [("m1",)]
        assert conn.execute(
            "SELECT memory_id FROM memories_vec WHERE memory_id='m1'"
        ).fetchall() == [("m1",)]
        assert (
            conn.execute(
                "SELECT * FROM memory_links WHERE src_id='m1' OR dst_id='m1'"
            ).fetchall()
            != []
        )

    def test_updated_at_refresh_between_selection_and_delete_is_retained(self) -> None:
        conn = sqlite3.connect(":memory:")
        _seed_delete_tables(conn)

        def _inject() -> None:
            conn.execute(
                "UPDATE memories SET updated_at = datetime('now') "
                "WHERE memory_id = 'm1'"
            )

        store = SQLiteMemoryDeleteStore(_RaceDeleteDB(conn, _inject))  # type: ignore[arg-type]
        result = store.delete_memories_before(30)

        assert result.deleted == 0
        assert conn.execute(
            "SELECT memory_id FROM memories WHERE memory_id = 'm1'"
        ).fetchone() == ("m1",)
        assert conn.execute(
            "SELECT memory_id FROM memories_fts WHERE memory_id='m1'"
        ).fetchall() == [("m1",)]
        assert conn.execute(
            "SELECT memory_id FROM memories_vec WHERE memory_id='m1'"
        ).fetchall() == [("m1",)]
        assert (
            conn.execute(
                "SELECT * FROM memory_links WHERE src_id='m1' OR dst_id='m1'"
            ).fetchall()
            != []
        )
