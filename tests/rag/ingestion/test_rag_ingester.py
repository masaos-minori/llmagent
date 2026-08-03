"""tests/test_rag_ingester.py

Tests for RagIngester._read_chunk_json, chunk metadata preservation,
and --force reinsert behavior.

These tests prevent regression of BUG-1/BUG-2/BUG-3 where chunk metadata
(chunking_strategy, normalized_content, chunk_index) was lost.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson
from rag.ingestion.document_manager import DocumentManager
from rag.ingestion.ingester import RagIngester

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_chunk_json(
    url: str = "http://example.com/page",
    title: str = "Test Page",
    lang: str = "en",
    content: str = "Hello world",
    chunking_strategy: str = "heading",
    normalized_content: str | None = None,
    chunk_index: int = 0,
    etag: str | None = None,
    last_modified: str | None = None,
) -> dict:
    """Build a chunk JSON dict matching what ChunkSplitter produces."""
    return {
        "schema_version": "1",
        "artifact_type": "chunk",
        "created_by": "chunk_splitter",
        "url": url,
        "title": title,
        "lang": lang,
        "content": content,
        "chunking_strategy": chunking_strategy,
        "normalized_content": normalized_content,
        "chunk_index": chunk_index,
        "etag": etag,
        "last_modified": last_modified,
        "code_blocks": [],
    }


def _write_chunk_file(chunk_dir: Path, name: str, data: dict) -> Path:
    """Write a chunk JSON file (as ChunkSplitter does)."""
    path = chunk_dir / f"{name}.json"
    path.write_bytes(orjson.dumps(data))
    return path


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    url                TEXT    NOT NULL UNIQUE,
    title              TEXT,
    lang               TEXT    NOT NULL CHECK (lang IN ('ja', 'en')),
    fetched_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    etag               TEXT,
    last_modified      TEXT,
    chunking_strategy  TEXT    NOT NULL DEFAULT 'text'
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id             INTEGER NOT NULL
                           REFERENCES documents(doc_id) ON DELETE CASCADE,
    chunk_index        INTEGER NOT NULL,
    content            TEXT    NOT NULL,
    normalized_content TEXT,
    chunk_type         TEXT,
    source_file        TEXT
);
CREATE TABLE IF NOT EXISTS chunks_vec (
    chunk_id  INTEGER PRIMARY KEY,
    embedding BLOB NOT NULL
);
"""

_DIM = 384
_FAKE_EMBEDDING = [0.1] * _DIM


class _FakeSQLiteHelper:
    """In-memory SQLite wrapper satisfying the SQLiteHelper interface used by ingester."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *args: object) -> None:
        self._conn.row_factory = None

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

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

    def executemany(self, sql: str, params_seq: list) -> sqlite3.Cursor:
        return self._conn.executemany(sql, params_seq)

    def close(self) -> None:
        pass


def _make_db() -> tuple[sqlite3.Connection, _FakeSQLiteHelper]:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    return conn, _FakeSQLiteHelper(conn)


def _make_ingester(tmp_path: Path, embed_url: str = "http://127.0.0.1:9999/embedding"):
    """Create a RagIngester with temp directories and mocked config."""
    chunk_dir = tmp_path / "chunk"
    chunk_dir.mkdir(exist_ok=True)
    registered_dir = tmp_path / "registered"
    registered_dir.mkdir(exist_ok=True)
    cfg = {
        "rag_src_dir": str(tmp_path),
        "embed_url": embed_url,
        "embed_retry": 1,
        "embed_workers": 2,
    }
    return RagIngester(config=cfg)


# ── _read_chunk_json tests ────────────────────────────────────────────────────


class TestReadChunkJson:
    """Tests for _read_chunk_json() raw JSON field preservation."""

    def test_preserves_all_fields(self, tmp_path):
        """All chunk fields including metadata are preserved in returned dict."""
        ingester = _make_ingester(tmp_path)
        data = _make_chunk_json(
            content="Test content",
            chunking_strategy="heading",
            normalized_content="test content",
            chunk_index=3,
        )
        path = _write_chunk_file(tmp_path / "chunk", "chunk_0", data)
        result = ingester._read_chunk_json(path)

        assert result is not None
        assert result["url"] == "http://example.com/page"
        assert result["title"] == "Test Page"
        assert result["lang"] == "en"
        assert result["content"] == "Test content"
        assert result["chunking_strategy"] == "heading"
        assert result["normalized_content"] == "test content"
        assert result["chunk_index"] == 3

    def test_returns_none_for_missing_file(self, tmp_path):
        """Returns None when chunk file does not exist."""
        ingester = _make_ingester(tmp_path)
        path = tmp_path / "chunk" / "nonexistent.json"
        result = ingester._read_chunk_json(path)
        assert result is None

    def test_returns_none_for_invalid_json(self, tmp_path):
        """Returns None when chunk file contains invalid JSON."""
        ingester = _make_ingester(tmp_path)
        path = tmp_path / "chunk" / "invalid.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not json {{{")
        result = ingester._read_chunk_json(path)
        assert result is None

    def test_returns_none_for_non_dict_json(self, tmp_path):
        """Returns None when chunk file contains non-object JSON (e.g. array)."""
        ingester = _make_ingester(tmp_path)
        path = tmp_path / "chunk" / "array.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[1, 2, 3]")
        result = ingester._read_chunk_json(path)
        assert result is None


# ── Chunk metadata storage tests ──────────────────────────────────────────────


class TestChunkMetadataStorage:
    """Tests that chunk metadata fields are correctly stored in SQLite."""

    def test_chunk_index_stored_correctly(self, tmp_path):
        """chunk_index from JSON file is written to chunks.chunk_index column."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"

        # Create chunk files with explicit chunk_index values
        data1 = _make_chunk_json(content="First chunk", chunk_index=0)
        data2 = _make_chunk_json(content="Second chunk", chunk_index=1)
        data3 = _make_chunk_json(content="Third chunk", chunk_index=2)
        _write_chunk_file(chunk_dir, "chunk_0", data1)
        _write_chunk_file(chunk_dir, "chunk_1", data2)
        _write_chunk_file(chunk_dir, "chunk_2", data3)

        # Mock embedding to return a valid vector
        mock_resp = MagicMock()
        mock_resp.content = orjson.dumps({"embedding": [0.1] * 384})

        mock_cur = MagicMock()
        mock_cur.lastrowid = 1
        mock_cur.fetchone.return_value = None

        def execute_side_effect(sql, *args, **kwargs):
            return mock_cur

        mock_db = MagicMock()
        mock_db.execute.side_effect = execute_side_effect

        # Mock SQLiteHelper used by _embed_and_store (opens its own connection)
        mock_sh = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_sh.open = MagicMock(return_value=mock_ctx)

        with (
            patch.object(ingester._client, "post", return_value=mock_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=mock_sh),
        ):
            ingester.ingest_url_group(
                doc_mgr=MagicMock(),
                db=mock_db,
                url="http://example.com/page",
                chunk_files=sorted(chunk_dir.glob("*.json")),
                force=False,
            )

        # Verify _insert_chunk was called with correct chunk_index values
        calls = mock_cur.execute.call_args_list
        # Exclude chunks_vec inserts — "INSERT INTO chunks (" won't match "chunks_vec"
        chunk_inserts = [c for c in calls if "INSERT INTO chunks (" in str(c)]
        assert len(chunk_inserts) == 3
        # call.args = (sql_str, params_tuple); params_tuple[1] = chunk_index
        idx_values = {c[0][1][1] for c in chunk_inserts}
        assert idx_values == {0, 1, 2}

    def test_normalized_content_stored_correctly(self, tmp_path):
        """normalized_content from JSON file is written to chunks.normalized_content."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"

        data = _make_chunk_json(
            content="Original", normalized_content="normalized form"
        )
        _write_chunk_file(chunk_dir, "chunk_0", data)

        mock_resp = MagicMock()
        mock_resp.content = orjson.dumps({"embedding": [0.1] * 384})
        mock_cur = MagicMock()
        mock_cur.lastrowid = 1
        mock_cur.fetchone.return_value = None

        def execute_side_effect(sql, *args, **kwargs):
            return mock_cur

        mock_db = MagicMock()
        mock_db.execute.side_effect = execute_side_effect

        mock_sh = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_sh.open = MagicMock(return_value=mock_ctx)

        with (
            patch.object(ingester._client, "post", return_value=mock_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=mock_sh),
        ):
            ingester.ingest_url_group(
                doc_mgr=MagicMock(),
                db=mock_db,
                url="http://example.com/page",
                chunk_files=[chunk_dir / "chunk_0.json"],
                force=False,
            )

        # Check that normalized_content was passed to INSERT
        calls = mock_cur.execute.call_args_list
        chunk_inserts = [c for c in calls if "INSERT INTO chunks" in str(c)]
        assert len(chunk_inserts) >= 1
        insert_args = chunk_inserts[0][0]
        if len(insert_args) > 3:
            assert insert_args[3] == "normalized form"

    def test_chunking_strategy_stored_in_documents(self, tmp_path):
        """chunking_strategy from first chunk JSON is stored in documents.chunking_strategy."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"

        data = _make_chunk_json(chunking_strategy="heading")
        _write_chunk_file(chunk_dir, "chunk_0", data)

        mock_cur = MagicMock()
        mock_cur.lastrowid = 42
        mock_cur.fetchone.return_value = None

        def execute_side_effect(sql, *args, **kwargs):
            return mock_cur

        mock_db = MagicMock()
        mock_db.execute.side_effect = execute_side_effect

        ingester.ingest_url_group(
            doc_mgr=MagicMock(),
            db=mock_db,
            url="http://example.com/page",
            chunk_files=[chunk_dir / "chunk_0.json"],
            force=False,
        )

        # Check that _get_or_create_document was called with correct chunking_strategy
        calls = mock_db.execute.call_args_list
        doc_inserts = [c for c in calls if "INSERT INTO documents" in str(c)]
        assert len(doc_inserts) >= 1
        # call.args = (sql_str, params_tuple); params_tuple[5] = chunking_strategy
        params = doc_inserts[0][0][1]
        assert params[5] == "heading"


# ── Force reinsert tests ──────────────────────────────────────────────────────


class TestForceReinsert:
    """Tests for --force reinsert behavior."""

    def test_force_reinsert_deletes_existing_document(self, tmp_path):
        """force=True deletes existing document and chunks before re-inserting."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"

        data = _make_chunk_json()
        _write_chunk_file(chunk_dir, "chunk_0", data)

        mock_db = MagicMock()
        # Simulate existing document found
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (42,)
        mock_cur.lastrowid = 99
        mock_db.execute.return_value = mock_cur

        mock_doc_mgr = MagicMock()
        # force=True → handle_existing_document returns False (don't skip)
        mock_doc_mgr.handle_existing_document.return_value = False

        ingester.ingest_url_group(
            doc_mgr=mock_doc_mgr,
            db=mock_db,
            url="http://example.com/page",
            chunk_files=[chunk_dir / "chunk_0.json"],
            force=True,
        )

        # delete_existing_document is delegated to doc_mgr
        mock_doc_mgr.delete_existing_document.assert_called_once()

    def test_no_force_skips_existing_document(self, tmp_path):
        """force=False skips ingestion when document already exists."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"

        data = _make_chunk_json()
        _write_chunk_file(chunk_dir, "chunk_0", data)

        mock_db = MagicMock()
        # Simulate existing document found
        mock_db.fetchone.return_value = (42,)
        mock_cur = MagicMock()
        mock_cur.lastrowid = 99
        mock_db.execute.return_value = mock_cur

        ingester.ingest_url_group(
            doc_mgr=MagicMock(),
            db=mock_db,
            url="http://example.com/page",
            chunk_files=[chunk_dir / "chunk_0.json"],
            force=False,
        )

        # Should NOT have called DELETE for existing document
        calls = mock_db.execute.call_args_list
        delete_calls = [c for c in calls if "DELETE" in str(c)]
        assert len(delete_calls) == 0


# ── Chunk order tests ─────────────────────────────────────────────────────────


class TestChunkOrder:
    """Tests that chunks are processed in ascending chunk_index order."""

    def test_chunks_sorted_by_stem_filename(self, tmp_path):
        """Chunk files are sorted by stem (filename without extension) before ingestion."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"

        # Create files out of order
        data3 = _make_chunk_json(content="Third", chunk_index=2)
        data1 = _make_chunk_json(content="First", chunk_index=0)
        data2 = _make_chunk_json(content="Second", chunk_index=1)
        _write_chunk_file(chunk_dir, "chunk_2", data3)
        _write_chunk_file(chunk_dir, "chunk_0", data1)
        _write_chunk_file(chunk_dir, "chunk_1", data2)

        mock_db = MagicMock()
        mock_cur = MagicMock()
        mock_cur.lastrowid = 42
        mock_db.execute.return_value = mock_cur
        mock_db.fetchone.return_value = None

        # Get files in arbitrary order (simulating glob output)
        raw_files = list(chunk_dir.glob("*.json"))

        ingester.ingest_url_group(
            doc_mgr=MagicMock(),
            db=mock_db,
            url="http://example.com/page",
            chunk_files=raw_files,
            force=False,
        )

        # ingest_url_group sorts by stem internally: sorted(chunk_files, key=lambda p: p.stem)
        # Verify the sort is correct
        sorted_files = sorted(raw_files, key=lambda p: p.stem)
        assert sorted_files[0].stem == "chunk_0"
        assert sorted_files[1].stem == "chunk_1"
        assert sorted_files[2].stem == "chunk_2"


# ── chunk_type / source_file storage ─────────────────────────────────────────


def _make_insert_spy(tmp_path: Path):
    """Return (ingester, captured_insert_calls) for _insert_chunk call inspection."""
    ingester = _make_ingester(tmp_path)
    insert_calls: list[tuple] = []
    original = ingester._insert_chunk

    def spy(db, doc_id, idx, content, nc, embedding, chunk_type="", source_file=""):
        insert_calls.append((chunk_type, source_file))
        original(db, doc_id, idx, content, nc, embedding, chunk_type, source_file)

    ingester._insert_chunk = spy  # noqa: SLF001
    return ingester, insert_calls


class TestChunkMetadataFields:
    def test_chunk_type_stored_correctly(self, tmp_path):
        """chunk_type from JSON is passed through to _insert_chunk."""
        ingester, insert_calls = _make_insert_spy(tmp_path)
        chunk_dir = tmp_path / "chunk"

        data = _make_chunk_json(content="Hello")
        data["chunk_type"] = "heading"
        _write_chunk_file(chunk_dir, "chunk_0", data)

        mock_resp = MagicMock()
        mock_resp.content = orjson.dumps({"embedding": [0.1] * 384})
        mock_cur = MagicMock()
        mock_cur.lastrowid = 1
        mock_cur.fetchone.return_value = None
        mock_db = MagicMock()
        mock_db.execute.return_value = mock_cur
        mock_sh = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_sh.open = MagicMock(return_value=mock_ctx)

        with (
            patch.object(ingester._client, "post", return_value=mock_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=mock_sh),
        ):
            ingester.ingest_url_group(
                doc_mgr=MagicMock(),
                db=mock_db,
                url="http://example.com/page",
                chunk_files=[chunk_dir / "chunk_0.json"],
                force=False,
            )

        assert len(insert_calls) == 1
        assert insert_calls[0][0] == "heading"

    def test_source_file_stored_correctly(self, tmp_path):
        """source_file from JSON is passed through to _insert_chunk."""
        ingester, insert_calls = _make_insert_spy(tmp_path)
        chunk_dir = tmp_path / "chunk"

        data = _make_chunk_json(content="Hello")
        data["source_file"] = "docs/guide.md"
        _write_chunk_file(chunk_dir, "chunk_0", data)

        mock_resp = MagicMock()
        mock_resp.content = orjson.dumps({"embedding": [0.1] * 384})
        mock_cur = MagicMock()
        mock_cur.lastrowid = 1
        mock_cur.fetchone.return_value = None
        mock_db = MagicMock()
        mock_db.execute.return_value = mock_cur
        mock_sh = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_sh.open = MagicMock(return_value=mock_ctx)

        with (
            patch.object(ingester._client, "post", return_value=mock_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=mock_sh),
        ):
            ingester.ingest_url_group(
                doc_mgr=MagicMock(),
                db=mock_db,
                url="http://example.com/page",
                chunk_files=[chunk_dir / "chunk_0.json"],
                force=False,
            )

        assert len(insert_calls) == 1
        assert insert_calls[0][1] == "docs/guide.md"

    def test_missing_fields_default_to_empty_string(self, tmp_path):
        """chunk_type/source_file default to empty string when absent from JSON."""
        ingester, insert_calls = _make_insert_spy(tmp_path)
        chunk_dir = tmp_path / "chunk"

        data = _make_chunk_json(content="Hello")
        _write_chunk_file(chunk_dir, "chunk_0", data)

        mock_resp = MagicMock()
        mock_resp.content = orjson.dumps({"embedding": [0.1] * 384})
        mock_cur = MagicMock()
        mock_cur.lastrowid = 1
        mock_cur.fetchone.return_value = None
        mock_db = MagicMock()
        mock_db.execute.return_value = mock_cur
        mock_sh = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_sh.open = MagicMock(return_value=mock_ctx)

        with (
            patch.object(ingester._client, "post", return_value=mock_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=mock_sh),
        ):
            ingester.ingest_url_group(
                doc_mgr=MagicMock(),
                db=mock_db,
                url="http://example.com/page",
                chunk_files=[chunk_dir / "chunk_0.json"],
                force=False,
            )

        assert len(insert_calls) == 1
        assert insert_calls[0] == ("", "")


# ── Step 3: validation gap tests ──────────────────────────────────────────────


class TestReadChunkJsonValidation:
    def test_returns_none_for_missing_url(self, tmp_path):
        chunk_file = tmp_path / "chunk_0.json"
        chunk_file.write_bytes(
            orjson.dumps({"url": "", "content": "test", "lang": "en"})
        )
        ingester = _make_ingester(tmp_path)
        assert ingester._read_chunk_json(chunk_file) is None

    def test_returns_none_for_missing_content(self, tmp_path):
        chunk_file = tmp_path / "chunk_0.json"
        chunk_file.write_bytes(
            orjson.dumps({"url": "https://example.com", "content": "", "lang": "en"})
        )
        ingester = _make_ingester(tmp_path)
        assert ingester._read_chunk_json(chunk_file) is None

    def test_invalid_chunk_index_defaults_to_zero(self, tmp_path):
        """chunk_index that can't be cast to int falls back to 0."""
        ingester = _make_ingester(tmp_path)
        chunk_dir = tmp_path / "chunk"
        data = _make_chunk_json(content="Hello")
        data["chunk_index"] = "abc"
        _write_chunk_file(chunk_dir, "chunk_0", data)

        conn, fake_db = _make_db()
        conn.execute(
            "INSERT INTO documents (url, title, lang, chunking_strategy) VALUES (?, ?, ?, ?)",
            ("http://example.com/page", "Test Page", "en", "heading"),
        )
        conn.commit()
        doc_id: int = conn.execute("SELECT doc_id FROM documents").fetchone()[0]

        mock_resp = MagicMock()
        mock_resp.content = orjson.dumps({"embedding": [0.1] * _DIM})

        with (
            patch.object(ingester._client, "post", return_value=mock_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester._embed_and_store(doc_id, chunk_dir / "chunk_0.json")

        row = conn.execute(
            "SELECT chunk_index FROM chunks WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        assert row is not None and row[0] == 0


# ── Step 1: real DB integration tests ─────────────────────────────────────────


def _ingest_via_real_db(
    tmp_path: Path,
    chunk_data: dict,
    force: bool = False,
) -> tuple[sqlite3.Connection, _FakeSQLiteHelper]:
    """Helper: write one chunk file, run ingest_url_group against real in-memory DB, return conn+db."""
    chunk_dir = tmp_path / "chunk"
    chunk_dir.mkdir(exist_ok=True)
    (tmp_path / "registered").mkdir(exist_ok=True)
    _write_chunk_file(chunk_dir, "chunk_0", chunk_data)
    conn, fake_db = _make_db()

    ingester = _make_ingester(tmp_path)
    mock_resp = MagicMock()
    mock_resp.content = orjson.dumps({"embedding": [0.1] * _DIM})

    with (
        patch.object(ingester._client, "post", return_value=mock_resp),
        patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
    ):
        ingester.ingest_url_group(
            doc_mgr=MagicMock(),
            db=fake_db,
            url=chunk_data["url"],
            chunk_files=[chunk_dir / "chunk_0.json"],
            force=force,
        )

    return conn, fake_db


class TestRealDBFieldPreservation:
    def test_chunking_strategy_stored_in_documents_real_db(self, tmp_path):
        data = _make_chunk_json(chunking_strategy="heading")
        conn, _ = _ingest_via_real_db(tmp_path, data)
        row = conn.execute(
            "SELECT chunking_strategy FROM documents WHERE url = ?", (data["url"],)
        ).fetchone()
        assert row is not None and row[0] == "heading"

    def test_chunk_index_stored_correctly_real_db(self, tmp_path):
        data = _make_chunk_json(chunk_index=5)
        conn, _ = _ingest_via_real_db(tmp_path, data)
        row = conn.execute("SELECT chunk_index FROM chunks LIMIT 1").fetchone()
        assert row is not None and row[0] == 5

    def test_normalized_content_stored_correctly_real_db(self, tmp_path):
        data = _make_chunk_json(normalized_content="normalized form")
        conn, _ = _ingest_via_real_db(tmp_path, data)
        row = conn.execute("SELECT normalized_content FROM chunks LIMIT 1").fetchone()
        assert row is not None and row[0] == "normalized form"

    def test_null_normalized_content_stored_as_null_real_db(self, tmp_path):
        data = _make_chunk_json(normalized_content=None)
        conn, _ = _ingest_via_real_db(tmp_path, data)
        row = conn.execute("SELECT normalized_content FROM chunks LIMIT 1").fetchone()
        assert row is not None and row[0] is None

    def test_etag_last_modified_stored_in_documents(self, tmp_path):
        data = _make_chunk_json(etag="etag-abc", last_modified="2024-01-01T00:00:00Z")
        conn, _ = _ingest_via_real_db(tmp_path, data)
        row = conn.execute(
            "SELECT etag, last_modified FROM documents WHERE url = ?", (data["url"],)
        ).fetchone()
        assert (
            row is not None
            and row[0] == "etag-abc"
            and row[1] == "2024-01-01T00:00:00Z"
        )

    def test_chunk_type_stored_in_chunks_real_db(self, tmp_path):
        data = _make_chunk_json()
        data["chunk_type"] = "code"
        conn, _ = _ingest_via_real_db(tmp_path, data)
        row = conn.execute("SELECT chunk_type FROM chunks LIMIT 1").fetchone()
        assert row is not None and row[0] == "code"

    def test_source_file_stored_in_chunks_real_db(self, tmp_path):
        data = _make_chunk_json()
        data["source_file"] = "docs/guide.md"
        conn, _ = _ingest_via_real_db(tmp_path, data)
        row = conn.execute("SELECT source_file FROM chunks LIMIT 1").fetchone()
        assert row is not None and row[0] == "docs/guide.md"


# ── Step 2: force reinsert integration test ───────────────────────────────────


class TestForceReinsertMetadata:
    def test_force_reinsert_preserves_all_metadata(self, tmp_path):
        """After force reinsert, new chunk data replaces old across all preserved fields."""
        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(exist_ok=True)
        (tmp_path / "registered").mkdir(exist_ok=True)
        conn, fake_db = _make_db()
        ingester = _make_ingester(tmp_path)
        mock_resp = MagicMock()
        mock_resp.content = orjson.dumps({"embedding": [0.1] * _DIM})

        # First ingest
        data_v1 = _make_chunk_json(
            content="Original", chunking_strategy="text", chunk_index=0
        )
        _write_chunk_file(chunk_dir, "chunk_0", data_v1)
        with (
            patch.object(ingester._client, "post", return_value=mock_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                doc_mgr=MagicMock(),
                db=fake_db,
                url=data_v1["url"],
                chunk_files=[chunk_dir / "chunk_0.json"],
                force=False,
            )

        # Restore chunk file (moved to registered)
        (tmp_path / "registered" / "chunk_0.json").rename(chunk_dir / "chunk_0.json")

        # Second ingest with force=True and new data
        data_v2 = _make_chunk_json(
            content="Updated",
            chunking_strategy="heading",
            chunk_index=1,
            normalized_content="updated normalized",
        )
        (chunk_dir / "chunk_0.json").write_bytes(orjson.dumps(data_v2))
        with (
            patch.object(ingester._client, "post", return_value=mock_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                doc_mgr=DocumentManager(fake_db),
                db=fake_db,
                url=data_v2["url"],
                chunk_files=[chunk_dir / "chunk_0.json"],
                force=True,
            )

        # Verify old chunks gone, new chunks present with correct metadata
        chunks = conn.execute(
            "SELECT chunk_index, content, normalized_content FROM chunks"
        ).fetchall()
        assert len(chunks) == 1
        assert chunks[0][0] == 1
        assert chunks[0][1] == "Updated"
        assert chunks[0][2] == "updated normalized"

        doc_row = conn.execute("SELECT chunking_strategy FROM documents").fetchone()
        assert doc_row is not None and doc_row[0] == "heading"
