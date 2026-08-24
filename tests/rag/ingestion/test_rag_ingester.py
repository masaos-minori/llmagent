from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson
import pytest
from db.helper import SQLiteHelper
from rag.ingestion.document_manager import DocumentManager
from rag.ingestion.ingester import (
    IngestUrlResult,
    PreparedChunk,
    RagIngester,
)

# ── Constants & Helpers ───────────────────────────────────────────────────────

_DIM = 384
_FAKE_EMBEDDING = [0.1] * _DIM


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
    fetched_at: str = "2024-01-01T00:00:00Z",
    chunk_type: str = "",
    source_file: str = "",
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
        "fetched_at": fetched_at,
        "chunk_type": chunk_type,
        "source_file": source_file,
        "code_blocks": [],
    }


def _make_ingester(
    tmp_path: Path, embed_url: str = "http://127.0.0.1:9999/embedding"
) -> RagIngester:
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
        "rag_pipeline_service_url": "",
    }
    return RagIngester(config=cfg)


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_db():
    """Mock SQLiteHelper for atomicity tests."""
    db = MagicMock(spec=SQLiteHelper)
    cm = MagicMock()
    cm.__enter__.return_value = None
    cm.__exit__.return_value = False
    db.begin_immediate.return_value = cm

    db.execute.called_after_begin_immediate = False

    def side_effect(*args, **kwargs):
        if cm.__enter__.called:
            db.execute.called_after_begin_immediate = True
        return MagicMock()

    db.execute.side_effect = side_effect
    yield db


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for embedding service."""
    client = MagicMock()
    client.post.return_value.json.return_value = {"embedding": [0.1] * 768}
    yield client


@pytest.fixture
def mock_doc_mgr(mock_db):
    """Mock DocumentManager."""
    mgr = MagicMock(spec=DocumentManager)
    mgr.handle_existing_document.return_value = (None, False, False)
    yield mgr


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestRagIngester:
    @pytest.mark.parametrize(
        "urls",
        [
            (["http://a.com", "http://b.com"]),
            (["http://c.com"]),
        ],
    )
    def test_ingest_url_group_success(
        self, tmp_path, urls, mock_db, mock_http_client, mock_doc_mgr
    ):
        ingester = _make_ingester(tmp_path)
        ingester._client = mock_http_client
        ingester.doc_mgr = mock_doc_mgr
        ingester.db = mock_db

        mock_doc_mgr.handle_existing_document.return_value = (1, False, False)

        chunk_path = tmp_path / "chunk" / "test.json"
        chunk_path.write_bytes(orjson.dumps(_make_chunk_json()))

        with patch.object(
            ingester,
            "_prepare_chunks",
            return_value=(
                [PreparedChunk(1, 0, "c", None, b"", "t", "s")],
                [chunk_path],
                [],
                0,
            ),
        ) as mock_prep:
            with patch.object(
                ingester, "_commit_url_transaction", return_value=None
            ) as mock_commit:
                result = ingester.ingest_url_group(
                    mock_doc_mgr, mock_db, urls[0], [chunk_path], force=False
                )

                assert isinstance(result, IngestUrlResult)
                assert result.n_success == 1
                assert mock_prep.called
                assert mock_commit.called

    def test_force_reinsert(self, tmp_path, mock_db, mock_doc_mgr):
        ingester = _make_ingester(tmp_path)
        ingester.doc_mgr = mock_doc_mgr
        ingester.db = mock_db

        # Scenario: document exists and should be replaced
        mock_doc_mgr.handle_existing_document.return_value = (1, False, True)

        chunk_path = tmp_path / "chunk" / "test.json"
        chunk_path.write_bytes(orjson.dumps(_make_chunk_json()))

        with patch.object(
            ingester,
            "_prepare_chunks",
            return_value=(
                [PreparedChunk(1, 0, "c", None, b"", "t", "s")],
                [chunk_path],
                [],
                0,
            ),
        ) as mock_prep:
            with patch.object(
                ingester, "_commit_url_transaction", return_value=None
            ) as mock_commit:
                result = ingester.ingest_url_group(
                    mock_doc_mgr, mock_db, "http://a.com", [chunk_path], force=True
                )
                assert result.n_success == 1
                assert mock_prep.called
                assert mock_commit.called


class TestAtomicity:
    def test_forced_reingest_with_embedding_failure(
        self, tmp_path, mock_db, mock_http_client, mock_doc_mgr
    ):
        """Verify previous document preserved when re-ingestion fails during preparation."""
        # Setup: existing document exists
        mock_doc_mgr.handle_existing_document.return_value = (123, False, False)

        ingester = _make_ingester(tmp_path)
        ingester._client = mock_http_client
        ingester.doc_mgr = mock_doc_mgr
        ingester.db = mock_db

        # Setup: valid chunk file so it doesn't exit early
        chunk_path = tmp_path / "chunk" / "valid.json"
        chunk_path.write_bytes(orjson.dumps(_make_chunk_json()))

        # Setup: embedding failure using a caught exception type
        from unittest.mock import MagicMock

        import httpx

        mock_http_client.post.side_effect = httpx.RequestError(
            "Embedding failed", request=MagicMock()
        )

        result = ingester.ingest_url_group(
            mock_doc_mgr, mock_db, "http://example.com", [chunk_path], force=True
        )

        # Verify: n_success is 0 because it failed during preparation
        assert result.n_success == 0
        # Verify: rollback happened — no transaction started yet since prep failed
        assert not mock_db.begin_immediate.called

    def test_database_failure_during_replacement(
        self, tmp_path, mock_db, mock_http_client, mock_doc_mgr
    ):
        """Verify rollback when database operation fails during commit."""
        # Setup: existing document exists
        mock_doc_mgr.handle_existing_document.return_value = (123, False, True)

        ingester = _make_ingester(tmp_path)
        ingester.doc_mgr = mock_doc_mgr
        ingester.db = mock_db
        ingester._client = mock_http_client

        # Setup: all chunks prepare successfully
        chunk_path = tmp_path / "chunk" / "valid.json"
        chunk_path.write_bytes(orjson.dumps(_make_chunk_json()))

        prepared_chunks = [PreparedChunk(123, 0, "c", None, b"", "t", "s")]

        with patch.object(
            ingester,
            "_prepare_chunks",
            return_value=(prepared_chunks, [chunk_path], [], 0),
        ):
            with patch.object(
                ingester,
                "_insert_chunks_batch",
                side_effect=sqlite3.DatabaseError("Database error"),
            ):
                with pytest.raises(sqlite3.DatabaseError, match="Database error"):
                    ingester.ingest_url_group(
                        mock_doc_mgr,
                        mock_db,
                        "http://example.com",
                        [chunk_path],
                        force=True,
                    )

                assert mock_db.begin_immediate.called

    def test_partial_preparation_failure(
        self, tmp_path, mock_db, mock_http_client, mock_doc_mgr
    ):
        """Verify no DB modification when any chunk fails during preparation."""
        # Setup: no existing document
        mock_doc_mgr.handle_existing_document.return_value = (None, False, False)

        ingester = _make_ingester(tmp_path)
        ingester.doc_mgr = mock_doc_mgr
        ingester.db = mock_db
        ingester._client = mock_http_client

        # Setup: two chunk files, only one prepares successfully
        chunk_path1 = tmp_path / "chunk" / "valid1.json"
        chunk_path1.write_bytes(orjson.dumps(_make_chunk_json()))
        chunk_path2 = tmp_path / "chunk" / "valid2.json"
        chunk_path2.write_bytes(orjson.dumps(_make_chunk_json()))
        chunk_files = [chunk_path1, chunk_path2]

        # Setup: first chunk prepares, second fails
        prepared_chunks = [PreparedChunk(1, 0, "c", None, b"", "t", "s")]
        failed_paths = [(chunk_path2, "embedding_failed")]

        with patch.object(
            ingester,
            "_prepare_chunks",
            return_value=(prepared_chunks, [chunk_path1], failed_paths, 1),
        ):
            result = ingester.ingest_url_group(
                mock_doc_mgr, mock_db, "http://example.com", chunk_files, force=False
            )

            # Verify: n_success is 0 because we didn't reach commit if we treat partial failures as group failure
            assert result.n_success == 0
            assert not mock_db.begin_immediate.called

    def test_successful_replacement(
        self, tmp_path, mock_db, mock_http_client, mock_doc_mgr
    ):
        """Verify all chunks committed atomically on success."""
        # Setup: existing document exists
        mock_doc_mgr.handle_existing_document.return_value = (123, False, True)

        ingester = _make_ingester(tmp_path)
        ingester.doc_mgr = mock_doc_mgr
        ingester.db = mock_db
        ingester._client = mock_http_client

        # Setup: all chunks succeed
        chunk_path = tmp_path / "chunk" / "valid.json"
        chunk_path.write_bytes(orjson.dumps(_make_chunk_json()))
        prepared_chunks = [PreparedChunk(123, 0, "c", None, b"", "t", "s")]

        with patch.object(
            ingester,
            "_prepare_chunks",
            return_value=(prepared_chunks, [chunk_path], [], 0),
        ):
            with patch.object(ingester, "_insert_chunks_batch") as mock_batch:
                result = ingester.ingest_url_group(
                    mock_doc_mgr,
                    mock_db,
                    "http://example.com",
                    [chunk_path],
                    force=True,
                )
                assert result.n_success == 1
                assert mock_db.begin_immediate.called
                assert mock_batch.called


class TestCacheInvalidation:
    def test_all_skipped_run_no_cache_invalidation(
        self, tmp_path, mock_db, mock_doc_mgr
    ):
        """Verify cache NOT invalidated when all URLs skipped."""
        ingester = _make_ingester(tmp_path)
        ingester.doc_mgr = mock_doc_mgr
        ingester.db = mock_db
        ingester._client = MagicMock()
        ingester._rag_pipeline_service_url = "http://cache-svc"

        # Add dummy chunk files
        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(exist_ok=True)
        chunk_file = chunk_dir / "test.json"
        chunk_file.write_bytes(orjson.dumps(_make_chunk_json()))

        # Mock process to return skipped results
        with patch("rag.ingestion.ingester.SQLiteHelper") as mock_sqlite_helper_cls:
            mock_sqlite_helper_cls.return_value.open.return_value.__enter__.return_value = mock_db
            with patch("rag.ingestion.ingester.DocumentManager") as mock_doc_mgr_cls:
                instance = mock_doc_mgr_cls.return_value
                instance.check_consistency.return_value = None

                with patch.object(
                    ingester,
                    "_process_url_groups",
                    return_value=[IngestUrlResult("u", 0, 0, True)],
                ):
                    ingester.ingest_all()
                    ingester._client.post.assert_not_called()

    def test_all_failed_run_no_cache_invalidation(
        self, tmp_path, mock_db, mock_doc_mgr
    ):
        """Verify cache NOT invalidated when all URLs fail."""
        ingester = _make_ingester(tmp_path)
        ingester.doc_mgr = mock_doc_mgr
        ingester.db = mock_db
        ingester._client = MagicMock()
        ingester._rag_pipeline_service_url = "http://cache-svc"

        # Add dummy chunk files
        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(exist_ok=True)
        chunk_file = chunk_dir / "test.json"
        chunk_file.write_bytes(orjson.dumps(_make_chunk_json()))

        with patch("rag.ingestion.ingester.SQLiteHelper") as mock_sqlite_helper_cls:
            mock_sqlite_helper_cls.return_value.open.return_value.__enter__.return_value = mock_db
            with patch("rag.ingestion.ingester.DocumentManager") as mock_doc_mgr_cls:
                instance = mock_doc_mgr_cls.return_value
                instance.check_consistency.return_value = None

                with patch.object(
                    ingester,
                    "_process_url_groups",
                    return_value=[IngestUrlResult("u", 0, 1, False)],
                ):
                    ingester.ingest_all()
                    ingester._client.post.assert_not_called()

    def test_partial_success_cache_invalidation(self, tmp_path, mock_db, mock_doc_mgr):
        """Verify cache invalidated only once on partial success."""
        ingester = _make_ingester(tmp_path)
        ingester.doc_mgr = mock_doc_mgr
        ingester.db = mock_db
        ingester._client = MagicMock()
        ingester._rag_pipeline_service_url = "http://cache-svc"

        # Add dummy chunk files
        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(exist_ok=True)
        chunk_file = chunk_dir / "test.json"
        chunk_file.write_bytes(orjson.dumps(_make_chunk_json()))

        with patch("rag.ingestion.ingester.SQLiteHelper") as mock_sqlite_helper_cls:
            mock_sqlite_helper_cls.return_value.open.return_value.__enter__.return_value = mock_db
            with patch("rag.ingestion.ingester.DocumentManager") as mock_doc_mgr_cls:
                instance = mock_doc_mgr_cls.return_value
                instance.check_consistency.return_value = None

                # One succeeds, one fails
                with patch.object(
                    ingester,
                    "_process_url_groups",
                    return_value=[
                        IngestUrlResult("u1", 1, 0, False),
                        IngestUrlResult("u2", 0, 1, False),
                    ],
                ):
                    ingester.ingest_all()
                    ingester._client.post.assert_called_once_with(
                        "http://cache-svc/rag_invalidate_cache"
                    )
