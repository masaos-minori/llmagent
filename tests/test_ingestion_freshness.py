"""tests/test_ingestion_freshness.py
Unit tests for file:// freshness detection in crawler.py and ingester.py.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any

from rag.ingestion.document_manager import DocumentManager
from rag.ingestion.ingester import RagIngester

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


# ── _get_or_create_document() freshness for file:// ──────────────────────────


def _make_ingester(tmp_path: Path) -> RagIngester:
    cfg: dict[str, Any] = {
        "rag_src_dir": str(tmp_path / "rag-src"),
        "embed_url": "http://localhost:8003",
        "embed_retry": 3,
    }
    return RagIngester(cfg)


def _make_fake_db(
    url: str, etag: str | None, last_modified: str | None
) -> tuple[Any, int]:
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
        "INSERT INTO documents (url, title, lang, etag, last_modified, chunking_strategy)"
        " VALUES (?, ?, ?, ?, ?, ?)",
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
        ingester = _make_ingester(tmp_path)
        ingester.close()

        doc_mgr = DocumentManager(db)  # type: ignore[arg-type]
        result = ingester._get_or_create_document(
            doc_mgr,
            db,
            url,
            "test.txt",
            "en",
            force=False,
            etag=sha,
            last_modified="2024-01-02",
        )
        assert result is None

    def test_changed_sha256_triggers_reingest(self, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        url = "file:///tmp/test.txt"
        db, _doc_id = _make_fake_db(url, "old_sha", "2024-01-01")
        ingester = _make_ingester(tmp_path)
        ingester.close()

        mock_doc_mgr = MagicMock()
        mock_doc_mgr.handle_existing_document.return_value = False
        ingester._get_or_create_document(
            mock_doc_mgr,
            db,
            url,
            "test.txt",
            "en",
            force=False,
            etag="new_sha",
            last_modified="2024-01-02",
        )
        mock_doc_mgr.delete_existing_document.assert_called_once()

    def test_force_true_skips_freshness_check(self, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        sha = "abc123"
        url = "file:///tmp/test.txt"
        db, _doc_id = _make_fake_db(url, sha, "2024-01-01")
        ingester = _make_ingester(tmp_path)
        ingester.close()

        mock_doc_mgr = MagicMock()
        mock_doc_mgr.handle_existing_document.return_value = False
        ingester._get_or_create_document(
            mock_doc_mgr,
            db,
            url,
            "test.txt",
            "en",
            force=True,
            etag=sha,
            last_modified="2024-01-01",
        )
        # force=True always calls delete regardless of hash equality
        mock_doc_mgr.delete_existing_document.assert_called_once()

    def test_non_file_url_uses_etag_update_path(self, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        url = "https://example.com/doc"
        db, doc_id = _make_fake_db(url, "old_etag", "2024-01-01")
        ingester = _make_ingester(tmp_path)
        ingester.close()

        mock_doc_mgr = MagicMock()
        mock_doc_mgr.handle_existing_document.return_value = True
        result = ingester._get_or_create_document(
            mock_doc_mgr,
            db,
            url,
            "doc",
            "en",
            force=False,
            etag="new_etag",
            last_modified="2024-01-02",
        )
        assert result is None
        mock_doc_mgr.handle_existing_document.assert_called_once()
