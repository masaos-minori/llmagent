"""tests/test_ingestion_freshness.py
Unit tests for file:// freshness detection in crawler.py and ingester.py, plus
real-schema freshness-atomicity regression tests (raging002 REQ-004).
"""

from __future__ import annotations

import contextlib
import hashlib
import sqlite3
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from rag.ingestion.document_manager import DocumentManager
from rag.ingestion.document_persistence import DocumentStore
from rag.ingestion.etag_manager import (
    ETagManager,
    InvalidIncomingTimestampError,
    InvalidStoredTimestampError,
)
from rag.ingestion.transaction_commit import TransactionManager
from rag.models_data import PreparedChunk

# ── _is_file_unchanged() ─────────────────────────────────────────────────────


class TestIsFileUnchanged:
    def test_same_etag_returns_true(self) -> None:
        assert DocumentManager._is_file_unchanged(
            "abc", "2024-01-01", "abc", "2024-01-02"
        )

    def test_different_etag_returns_false(self) -> None:
        assert not DocumentManager._is_file_unchanged(
            "abc", "2024-01-01", "xyz", "2024-01-01"
        )

    def test_none_existing_etag_returns_false(self) -> None:
        assert not DocumentManager._is_file_unchanged(
            None, "2024-01-01", "abc", "2024-01-01"
        )

    def test_none_new_etag_returns_false(self) -> None:
        assert not DocumentManager._is_file_unchanged(
            "abc", "2024-01-01", None, "2024-01-01"
        )

    def test_both_none_returns_false(self) -> None:
        assert not DocumentManager._is_file_unchanged(None, None, None, None)

    def test_mtime_changed_but_sha256_same_returns_true(self) -> None:
        assert DocumentManager._is_file_unchanged(
            "abc", "2024-01-01", "abc", "2024-01-02"
        )


# ── WebCrawler: mtime + SHA-256 in payload ───────────────────────────────────


class TestCrawlFilePayload:
    def test_etag_and_last_modified_in_payload(self, tmp_path: Path) -> None:
        from rag.ingestion.crawler import WebCrawler

        target = tmp_path / "test.txt"
        content = "hello world"
        target.write_text(content)

        cfg = {
            "target_urls": [],
            "rag_src_dir": str(tmp_path / "rag-src"),
            "skip_external": True,
            "crawl_delay": 0,
            "max_depth": 1,
            "min_chunk": 10,
            "fetch_retry": 1,
        }
        crawler = WebCrawler(cfg)
        crawler.crawl_file(target, "en")

        rag_src = tmp_path / "rag-src"
        files = list(rag_src.glob("*.json"))
        assert len(files) == 1

        import orjson

        payload = orjson.loads(files[0].read_bytes())
        assert "etag" in payload
        assert "last_modified" in payload
        expected_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        assert payload["etag"] == expected_sha

    def test_etag_is_sha256_of_content(self, tmp_path: Path) -> None:
        from rag.ingestion.crawler import WebCrawler

        target = tmp_path / "doc.txt"
        content = "some content"
        target.write_text(content)

        cfg = {
            "target_urls": [],
            "rag_src_dir": str(tmp_path / "rag-src"),
            "skip_external": True,
            "crawl_delay": 0,
            "max_depth": 1,
            "min_chunk": 10,
            "fetch_retry": 1,
        }
        crawler = WebCrawler(cfg)
        crawler.crawl_file(target, "en")

        import orjson

        rag_src = tmp_path / "rag-src"
        payload = orjson.loads(next(rag_src.glob("*.json")).read_bytes())
        assert payload["etag"] == hashlib.sha256(content.encode("utf-8")).hexdigest()


# ── DocumentStore.get_or_create() freshness for file:// ──────────────────────
#
# get_or_create() (and the freshness/reingest decision it delegates to
# DocumentManager.handle_existing_document()) used to live on RagIngester as
# _get_or_create_document(); it was extracted into DocumentStore
# (document_persistence.py) as part of isolating document CRUD concerns out
# of ingester.py.


def _make_fake_db(
    url: str, etag: str | None, last_modified: str | None
) -> tuple[Any, int | None]:
    """Create in-memory SQLite with documents/chunks tables; return (db_helper, doc_id)."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE documents"
        " (doc_id INTEGER PRIMARY KEY, url TEXT, title TEXT, lang TEXT,"
        "  etag TEXT, last_modified TEXT, chunking_strategy TEXT)"
    )
    conn.execute(
        "CREATE TABLE chunks (chunk_id INTEGER PRIMARY KEY, doc_id INTEGER,"
        " chunk_index INTEGER, content TEXT, normalized_content TEXT,"
        " chunk_type TEXT, source_file TEXT)"
    )
    conn.execute("CREATE TABLE chunks_vec (chunk_id INTEGER, embedding BLOB)")
    cur = conn.execute(
        "INSERT INTO documents (url, title, lang, etag, last_modified, chunking_strategy) VALUES (?, ?, ?, ?, ?, ?)",
        (url, "title", "en", etag, last_modified, "text"),
    )
    conn.commit()
    doc_id = cur.lastrowid

    class _Helper:
        def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
            return conn.execute(sql, params)

    return _Helper(), doc_id


class TestGetOrCreateDocumentFreshness:
    def test_unchanged_file_skips_reingest(self, tmp_path: Path) -> None:
        sha = "abc123"
        url = "file:///tmp/test.txt"
        db, _doc_id = _make_fake_db(url, sha, "2024-01-01")

        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]
        store = DocumentStore(db, doc_mgr)  # type: ignore[arg-type]
        result = store.get_or_create(
            db,
            url,
            "test.txt",
            "en",
            force=False,
            etag=sha,
            last_modified="2024-01-02",
            fetched_at="2024-01-01T00:00:00Z",
        )
        assert result == (None, True, False)

    def test_changed_sha256_triggers_reingest_via_real_document_manager(
        self, tmp_path: Path
    ) -> None:
        old_sha = "old_sha"
        new_sha = "new_sha"
        url = "file:///tmp/test.txt"
        db, _doc_id = _make_fake_db(url, old_sha, "2024-01-01")

        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]
        store = DocumentStore(db, doc_mgr)  # type: ignore[arg-type]
        result = store.get_or_create(
            db,
            url,
            "test.txt",
            "en",
            force=False,
            etag=new_sha,
            last_modified="2024-01-02",
            fetched_at="2024-01-01T00:00:00Z",
        )
        _, skip, replace = result
        assert skip is False
        assert replace is True

    def test_changed_sha256_triggers_reingest(self, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        url = "file:///tmp/test.txt"
        db, _doc_id = _make_fake_db(url, "old_sha", "2024-01-01")

        mock_doc_mgr = MagicMock()
        mock_doc_mgr.handle_existing_document.return_value = (42, False, True)
        store = DocumentStore(db, mock_doc_mgr)  # type: ignore[arg-type]
        store.get_or_create(
            db,
            url,
            "test.txt",
            "en",
            force=False,
            etag="new_sha",
            last_modified="2024-01-02",
            fetched_at="2024-01-01T00:00:00Z",
        )

    def test_force_true_skips_freshness_check(self, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        sha = "abc123"
        url = "file:///tmp/test.txt"
        db, _doc_id = _make_fake_db(url, sha, "2024-01-01")

        mock_doc_mgr = MagicMock()
        mock_doc_mgr.handle_existing_document.return_value = (42, False, True)
        store = DocumentStore(db, mock_doc_mgr)  # type: ignore[arg-type]
        store.get_or_create(
            db,
            url,
            "test.txt",
            "en",
            force=True,
            etag=sha,
            last_modified="2024-01-01",
            fetched_at="2024-01-01T00:00:00Z",
        )

    def test_non_file_url_uses_etag_update_path(self, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        url = "https://example.com/doc"
        db, doc_id = _make_fake_db(url, "old_etag", "2024-01-01")

        mock_doc_mgr = MagicMock()
        mock_doc_mgr.handle_existing_document.return_value = (doc_id, True, False)
        store = DocumentStore(db, mock_doc_mgr)  # type: ignore[arg-type]
        result = store.get_or_create(
            db,
            url,
            "doc",
            "en",
            force=False,
            etag="new_etag",
            last_modified="2024-01-02",
            fetched_at="2024-01-01T00:00:00Z",
        )
        assert result == (None, True, False)
        mock_doc_mgr.handle_existing_document.assert_called_once()


# ── Freshness atomicity (raging002 REQ-004) ───────────────────────────────────
#
# Real in-memory SQLite harness (documents has fetched_at; FK ON DELETE CASCADE)
# so transaction rollback is genuinely exercised — the pattern is the
# _FakeSQLiteHelper harness from tests/rag/ingestion/test_ingester.py.

_FRESHNESS_SCHEMA_SQL = """
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


class _FreshnessSQLiteHelper:
    """In-memory SQLite wrapper satisfying the SQLiteHelper interface."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        conn.row_factory = sqlite3.Row

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    @contextlib.contextmanager
    def begin_immediate(self) -> Generator[None]:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._conn.commit()
        except Exception:
            with contextlib.suppress(sqlite3.OperationalError):
                self._conn.rollback()
            raise

    def commit(self) -> None:
        self._conn.commit()


def _make_freshness_db() -> tuple[sqlite3.Connection, _FreshnessSQLiteHelper]:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript(_FRESHNESS_SCHEMA_SQL)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.commit()
    return conn, _FreshnessSQLiteHelper(conn)


def _seed_document(
    conn: sqlite3.Connection,
    url: str = "https://example.com/doc",
    etag: str | None = "old_etag",
    last_modified: str | None = "lm-old",
    fetched_at: str = "2024-06-10T00:00:00Z",
    content: str = "old chunk",
) -> int:
    """Insert one document with one chunk/chunks_vec row; return its doc_id."""
    cur = conn.execute(
        "INSERT INTO documents (url, title, lang, fetched_at, etag, last_modified,"
        " chunking_strategy) VALUES (?, 'Doc', 'en', ?, ?, ?, 'text')",
        (url, fetched_at, etag, last_modified),
    )
    doc_id = cur.lastrowid
    assert doc_id is not None
    cur = conn.execute(
        "INSERT INTO chunks (doc_id, chunk_index, content, chunk_type, source_file)"
        " VALUES (?, 0, ?, 'chunk', 'old.json')",
        (doc_id, content),
    )
    assert cur.lastrowid is not None
    conn.execute(
        "INSERT INTO chunks_vec (chunk_id, embedding) VALUES (?, ?)",
        (cur.lastrowid, b"\x00\x01"),
    )
    conn.commit()
    return doc_id


def _freshness_row(conn: sqlite3.Connection) -> tuple[Any, ...]:
    row = conn.execute(
        "SELECT etag, last_modified, fetched_at FROM documents ORDER BY doc_id"
    ).fetchall()
    return tuple(tuple(r) for r in row)


def _prepared(content: str = "new chunk") -> list[PreparedChunk]:
    return [
        PreparedChunk(
            doc_id=0,
            chunk_index=0,
            content=content,
            normalized_content=None,
            chunk_type="chunk",
            source_file="new.json",
            embedding_blob=b"\x00\x01",
        )
    ]


class TestFreshnessAtomicity:
    """Failed re-ingestion must not advance stored freshness before commit."""

    def test_failed_reingestion_leaves_stored_freshness_intact(self) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn)
        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]

        _id, skip, replace = doc_mgr.handle_existing_document(
            "https://example.com/doc",
            doc_id,
            False,
            "new_etag",
            "lm-new",
            "2024-06-20T00:00:00Z",
            lambda u: False,
        )
        assert (skip, replace) == (False, True)
        # No freshness write may happen before the commit transaction.
        assert _freshness_row(conn) == (("old_etag", "lm-old", "2024-06-10T00:00:00Z"),)

    def test_failed_reingestion_allows_next_run_to_reprocess(self) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn)
        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]

        doc_mgr.handle_existing_document(
            "https://example.com/doc",
            doc_id,
            False,
            "new_etag",
            "lm-new",
            "2024-06-20T00:00:00Z",
            lambda u: False,
        )
        # Second run with the same payload must reach the replace path again.
        _id, skip, replace = doc_mgr.handle_existing_document(
            "https://example.com/doc",
            doc_id,
            False,
            "new_etag",
            "lm-new",
            "2024-06-20T00:00:00Z",
            lambda u: False,
        )
        assert (skip, replace) == (False, True)

    def test_abort_leaves_documents_and_chunks_at_pre_run_values(self) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn)
        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]
        store = DocumentStore(db, doc_mgr)  # type: ignore[arg-type]
        tx_mgr = TransactionManager(db, doc_mgr, store)

        doc_mgr.handle_existing_document(
            "https://example.com/doc",
            doc_id,
            False,
            "new_etag",
            "lm-new",
            "2024-06-20T00:00:00Z",
            lambda u: False,
        )
        before = _freshness_row(conn)
        chunks_before = conn.execute(
            "SELECT content FROM chunks WHERE doc_id = ?", (doc_id,)
        ).fetchall()

        with (
            patch.object(
                TransactionManager,
                "_insert_chunks_batch",
                side_effect=RuntimeError("forced abort"),
            ),
            pytest.raises(RuntimeError, match="forced abort"),
        ):
            tx_mgr.commit(
                "https://example.com/doc",
                doc_id,
                _prepared(),
                [],
                force=False,
                replace=True,
                title="Doc",
                lang="en",
                etag="new_etag",
                last_modified="lm-new",
                chunking_strategy="text",
                fetched_at="2024-06-20T00:00:00Z",
            )

        assert _freshness_row(conn) == before
        assert (
            conn.execute(
                "SELECT content FROM chunks WHERE doc_id = ?", (doc_id,)
            ).fetchall()
            == chunks_before
        )

    def test_fresh_payload_insert_carries_payload_freshness(self) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn)
        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]
        store = DocumentStore(db, doc_mgr)  # type: ignore[arg-type]
        tx_mgr = TransactionManager(db, doc_mgr, store)

        tx_mgr.commit(
            "https://example.com/doc",
            doc_id,
            _prepared(),
            [],
            force=False,
            replace=True,
            title="Doc",
            lang="en",
            etag="new_etag",
            last_modified="lm-new",
            chunking_strategy="text",
            fetched_at="2024-06-20T00:00:00Z",
        )
        assert _freshness_row(conn) == (("new_etag", "lm-new", "2024-06-20T00:00:00Z"),)
        assert conn.execute("SELECT content FROM chunks").fetchone()[0] == "new chunk"

    def test_stale_payload_cannot_regress_stored_freshness(self) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn)
        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]
        store = DocumentStore(db, doc_mgr)  # type: ignore[arg-type]
        tx_mgr = TransactionManager(db, doc_mgr, store)

        chunks_before = conn.execute(
            "SELECT content FROM chunks WHERE doc_id = ?", (doc_id,)
        ).fetchall()

        _, skipped, _ = tx_mgr.commit(
            "https://example.com/doc",
            doc_id,
            _prepared(),
            [],
            force=False,
            replace=True,
            title="Doc",
            lang="en",
            etag="stale_etag",
            last_modified="lm-stale",
            chunking_strategy="text",
            fetched_at="2024-01-01T00:00:00Z",
        )
        # Stale incoming must not overwrite stored freshness on the replace path.
        assert skipped is True
        assert _freshness_row(conn) == (("old_etag", "lm-old", "2024-06-10T00:00:00Z"),)
        # And no chunk replacement happened either — byte-identical before/after.
        assert (
            conn.execute(
                "SELECT content FROM chunks WHERE doc_id = ?", (doc_id,)
            ).fetchall()
            == chunks_before
        )

    def test_stale_http_commit_skips_replacement(self) -> None:
        # AC-1: a stale HTTP payload on the replace path returns the skip tuple
        # and leaves both freshness and content byte-identical.
        conn, db = _make_freshness_db()
        doc_id = _seed_document(
            conn,
            etag="old_etag",
            last_modified="lm-old",
            fetched_at="2024-06-10T00:00:00Z",
        )
        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]
        store = DocumentStore(db, doc_mgr)  # type: ignore[arg-type]
        tx_mgr = TransactionManager(db, doc_mgr, store)

        chunks_before = conn.execute(
            "SELECT content FROM chunks WHERE doc_id = ?", (doc_id,)
        ).fetchall()
        vec_before = conn.execute(
            "SELECT chunk_id, embedding FROM chunks_vec ORDER BY chunk_id"
        ).fetchall()

        returned, skipped, replaced = tx_mgr.commit(
            "https://example.com/doc",
            doc_id,
            _prepared("stale should not land"),
            [],
            force=False,
            replace=True,
            title="Doc",
            lang="en",
            etag="stale_etag",
            last_modified="lm-stale",
            chunking_strategy="text",
            fetched_at="2024-01-01T00:00:00Z",
        )
        assert returned == doc_id
        assert (skipped, replaced) == (True, False)
        assert _freshness_row(conn) == (("old_etag", "lm-old", "2024-06-10T00:00:00Z"),)
        assert (
            conn.execute(
                "SELECT content FROM chunks WHERE doc_id = ?", (doc_id,)
            ).fetchall()
            == chunks_before
        )
        assert (
            conn.execute(
                "SELECT chunk_id, embedding FROM chunks_vec ORDER BY chunk_id"
            ).fetchall()
            == vec_before
        )

    def test_file_payload_older_mtime_replaces_with_incoming_metadata(self) -> None:
        # AC-2: a stale `file://` payload still replaces content and writes the
        # incoming metadata; the next run recognizes it as unchanged (no loop).
        conn, db = _make_freshness_db()
        url = "file:///tmp/doc.txt"
        doc_id = _seed_document(
            conn,
            url=url,
            etag="old_hash",
            last_modified="lm-old",
            fetched_at="2024-06-10T00:00:00Z",
        )
        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]
        store = DocumentStore(db, doc_mgr)  # type: ignore[arg-type]
        tx_mgr = TransactionManager(db, doc_mgr, store)

        chunks_before = conn.execute(
            "SELECT content FROM chunks WHERE doc_id = ?", (doc_id,)
        ).fetchall()

        # Incoming is older (fetched_at) and a different hash, but file:// bypasses
        # the stale-skip guard entirely.
        new_doc_id, skipped, _ = tx_mgr.commit(
            url,
            doc_id,
            _prepared("new file chunk"),
            [],
            force=False,
            replace=True,
            title="Doc",
            lang="en",
            etag="new_hash",
            last_modified="lm-new",
            chunking_strategy="text",
            fetched_at="2024-01-01T00:00:00Z",
        )
        assert skipped is False
        assert new_doc_id is not None
        # Content replaced and stored metadata equals the incoming (stale) values.
        assert _freshness_row(conn) == (("new_hash", "lm-new", "2024-01-01T00:00:00Z"),)
        assert (
            conn.execute(
                "SELECT content FROM chunks WHERE doc_id = ?", (new_doc_id,)
            ).fetchall()
            != chunks_before
        )
        assert (
            conn.execute(
                "SELECT content FROM chunks WHERE doc_id = ?", (new_doc_id,)
            ).fetchone()[0]
            == "new file chunk"
        )
        # Follow-up run with the same payload is recognized as unchanged: loop broken.
        _follow, skip_next, _ = doc_mgr.handle_existing_document(
            url,
            new_doc_id,
            False,
            "new_hash",
            "lm-new",
            "2024-01-01T00:00:00Z",
            lambda u: u.startswith("file://"),
        )
        assert skip_next is True

    def test_force_stale_commit_writes_incoming_metadata(self) -> None:
        # AC-2: force=True bypasses the stale guard and writes the incoming
        # (stale) metadata even for an HTTP payload.
        conn, db = _make_freshness_db()
        doc_id = _seed_document(
            conn,
            etag="old_etag",
            last_modified="lm-old",
            fetched_at="2024-06-10T00:00:00Z",
        )
        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]
        store = DocumentStore(db, doc_mgr)  # type: ignore[arg-type]
        tx_mgr = TransactionManager(db, doc_mgr, store)

        new_doc_id, skipped, _ = tx_mgr.commit(
            "https://example.com/doc",
            doc_id,
            _prepared("forced chunk"),
            [],
            force=True,
            replace=True,
            title="Doc",
            lang="en",
            etag="stale_etag",
            last_modified="lm-stale",
            chunking_strategy="text",
            fetched_at="2024-01-01T00:00:00Z",
        )
        assert skipped is False
        assert new_doc_id is not None
        assert _freshness_row(conn) == (
            ("stale_etag", "lm-stale", "2024-01-01T00:00:00Z"),
        )
        assert (
            conn.execute(
                "SELECT content FROM chunks WHERE doc_id = ?", (new_doc_id,)
            ).fetchone()[0]
            == "forced chunk"
        )


class TestResolveIncomingGuard:
    """resolve_incoming unit tests mirroring test_ingester_etag_guard.py guard cases."""

    def _mgr(
        self, conn: sqlite3.Connection, db: _FreshnessSQLiteHelper, doc_id: int
    ) -> ETagManager:
        return ETagManager(db, doc_id)  # type: ignore[arg-type]

    def test_stale_incoming_keeps_stored_values(self) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn)
        mgr = self._mgr(conn, db, doc_id)
        assert mgr.resolve_incoming(
            "stale_etag", "lm-stale", "2024-01-01T00:00:00Z"
        ) == (
            "old_etag",
            "lm-old",
            "2024-06-10T00:00:00Z",
        )
        assert conn.execute("SELECT COUNT(*) FROM chunks_vec").fetchone()[0] == 1

    def test_fresh_incoming_wins(self) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn)
        mgr = self._mgr(conn, db, doc_id)
        assert mgr.resolve_incoming("new_etag", "lm-new", "2024-06-20T00:00:00Z") == (
            "new_etag",
            "lm-new",
            "2024-06-20T00:00:00Z",
        )

    def test_both_none_keeps_stored_row(self) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn)
        mgr = self._mgr(conn, db, doc_id)
        assert mgr.resolve_incoming(None, None, "2024-06-20T00:00:00Z") == (
            "old_etag",
            "lm-old",
            "2024-06-10T00:00:00Z",
        )

    def test_both_none_without_stored_row_keeps_incoming(self) -> None:
        conn, db = _make_freshness_db()
        mgr = ETagManager(db, 999)  # type: ignore[arg-type]
        assert mgr.resolve_incoming(None, None, "2024-06-20T00:00:00Z") == (
            None,
            None,
            "2024-06-20T00:00:00Z",
        )

    def test_no_stored_row_keeps_incoming(self) -> None:
        conn, db = _make_freshness_db()
        mgr = ETagManager(db, 999)  # type: ignore[arg-type]
        assert mgr.resolve_incoming("new_etag", "lm-new", "2024-06-20T00:00:00Z") == (
            "new_etag",
            "lm-new",
            "2024-06-20T00:00:00Z",
        )

    def test_empty_new_fetched_at_raises_value_error(self) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn)
        mgr = self._mgr(conn, db, doc_id)
        with pytest.raises(ValueError):
            mgr.resolve_incoming("etag", "lm", "")

    def test_invalid_incoming_raises_incoming_error(self) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn)
        mgr = self._mgr(conn, db, doc_id)
        with pytest.raises(InvalidIncomingTimestampError):
            mgr.resolve_incoming("etag", "lm", "not-a-date")

    def test_invalid_stored_raises_stored_error(self) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn, fetched_at="not-a-date")
        mgr = self._mgr(conn, db, doc_id)
        with pytest.raises(InvalidStoredTimestampError):
            mgr.resolve_incoming("etag", "lm", "2024-06-20T00:00:00Z")


# ── handle_existing_document() HTTP branch validator-absence rule ────────────
#
# ragrev010 REQ-001..REQ-004: an HTTP page whose stored and incoming validator
# pairs are both absent must be re-ingested, while pages with equal non-null
# validators still skip. One shared absence helper (_has_validator) governs both
# the HTTP and file branches.


class TestHandleExistingDocumentHttpValidators:
    """HTTP branch: validators prove "unchanged" only when present and equal."""

    @pytest.mark.parametrize(
        "stored_etag,stored_lm,incoming_etag,incoming_lm,expected",
        [
            (None, None, None, None, (False, True)),  # REQ-001: absent pair re-ingests
            ("e", "lm", "e", "lm", (True, False)),  # REQ-002: equal non-null skips
            ("e", None, "e", None, (True, False)),  # one-sided present, equal
            (None, "lm", None, "lm", (True, False)),  # one-sided present, equal
            ("e", "lm", "e2", "lm", (False, True)),  # differing etag
            ("e", "lm", "e", "lm2", (False, True)),  # differing last_modified
            ("e", "lm", None, None, (False, True)),  # incoming absent
            (None, None, "e", "lm", (False, True)),  # stored absent
            ("e", None, "e", "lm", (False, True)),  # last_modified differs
        ],
    )
    def test_http_validator_matrix(
        self,
        stored_etag: str | None,
        stored_lm: str | None,
        incoming_etag: str | None,
        incoming_lm: str | None,
        expected: tuple[bool, bool],
    ) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn, etag=stored_etag, last_modified=stored_lm)
        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]

        _id, skip, replace = doc_mgr.handle_existing_document(
            "https://example.com/doc",
            doc_id,
            False,
            incoming_etag,
            incoming_lm,
            "2024-06-20T00:00:00Z",
            lambda u: False,
        )
        assert (skip, replace) == expected
        # No freshness write happens on the handle_existing_document path.
        assert _freshness_row(conn) == (
            (stored_etag, stored_lm, "2024-06-10T00:00:00Z"),
        )

    def test_http_force_true_with_absent_validators(self) -> None:
        conn, db = _make_freshness_db()
        doc_id = _seed_document(conn, etag=None, last_modified=None)
        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]

        _id, skip, replace = doc_mgr.handle_existing_document(
            "https://example.com/doc",
            doc_id,
            True,
            None,
            None,
            "2024-06-20T00:00:00Z",
            lambda u: False,
        )
        assert (skip, replace) == (False, True)

    def test_http_missing_stored_row(self) -> None:
        conn, db = _make_freshness_db()
        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]

        result = doc_mgr.handle_existing_document(
            "https://example.com/doc",
            999,
            False,
            None,
            None,
            "2024-06-20T00:00:00Z",
            lambda u: False,
        )
        assert result == (999, False, False)

    def test_has_validator_returns_presence(self) -> None:
        assert DocumentManager._has_validator(None, None) is False
        assert DocumentManager._has_validator(None, "x") is True
        assert DocumentManager._has_validator("e", None) is True

    def test_is_file_unchanged_still_guards_none_etag(self) -> None:
        assert not DocumentManager._is_file_unchanged(None, "lm", "e", "lm")
        assert not DocumentManager._is_file_unchanged("e", "lm", None, "lm")
        assert DocumentManager._is_file_unchanged("e", "lm", "e", "lm")
