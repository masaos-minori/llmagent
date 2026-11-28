"""tests/test_mdq_read_authorization.py

Read-time authorization regression tests for `search_docs`, `get_chunk`, `grep_docs` —
verifies narrowing `allowed_dirs` after indexing immediately hides previously-indexed
content, per `plans/20260719-205532_plan.md`.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import (
    GetChunkRequest,
    GrepDocsRequest,
    IndexPathsRequest,
    MdqAuthorizationError,
    SearchDocsRequest,
    StatsRequest,
)
from mcp_servers.mdq.mdq_service import MdqService
from mcp_servers.mdq.search import search_docs

from tests.mcp_servers.mdq._startup import make_startup


@pytest.fixture
def service(tmp_path: Path) -> MdqService:
    """MdqService with a temp DB path and tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    try:
        svc = MdqService(make_startup(db))
        svc._allowed_dirs = [str(tmp_path)]
        return svc
    finally:
        import os

        os.close(fd)


def _chunk_id_for(service: MdqService, source_path: Path) -> str:
    conn = service._get_db_connection()
    try:
        row = conn.execute(
            "SELECT chunk_id FROM chunks WHERE source_path = ?",
            (str(source_path),),
        ).fetchone()
        assert row is not None
        return str(row["chunk_id"])
    finally:
        conn.close()


class TestSearchDocsReadTimeAuthorization:
    async def test_narrowed_allowed_dirs_hides_indexed_content(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        f = tmp_path / "visible.md"
        f.write_text("# Title\n\nSecretKeyword content.", encoding="utf-8")
        await index_paths(service, IndexPathsRequest(paths=[str(f)]))

        text, _metadata = await search_docs(
            service, SearchDocsRequest(query="SecretKeyword")
        )
        assert "Title" in text

        other_dir = tmp_path / "other-unrelated-dir"
        other_dir.mkdir()
        service._allowed_dirs = [str(other_dir)]

        text, _metadata = await search_docs(
            service, SearchDocsRequest(query="SecretKeyword")
        )
        assert "No results found" in text


class TestGetChunkReadTimeAuthorization:
    async def test_narrowed_allowed_dirs_denies_get_chunk(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        f = tmp_path / "chunk_target.md"
        f.write_text("# Title\n\nBody content.", encoding="utf-8")
        await index_paths(service, IndexPathsRequest(paths=[str(f)]))
        chunk_id = _chunk_id_for(service, f)

        other_dir = tmp_path / "other-unrelated-dir"
        other_dir.mkdir()
        service._allowed_dirs = [str(other_dir)]

        with pytest.raises(MdqAuthorizationError) as exc_info:
            await service.get_chunk(GetChunkRequest(chunk_id=chunk_id))
        assert str(f) not in str(exc_info.value)


class TestGrepDocsReadTimeAuthorization:
    async def test_narrowed_allowed_dirs_hides_content_no_filter(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        f = tmp_path / "grep_target.md"
        f.write_text("# Title\n\nfind_me_pattern content.", encoding="utf-8")
        await index_paths(service, IndexPathsRequest(paths=[str(f)]))

        other_dir = tmp_path / "other-unrelated-dir"
        other_dir.mkdir()
        service._allowed_dirs = [str(other_dir)]

        text, _metadata = await service.grep_docs(
            GrepDocsRequest(pattern="find_me_pattern", paths=None)
        )
        assert "No matches found" in text

    async def test_explicit_unauthorized_path_rejected(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        f = tmp_path / "explicit_target.md"
        f.write_text("# Title\n\nfind_me_pattern content.", encoding="utf-8")
        await index_paths(service, IndexPathsRequest(paths=[str(f)]))

        other_dir = tmp_path / "other-unrelated-dir"
        other_dir.mkdir()
        service._allowed_dirs = [str(other_dir)]

        with pytest.raises(MdqAuthorizationError):
            await service.grep_docs(
                GrepDocsRequest(pattern="find_me_pattern", paths=[str(f)])
            )

    async def test_explicit_authorized_path_is_permitted(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        f = tmp_path / "explicit_allowed_target.md"
        f.write_text("# Title\n\nfind_me_pattern content.", encoding="utf-8")
        await index_paths(service, IndexPathsRequest(paths=[str(f)]))

        text, _metadata = await service.grep_docs(
            GrepDocsRequest(pattern="find_me_pattern", paths=[str(f)])
        )
        assert "find_me_pattern" in text

    async def test_deny_all_returns_no_matches_not_unfiltered_scan(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        f = tmp_path / "deny_all_target.md"
        f.write_text("# Title\n\nfind_me_pattern content.", encoding="utf-8")
        await index_paths(service, IndexPathsRequest(paths=[str(f)]))

        service._allowed_dirs = []

        text, _metadata = await service.grep_docs(
            GrepDocsRequest(pattern="find_me_pattern", paths=None)
        )
        assert text == "No matches found."


class TestStatsReadTimeAuthorization:
    """stats() describes only the roots authorized when the call runs (REQ-002)."""

    async def test_stats_refused_when_no_roots_are_authorized(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        f = tmp_path / "stats_target.md"
        f.write_text("# Title\n\nBody content.", encoding="utf-8")
        await index_paths(service, IndexPathsRequest(paths=[str(f)]))

        service._allowed_dirs = []

        # A refusal, not zero counts: "no access" and "nothing indexed" stay distinguishable.
        with pytest.raises(MdqAuthorizationError):
            await service.stats(StatsRequest())

    async def test_shrunk_allowlist_removes_prior_root_counts(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        f = tmp_path / "stats_target.md"
        f.write_text("# Title\n\nBody content.", encoding="utf-8")
        await index_paths(service, IndexPathsRequest(paths=[str(f)]))

        result = await service.stats(StatsRequest())
        assert "Documents: 1, Chunks: 1, FTS rows: 1, Stale: 0" in result

        other_dir = tmp_path / "other-unrelated-dir"
        other_dir.mkdir()
        service._allowed_dirs = [str(other_dir)]

        result = await service.stats(StatsRequest())
        assert "Documents: 0, Chunks: 0, FTS rows: 0, Stale: 0" in result
        assert "Metadata" not in result
