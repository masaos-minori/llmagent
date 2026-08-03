"""tests/test_mdq_get_chunk_behavior.py

Regression coverage for get_chunk() after the summary-cache stub removal.
Replaces the deleted tests/test_mdq_summary_cache.py.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import (
    GetChunkRequest,
    IndexPathsRequest,
    MdqNotFoundError,
)
from mcp_servers.mdq.mdq_service import MdqService


@pytest.fixture
def service(tmp_path: Path) -> MdqService:
    """MdqService with a temp DB path and tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    try:
        svc = MdqService(db_path=db)
        svc._allowed_dirs = [str(tmp_path)]
        return svc
    finally:
        import os  # noqa: PLC0415

        os.close(fd)


class TestGetChunkNormalBehavior:
    def test_get_chunk_returns_raw_content(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        f = tmp_path / "test.md"
        f.write_text("# Title\n\nContent here.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))
        conn = service._get_db_connection()
        try:
            row = conn.execute("SELECT chunk_id FROM chunks LIMIT 1").fetchone()
            assert row is not None
            chunk_id = row["chunk_id"]
        finally:
            conn.close()
        result = asyncio.run(service.get_chunk(GetChunkRequest(chunk_id=chunk_id)))
        assert "Content here." in result
        assert "[Summary" not in result

    def test_get_chunk_truncates_large_content(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        f = tmp_path / "big.md"
        f.write_text("# Big\n\n" + "X" * 2000, encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))
        service.max_chars_per_chunk = 100
        conn = service._get_db_connection()
        try:
            row = conn.execute("SELECT chunk_id FROM chunks LIMIT 1").fetchone()
            assert row is not None
            chunk_id = row["chunk_id"]
        finally:
            conn.close()
        result = asyncio.run(service.get_chunk(GetChunkRequest(chunk_id=chunk_id)))
        assert "[Truncated —" in result

    def test_get_chunk_raises_not_found(self, service: MdqService) -> None:
        with pytest.raises(MdqNotFoundError):
            asyncio.run(service.get_chunk(GetChunkRequest(chunk_id="nonexistent")))


class TestUseSummaryFieldRemoved:
    def test_use_summary_field_silently_ignored(self) -> None:
        """use_summary was removed; extra kwargs are silently ignored (not rejected)."""
        req = GetChunkRequest(chunk_id="x", use_summary=True)
        assert not hasattr(req, "use_summary")
