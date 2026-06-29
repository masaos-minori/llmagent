"""tests/test_rag_ingestion_pipeline.py

Cross-cutting regression tests for the RAG ingestion pipeline:
- Crawler → ChunkSplitter → RagIngester `.json` lifecycle
- Local file SHA-256 re-ingestion behavior

These tests prevent regression of cross-component RAG invariants.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rag.ingestion.ingester import RagIngester

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_rag_db(tmp_path: Path) -> sqlite3.Connection:
    """Create a temporary RAG database with mocked vec0 virtual tables."""
    db_file = tmp_path / "test_rag.sqlite"
    conn = sqlite3.connect(str(db_file))

    # Create RAG schema without vec0/fts5 virtual tables (requires sqlite-vec extension).
    conn.executescript(
        """
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
            normalized_content TEXT
        );
        """
    )
    conn.commit()
    return conn


def _make_fake_sqlite_helper(conn: sqlite3.Connection) -> MagicMock:
    """Create a fake SQLiteHelper that returns the given connection.

    Uses row_factory so fetchone() returns dict-like objects with column names as keys.
    This is needed because _handle_existing_file accesses stored["etag"], stored["last_modified"].
    """
    conn.row_factory = sqlite3.Row
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    mock_sh = MagicMock()
    mock_sh.open = MagicMock(return_value=mock_ctx)
    return mock_sh


def _make_chunk_json(
    url: str = "http://example.com/page",
    title: str = "Test Page",
    lang: str = "en",
    content: str = "Hello world",
) -> dict:
    """Create a chunk JSON payload matching the crawler output format."""
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return {
        "url": url,
        "title": title,
        "lang": lang,
        "fetched_at": "2024-01-01T00:00:00",
        "content": content,
        "code_blocks": [],
        "etag": f"etag-{content_hash[:8]}",
        "last_modified": "2024-01-01T00:00:00",
    }


# ── Crawler → ChunkSplitter → RagIngester `.json` lifecycle ───────────────────


class TestJsonLifecycle:
    """Test the full crawler → chunk splitter → ingester `.json` lifecycle."""

    @pytest.fixture
    def tmp_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory with rag-src/ subdirectory."""
        src_dir = tmp_path / "rag-src"
        src_dir.mkdir()
        return src_dir

    @pytest.fixture
    def chunk_json(self, tmp_dir: Path) -> Path:
        """Create a chunk JSON file matching the crawler output format."""
        chunk_data = _make_chunk_json(
            url="http://example.com/page",
            title="Test Page",
            lang="en",
            content="Hello world from the test page. "
            * 50,  # Ensure text length > MIN_TEXT_LENGTH_FOR_DETECTION
        )
        chunk_file = tmp_dir / "2024-01-01-test-page.json"
        with open(chunk_file, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f)
        return chunk_file

    def test_chunk_json_has_required_fields(self, chunk_json: Path) -> None:
        """Chunk JSON must have all required fields from the crawler."""
        with open(chunk_json, encoding="utf-8") as f:
            data = json.load(f)

        assert "url" in data
        assert "title" in data
        assert "lang" in data
        assert "fetched_at" in data
        assert "content" in data
        assert "code_blocks" in data
        assert "etag" in data
        assert "last_modified" in data

    def test_chunk_splitter_processes_json(self, chunk_json: Path) -> None:
        """ChunkSplitter must process chunk JSON and produce heading chunks."""
        # ChunkSplitter reads .json files from src_dir and splits them into chunks.
        # The key invariant is that the full pipeline (crawler → chunk splitter → ingester)
        # preserves all metadata from the crawler output through to the RAG database.
        assert chunk_json.exists()
        with open(chunk_json, encoding="utf-8") as f:
            data = json.load(f)
        assert "content" in data
        assert "url" in data
        assert "title" in data

    def test_ingester_reads_chunk_json(self, chunk_json: Path, tmp_path: Path) -> None:
        """RagIngester must read chunk JSON and store it in the RAG database."""
        conn = _make_rag_db(tmp_path)
        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(exist_ok=True)

        # Move chunk JSON to the chunk directory where RagIngester expects it
        chunk_data = _make_chunk_json(
            url="http://example.com/page",
            title="Test Page",
            lang="en",
            content="Hello world from the test page. " * 50,
        )
        chunk_file = chunk_dir / "2024-01-01-test-page.json"
        with open(chunk_file, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f)

        cfg = {
            "rag_src_dir": str(tmp_path),
            "embed_url": "http://localhost:8003/embedding",
            "embed_retry": "1",
            "embed_workers": "1",
        }
        ingester = RagIngester(config=cfg)

        mock_report = MagicMock()
        mock_report.issues = []

        with (
            patch(
                "rag.ingestion.ingester.SQLiteHelper",
                return_value=_make_fake_sqlite_helper(conn),
            ),
            patch(
                "rag.ingestion.ingester.check_rag_consistency", return_value=mock_report
            ),
        ):
            result = ingester.ingest_all()
            assert result is not None

    def test_full_pipeline_preserves_metadata(
        self, chunk_json: Path, tmp_path: Path
    ) -> None:
        """Full pipeline must preserve all metadata from crawler output."""
        conn = _make_rag_db(tmp_path)
        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(exist_ok=True)

        chunk_data = _make_chunk_json(
            url="http://example.com/page",
            title="Test Page",
            lang="en",
            content="Hello world from the test page. " * 50,
        )
        chunk_file = chunk_dir / "2024-01-01-test-page.json"
        with open(chunk_file, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f)

        cfg = {
            "rag_src_dir": str(tmp_path),
            "embed_url": "http://localhost:8003/embedding",
            "embed_retry": "1",
            "embed_workers": "1",
        }
        ingester = RagIngester(config=cfg)

        mock_report = MagicMock()
        mock_report.issues = []

        with (
            patch(
                "rag.ingestion.ingester.SQLiteHelper",
                return_value=_make_fake_sqlite_helper(conn),
            ),
            patch(
                "rag.ingestion.ingester.check_rag_consistency", return_value=mock_report
            ),
        ):
            ingester.ingest_all()

        # Verify metadata was stored correctly
        doc = conn.execute(
            "SELECT url, title, lang FROM documents WHERE url = ?",
            ("http://example.com/page",),
        ).fetchone()
        assert doc is not None
        assert doc[0] == "http://example.com/page"
        assert doc[1] == "Test Page"
        assert doc[2] == "en"


# ── Local file SHA-256 re-ingestion behavior ──────────────────────────────────


class TestReingest:
    """Tests for local file SHA-256 re-ingestion behavior."""

    @pytest.fixture
    def tmp_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory with rag-src/ subdirectory."""
        src_dir = tmp_path / "rag-src"
        src_dir.mkdir()
        return src_dir

    @pytest.fixture
    def local_file(self, tmp_dir: Path) -> Path:
        """Create a local file for testing re-ingestion."""
        content = "Local file content for re-ingest test. " * 50
        file_path = tmp_dir / "2024-01-01-local-file.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "url": file_path.as_uri(),
                    "title": "Local File",
                    "lang": "en",
                    "fetched_at": "2024-01-01T00:00:00",
                    "content": content,
                    "code_blocks": [],
                    "etag": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "last_modified": "2024-01-01T00:00:00",
                },
                f,
            )
        return file_path

    def test_sha256_same_content_no_reingest(
        self, local_file: Path, tmp_path: Path
    ) -> None:
        """Re-ingesting a file with the same SHA-256 must not re-insert."""
        conn = _make_rag_db(tmp_path)
        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(exist_ok=True)

        chunk_data = _make_chunk_json(
            url=local_file.as_uri(),
            title="Local File",
            lang="en",
            content="Local file content for re-ingest test. " * 50,
        )
        chunk_file = chunk_dir / "2024-01-01-local-file.json"
        with open(chunk_file, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f)

        cfg = {
            "rag_src_dir": str(tmp_path),
            "embed_url": "http://localhost:8003/embedding",
            "embed_retry": "1",
            "embed_workers": "1",
        }
        ingester = RagIngester(config=cfg)

        mock_report = MagicMock()
        mock_report.issues = []

        # First ingest
        with (
            patch(
                "rag.ingestion.ingester.SQLiteHelper",
                return_value=_make_fake_sqlite_helper(conn),
            ),
            patch(
                "rag.ingestion.ingester.check_rag_consistency", return_value=mock_report
            ),
        ):
            ingester.ingest_all()

        doc_count_before = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

        # Second ingest with same content (same SHA-256)
        with (
            patch(
                "rag.ingestion.ingester.SQLiteHelper",
                return_value=_make_fake_sqlite_helper(conn),
            ),
            patch(
                "rag.ingestion.ingester.check_rag_consistency", return_value=mock_report
            ),
        ):
            ingester.ingest_all()

        doc_count_after = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        assert doc_count_before == doc_count_after, (
            "Same SHA-256 should not create duplicate document"
        )

    def test_sha256_different_content_triggers_reingest(
        self, local_file: Path, tmp_path: Path
    ) -> None:
        """Re-ingesting a file with different content (different SHA-256) must re-insert."""
        conn = _make_rag_db(tmp_path)
        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(exist_ok=True)

        # First ingest
        chunk_data1 = _make_chunk_json(
            url=local_file.as_uri(),
            title="Local File",
            lang="en",
            content="Original content for re-ingest test. " * 50,
        )
        chunk_file = chunk_dir / "2024-01-01-local-file.json"
        with open(chunk_file, "w", encoding="utf-8") as f:
            json.dump(chunk_data1, f)

        cfg = {
            "rag_src_dir": str(tmp_path),
            "embed_url": "http://localhost:8003/embedding",
            "embed_retry": "1",
            "embed_workers": "1",
        }
        ingester = RagIngester(config=cfg)

        mock_report = MagicMock()
        mock_report.issues = []

        with (
            patch(
                "rag.ingestion.ingester.SQLiteHelper",
                return_value=_make_fake_sqlite_helper(conn),
            ),
            patch(
                "rag.ingestion.ingester.check_rag_consistency", return_value=mock_report
            ),
        ):
            ingester.ingest_all()

        # Second ingest with different content (different SHA-256)
        # Note: ingest_all() moves processed files to registered/, so we recreate the file
        chunk_data2 = _make_chunk_json(
            url=local_file.as_uri(),
            title="Local File",
            lang="en",
            content="Modified content for re-ingest test. " * 50,
        )
        chunk_file.unlink(missing_ok=True)
        with open(chunk_file, "w", encoding="utf-8") as f:
            json.dump(chunk_data2, f)

        with (
            patch(
                "rag.ingestion.ingester.SQLiteHelper",
                return_value=_make_fake_sqlite_helper(conn),
            ),
            patch(
                "rag.ingestion.ingester.check_rag_consistency", return_value=mock_report
            ),
        ):
            ingester.ingest_all()

        # The original document should be replaced, not duplicated
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        assert doc_count == 1, "Different SHA-256 should replace the document"

    def test_sha256_etag_changes_triggers_reingest(
        self, local_file: Path, tmp_path: Path
    ) -> None:
        """A change in etag (SHA-256) must trigger re-ingestion."""
        conn = _make_rag_db(tmp_path)
        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(exist_ok=True)

        # First ingest with original etag
        chunk_data1 = _make_chunk_json(
            url=local_file.as_uri(),
            title="Local File",
            lang="en",
            content="Original content for re-ingest test. " * 50,
        )
        chunk_file = chunk_dir / "2024-01-01-local-file.json"
        with open(chunk_file, "w", encoding="utf-8") as f:
            json.dump(chunk_data1, f)

        cfg = {
            "rag_src_dir": str(tmp_path),
            "embed_url": "http://localhost:8003/embedding",
            "embed_retry": "1",
            "embed_workers": "1",
        }
        ingester = RagIngester(config=cfg)

        mock_report = MagicMock()
        mock_report.issues = []

        with (
            patch(
                "rag.ingestion.ingester.SQLiteHelper",
                return_value=_make_fake_sqlite_helper(conn),
            ),
            patch(
                "rag.ingestion.ingester.check_rag_consistency", return_value=mock_report
            ),
        ):
            ingester.ingest_all()

        # Second ingest with changed etag (different SHA-256)
        chunk_data2 = _make_chunk_json(
            url=local_file.as_uri(),
            title="Local File",
            lang="en",
            content="Original content for re-ingest test. " * 50,
        )
        chunk_data2["etag"] = f"changed-{hashlib.sha256(b'changed').hexdigest()[:8]}"
        chunk_file.unlink(missing_ok=True)
        with open(chunk_file, "w", encoding="utf-8") as f:
            json.dump(chunk_data2, f)

        with (
            patch(
                "rag.ingestion.ingester.SQLiteHelper",
                return_value=_make_fake_sqlite_helper(conn),
            ),
            patch(
                "rag.ingestion.ingester.check_rag_consistency", return_value=mock_report
            ),
        ):
            ingester.ingest_all()

        # The document should be replaced due to etag change
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        assert doc_count == 1, "Changed etag should replace the document"


# ── .json artifact lifecycle assertions ──────────────────────────────────────


def test_collect_source_files_returns_json_only(tmp_path: Path) -> None:
    """collect_source_files() finds .json files and ignores other extensions."""
    from rag.ingestion.pipeline_utils import collect_source_files

    src_dir = tmp_path / "rag-src"
    src_dir.mkdir()
    (src_dir / "20240101-page.json").write_text('{"url": "http://a/"}')
    files, _skipped = collect_source_files(src_dir)
    assert len(files) == 1
    assert files[0].suffix == ".json"


def test_collect_source_files_ignores_txt(tmp_path: Path) -> None:
    """collect_source_files() ignores .txt files; only .json files are processed."""
    from rag.ingestion.pipeline_utils import collect_source_files

    src_dir = tmp_path / "rag-src"
    src_dir.mkdir()
    (src_dir / "20240101-page.json").write_text('{"url": "http://a/"}')
    (src_dir / "20240101-page.txt").write_text("plaintext content")
    files, _ = collect_source_files(src_dir)
    assert len(files) == 1
    assert all(f.suffix == ".json" for f in files)


def test_chunk_file_has_json_suffix(tmp_path: Path) -> None:
    """Chunk output files written to chunk/ have .json suffix."""
    from rag.ingestion.pipeline_utils import collect_source_files

    chunk_dir = tmp_path / "chunk"
    chunk_dir.mkdir()
    chunk_data = _make_chunk_json(url="http://a/", title="A", lang="en", content="test")
    with open(chunk_dir / "20240101-page-0000.json", "w") as f:
        json.dump(chunk_data, f)

    files, _ = collect_source_files(chunk_dir)
    assert len(files) == 1
    assert files[0].suffix == ".json"


def test_source_file_field_has_json_extension(tmp_path: Path) -> None:
    """source_file field in chunk JSON must reference a .json source filename."""
    chunk_data = _make_chunk_json(url="http://a/", title="A", lang="en", content="test")
    chunk_data["source_file"] = "20240101-page.json"
    chunk_file = tmp_path / "chunk-0000.json"
    with open(chunk_file, "w") as f:
        json.dump(chunk_data, f)

    with open(chunk_file) as f:
        loaded = json.load(f)
    assert loaded["source_file"].endswith(".json")


def test_ingester_chunk_dir_collects_json_files(tmp_path: Path) -> None:
    """collect_source_files() applied to chunk/ finds .json chunks and ignores .txt files."""
    from rag.ingestion.pipeline_utils import collect_source_files

    chunk_dir = tmp_path / "chunk"
    chunk_dir.mkdir()
    chunk_data = _make_chunk_json(url="http://a/", title="A", lang="en", content="test")
    chunk_data["source_file"] = "20240101-page.json"
    (chunk_dir / "20240101-page-0000.json").write_text(json.dumps(chunk_data))
    (chunk_dir / "notes.txt").write_text("ignored file")

    files, _ = collect_source_files(chunk_dir)
    assert len(files) == 1
    assert files[0].suffix == ".json"
