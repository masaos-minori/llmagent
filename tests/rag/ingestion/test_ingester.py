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
from db.store_protocols import get_embedding_dims
from rag.exceptions import IngestionFailureReason
from rag.ingestion.chunk_preparation import ChunkFactory
from rag.ingestion.document_manager import DocumentManager
from rag.ingestion.document_persistence import DocumentStore
from rag.ingestion.file_routing import FileRouter
from rag.ingestion.ingester import RagIngester
from rag.ingestion.transaction_commit import TransactionManager
from rag.models_data import PreparedChunk

# Canonical rag.sqlite DDL (scripts/db/schema_sql.py _RAG_SCHEMA_TEMPLATE), with the
# vec0 virtual table replaced by a plain stand-in: the schema fingerprint compares
# virtual tables by NAME only, so a plain `chunks_vec` is equivalent in fixtures.
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    url                TEXT    NOT NULL UNIQUE,
    title              TEXT,
    lang               TEXT    NOT NULL CHECK (lang IN ('ja', 'en')),
    fetched_at         TEXT    NOT NULL,
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
    chunk_type         TEXT    NOT NULL DEFAULT 'text',
    source_file        TEXT    NOT NULL DEFAULT '',
    UNIQUE (doc_id, chunk_index),
    CHECK (chunk_index >= 0),
    CHECK (chunk_type IN ('text', 'code')),
    CHECK (length(content) > 0)
);
CREATE TABLE IF NOT EXISTS chunks_vec (
    chunk_id  INTEGER PRIMARY KEY,
    embedding BLOB NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content,
    content       = 'chunks',
    content_rowid = 'chunk_id',
    tokenize      = 'unicode61'
);
CREATE TRIGGER IF NOT EXISTS chunks_ai
AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts (rowid, content)
    VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad
AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts (chunks_fts, rowid, content)
    VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
END;
CREATE TRIGGER IF NOT EXISTS chunks_au
AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts (chunks_fts, rowid, content)
    VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
    INSERT INTO chunks_fts (rowid, content)
    VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
END;
CREATE TRIGGER IF NOT EXISTS chunks_vec_ad
AFTER DELETE ON chunks BEGIN
    DELETE FROM chunks_vec WHERE chunk_id = old.chunk_id;
END;
"""

_DIM = get_embedding_dims()
_FAKE_EMBEDDING = [0.1] * _DIM


class _FakeSQLiteHelper:
    """In-memory SQLite wrapper satisfying the SQLiteHelper interface used by ingester."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.conn = conn  # db.conn alias: consistency probes reach the raw connection
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
    chunk_type: str = "text"
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


def _error_reasons(failed_dir: Path, stems: list[str]) -> list[str]:
    """Read the failure_reason of each routed chunk file's .error.json sidecar."""
    return [
        str(
            orjson.loads((failed_dir / f"{stem}.error.json").read_bytes())[
                "failure_reason"
            ]
        )
        for stem in stems
    ]


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
            "INSERT INTO documents (url, title, lang, chunking_strategy, fetched_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (url, "Doc", "ja", "text", "2026-01-01T00:00:00Z"),
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
            "INSERT INTO documents (url, title, lang, chunking_strategy, fetched_at)"
            " VALUES (?, ?, ?, ?, ?)",
            ("https://example.com/doc", "Doc", "en", "text", "2026-01-01T00:00:00Z"),
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

        wrong_dim_resp = _fake_embed_resp(
            embedding=[0.1] * 8
        )  # wrong dim (expect get_embedding_dims())

        with patch.object(ingester._client, "post", return_value=wrong_dim_resp):
            factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)
            result = factory._embed_and_store(doc_id, path)

        # seq-1: the size check runs after get_embedding returns, so no retry happens
        # and the failure is deterministic VALIDATION_FAILED, not a PreparedChunk.
        assert result is IngestionFailureReason.VALIDATION_FAILED


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
        first = _ChunkSpec(etag='"e1"', last_modified="lm1")
        path = _write_chunk(chunk_dir, "c.json", first)

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

        second = _ChunkSpec(etag='"e1"', last_modified="lm1", content="别本文")
        path2 = _write_chunk(chunk_dir, "c2.json", second)
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
        stored_content = conn.execute(
            "SELECT content FROM chunks ORDER BY chunk_index"
        ).fetchone()[0]
        assert stored_content == "本文"  # second ingest skipped, first retained

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

    def test_wrong_size_embedding_routes_group_to_failed(self, tmp_path: Path) -> None:
        """AC-1: a wrong-size embedding routes the whole group to failed/ with no commit."""
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        paths = [
            _write_chunk(
                chunk_dir,
                "c0.json",
                dataclasses.replace(_DEFAULT_CHUNK, chunk_index=0),
            ),
            _write_chunk(
                chunk_dir,
                "c1.json",
                dataclasses.replace(_DEFAULT_CHUNK, chunk_index=1),
            ),
        ]
        wrong_dim_resp = _fake_embed_resp(
            embedding=[0.1] * 8
        )  # 8 dims != get_embedding_dims()
        with (
            patch.object(ingester._client, "post", return_value=wrong_dim_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
            patch.object(TransactionManager, "commit") as mock_commit,
        ):
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                paths,
                force=False,
            )
        mock_commit.assert_not_called()  # the failed_paths gate skips commit entirely
        assert result.n_failed == 2
        failed_dir = tmp_path / "failed"
        assert _error_reasons(failed_dir, ["c0", "c1"]) == [
            "validation_failed",
            "validation_failed",
        ]
        assert not any(chunk_dir.iterdir())  # nothing left in chunk/
        assert conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0


# ── Artifact validation (strict vs lenient) ───────────────────────────────────


class TestPartialFailureHandling:
    """Tests for partial failure handling during RAG ingestion."""

    def test_consistency_check_runs_inside_db_context(self, tmp_path: Path) -> None:
        """Consistency check should run inside the DB context, not after."""
        conn, fake_db = _make_db()

        conn.execute(
            "INSERT INTO documents (url, title, lang, chunking_strategy, fetched_at)"
            " VALUES (?, ?, ?, ?, ?)",
            ("https://example.com/doc", "Doc", "ja", "text", "2026-01-01T00:00:00Z"),
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

    def test_embedding_failure_moves_to_failed_not_registered(
        self, tmp_path: Path
    ) -> None:
        """Chunks that fail embedding should be moved to failed/, not registered/."""
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
        assert (chunk_dir.parent / "failed" / "c.json").exists()
        assert (chunk_dir.parent / "failed" / "c.error.json").exists()
        assert not (chunk_dir.parent / "retry").exists()
        assert not (tmp_path / "registered" / "c.json").exists()

    def test_mixed_success_and_failure_routes_correctly(self, tmp_path: Path) -> None:
        """A group with any failure drains every chunk to failed/; nothing reaches registered/ or retry/."""
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
            patch("rag.ingestion.file_routing.logger") as mocked_logger,
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
        assert (chunk_dir.parent / "failed" / "c_ok.json").exists()
        assert (chunk_dir.parent / "failed" / "c_ok.error.json").exists()
        assert (chunk_dir.parent / "failed" / "c_fail.json").exists()
        assert (chunk_dir.parent / "failed" / "c_fail.error.json").exists()
        assert not (chunk_dir.parent / "retry").exists()
        mocked_logger.warning.assert_not_called()

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

    def test_retry_directory_is_never_created(self, tmp_path: Path) -> None:
        """The retry/ tier is never created: not after an embedding failure, not after a clean run."""
        conn, fake_db = _make_db()
        chunk_dir = tmp_path / "chunk"

        # A run with an embedding failure.
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
                "https://example.com/doc",
                [path],
                force=False,
            )
        assert result.n_embed_failed == 1
        assert not path.exists()
        assert not (chunk_dir.parent / "retry").exists()
        assert (chunk_dir.parent / "failed" / "c.json").exists()

        # A clean run with no failures.
        conn.commit()
        path_ok = _write_chunk(chunk_dir, "ok.json")
        ingester2 = _make_ingester(tmp_path)
        with (
            patch.object(ingester2._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester2.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/clean",
                [path_ok],
                force=False,
            )
        assert not (chunk_dir.parent / "retry").exists()
        assert (tmp_path / "registered" / "ok.json").exists()

    def test_route_unknown_reason_warns_and_goes_to_failed(
        self, tmp_path: Path
    ) -> None:
        """An unknown failure reason logs a WARNING naming the reason and file, then routes to failed/."""
        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        path = _write_chunk(chunk_dir, "c.json")
        router = FileRouter(tmp_path / "registered", chunk_dir)
        reason = "some httpx error text"

        with patch("rag.ingestion.file_routing.logger") as mocked_logger:
            router.route([], [(path, reason)])
            assert mocked_logger.warning.called
            matched = False
            for call in mocked_logger.warning.call_args_list:
                if (
                    len(call.args) >= 3
                    and str(call.args[1]) == reason
                    and str(call.args[2]) == str(path)
                ):
                    matched = True
            assert matched

        assert not path.exists()
        assert (chunk_dir.parent / "failed" / "c.json").exists()
        assert (chunk_dir.parent / "failed" / "c.error.json").exists()
        assert not (chunk_dir.parent / "retry").exists()


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
            ("chunk_type", "code"),
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
        assert result.failure_reason == IngestionFailureReason.GROUP_VALIDATION_FAILED
        # REQ-003: a rejected group is drained to failed/ with .error.json metadata
        assert not path0.exists() and not path1.exists()
        failed_dir = tmp_path / "failed"
        assert (failed_dir / "c0.json").exists() and (failed_dir / "c1.json").exists()
        assert _error_reasons(failed_dir, ["c0", "c1"]) == [
            "group_validation_failed",
            "group_validation_failed",
        ]
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
        # REQ-003: a rejected group is drained to failed/ with .error.json metadata
        assert not path0.exists() and not path1.exists()
        failed_dir = tmp_path / "failed"
        assert (failed_dir / "c0.json").exists() and (failed_dir / "c1.json").exists()
        assert _error_reasons(failed_dir, ["c0", "c1"]) == [
            "group_validation_failed",
            "group_validation_failed",
        ]
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
        # REQ-003: a rejected group is drained to failed/ with .error.json metadata
        assert not path0.exists() and not path1.exists()
        failed_dir = tmp_path / "failed"
        assert (failed_dir / "c0.json").exists() and (failed_dir / "c1.json").exists()
        assert _error_reasons(failed_dir, ["c0", "c1"]) == [
            "group_validation_failed",
            "group_validation_failed",
        ]
        mock_post.assert_not_called()

    def test_malformed_first_file_routes_group_as_parse_failed(
        self, tmp_path: Path
    ) -> None:
        """ChunkFormatError on the first file drains the whole group (REQ-003 site 1)."""
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        path0 = chunk_dir / "c0.json"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        path0.write_bytes(orjson.dumps({"url": "https://example.com/doc"}))
        path1 = _write_chunk(
            chunk_dir, "c1.json", dataclasses.replace(_DEFAULT_CHUNK, chunk_index=1)
        )
        with patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db):
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path0, path1],
                force=False,
            )
        assert result.failure_reason == IngestionFailureReason.PARSE_FAILED
        assert not path0.exists() and not path1.exists()
        failed_dir = tmp_path / "failed"
        # FileRouter writes a generic sidecar even for the unparseable payload (seq-7
        # always-write guarantee); the parseable sibling gets the full-metadata sidecar.
        assert _error_reasons(failed_dir, ["c0", "c1"]) == [
            "parse_failed",
            "parse_failed",
        ]

    def test_malformed_later_file_routes_group_as_parse_failed(
        self, tmp_path: Path
    ) -> None:
        """ChunkFormatError on a later file drains the whole group (REQ-003 site 2)."""
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        path0 = _write_chunk(chunk_dir, "c0.json")
        path1 = chunk_dir / "c1.json"
        path1.write_bytes(
            orjson.dumps({"url": "https://example.com/doc", "chunk_index": 1})
        )
        with patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db):
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path0, path1],
                force=False,
            )
        assert result.failure_reason == IngestionFailureReason.PARSE_FAILED
        assert not path0.exists() and not path1.exists()
        failed_dir = tmp_path / "failed"
        assert _error_reasons(failed_dir, ["c0", "c1"]) == [
            "parse_failed",
            "parse_failed",
        ]

    def test_unparseable_payload_still_gets_error_sidecar(self, tmp_path: Path) -> None:
        """seq-7 always-write guarantee: an unreadable payload gets a generic sidecar."""
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        path = chunk_dir / "c0.json"
        path.write_bytes(b"not a chunk payload")
        with patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db):
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path],
                force=False,
            )
        assert result.failure_reason == IngestionFailureReason.PARSE_FAILED
        failed_dir = tmp_path / "failed"
        sidecar = failed_dir / "c0.error.json"
        assert sidecar.exists()
        metadata = orjson.loads(sidecar.read_bytes())
        assert metadata["failure_reason"] == "parse_failed"
        assert (
            "url" not in metadata
        )  # payload-derived keys omitted by the generic envelope
        assert "chunk_index" not in metadata


class TestGenerationDrain:
    """REQ-003/REQ-004/AC-2/AC-4: rejected files drain out and generations resolve oldest-first."""

    def test_two_generations_ingest_oldest_first_newest_final(
        self, tmp_path: Path
    ) -> None:
        """Two generations of one URL are ingested independently; the newest writes last."""
        conn, fake_db = _make_db()
        chunk_dir = tmp_path / "chunk"
        _write_chunk(
            chunk_dir,
            "old-0.json",
            dataclasses.replace(
                _DEFAULT_CHUNK,
                content="old",
                etag='"gen-2024"',
                last_modified="2024-01-01T00:00:00Z",
                fetched_at="2024-01-01T00:00:00Z",
            ),
        )
        _write_chunk(
            chunk_dir,
            "new-0.json",
            dataclasses.replace(
                _DEFAULT_CHUNK,
                content="new",
                etag='"gen-2025"',
                last_modified="2025-06-01T00:00:00Z",
                fetched_at="2025-06-01T00:00:00Z",
            ),
        )
        ingester = _make_ingester(tmp_path)

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_all(force=True)

        row = conn.execute(
            "SELECT fetched_at FROM documents WHERE url = ?",
            ("https://example.com/doc",),
        ).fetchone()
        assert row is not None
        assert row["fetched_at"] == "2025-06-01T00:00:00Z"
        contents = [
            r["content"]
            for r in conn.execute("SELECT content FROM chunks ORDER BY chunk_id")
        ]
        assert contents == ["new"]
        registered = sorted(p.name for p in (tmp_path / "registered").iterdir())
        assert registered == ["new-0.json", "old-0.json"]
        assert list((tmp_path / "chunk").glob("*.json")) == []

    def test_second_ingest_all_reprocesses_no_drained_files(
        self, tmp_path: Path
    ) -> None:
        """After a group is drained to failed/, a second run re-processes nothing."""
        conn, fake_db = _make_db()
        chunk_dir = tmp_path / "chunk"
        _write_chunk(chunk_dir, "good-0.json")
        _write_chunk(
            chunk_dir,
            "bad-0.json",
            dataclasses.replace(_DEFAULT_CHUNK, url="not-a-url"),
        )
        ingester = _make_ingester(tmp_path)

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_all(force=False)

        failed_dir = tmp_path / "failed"
        assert (failed_dir / "bad-0.json").exists()
        assert _error_reasons(failed_dir, ["bad-0"]) == ["validation_failed"]
        assert not (chunk_dir / "bad-0.json").exists()
        assert (tmp_path / "registered" / "good-0.json").exists()

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester.ingest_all(force=False)

        assert result is None
        assert sorted(p.name for p in failed_dir.iterdir()) == [
            "bad-0.error.json",
            "bad-0.json",
        ]


class TestIntegrityErrorPropagation:
    """Tests for sqlite3 error handling split: propagation from TransactionManager, quarantine in the ingester.

    IntegrityError is deterministic: ingest_url_group routes the group to failed/ with
    STORAGE_FAILED (commit_url_group). Other sqlite3.Error (e.g. lock timeouts) stay
    retryable: they propagate to _process_url_groups and move no files.
    """

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
            "INSERT INTO documents (url, title, lang, chunking_strategy, fetched_at)"
            " VALUES (?, ?, ?, ?, ?)",
            ("https://example.com/doc", "Doc", "ja", "text", "2026-01-01T00:00:00Z"),
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
            result = ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                DocumentStore(fake_db, DocumentManager(fake_db)),
                "https://example.com/doc",
                [path],
                force=True,
            )
        # AC-3: a deterministic IntegrityError quarantines the group instead of retrying
        assert result.failure_reason == IngestionFailureReason.STORAGE_FAILED
        failed_dir = tmp_path / "failed"
        assert (failed_dir / "c.json").exists()
        assert _error_reasons(failed_dir, ["c"]) == ["storage_failed"]
        # After rollback via begin_immediate fix, no partial rows remain
        assert conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0

    def test_transient_operational_error_keeps_group_retryable(
        self, tmp_path: Path
    ) -> None:
        """AC-4: a transient sqlite3.OperationalError propagates and moves no files."""
        conn, fake_db, ingester = self._setup(tmp_path)
        conn.execute(
            "INSERT INTO documents (url, title, lang, chunking_strategy, fetched_at)"
            " VALUES (?, ?, ?, ?, ?)",
            ("https://example.com/doc", "Doc", "ja", "text", "2026-01-01T00:00:00Z"),
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
                side_effect=sqlite3.OperationalError("database is locked"),
            ),
        ):
            with pytest.raises(sqlite3.OperationalError):
                ingester.ingest_url_group(
                    DocumentManager(fake_db),
                    fake_db,
                    DocumentStore(fake_db, DocumentManager(fake_db)),
                    "https://example.com/doc",
                    [path],
                    force=True,
                )
        # retryable: the group stays in chunk/ for the next run, nothing routed to failed/
        assert path.exists()
        assert not (tmp_path / "failed").exists()
