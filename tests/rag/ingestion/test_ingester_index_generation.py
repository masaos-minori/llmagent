"""tests/rag/ingestion/test_ingester_index_generation.py

RAGCORPUS001 REQ-001: ``RagIngester.ingest_all()`` advances the corpus
``index_generation`` exactly once per completed run that wrote new content.

The bump is best-effort (``rag.corpus_identity.bump_index_generation`` never
raises); these tests lock that contract end-to-end through the real
``ingest_all()`` path using a temp RAG database and a fake ``SQLiteHelper`` that
delegates to a real ``sqlite3.Connection`` (same technique as
``tests/rag/ingestion/test_rag_ingestion_pipeline.py``).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

from rag.corpus_identity import ensure_corpus_meta
from rag.ingestion.embedding import EmbeddingService
from rag.ingestion.ingester import RagIngester


def _make_rag_db(tmp_path: Path) -> sqlite3.Connection:
    """Create a temporary RAG database without vec0/fts5 virtual tables."""
    conn = sqlite3.connect(str(tmp_path / "test_rag.sqlite"))
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
            normalized_content TEXT,
            chunk_type         TEXT,
            source_file        TEXT
        );
        CREATE TABLE IF NOT EXISTS chunks_vec (
            chunk_id           INTEGER PRIMARY KEY REFERENCES chunks(chunk_id) ON DELETE CASCADE,
            embedding          BLOB
        );
        CREATE TABLE IF NOT EXISTS rag_corpus_meta (
            corpus_id                TEXT    NOT NULL,
            index_generation         INTEGER NOT NULL,
            embedding_model_id       TEXT    NOT NULL,
            normalization_version    TEXT    NOT NULL,
            chunking_policy_version  TEXT    NOT NULL,
            updated_at               TEXT    NOT NULL,
            CHECK (rowid = 1)
        );
        """
    )
    conn.commit()
    return conn


def _make_rag_db_without_meta(tmp_path: Path) -> sqlite3.Connection:
    """Like :func:`_make_rag_db` but without the ``rag_corpus_meta`` table."""
    conn = sqlite3.connect(str(tmp_path / "test_rag_no_meta.sqlite"))
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS documents (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE, title TEXT, lang TEXT NOT NULL
                CHECK (lang IN ('ja', 'en')), fetched_at TEXT NOT NULL
                DEFAULT (datetime('now')), etag TEXT, last_modified TEXT,
            chunking_strategy TEXT NOT NULL DEFAULT 'text'
        );
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id INTEGER NOT NULL
                REFERENCES documents(doc_id) ON DELETE CASCADE, chunk_index
                INTEGER NOT NULL, content TEXT NOT NULL, normalized_content TEXT,
            chunk_type TEXT, source_file TEXT
        );
        CREATE TABLE IF NOT EXISTS chunks_vec (
            chunk_id INTEGER PRIMARY KEY REFERENCES chunks(chunk_id)
                ON DELETE CASCADE, embedding BLOB
        );
        """
    )
    conn.commit()
    return conn


def _make_fake_sqlite_helper(conn: sqlite3.Connection) -> MagicMock:
    """Fake SQLiteHelper delegating execute/fetchall to a real connection."""
    conn.row_factory = sqlite3.Row
    mock_sh = MagicMock()
    mock_sh.execute = MagicMock(side_effect=conn.execute)
    mock_sh.fetchall = MagicMock(
        side_effect=lambda sql, params=(): conn.execute(sql, params).fetchall()
    )

    class _BeginImmediate:
        def __enter__(self) -> sqlite3.Connection:
            conn.execute("BEGIN IMMEDIATE")
            return conn

        def __exit__(self, *exc: object) -> bool:
            if exc[0] is None:
                conn.execute("COMMIT")
            else:
                conn.execute("ROLLBACK")
            return False

    mock_sh.begin_immediate.return_value = _BeginImmediate()
    mock_sh.open.return_value.__enter__.return_value = mock_sh
    return mock_sh


def _write_chunk(chunk_dir: Path) -> None:
    """Write one valid chunk JSON so ingest_all() has content to process."""
    chunk_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": "1",
        "artifact_type": "chunk",
        "created_by": "chunk_splitter",
        "url": "http://example.com/page",
        "title": "Test Page",
        "lang": "en",
        "content": "Hello world from the test page. " * 50,
        "chunking_strategy": "heading",
        "normalized_content": None,
        "chunk_index": 0,
        "etag": "etag-test-page",
        "last_modified": "2024-01-01T00:00:00",
        "fetched_at": "2024-01-01T00:00:00",
        "chunk_type": "",
        "source_file": "",
        "code_blocks": [],
    }
    (chunk_dir / "2024-01-01-test-page.json").write_text(json.dumps(data))


def _make_ingester(tmp_path: Path, db_path: Path) -> RagIngester:
    cfg = {
        "rag_src_dir": str(tmp_path),
        "embed_url": "http://localhost:8081/embedding",
        "embed_retry": "1",
        "embed_workers": "1",
        "rag_db_path": str(db_path),
        "sqlite_vec_so": "",
    }
    return RagIngester(config=cfg)


def _seed_generation(
    conn: sqlite3.Connection,
    *,
    embedding_model_id: str = "test-embed-v1",
    schema_version: str = "1",
) -> str:
    """Insert a rag_corpus_meta row at generation 0; return its corpus_id."""
    identity = ensure_corpus_meta(
        conn,
        embedding_model_id=embedding_model_id,
        schema_version=schema_version,
    )
    assert identity is not None
    return identity.corpus_id


def _read_generation(conn: sqlite3.Connection) -> int | None:
    # Tolerate a missing table (Test C verifies best-effort behaviour when the
    # rag_corpus_meta table does not exist).
    try:
        row = conn.execute(
            "SELECT index_generation FROM rag_corpus_meta LIMIT 1"
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    return int(row[0]) if row is not None else None


class TestIngestAllIndexGenerationBump:
    def test_completed_ingest_advances_generation_by_one(self, tmp_path: Path) -> None:
        """A run that writes new content advances index_generation by exactly one."""
        conn = _make_rag_db(tmp_path)
        corpus_id = _seed_generation(conn)
        _write_chunk(tmp_path / "chunk")
        ingester = _make_ingester(tmp_path, tmp_path / "test_rag.sqlite")

        mock_report = MagicMock()
        mock_report.issues = []

        with (
            patch(
                "rag.ingestion.ingester.SQLiteHelper",
                return_value=_make_fake_sqlite_helper(conn),
            ),
            patch(
                "rag.ingestion.document_manager.check_rag_consistency",
                return_value=mock_report,
            ),
            patch.object(EmbeddingService, "get_embedding", return_value=[0.1] * 128),
        ):
            result = ingester.ingest_all()

        assert result is not None
        assert _read_generation(conn) == 1
        # The corpus identity is otherwise intact after the bump.
        # NOTE: rag_corpus_meta has no schema_version column; schema_version is a
        # caller-supplied value, never persisted (see scripts/db/schema_sql.py).
        row = conn.execute(
            "SELECT corpus_id, index_generation FROM rag_corpus_meta LIMIT 1"
        ).fetchone()
        assert row[0] == corpus_id
        assert int(row[1]) == 1

    def test_no_chunk_files_leaves_generation_unchanged(self, tmp_path: Path) -> None:
        """A no-op run (no chunk files) must not bump the generation."""
        conn = _make_rag_db(tmp_path)
        _seed_generation(conn)
        (tmp_path / "chunk").mkdir(exist_ok=True)
        ingester = _make_ingester(tmp_path, tmp_path / "test_rag.sqlite")

        with (
            patch(
                "rag.ingestion.ingester.SQLiteHelper",
                return_value=_make_fake_sqlite_helper(conn),
            ),
            patch.object(EmbeddingService, "get_embedding"),
        ):
            result = ingester.ingest_all()

        assert result is None
        assert _read_generation(conn) == 0

    def test_missing_meta_table_returns_none_without_raising(
        self, tmp_path: Path
    ) -> None:
        """A missing meta table yields None (best-effort) rather than raising."""
        conn = _make_rag_db_without_meta(tmp_path)
        _write_chunk(tmp_path / "chunk")
        ingester = _make_ingester(tmp_path, tmp_path / "test_rag_no_meta.sqlite")

        mock_report = MagicMock()
        mock_report.issues = []

        with (
            patch(
                "rag.ingestion.ingester.SQLiteHelper",
                return_value=_make_fake_sqlite_helper(conn),
            ),
            patch(
                "rag.ingestion.document_manager.check_rag_consistency",
                return_value=mock_report,
            ),
            patch.object(EmbeddingService, "get_embedding", return_value=[0.1] * 128),
        ):
            # Must not raise even though bump_index_generation() finds no table.
            ingester.ingest_all()

        assert _read_generation(conn) is None
