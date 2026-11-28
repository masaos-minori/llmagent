#!/usr/bin/env python3
"""Tests for the indexer's internal failure outcomes, measured through the DTO.

Each branch of _index_single_file() reports a FileOutcome, and every caller tallies from
its status: a skipped or failed file never advances index_state, never counts as
committed, and a run whose every file failed reports the tool error instead of a summary
or a text the caller would read as completed.
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from pathlib import Path

import mcp_servers.mdq.indexer as indexer
import pytest
from mcp_servers.mdq.indexer import refresh_paths as _refresh_paths
from mcp_servers.mdq.mdq_models import (
    PARTIAL_SUCCESS_TEXT,
    IndexPathsRequest,
    MdqServiceError,
    RefreshIndexRequest,
)
from mcp_servers.mdq.mdq_service import MdqService

from tests.mcp_servers.mdq._startup import make_startup


def _fresh_service(tmp_path: Path) -> MdqService:
    """An MdqService with a private database, jailed to tmp_path."""
    service = MdqService(make_startup(str(tmp_path / "mdq.sqlite")))
    service._allowed_dirs = [str(tmp_path)]
    return service


def _table_count(service: MdqService, table: str) -> int:
    conn = sqlite3.connect(service.db_path)
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        conn.close()


def _drop_chunks_table(service: MdqService) -> None:
    """Break the schema so the production write path hits a real sqlite3.Error."""
    conn = sqlite3.connect(service.db_path)
    conn.execute("DROP TABLE chunks")
    conn.commit()
    conn.close()


def _index_state_keys(service: MdqService) -> set[str]:
    conn = sqlite3.connect(service.db_path)
    try:
        return {row[0] for row in conn.execute("SELECT key FROM index_state")}
    finally:
        conn.close()


def _index_state_value(service: MdqService, key: str) -> str | None:
    conn = sqlite3.connect(service.db_path)
    try:
        row = conn.execute(
            "SELECT value FROM index_state WHERE key = ?", (key,)
        ).fetchone()
        return None if row is None else str(row[0])
    finally:
        conn.close()


class TestSingleFileOutcomes:
    """Every branch of _index_single_file() reports one DTO, never a silent return."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        return _fresh_service(tmp_path)

    def test_indexed_outcome_reports_a_root_relative_path(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        target = tmp_path / "a.md"
        target.write_text("# A\n\nOne")

        outcome = asyncio.run(indexer._index_single_file(service, target))

        assert outcome.status == "indexed"
        assert outcome.reason_code is None
        assert outcome.path == "a.md"
        assert not outcome.path.startswith("/")

    def test_size_limit_is_a_skipped_outcome(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        service.max_file_bytes = 10
        target = tmp_path / "big.md"
        target.write_text("# Big\n\n" + "x" * 100)

        outcome = asyncio.run(indexer._index_single_file(service, target))

        assert outcome.status == "skipped_size_limit"
        assert outcome.reason_code == "size_limit"
        assert _table_count(service, "chunks") == 0

    def test_no_content_is_a_skipped_outcome(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        target = tmp_path / "empty.md"
        target.write_text("")

        outcome = asyncio.run(indexer._index_single_file(service, target))

        assert outcome.status == "skipped_no_content"
        assert outcome.reason_code == "no_content"

    def test_disappearing_file_is_a_failed_outcome(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        outcome = asyncio.run(
            indexer._index_single_file(service, tmp_path / "ghost.md")
        )

        assert outcome.status == "failed"
        assert outcome.reason_code == "file_disappeared"

    def test_production_write_failure_is_a_failed_outcome(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """The dropped table makes the production transaction fail with a real sqlite3.Error."""
        target = tmp_path / "a.md"
        target.write_text("# A\n\nOne")
        _drop_chunks_table(service)

        outcome = asyncio.run(indexer._index_single_file(service, target))

        assert outcome.status == "failed"
        assert outcome.reason_code == "write_failure"
        # The failed transaction wrote nothing: its documents insert was rolled back.
        assert _table_count(service, "documents") == 0


class TestScanToReadGap:
    """A file that changed after the scan is reported, not indexed blind."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        return _fresh_service(tmp_path)

    def test_file_disappearing_after_scan_is_a_failed_outcome(
        self,
        service: MdqService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The scan lists a file that no longer exists by the time it is read."""

        def _listing(_service: MdqService, _directory: Path) -> list[Path]:
            return [tmp_path / "gone.md"]

        monkeypatch.setattr(indexer, "iter_indexable_files", _listing)
        tally = indexer._PathTally()

        outcomes = asyncio.run(indexer._index_directory(service, tmp_path, tally))

        assert [outcome.status for outcome in outcomes] == ["failed"]
        assert outcomes[0].reason_code == "file_disappeared"
        assert (tally.discovered_files, tally.committed_files, tally.failed_files) == (
            1,
            0,
            1,
        )

    def test_file_leaving_the_roots_between_scan_and_read_counts_as_failed(
        self,
        service: MdqService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The first authorization (the scan) passes; the read-time re-authorization does not."""
        target = tmp_path / "a.md"
        target.write_text("# A\n\nOne")
        calls = 0

        def _flaky_authorize(_path: Path, _roots: object) -> bool:
            nonlocal calls
            calls += 1
            return calls == 1

        monkeypatch.setattr(indexer, "authorize_path", _flaky_authorize)

        with pytest.raises(MdqServiceError, match="discovered files failed"):
            asyncio.run(index_paths_all(service, [str(target)]))
        assert "Failed to index" in caplog.text


def index_paths_all(service: MdqService, paths: list[str]) -> object:
    return indexer.index_paths(service, IndexPathsRequest(paths=paths))


class TestCommitAndStateRules:
    """index_state advances only on a committed write, so a failed file is re-read."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        return _fresh_service(tmp_path)

    def test_size_limit_skip_does_not_advance_index_state(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        service.max_file_bytes = 10
        (tmp_path / "small.md").write_text("# S\n\nfit")
        (tmp_path / "big.md").write_text("# B\n\n" + "x" * 100)

        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(tmp_path)]))
        )

        assert (result["indexed_count"], result["skipped_count"]) == (1, 1)
        assert (
            result["discovered_file_count"],
            result["committed_file_count"],
            result["skipped_file_count"],
            result["failed_file_count"],
        ) == (2, 1, 1, 0)
        assert _index_state_keys(service) == {f"mtime:{tmp_path / 'small.md'}"}

    def test_write_failure_keeps_index_state_and_the_retry_reindexes(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A production write failure leaves index_state where it was, so the next run re-reads."""
        target = tmp_path / "b.md"
        target.write_text("# B\n\nTwo")
        asyncio.run(_refresh_paths(service, RefreshIndexRequest(paths=[str(target)])))
        state_key = f"mtime:{target}"
        recorded = _index_state_value(service, state_key)
        assert recorded is not None

        first_mtime_ns = target.stat().st_mtime_ns
        target.write_text("# B\n\nThree")
        later_ns = first_mtime_ns + 1_000_000_000
        os.utime(target, ns=(later_ns, later_ns))

        # A held write lock makes the production transaction fail with a real
        # sqlite3.OperationalError (database is locked) without breaking the schema.
        service.sqlite_busy_timeout = (
            50  # fail fast instead of waiting out the 5 s default
        )
        blocker = sqlite3.connect(service.db_path, isolation_level=None)
        blocker.execute("BEGIN EXCLUSIVE")
        try:
            with pytest.raises(MdqServiceError, match="discovered files failed"):
                asyncio.run(
                    _refresh_paths(service, RefreshIndexRequest(paths=[str(target)]))
                )
        finally:
            blocker.execute("ROLLBACK")
            blocker.close()

        assert _index_state_value(service, state_key) == recorded
        assert _table_count(service, "documents") == 1  # the failed re-index added none

        result = asyncio.run(
            _refresh_paths(service, RefreshIndexRequest(paths=[str(target)]))
        )

        assert result["committed_file_count"] == 1
        assert _index_state_value(service, state_key) != recorded
        assert _table_count(service, "chunks") == 1

    def test_uncommitted_outcomes_never_count_as_committed(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A run of only skipped files commits nothing and reports neither success nor an error."""
        service.max_file_bytes = 10
        (tmp_path / "big.md").write_text("# B\n\n" + "x" * 100)

        message, meta = asyncio.run(
            indexer.index_paths(service, IndexPathsRequest(paths=[str(tmp_path)]))
        )

        assert message == PARTIAL_SUCCESS_TEXT
        assert meta["committed_file_count"] == 0
        assert meta["skipped_file_count"] == 1
        assert meta["failed_file_count"] == 0
