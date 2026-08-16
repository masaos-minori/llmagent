"""tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py

Characterization test for MdqService._check_stale_document(), extracted from
outline() during refactoring. Locks the "no matching documents row" branch,
which existing stale-detection tests do not exercise (they only cover: fresh
index / genuinely stale). Note: mtime_ns/indexed_at are NOT NULL columns in
the documents table (see db_schema.py), so the "row present but a field is
NULL" half of the guard is unreachable via the production schema — only the
"no row at all" half is reachable in practice.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import IndexPathsRequest, OutlineRequest
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


def test_outline_no_stale_warning_when_document_row_missing(
    service: MdqService, tmp_path: Path
) -> None:
    """If chunks exist for a path but the documents row is absent, outline()
    must not raise and must not show a stale warning (matches pre-refactor
    behavior: the guard silently skips staleness evaluation)."""
    f = tmp_path / "doc.md"
    f.write_text("# Title\n\nContent here.", encoding="utf-8")
    asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))

    conn = service._get_db_connection()
    try:
        conn.execute(
            "DELETE FROM documents WHERE source_path = ?",
            (str(f),),
        )
        conn.commit()
    finally:
        conn.close()

    result = asyncio.run(service.outline(OutlineRequest(path=str(f))))
    assert "modified since last indexing" not in result
    assert "Title" in result
