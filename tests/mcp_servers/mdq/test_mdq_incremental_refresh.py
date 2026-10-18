#!/usr/bin/env python3
"""Tests for MDQ incremental refresh_index behavior."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import sqlite3
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

import mcp_servers.mdq.indexer as indexer
import pytest
from mcp_servers.mdq.indexer import RefreshSummary, index_paths
from mcp_servers.mdq.indexer import refresh_paths as _refresh_paths
from mcp_servers.mdq.mdq_models import (
    IndexPathsMetadata,
    IndexPathsRequest,
    MdqAuthorizationError,
    RefreshIndexRequest,
)
from mcp_servers.mdq.mdq_service import MdqService


@pytest.fixture()
def md_file(tmp_path: Path) -> Path:
    f = tmp_path / "test.md"
    f.write_text("# Hello\n\nWorld")
    return f


class TestIncrementalRefresh:
    """Test incremental refresh skips unchanged files."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        db = tmp_path / "mdq.sqlite"
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
        import sqlite3

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


# ── Characterization tests for the refresh_paths() and index_paths() branches ───
#
# Both entry points tally one counter per requested path, and the counters are not
# symmetric: force mode counts a directory as one indexed path while incremental mode
# counts one per changed file, a mid-directory failure keeps the counts already
# recorded for the earlier files, and a nonexistent path is counted as skipped by
# index_paths() but by no counter at all in refresh_paths(). These pin those shapes.


def _fresh_service(tmp_path: Path) -> MdqService:
    """An MdqService with a private database, jailed to tmp_path."""
    service = MdqService(db_path=str(tmp_path / "mdq.sqlite"))
    service._allowed_dirs = [str(tmp_path)]
    return service


def _counters(result: RefreshSummary) -> tuple[int, int, int]:
    """(indexed, skipped, failed) from a RefreshSummary."""
    return (
        int(result["indexed_count"]),
        int(result["skipped_count"]),
        int(result["failed_count"]),
    )


def _meta_counts(meta: IndexPathsMetadata) -> tuple[int, int, int]:
    """(indexed, skipped, failed) from an IndexPathsMetadata record."""
    return (meta["indexed_count"], meta["skipped_count"], meta["failed_count"])


def _index_state_keys(service: MdqService) -> set[str]:
    """Every index_state key in the service database."""
    conn = sqlite3.connect(service.db_path)
    try:
        return {row[0] for row in conn.execute("SELECT key FROM index_state")}
    finally:
        conn.close()


def _fail_on_nth(n: int) -> Callable[..., Awaitable[None]]:
    """A stand-in for _index_single_file that fails on its nth call and succeeds before it."""
    calls = 0

    async def _fail(service: MdqService, path: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == n:
            raise RuntimeError(f"indexing failed on call {calls}")

    return _fail


async def _always_fail(service: MdqService, path: Path) -> None:
    """A stand-in for _index_single_file that always fails."""
    raise RuntimeError("indexing failed")


class TestRefreshForceModeBranches:
    """Force mode re-indexes unconditionally and counts a directory as one path."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        return _fresh_service(tmp_path)

    def test_directory_counts_one_indexed_path_not_one_per_file(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        (tmp_path / "a.md").write_text("# A\n\nOne")
        (tmp_path / "b.md").write_text("# B\n\nTwo")

        result = asyncio.run(
            _refresh_paths(
                service, RefreshIndexRequest(paths=[str(tmp_path)], force=True)
            )
        )

        assert _counters(result) == (1, 0, 0)

    def test_directory_without_indexable_files_counts_nothing(
        self, service: MdqService, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger="mcp_servers.mdq.indexer")
        empty = tmp_path / "empty"
        empty.mkdir()

        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(empty)], force=True))
        )

        assert _counters(result) == (0, 0, 0)
        assert "No indexable files found in directory" in caplog.text

    def test_non_markdown_file_reports_as_neither_file_nor_directory(
        self, service: MdqService, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        target = tmp_path / "notes.txt"
        target.write_text("plain text")

        result = asyncio.run(
            _refresh_paths(
                service, RefreshIndexRequest(paths=[str(target)], force=True)
            )
        )

        assert _counters(result) == (0, 0, 0)
        assert "Path is not a file or directory" in caplog.text

    def test_path_outside_allowed_directories_raises(self, service: MdqService) -> None:
        with pytest.raises(MdqAuthorizationError, match="outside allowed directories"):
            asyncio.run(
                _refresh_paths(service, RefreshIndexRequest(paths=["/etc/passwd"]))
            )


class TestRefreshIncrementalBranches:
    """Incremental mode counts per changed file and ignores non-Markdown paths."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        return _fresh_service(tmp_path)

    def test_non_markdown_file_is_not_counted_by_any_counter(
        self, service: MdqService, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """refresh_paths() has no else branch: a .txt path is silently dropped."""
        target = tmp_path / "notes.txt"
        target.write_text("plain text")

        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(target)]))
        )

        assert _counters(result) == (0, 0, 0)
        assert "Skipping non-Markdown path" not in caplog.text

    def test_failed_reindex_does_not_record_the_new_mtime(
        self, service: MdqService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """index_state is written only after a successful re-index."""
        target = tmp_path / "a.md"
        target.write_text("# A\n\nOne")
        asyncio.run(_refresh_paths(service, RefreshIndexRequest(paths=[str(target)])))
        state_key = f"mtime:{str(target)}"
        recorded_before = _index_state_keys(service)
        assert state_key in recorded_before

        target.write_text("# A\n\nTwo")
        monkeypatch.setattr(indexer, "_index_single_file", _always_fail)
        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(target)]))
        )

        assert _counters(result) == (0, 0, 1)
        assert _index_state_keys(service) == recorded_before


class TestRefreshFailureCounters:
    """One failure records one failed_count and keeps the progress already made."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        return _fresh_service(tmp_path)

    def test_single_file_failure(
        self,
        service: MdqService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        target = tmp_path / "a.md"
        target.write_text("# A\n\nOne")
        monkeypatch.setattr(indexer, "_index_single_file", _always_fail)

        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(target)]))
        )

        assert _counters(result) == (0, 0, 1)
        assert "Failed to refresh" in caplog.text

    def test_directory_failure_keeps_the_counts_already_recorded(
        self, service: MdqService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The try/except wraps the whole file loop, so files after the failure are never visited."""
        for name in ("a.md", "b.md", "c.md"):
            (tmp_path / name).write_text(f"# {name}\n\nBody")
        monkeypatch.setattr(indexer, "_index_single_file", _fail_on_nth(2))

        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(tmp_path)]))
        )

        assert _counters(result) == (1, 0, 1)
        assert _index_state_keys(service) == {f"mtime:{tmp_path / 'a.md'}"}

    def test_force_mode_failure(
        self,
        service: MdqService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        target = tmp_path / "a.md"
        target.write_text("# A\n\nOne")
        monkeypatch.setattr(indexer, "_index_single_file", _always_fail)

        result = asyncio.run(
            _refresh_paths(
                service, RefreshIndexRequest(paths=[str(target)], force=True)
            )
        )

        assert _counters(result) == (0, 0, 1)
        assert "Failed to index" in caplog.text

    def test_deletion_scan_failure_is_not_a_failed_count(
        self,
        service: MdqService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """_detect_deleted_files() logs its own failure and never touches failed_count."""
        sub = tmp_path / "sub"
        sub.mkdir()
        for name in ("a.md", "b.md"):
            (sub / name).write_text(f"# {name}\n\nBody")
        asyncio.run(_refresh_paths(service, RefreshIndexRequest(paths=[str(sub)])))
        (sub / "a.md").unlink()

        def _scan_fails(service: MdqService, directory: Path) -> list[Path]:
            raise RuntimeError("scan failed")

        monkeypatch.setattr(indexer, "_iter_indexable_files", _scan_fails)
        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(sub / "b.md")]))
        )

        assert result["deleted_count"] == 0
        assert _counters(result) == (0, 1, 0)
        assert "Failed to scan for deleted files" in caplog.text

    def test_index_state_keys_that_are_not_mtime_records_are_ignored(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A six-character prefix makes the key look like a deleted file once sliced."""
        sub = tmp_path / "sub"
        sub.mkdir()
        target = sub / "a.md"
        target.write_text("# A\n\nOne")
        asyncio.run(_refresh_paths(service, RefreshIndexRequest(paths=[str(sub)])))

        conn = sqlite3.connect(service.db_path)
        conn.execute("DELETE FROM index_state")
        conn.execute(
            "INSERT OR REPLACE INTO index_state (key, value) VALUES (?, ?)",
            (f"prefix{target}", "1"),
        )
        conn.commit()
        conn.close()
        target.unlink()

        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(sub)]))
        )

        assert result["deleted_count"] == 0


class TestIndexPathsCounters:
    """index_paths() counts one entry per requested path, including skipped ones."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        return _fresh_service(tmp_path)

    def test_directory_counts_one_indexed_path(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        (tmp_path / "a.md").write_text("# A\n\nOne")
        (tmp_path / "b.md").write_text("# B\n\nTwo")

        message, meta = asyncio.run(
            index_paths(service, IndexPathsRequest(paths=[str(tmp_path)]))
        )

        assert message == "Indexing complete"
        assert meta["input_path_count"] == 1
        assert _meta_counts(meta) == (1, 0, 0)
        assert meta["duration_ms"] >= 0

    def test_nonexistent_path_is_skipped(self, service: MdqService) -> None:
        _, meta = asyncio.run(
            index_paths(service, IndexPathsRequest(paths=["/nonexistent/path.md"]))
        )

        assert _meta_counts(meta) == (0, 1, 0)

    def test_non_markdown_file_is_skipped_with_a_warning(
        self, service: MdqService, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        target = tmp_path / "notes.txt"
        target.write_text("plain text")

        _, meta = asyncio.run(
            index_paths(service, IndexPathsRequest(paths=[str(target)]))
        )

        assert _meta_counts(meta) == (0, 1, 0)
        assert "Skipping non-Markdown path" in caplog.text

    def test_single_file_failure(
        self,
        service: MdqService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        target = tmp_path / "a.md"
        target.write_text("# A\n\nOne")
        monkeypatch.setattr(indexer, "_index_single_file", _always_fail)

        _, meta = asyncio.run(
            index_paths(service, IndexPathsRequest(paths=[str(target)]))
        )

        assert _meta_counts(meta) == (0, 0, 1)
        assert "Failed to index" in caplog.text

    def test_directory_failure(
        self, service: MdqService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / "a.md").write_text("# A\n\nOne")
        monkeypatch.setattr(indexer, "_index_single_file", _always_fail)

        _, meta = asyncio.run(
            index_paths(service, IndexPathsRequest(paths=[str(tmp_path)]))
        )

        assert _meta_counts(meta) == (0, 0, 1)

    def test_path_outside_allowed_directories_raises(self, service: MdqService) -> None:
        with pytest.raises(MdqAuthorizationError, match="outside allowed directories"):
            asyncio.run(index_paths(service, IndexPathsRequest(paths=["/etc/passwd"])))


def _documents_row_count(service: MdqService, path: Path) -> int:
    """Rows in documents for the doc_id the indexer derives from path."""
    doc_id = hashlib.sha256(str(path).encode()).hexdigest()
    conn = sqlite3.connect(service.db_path)
    try:
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM documents WHERE doc_id = ?", (doc_id,)
            ).fetchone()[0]
        )
    finally:
        conn.close()


class _RecordingConnection:
    """Wraps a real connection and records every statement it is asked to execute."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.statements: list[str] = []

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Cursor:
        self.statements.append(sql)
        return self._conn.execute(sql, params)

    def close(self) -> None:
        self._conn.close()


class TestIndexSingleFileWriteFailure:
    """Characterization: a sqlite3.Error mid-transaction rolls back the whole write."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        return _fresh_service(tmp_path)

    def test_chunk_write_failure_rolls_back_the_document_upsert(
        self,
        service: MdqService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The document upsert is rolled back when a chunk write fails."""
        target = tmp_path / "a.md"
        target.write_text("# A\n\nOne")

        def _fail_on_chunk(content: str) -> int:
            raise sqlite3.OperationalError("simulated chunk write failure")

        monkeypatch.setattr(indexer, "_estimate_token_count", _fail_on_chunk)

        recorded = _RecordingConnection(service._get_db_connection())
        monkeypatch.setattr(service, "_get_db_connection", lambda: recorded)

        caplog.set_level(logging.ERROR, logger="mcp_servers.mdq.indexer")
        asyncio.run(indexer._index_single_file(service, target))

        assert "Failed to write chunks for" in caplog.text
        assert "BEGIN IMMEDIATE" in recorded.statements
        assert "ROLLBACK" in recorded.statements
        assert "COMMIT" not in recorded.statements
        assert _documents_row_count(service, target) == 0

    def test_rollback_quietly_discards_the_open_transaction(self) -> None:
        conn = sqlite3.connect(":memory:")
        try:
            conn.execute("CREATE TABLE t (v INTEGER)")
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("INSERT INTO t VALUES (1)")

            indexer._rollback_quietly(conn)

            assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 0
        finally:
            conn.close()

    def test_rollback_quietly_ignores_a_connection_that_cannot_rollback(self) -> None:
        """A second sqlite3.Error during ROLLBACK is swallowed, not reported."""
        conn = sqlite3.connect(":memory:")
        conn.close()

        indexer._rollback_quietly(conn)


class TestDeletedFileDetectionFailureIsolation:
    """Characterization: a directory's failure stops that directory only."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        return _fresh_service(tmp_path)

    def _index(self, service: MdqService, directory: Path) -> None:
        asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(directory)]))
        )

    def test_scan_failure_in_one_directory_does_not_stop_another(
        self,
        service: MdqService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        first = tmp_path / "first"
        second = tmp_path / "second"
        for directory in (first, second):
            directory.mkdir()
            for name in ("a.md", "b.md"):
                (directory / name).write_text(f"# {name}\n\nBody")
        self._index(service, first)
        self._index(service, second)
        (first / "a.md").unlink()
        (second / "a.md").unlink()

        original_scan = indexer._iter_indexable_files

        def _scan(service: MdqService, directory: Path) -> list[Path]:
            if directory == first:
                raise RuntimeError("scan failed")
            return original_scan(service, directory)

        monkeypatch.setattr(indexer, "_iter_indexable_files", _scan)
        caplog.set_level(logging.ERROR, logger="mcp_servers.mdq.indexer")

        result = asyncio.run(
            _refresh_paths(
                service,
                RefreshIndexRequest(paths=[str(first / "b.md"), str(second / "b.md")]),
            )
        )

        assert result["deleted_count"] == 1
        assert "Failed to scan for deleted files in" in caplog.text

    def test_mid_directory_failure_keeps_the_deletions_already_made(
        self,
        service: MdqService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """deleted_count keeps what the directory removed before it failed."""
        directory = tmp_path / "docs"
        directory.mkdir()
        for name in ("a.md", "b.md", "c.md"):
            (directory / name).write_text(f"# {name}\n\nBody")
        self._index(service, directory)
        (directory / "a.md").unlink()
        (directory / "b.md").unlink()

        original_delete = indexer.delete_file_from_index
        calls = 0

        def _delete(service: MdqService, conn: sqlite3.Connection, path: Path) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("delete failed")
            original_delete(service, conn, path)

        monkeypatch.setattr(indexer, "delete_file_from_index", _delete)
        caplog.set_level(logging.ERROR, logger="mcp_servers.mdq.indexer")

        result = asyncio.run(
            _refresh_paths(
                service, RefreshIndexRequest(paths=[str(directory / "c.md")])
            )
        )

        assert result["deleted_count"] == 1
        assert "Failed to scan for deleted files in" in caplog.text
