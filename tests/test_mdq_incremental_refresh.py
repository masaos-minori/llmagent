#!/usr/bin/env python3
"""Tests for MDQ incremental refresh_index behavior."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest
from mcp.mdq.indexer import refresh_paths as _refresh_paths
from mcp.mdq.models import RefreshIndexRequest
from mcp.mdq.service import MdqService


@pytest.fixture()
def md_file(tmp_path: Path) -> Path:
    f = tmp_path / "test.md"
    f.write_text("# Hello\n\nWorld")
    return f


class TestIncrementalRefresh:
    """Test incremental refresh skips unchanged files."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        db = tmp_path / "mdq.db"
        svc = MdqService(db_path=str(db))
        svc._allowed_dirs = [str(tmp_path)]
        return svc

    async def _index_and_wait(self, service: MdqService, path: Path) -> None:
        """Index a file and wait for mtime to change."""
        await _refresh_paths(service, RefreshIndexRequest(paths=[str(path)]))
        # Wait for filesystem mtime granularity
        time.sleep(0.05)

    def test_skips_unchanged_file(self, service: MdqService, md_file: Path) -> None:
        """First refresh indexes the file; second refresh skips it."""
        asyncio.run(self._index_and_wait(service, md_file))
        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(md_file)]))
        )
        assert result["indexed_count"] == 0
        assert result["skipped_count"] == 1
        assert result["deleted_count"] == 0

    def test_reindexes_changed_file(self, service: MdqService, md_file: Path) -> None:
        """Changed file is re-indexed."""
        asyncio.run(self._index_and_wait(service, md_file))
        # Wait for mtime to change
        time.sleep(0.05)
        md_file.write_text("# Hello\n\nWorld Changed")
        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(md_file)]))
        )
        assert result["indexed_count"] == 1
        assert result["skipped_count"] == 0

    def test_force_bypasses_skip(self, service: MdqService, md_file: Path) -> None:
        """Force=True re-indexes unchanged files."""
        asyncio.run(self._index_and_wait(service, md_file))
        result = asyncio.run(
            _refresh_paths(
                service, RefreshIndexRequest(paths=[str(md_file)], force=True)
            )
        )
        assert result["indexed_count"] == 1
        assert result["skipped_count"] == 0

    def test_deleted_file_removed(self, service: MdqService, tmp_path: Path) -> None:
        """Deleted file is removed from index."""
        sub = tmp_path / "sub"
        sub.mkdir()
        md_file = sub / "deleted.md"
        md_file.write_text("# Deleted\n\nThis will be deleted")
        asyncio.run(_refresh_paths(service, RefreshIndexRequest(paths=[str(sub)])))

        # Delete the file
        md_file.unlink()

        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(sub)]))
        )
        assert result["deleted_count"] == 1

    def test_force_deletes_removed_files(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Force=True also removes deleted files."""
        sub = tmp_path / "sub"
        sub.mkdir()
        md_file = sub / "deleted2.md"
        md_file.write_text("# Deleted\n\nThis will be deleted")
        asyncio.run(_refresh_paths(service, RefreshIndexRequest(paths=[str(sub)])))

        # Delete the file
        md_file.unlink()

        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(sub)], force=True))
        )
        assert result["deleted_count"] == 1
        assert result["indexed_count"] == 0  # No new files to index

    def test_directory_refresh_skips_unchanged(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Directory refresh skips unchanged files."""
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("# A\n\nContent")
        f2.write_text("# B\n\nContent")
        asyncio.run(_refresh_paths(service, RefreshIndexRequest(paths=[str(tmp_path)])))
        time.sleep(0.05)

        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(tmp_path)]))
        )
        assert result["indexed_count"] == 0
        assert result["skipped_count"] == 2

    def test_directory_refresh_reindexes_changed(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Directory refresh re-indexes changed files only."""
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("# A\n\nContent")
        f2.write_text("# B\n\nContent")
        asyncio.run(_refresh_paths(service, RefreshIndexRequest(paths=[str(tmp_path)])))
        time.sleep(0.05)

        # Change only f1
        f1.write_text("# A\n\nChanged Content")
        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(tmp_path)]))
        )
        assert result["indexed_count"] == 1
        assert result["skipped_count"] == 1

    def test_elapsed_seconds_included(self, service: MdqService, md_file: Path) -> None:
        """Elapsed seconds is included in the summary."""
        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(md_file)]))
        )
        assert "elapsed_seconds" in result
        assert result["elapsed_seconds"] >= 0

    def test_skips_nonexistent_path(self, service: MdqService) -> None:
        """Non-existent paths are skipped without incrementing any counters."""
        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=["/nonexistent/path.md"]))
        )
        assert result["indexed_count"] == 0
        assert result["skipped_count"] == 0
        assert result["deleted_count"] == 0
        assert result["failed_count"] == 0

    def test_chunk_id_stable_after_refresh(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Force-index, record IDs, force-index again (unchanged); IDs are identical."""
        import sqlite3  # noqa: PLC0415

        f = tmp_path / "stable.md"
        f.write_text("# Stable\n\nContent.")

        asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(f)], force=True))
        )
        conn = sqlite3.connect(service.db_path)
        conn.row_factory = sqlite3.Row
        ids_before = {
            r["chunk_id"] for r in conn.execute("SELECT chunk_id FROM chunks")
        }
        conn.close()

        asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(f)], force=True))
        )
        conn = sqlite3.connect(service.db_path)
        conn.row_factory = sqlite3.Row
        ids_after = {r["chunk_id"] for r in conn.execute("SELECT chunk_id FROM chunks")}
        conn.close()

        assert ids_before == ids_after
