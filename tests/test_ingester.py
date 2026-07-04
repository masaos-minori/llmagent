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
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson
from rag.ingestion.document_manager import DocumentManager
from rag.ingestion.ingester import RagIngester

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


def _make_db() -> tuple[sqlite3.Connection, _FakeSQLiteHelper]:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript(_SCHEMA_SQL)
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
    chunking_strategy: str = "heading"
    etag: str | None = None
    last_modified: str | None = None


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
            "embed_url": "http://localhost:8003/embedding",
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
            "embed_url": "http://localhost:8003/embedding",
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
            result = ingester._embed_and_store(doc_id, path)

        assert result == (True, True)
        row = conn.execute(
            "SELECT chunk_index FROM chunks WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        assert row is not None and row[0] == 7

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
            ingester._embed_and_store(doc_id, path)

        row = conn.execute(
            "SELECT normalized_content FROM chunks WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        assert row is not None and row[0] == "正規化"

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
            ingester._embed_and_store(doc_id, path)

        row = conn.execute(
            "SELECT normalized_content FROM chunks WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        assert row is not None and row[0] is None

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
            result = ingester._embed_and_store(doc_id, path)

        assert result == (False, False)
        count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == 0

    def test_read_chunk_json_returns_none_fails_immediately(
        self, tmp_path: Path
    ) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(tmp_path / "chunk", "c.json")
        ingester = _make_ingester(tmp_path)

        with (
            patch.object(ingester, "_read_chunk_json", return_value=None),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester._embed_and_store(doc_id, path)

        assert result == (False, False)
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
            result = ingester._embed_and_store(doc_id, path)

        assert result == (False, False)
        count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == 0

    def test_invalid_chunk_index_falls_back_to_zero(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(
            tmp_path / "chunk",
            "c.json",
            dataclasses.replace(_DEFAULT_CHUNK, chunk_index=0),
        )
        # Overwrite with invalid chunk_index string
        data = orjson.loads(path.read_bytes())
        data["chunk_index"] = "invalid_str"
        path.write_bytes(orjson.dumps(data))
        ingester = _make_ingester(tmp_path)

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester._embed_and_store(doc_id, path)

        assert result == (True, True)
        row = conn.execute(
            "SELECT chunk_index FROM chunks WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        assert row is not None and row[0] == 0

    def test_retry_success(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(tmp_path / "chunk", "c.json")
        ingester = _make_ingester_with_retry(tmp_path, embed_retry=2)

        bad_resp = MagicMock()
        bad_resp.raise_for_status.return_value = None
        bad_resp.content = orjson.dumps({"embedding": []})  # empty → ValueError

        with (
            patch("rag.ingestion.ingester.time.sleep"),
            patch.object(
                ingester._client,
                "post",
                side_effect=[bad_resp, _fake_embed_resp()],
            ),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester._embed_and_store(doc_id, path)

        assert result == (True, True)
        count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == 1

    def test_all_retries_exhausted(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(tmp_path / "chunk", "c.json")
        ingester = _make_ingester_with_retry(tmp_path, embed_retry=3)

        bad_resp = MagicMock()
        bad_resp.raise_for_status.return_value = None
        bad_resp.content = orjson.dumps({"embedding": []})

        with (
            patch("rag.ingestion.ingester.time.sleep"),
            patch.object(ingester._client, "post", return_value=bad_resp),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester._embed_and_store(doc_id, path)

        assert result == (False, False)
        count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == 0

    def test_network_error_during_retry(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(tmp_path / "chunk", "c.json")
        ingester = _make_ingester_with_retry(tmp_path, embed_retry=2)

        import httpx

        with (
            patch("rag.ingestion.ingester.time.sleep"),
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
            result = ingester._embed_and_store(doc_id, path)

        assert result == (True, True)
        count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == 1

    def test_dimension_mismatch_on_retry(self, tmp_path: Path) -> None:
        conn, fake_db = _make_db()
        doc_id = self._insert_parent_doc(conn)
        path = _write_chunk(tmp_path / "chunk", "c.json")
        ingester = _make_ingester_with_retry(tmp_path, embed_retry=2)

        wrong_dim_resp = _fake_embed_resp(embedding=[0.1] * 8)  # wrong dim (expect 384)

        with (
            patch("rag.ingestion.ingester.time.sleep"),
            patch.object(
                ingester._client,
                "post",
                side_effect=[wrong_dim_resp, _fake_embed_resp()],
            ),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            result = ingester._embed_and_store(doc_id, path)

        assert result == (True, True)
        count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        assert count == 1


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
            dataclasses.replace(_DEFAULT_CHUNK, chunking_strategy="heading"),
        )
        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                "https://example.com/doc",
                [path],
                force=False,
            )

        row = conn.execute("SELECT chunking_strategy FROM documents").fetchone()
        assert row is not None and row[0] == "heading"

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
            dataclasses.replace(
                _DEFAULT_CHUNK, chunking_strategy="text", content="old"
            ),
        )

        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                "https://example.com/doc",
                [path],
                force=False,
            )

        assert conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 1

        path2 = _write_chunk(
            chunk_dir,
            "c_new.json",
            dataclasses.replace(
                _DEFAULT_CHUNK, chunking_strategy="heading", content="new"
            ),
        )
        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                "https://example.com/doc",
                [path2],
                force=True,
            )

        doc_row = conn.execute("SELECT chunking_strategy FROM documents").fetchone()
        assert doc_row is not None and doc_row[0] == "heading"
        content_rows = conn.execute("SELECT content FROM chunks").fetchall()
        assert len(content_rows) == 1
        assert content_rows[0][0] == "new"

    def test_force_preserves_new_chunking_strategy(self, tmp_path: Path) -> None:
        conn, fake_db, ingester = self._setup(tmp_path)
        chunk_dir = tmp_path / "chunk"
        _write_chunk(
            chunk_dir,
            "c.json",
            dataclasses.replace(_DEFAULT_CHUNK, chunking_strategy="text"),
        )
        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                "https://example.com/doc",
                [chunk_dir / "c.json"],
                force=False,
            )

        _write_chunk(
            chunk_dir,
            "c2.json",
            dataclasses.replace(_DEFAULT_CHUNK, chunking_strategy="markdown"),
        )
        with (
            patch.object(ingester._client, "post", return_value=_fake_embed_resp()),
            patch("rag.ingestion.ingester.SQLiteHelper", return_value=fake_db),
        ):
            ingester.ingest_url_group(
                DocumentManager(fake_db),
                fake_db,
                "https://example.com/doc",
                [chunk_dir / "c2.json"],
                force=True,
            )

        row = conn.execute("SELECT chunking_strategy FROM documents").fetchone()
        assert row is not None and row[0] == "markdown"

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
                url,
                list(chunk_dir.iterdir()),
                force=False,
            )

        assert result.url == url
        assert result.n_embed_failed == 2  # both chunks failed embedding


# ── Artifact validation (strict vs lenient) ───────────────────────────────────


class TestValidateArtifact:
    BASE_PAYLOAD = {
        "artifact_type": "chunk",
        "schema_version": "1",
        "created_by": "chunk_splitter",
    }

    def test_lenient_missing_schema_version_passes(self) -> None:
        payload = {k: v for k, v in self.BASE_PAYLOAD.items() if k != "schema_version"}
        assert RagIngester._validate_artifact(payload, "chunk", strict=False) is True

    def test_lenient_missing_created_by_passes(self) -> None:
        payload = {k: v for k, v in self.BASE_PAYLOAD.items() if k != "created_by"}
        assert RagIngester._validate_artifact(payload, "chunk", strict=False) is True

    def test_lenient_wrong_artifact_type_rejects(self) -> None:
        assert (
            RagIngester._validate_artifact(self.BASE_PAYLOAD, "image", strict=False)
            is False
        )

    def test_strict_missing_schema_version_rejects(self) -> None:
        payload = {k: v for k, v in self.BASE_PAYLOAD.items() if k != "schema_version"}
        assert RagIngester._validate_artifact(payload, "chunk", strict=True) is False

    def test_strict_missing_artifact_type_rejects(self) -> None:
        payload = {k: v for k, v in self.BASE_PAYLOAD.items() if k != "artifact_type"}
        assert RagIngester._validate_artifact(payload, "chunk", strict=True) is False

    def test_strict_missing_created_by_rejects(self) -> None:
        payload = {k: v for k, v in self.BASE_PAYLOAD.items() if k != "created_by"}
        assert RagIngester._validate_artifact(payload, "chunk", strict=True) is False

    def test_strict_all_fields_correct_type_passes(self) -> None:
        assert (
            RagIngester._validate_artifact(self.BASE_PAYLOAD, "chunk", strict=True)
            is True
        )
