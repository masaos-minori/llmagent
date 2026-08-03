"""
tests/test_rag_ingester_callback.py
Verify RagIngester.ingest_all() invokes on_ingest_complete exactly once.

Resolves: OPEN-01 (docs/03_rag_90_inconsistencies_and_known_issues.md)
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import MagicMock, Mock, patch

import pytest
from rag.ingestion.ingester import RagIngester


class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        pass

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


@pytest.fixture()
def db(tmp_path: str) -> Generator[_FakeSQLiteHelper]:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    yield _FakeSQLiteHelper(conn)
    conn.close()


@pytest.fixture()
def ingester(tmp_path: str, db: _FakeSQLiteHelper) -> RagIngester:
    """Minimal RagIngester instance that does not hit the filesystem or DB."""
    cfg = {
        "rag_src_dir": tmp_path,
        "embed_url": "http://localhost:8081/embedding",
        "embed_retry": "1",
        "embed_workers": "1",
    }
    ingester = RagIngester(config=cfg)
    mock_report = MagicMock()
    mock_report.issues = []
    with (
        patch(
            "rag.ingestion.ingester.SQLiteHelper",
            return_value=db,
        ),
        patch(
            "rag.ingestion.document_manager.check_rag_consistency",
            return_value=mock_report,
        ),
    ):
        yield ingester
    ingester.close()


def test_ingest_all_calls_on_ingest_complete(ingester: RagIngester) -> None:
    """ingest_all() must call on_ingest_complete exactly once after completion."""
    callback = Mock()

    mock_chunk_dir = MagicMock()
    mock_chunk_dir.glob.return_value = [MagicMock()]

    with (
        patch.object(ingester, "_chunk_dir", mock_chunk_dir),
        patch.object(type(ingester), "_process_url_groups", return_value=[]),
    ):
        ingester.ingest_all(force=False, on_ingest_complete=callback)

    callback.assert_called_once()
