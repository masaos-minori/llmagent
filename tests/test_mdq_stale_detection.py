"""tests/test_mdq_stale_detection.py

Unit and behavior coverage for the shared stale-detection helper
(`is_stale`/`STALE_SQL_CONDITION`) and MdqService.outline()'s fixed
staleness comparison (mtime_ns in nanoseconds vs. indexed_at in seconds).
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import (
    STALE_SQL_CONDITION,
    IndexPathsRequest,
    OutlineRequest,
    is_stale,
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
        os.close(fd)


class TestIsStale:
    def test_not_stale_at_exact_boundary(self) -> None:
        """Equal mtime_ns/indexed_at (in ns terms) is not stale — `>` not `>=`."""
        assert is_stale(mtime_ns=int(1000.0 * 1e9), indexed_at=1000.0) is False

    def test_stale_one_nanosecond_past_boundary(self) -> None:
        assert is_stale(mtime_ns=int(1000.0 * 1e9) + 1, indexed_at=1000.0) is True

    def test_not_stale_when_mtime_much_older(self) -> None:
        """Regression case: under the old buggy direct comparison
        (`mtime_ns > indexed_at`, i.e. `500_000_000_000 > 1000.0`), this
        would have incorrectly evaluated True; is_stale() correctly
        evaluates False."""
        assert is_stale(mtime_ns=int(500.0 * 1e9), indexed_at=1000.0) is False

    def test_sql_condition_agrees_with_python_predicate(self) -> None:
        """STALE_SQL_CONDITION's SQL formula must never diverge from
        is_stale()'s Python formula."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("CREATE TABLE t (mtime_ns INTEGER, indexed_at REAL)")
            rows = [
                (int(1000.0 * 1e9), 1000.0),
                (int(1000.0 * 1e9) + 1, 1000.0),
                (int(500.0 * 1e9), 1000.0),
            ]
            conn.executemany("INSERT INTO t VALUES (?, ?)", rows)
            conn.commit()
            result_rows = conn.execute(
                f"SELECT mtime_ns, indexed_at, ({STALE_SQL_CONDITION}) as is_stale_sql FROM t"
            ).fetchall()
            assert len(result_rows) == len(rows)
            for row in result_rows:
                assert bool(row["is_stale_sql"]) == is_stale(
                    row["mtime_ns"], row["indexed_at"]
                )
        finally:
            conn.close()


class TestOutlineStaleWarning:
    def test_outline_no_stale_warning_immediately_after_indexing(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Regression test for the reported bug: freshly indexed files must
        not spuriously show a stale warning."""
        f = tmp_path / "doc.md"
        f.write_text("# Title\n\nContent here.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))
        result = asyncio.run(service.outline(OutlineRequest(path=str(f))))
        assert "modified since last indexing" not in result

    def test_outline_shows_stale_warning_when_mtime_is_newer(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A genuinely stale document (mtime_ns newer than indexed_at) must
        still be flagged — the fix must not simply suppress the warning
        unconditionally."""
        f = tmp_path / "doc.md"
        f.write_text("# Title\n\nContent here.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))

        conn = service._get_db_connection()
        try:
            row = conn.execute(
                "SELECT indexed_at FROM documents WHERE source_path = ?",
                (str(f),),
            ).fetchone()
            assert row is not None
            stale_mtime_ns = int(row["indexed_at"] * 1e9) + 1
            conn.execute(
                "UPDATE documents SET mtime_ns = ? WHERE source_path = ?",
                (stale_mtime_ns, str(f)),
            )
            conn.commit()
        finally:
            conn.close()

        result = asyncio.run(service.outline(OutlineRequest(path=str(f))))
        assert "modified since last indexing" in result
