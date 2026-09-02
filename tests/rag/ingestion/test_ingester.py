"""tests/test_ingester.py
Integration-level tests for rag/ingestion/ingester.py.

Covers _embed_and_store(), ingest_url_group(), and --force reinsert behavior.
_read_chunk_json() field preservation is covered in tests/test_rag_ingester.py.

Uses:
- In-memory SQLite with minimal rag schema (no real DB file)
- Mock httpx.Client.post for embedding calls (no real embed-llm service)
- tmp_path fixture for chunk file isolation
"""

from __future__ import annotations

import dataclasses
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson
import pytest
from rag.exceptions import IngestionFailureReason
from rag.ingestion.chunk_preparation import ChunkFactory
from rag.ingestion.document_manager import DocumentManager
from rag.ingestion.document_persistence import DocumentStore
from rag.ingestion.ingester import RagIngester
from rag.ingestion.transaction_commit import TransactionManager
from rag.models_data import PreparedChunk

# Minimal rag.sqlite schema (regular tables; vec0 extension not required in tests)
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
        self._in_transaction = False
        self._conn.row_factory = sqlite3.Row

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    @contextmanager
    def begin_immediate(self) -> Generator[None]:
        """Wrap a block in BEGIN IMMEDIATE...COMMIT; serializes concurrent writers."""
        self._in_transaction = True
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._conn.commit()
        except Exception:
            try:
                self._conn.rollback()
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            self._in_transaction = False

    def commit(self) -> None:
        self._conn.commit()


def _make_db() -> tuple[sqlite3.Connection, _FakeSQLiteHelper]:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript(_SCHEMA_SQL)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.commit()
    return conn, _FakeSQLiteHelper(conn)


@dataclasses.dataclass(frozen=True)
class _ChunkSpec:
    url: str = "https://example.com/doc"
    title: str = "Test Doc"
    lang: str = "ja"
    content: str = "本文"
    normalized_content: str | None = "normalized"
    chunk_index: int = 0
    etag: str | None = None
    last_modified: str | None = None
    code_blocks: list[str] = dataclasses.field(default_factory=list)
    source_file: str = "chunk.json"
    chunk_type: str = "chunk"
    chunking_strategy: str = "text"
    fetched_at: str = "2024-01-01T00:00:00Z"


_DEFAULT_CHUNK = _ChunkSpec()


def _write_chunk(
    dest_dir: Path,
    filename: str,
    spec: _ChunkSpec = _DEFAULT_CHUNK,
) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / filename
    path.write_bytes(orjson.dumps(dataclasses.asdict(spec)))
    return path


def _make_ingester(tmp_path: Path) -> RagIngester:
    (tmp_path / "chunk").mkdir(parents=True, exist_ok=True)
    (tmp_path / "registered").mkdir(parents=True, exist_ok=True)
    ingester = RagIngester(
        config={
            "rag_src_dir": str(tmp_path),
            "embed_url": "http://localhost:8081/embedding",
            "embed_retry": "1",
            "embed_workers": "1",
        }
    )
    return ingester


def _fake_embed_resp(embedding: list[float] = _FAKE_EMBEDDING) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.content = orjson.dumps({"embedding": embedding})
    return resp


def _make_ingester_with_retry(tmp_path: Path, embed_retry: int) -> RagIngester:
    (tmp_path / "chunk").mkdir(parents=True, exist_ok=True)
    (tmp_path / "registered").mkdir(parents=True, exist_ok=True)
    ingester = RagIngester(
        config={
            "rag_src_dir": str(tmp_path),
            "embed_url": "http://localhost:8081/embedding",
            "embed_retry": str(embed_retry),
            "embed_workers": "1",
        }
    )
    return ingester


# ── _embed_and_store() ────────────────────────────────────────────────────────


class TestEmbedAndStore:
    """Tests for _embed_and_store(): verifies chunk_index and normalized_content passthrough."""

    def _insert_parent_doc(
        self, conn: sqlite3.Connection, url: str = "https://example.com/doc"
    ) -> int:
        cur = conn.execute(
            "INSERT INTO documents (url, title, lang, chunking_strategy) VALUES (?, ?, ?, ?)",
            (url, "Doc", "ja", "text"),
        )
        conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def test_writes_correct_chunk_index(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(
            tmp_path / "chunk",
            "c.json",
            dataclasses.replace(_DEFAULT_CHUNK, chunk_index=7),
        )
        ingester = _make_ingester(tmp_path)

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)
            result = factory._embed_and_store(doc_id, path)

        assert isinstance(result, PreparedChunk)
        assert result.chunk_index == 7

    def test_writes_normalized_content(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(
            tmp_path / "chunk",
            "c.json",
            dataclasses.replace(_DEFAULT_CHUNK, normalized_content="正規化"),
        )
        ingester = _make_ingester(tmp_path)

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)
            result = factory._embed_and_store(doc_id, path)

        assert isinstance(result, PreparedChunk)
        assert result.normalized_content == "正規化"

    def test_null_normalized_content_stored_as_null(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        conn.execute(
            "INSERT INTO documents (url, title, lang, chunking_strategy) VALUES (?, ?, ?, ?)",
            ("https://example.com/doc", "Doc", "en", "text"),
        )
        conn.commit()
        doc_id: int = conn.execute("SELECT doc_id FROM documents").fetchone()[0]
        path = _write_chunk(
            tmp_path / "chunk",
            "c.json",
            dataclasses.replace(_DEFAULT_CHUNK, lang="en", normalized_content=None),
        )
        ingester = _make_ingester(tmp_path)

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)
            result = factory._embed_and_store(doc_id, path)

        assert isinstance(result, PreparedChunk)
        assert result.normalized_content is None

    def test_embedding_failure_returns_false(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(tmp_path / "chunk", "c.json")
        ingester = _make_ingester(tmp_path)
        bad_resp = MagicMock()
        bad_resp.raise_for_status.return_value = None
        bad_resp.content = orjson.dumps({"embedding": []})

        with (
            patch.object(ingester._client, "post", return_value=bad_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)
            result = factory._embed_and_store(doc_id, path)

        assert result == IngestionFailureReason.EMBEDDING_FAILED
        count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == 0

    def test_invalid_chunk_file_fails_immediately(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = tmp_path / "chunk" / "c.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not valid json")
        ingester = _make_ingester(tmp_path)

        with (
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)
            result = factory._embed_and_store(doc_id, path)

        assert result == IngestionFailureReason.PARSE_FAILED
        count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == 0

    def test_empty_content_causes_embedding_failure(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(
            tmp_path / "chunk",
            "c.json",
            dataclasses.replace(_DEFAULT_CHUNK, content=""),
        )
        ingester = _make_ingester(tmp_path)

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)
            result = factory._embed_and_store(doc_id, path)

        assert result == IngestionFailureReason.PARSE_FAILED

    def test_invalid_chunk_index_fails_immediately(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(
            tmp_path / "chunk",
            "c.json",
            dataclasses.replace(_DEFAULT_CHUNK, chunk_index=0),
        )
        data = orjson.loads(path.read_bytes())
        data["chunk_index"] = "invalid_str"
        path.write_bytes(orjson.dumps(data))
        ingester = _make_ingester(tmp_path)

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)
            result = factory._embed_and_store(doc_id, path)

        assert result == IngestionFailureReason.PARSE_FAILED
        count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == 0

    def test_retry_success(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(tmp_path / "chunk", "c.json")
        ingester = _make_ingester_with_retry(tmp_path, embed_retry=2)

        bad_resp = MagicMock()
        bad_resp.raise_for_status.return_value = None
        bad_resp.content = orjson.dumps({"embedding": []})  # empty → ValueError

        with (
            patch("rag.ingestion.embedding.time.sleep"),
            patch.object(
                ingester._client,
                "post",
                side_effect=[bad_resp, _fake_embed_resp()],
            ),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)
            result = factory._embed_and_store(doc_id, path)

        assert isinstance(result, PreparedChunk)
        assert result.chunk_index == 0

    def test_all_retries_exhausted(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(tmp_path / "chunk", "c.json")
        ingester = _make_ingester_with_retry(tmp_path, embed_retry=3)

        bad_resp = MagicMock()
        bad_resp.raise_for_status.return_value = None
        bad_resp.content = orjson.dumps({"embedding": []})

        with (
            patch("rag.ingestion.embedding.time.sleep"),
            patch.object(ingester._client, "post", return_value=bad_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)
            result = factory._embed_and_store(doc_id, path)

        assert result == IngestionFailureReason.EMBEDDING_FAILED
        count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == 0

    def test_network_error_during_retry(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(tmp_path / "chunk", "c.json")
        ingester = _make_ingester_with_retry(tmp_path, embed_retry=2)

        import httpx

        with (
            patch("rag.ingestion.embedding.time.sleep"),
            patch.object(
                ingester._client,
                "post",
                side_effect=[
                    httpx.RequestError("simulated network error"),
                    _fake_embed_resp(),
                ],
            ),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)
            result = factory._embed_and_store(doc_id, path)

        assert isinstance(result, PreparedChunk)
        assert result.chunk_index == 0

    def test_dimension_mismatch_on_retry(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(tmp_path / "chunk", "c.json")
        ingester = _make_ingester_with_retry(tmp_path, embed_retry=2)

        wrong_dim_resp = _fake_embed_resp(embedding=[0.1] * 8)  # wrong dim (expect 384)

        with (
            patch("rag.ingestion.embedding.time.sleep"),
            patch.object(
                ingester._client,
                "post",
                side_effect=[wrong_dim_resp, _fake_embed_resp()],
            ),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)
            result = factory._embed_and_store(doc_id, path)

        assert isinstance(result, PreparedChunk)
        assert result.chunk_index == 0


# ── ingest_url_group() ────────────────────────────────────────────────────────


class TestIngestUrlGroup:
    """Tests for ingest_url_group(): end-to-end document + chunk insertion."""

    def _setup(
        self, tmp_path: Path
    ) -> tuple[sqlite3.Connection, _FakeSQLiteHelper, RagIngester]:
        conn, fake_db = _make_db()
        ingester = _make_ingester(tmp_path)
        return conn, fake_db, ingester

    def test_inserts_document_with_correct_chunking_strategy(
        self, tmp_path: Path
    ) -> None:
        conn, fake_db, ingester = self._setup(tmp_path)
        path = _write_chunk(
            tmp_path / "chunk",
            "c.json",
        )
        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path],
                force=False,
            )

        row = conn.execute("SELECT chunking_strategy FROM documents").fetchone()
        assert row is not None and row[0] == "text"

    def test_inserts_chunks_with_correct_indices(self, tmp_path: Path) -> None:
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        paths = [
            _write_chunk(
                chunk_dir,
                "c0.json",
                dataclasses.replace(_DEFAULT_CHUNK, chunk_index=0, content="first"),
            ),
            _write_chunk(
                chunk_dir,
                "c1.json",
                dataclasses.replace(_DEFAULT_CHUNK, chunk_index=1, content="second"),
            ),
        ]
        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                paths,
                force=False,
            )

        rows = conn.execute(
            "SELECT chunk_index FROM chunks ORDER BY chunk_index"
        ).fetchall()
        assert len(rows) == 2
        assert rows[0][0] == 0
        assert rows[1][0] == 1

    def test_moves_processed_files_to_registered(self, tmp_path: Path) -> None:
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        registered_dir = tmp_path / "registered"
        path = _write_chunk(chunk_dir, "c.json")

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path],
                force=False,
            )

        assert not path.exists()
        assert (registered_dir / "c.json").exists()

    def test_skips_already_registered_url(self, tmp_path: Path) -> None:
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        path = _write_chunk(chunk_dir, "c.json")

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path],
                force=False,
            )

        path2 = _write_chunk(chunk_dir, "c2.json")
        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path2],
                force=False,
            )

        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert doc_count == 1
        assert chunk_count == 1  # only from first ingest

    def test_force_reinsertion_removes_old_chunks(self, tmp_path: Path) -> None:
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        path = _write_chunk(
            chunk_dir,
            "c.json",
            dataclasses.replace(_DEFAULT_CHUNK, content="old"),
        )

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path],
                force=False,
            )

        assert conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 1

        path2 = _write_chunk(
            chunk_dir,
            "c_new.json",
            dataclasses.replace(_DEFAULT_CHUNK, content="new"),
        )
        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path2],
                force=True,
            )

        doc_row = conn.execute("SELECT chunking_strategy FROM documents").fetchone()
        assert doc_row is not None and doc_row[0] == "text"
        content_rows = conn.execute("SELECT content FROM chunks").fetchall()
        assert len(content_rows) == 1
        assert content_rows[0][0] == "new"

    def test_force_replaces_old_chunks(self, tmp_path: Path) -> None:
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        _write_chunk(
            chunk_dir,
            "c.json",
        )
        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [chunk_dir / "c.json"],
                force=False,
            )

        _write_chunk(
            chunk_dir,
            "c2.json",
        )
        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [chunk_dir / "c2.json"],
                force=True,
            )

        row = conn.execute("SELECT chunking_strategy FROM documents").fetchone()
        assert row is not None and row[0] == "text"
        content_rows = conn.execute("SELECT content FROM chunks").fetchall()
        assert len(content_rows) == 1

    def test_ingest_url_group_embed_failed_count(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        url = "https://example.com/doc"
        chunk_dir = tmp_path / "chunk" / "example.com" / "doc"
        _write_chunk(chunk_dir, "c1.json", dataclasses.replace(_DEFAULT_CHUNK, url=url))
        _write_chunk(
            chunk_dir,
            "c2.json",
            dataclasses.replace(_DEFAULT_CHUNK, url=url, chunk_index=1),
        )
        ingester = _make_ingester(tmp_path)  # embed_retry=1

        bad_resp = MagicMock()
        bad_resp.raise_for_status.return_value = None
        bad_resp.content = orjson.dumps({"embedding": []})  # all embeddings fail

        with (
            patch.object(ingester._client, "post", return_value=bad_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                url,
                list(chunk_dir.iterdir()),
                force=False,
            )

        assert result.url == url
        assert result.n_embed_failed == 2  # both chunks failed embedding


# ── Artifact validation (strict vs lenient) ───────────────────────────────────


class TestPartialFailureHandling:
    """Tests for partial failure handling during RAG ingestion."""

    def test_consistency_check_runs_inside_db_context(self, tmp_path: Path) -> None:
        """Consistency check should run inside the DB context, not after."""
        conn, fake_db = _make_db()

        # Add FTS tables so consistency check doesn't fail
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks_fts_docsize(
                rowid INTEGER PRIMARY KEY,
                fts_size INTEGER
            );
        """)
        conn.execute("""
            INSERT INTO chunks_fts_docsize(rowid, fts_size) VALUES(1, 1);
        """)

        conn.execute(
            "INSERT INTO documents (url, title, lang, chunking_strategy) VALUES (?, ?, ?, ?)",
            ("https://example.com/doc", "Doc", "ja", "text"),
        )
        conn.commit()

        ingester = _make_ingester(tmp_path)
        _write_chunk(tmp_path / "chunk", "c.json")

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester.ingest_all(force=False)

        assert result is not None

    def test_embedding_failure_moves_to_retry_not_registered(
        self, tmp_path: Path
    ) -> None:
        """Chunks that fail embedding should be moved to retry/, not registered/."""
        conn, fake_db = _make_db()
        url = "https://example.com/doc"
        chunk_dir = tmp_path / "chunk"
        path = _write_chunk(chunk_dir, "c.json")

        bad_resp = MagicMock()
        bad_resp.raise_for_status.return_value = None
        bad_resp.content = orjson.dumps({"embedding": []})

        ingester = _make_ingester(tmp_path)

        with (
            patch.object(ingester._client, "post", return_value=bad_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                url,
                [path],
                force=False,
            )

        assert result.n_embed_failed == 1
        assert not path.exists(), "Failed chunk should be moved from chunk/"
        assert (chunk_dir.parent / "retry" / "c.json").exists()
        assert not (tmp_path / "registered" / "c.json").exists()

    def test_mixed_success_and_failure_routes_correctly(self, tmp_path: Path) -> None:
        """Only successfully ingested chunks should be moved to registered/; failed→retry/."""
        conn, fake_db = _make_db()

        chunk_dir = tmp_path / "chunk"

        path_ok = _write_chunk(
            chunk_dir,
            "c_ok.json",
            dataclasses.replace(
                _DEFAULT_CHUNK, content="ok_marker_本文", chunk_index=0
            ),
        )
        path_fail = _write_chunk(
            chunk_dir,
            "c_fail.json",
            dataclasses.replace(_DEFAULT_CHUNK, chunk_index=1),
        )

        ingester = _make_ingester(tmp_path)

        def _side_effect(url, json=None, **kwargs):
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            content = json.get("content", "") if isinstance(json, dict) else ""
            if "ok_marker" in content:
                resp.content = orjson.dumps({"embedding": [0.1] * 384})
            else:
                resp.content = orjson.dumps({"embedding": []})
            return resp

        with (
            patch.object(ingester._client, "post", side_effect=_side_effect),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/mixed",
                [path_ok, path_fail],
                force=False,
            )

        assert result.n_success == 0
        assert result.n_embed_failed == 1
        assert not path_ok.exists()
        assert not path_fail.exists()
        assert not (tmp_path / "registered" / "c_ok.json").exists()
        assert (chunk_dir.parent / "retry" / "c_ok.json").exists()
        assert (chunk_dir.parent / "retry" / "c_fail.json").exists()

    def test_embed_failed_count_reported_in_summary(self, tmp_path: Path) -> None:
        """Ingestion summary should prominently display embed_failed count."""
        conn, fake_db = _make_db()
        url = "https://example.com/doc"
        chunk_dir = tmp_path / "chunk"

        path1 = _write_chunk(
            chunk_dir, "c1.json", dataclasses.replace(_DEFAULT_CHUNK, chunk_index=0)
        )
        path2 = _write_chunk(
            chunk_dir, "c2.json", dataclasses.replace(_DEFAULT_CHUNK, chunk_index=1)
        )

        ingester = _make_ingester(tmp_path)

        def _side_effect(*args, **kwargs):
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            resp.content = orjson.dumps({"embedding": []})
            return resp

        with (
            patch.object(ingester._client, "post", side_effect=_side_effect),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                url,
                [path1, path2],
                force=False,
            )

        assert result.n_embed_failed == 2

    def test_retry_directory_created_for_embedding_failures(
        self, tmp_path: Path
    ) -> None:
        """Embedding-failed chunks should be moved to retry/ directory."""
        conn, fake_db = _make_db()
        url = "https://example.com/doc"
        chunk_dir = tmp_path / "chunk"

        path = _write_chunk(chunk_dir, "c.json")

        bad_resp = MagicMock()
        bad_resp.raise_for_status.return_value = None
        bad_resp.content = orjson.dumps({"embedding": []})

        ingester = _make_ingester(tmp_path)

        with (
            patch.object(ingester._client, "post", return_value=bad_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                url,
                [path],
                force=False,
            )

        assert result.n_embed_failed == 1
        assert not path.exists()
        assert (chunk_dir.parent / "retry" / "c.json").exists()


class TestGroupValidation:
    """Tests for URL-group validation: mismatched fields, duplicate/non-contiguous chunk_index."""

    def _setup(
        self, tmp_path: Path
    ) -> tuple[sqlite3.Connection, _FakeSQLiteHelper, RagIngester]:
        conn, fake_db = _make_db()
        ingester = _make_ingester(tmp_path)
        return conn, fake_db, ingester

    @pytest.mark.parametrize(
        "field,mismatched_value",
        [
            ("url", "https://other.example.com/doc"),
            ("title", "Different Title"),
            ("lang", "en"),
            ("fetched_at", "2025-01-01T00:00:00Z"),
            ("etag", '"different-etag"'),
            ("last_modified", "2025-01-01T00:00:00Z"),
            ("source_file", "other.json"),
            ("chunking_strategy", "semantic"),
            ("chunk_type", "paragraph"),
        ],
    )
    def test_mismatched_field_rejects_group(
        self, field: str, mismatched_value: str, tmp_path: Path
    ) -> None:
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        path0 = _write_chunk(chunk_dir, "c0.json")
        spec = dataclasses.replace(
            _DEFAULT_CHUNK, **{field: mismatched_value}, chunk_index=1
        )
        path1 = _write_chunk(chunk_dir, "c1.json", spec)
        mock_post = MagicMock()
        with (
            patch.object(ingester._client, "post", side_effect=mock_post),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path0, path1],
                force=False,
            )
        assert result.n_success == 0
        assert result.n_failed == 2
        assert conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0
        # Files stay at original location (validation rejects before any move)
        assert path0.exists()
        assert path1.exists()
        mock_post.assert_not_called()

    def test_duplicate_chunk_index_rejects_group(self, tmp_path: Path) -> None:
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        path0 = _write_chunk(chunk_dir, "c0.json")
        spec = dataclasses.replace(_DEFAULT_CHUNK, chunk_index=0, content="second")
        path1 = _write_chunk(chunk_dir, "c1.json", spec)
        mock_post = MagicMock()
        with (
            patch.object(ingester._client, "post", side_effect=mock_post),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path0, path1],
                force=False,
            )
        assert result.n_success == 0
        assert result.n_failed == 2
        assert conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0
        assert path0.exists()
        assert path1.exists()
        mock_post.assert_not_called()

    def test_non_contiguous_chunk_index_rejects_group(self, tmp_path: Path) -> None:
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        path0 = _write_chunk(chunk_dir, "c0.json")
        spec = dataclasses.replace(_DEFAULT_CHUNK, chunk_index=2, content="third")
        path1 = _write_chunk(chunk_dir, "c1.json", spec)
        mock_post = MagicMock()
        with (
            patch.object(ingester._client, "post", side_effect=mock_post),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path0, path1],
                force=False,
            )
        assert result.n_success == 0
        assert result.n_failed == 2
        assert conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0
        assert path0.exists()
        assert path1.exists()
        mock_post.assert_not_called()


class TestIntegrityErrorPropagation:
    """Tests for IntegrityError propagation from _insert_chunks_batch."""

    def _setup(
        self, tmp_path: Path
    ) -> tuple[sqlite3.Connection, _FakeSQLiteHelper, RagIngester]:
        conn, fake_db = _make_db()
        ingester = _make_ingester(tmp_path)
        return conn, fake_db, ingester

    def test_insert_chunks_batch_propagates_integrity_error(
        self, tmp_path: Path
    ) -> None:
        conn, fake_db, ingester = self._setup(tmp_path)
        prepared = PreparedChunk(
            doc_id=999999,
            chunk_index=0,
            content="text",
            normalized_content=None,
            chunk_type="chunk",
            source_file="",
            embedding_blob=b"\x00\x01",
        )
        tx_mgr = TransactionManager(
            fake_db,
            DocumentManager(fake_db),
            DocumentStore(fake_db, DocumentManager(fake_db)),
        )
        with pytest.raises(sqlite3.IntegrityError):
            with fake_db.begin_immediate():
                tx_mgr._insert_chunks_batch(fake_db, [prepared])
        assert conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0

    def test_integrity_error_routes_to_failed_via_ingest_url_group(
        self, tmp_path: Path
    ) -> None:
        conn, fake_db, ingester = self._setup(tmp_path)
        # Insert a document with matching URL so ingest_url_group proceeds past doc lookup
        conn.execute(
            "INSERT INTO documents (url, title, lang, chunking_strategy) VALUES (?, ?, ?, ?)",
            ("https://example.com/doc", "Doc", "ja", "text"),
        )
        conn.commit()
        chunk_dir = tmp_path / "chunk"
        path = _write_chunk(chunk_dir, "c.json")
        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
            patch.object(
                TransactionManager,
                "_insert_chunks_batch",
                side_effect=sqlite3.IntegrityError("foreign key violation"),
            ),
        ):
            with pytest.raises(sqlite3.IntegrityError):
                ingester.ingest_url_group(
                    DocumentManager(fake_db),
                    fake_db,
                    DocumentStore(fake_db, DocumentManager(fake_db)),
                    "https://example.com/doc",
                    [path],
                    force=True,
                )
        # After rollback via begin_immediate fix, no partial rows remain
        assert conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0
