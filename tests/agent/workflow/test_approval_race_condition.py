"""
tests/test_approval_race_condition.py

Characterization tests for approval resolution race condition.
"""

from __future__ import annotations

import asyncio
import sqlite3
import threading
import time
from typing import Any

import pytest
from agent.workflow.approval_ops import resolve_approval
from db.helper import SQLiteHelper


def _make_db(tmp_path: Any) -> SQLiteHelper:
    """Create a temp SQLite DB with approvals table."""
    db_path = str(tmp_path / "test_approvals.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS approvals (
            approval_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            stage_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            reason TEXT,
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            workflow_id TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO approvals (approval_id, task_id, stage_id, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            "test-approval-1",
            "task-1",
            "stage-1",
            "pending",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    conn.commit()
    conn.close()
    return SQLiteHelper(db_path)


class TestConcurrentResolutionDetection:
    """Test concurrent resolution detection — verify only one succeeds."""

    def test_concurrent_resolution_only_one_succeeds(self, tmp_path: Any) -> None:
        """Two threads resolving simultaneously — only one should succeed."""
        db = _make_db(tmp_path)
        errors: list[Exception] = []

        def resolve():
            try:
                resolve_approval(db, "test-approval-1", "approved")
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=resolve)
        t2 = threading.Thread(target=resolve)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        assert len(errors) == 1
        assert isinstance(errors[0], RuntimeError)
        assert "already resolved" in str(errors[0])

    def test_concurrent_resolution_both_fail(self, tmp_path: Any) -> None:
        """Both threads fail when timing is tight enough."""
        db = _make_db(tmp_path)
        success_count = [0]
        errors: list[Exception] = []

        def resolve():
            try:
                resolve_approval(db, "test-approval-1", "approved")
                success_count[0] += 1
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=resolve)
        t2 = threading.Thread(target=resolve)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        # At least one must fail; both may fail depending on timing
        assert success_count[0] <= 1

    @pytest.mark.asyncio
    async def test_concurrent_resolution_async(self, tmp_path: Any) -> None:
        """Async concurrent resolution — only one should succeed."""
        db = _make_db(tmp_path)
        results: list[tuple[int, Exception | None]] = []

        async def resolve(idx: int):
            try:
                await asyncio.to_thread(
                    resolve_approval, db, "test-approval-1", "approved"
                )
                results.append((idx, None))
            except Exception as exc:
                results.append((idx, exc))

        await asyncio.gather(resolve(1), resolve(2))
        successes = sum(1 for _, e in results if e is None)
        failures = sum(1 for _, e in results if e is not None)
        assert successes <= 1
        assert failures >= 1


class TestOptimisticLocking:
    """Test optimistic locking — verify second resolution fails."""

    def test_second_resolution_fails(self, tmp_path: Any) -> None:
        """Second sequential resolution should fail with appropriate error."""
        db = _make_db(tmp_path)
        resolve_approval(db, "test-approval-1", "approved")

        with pytest.raises(RuntimeError, match="already resolved"):
            resolve_approval(db, "test-approval-1", "rejected")

    def test_second_resolution_different_status(self, tmp_path: Any) -> None:
        """Second resolution with different status should also fail."""
        db = _make_db(tmp_path)
        resolve_approval(db, "test-approval-1", "approved")

        with pytest.raises(RuntimeError, match="already resolved"):
            resolve_approval(db, "test-approval-1", "approved")

    def test_sequential_resolutions_all_fail_after_first(self, tmp_path: Any) -> None:
        """Multiple sequential resolutions after first all fail."""
        db = _make_db(tmp_path)
        resolve_approval(db, "test-approval-1", "approved")

        for i in range(3):
            with pytest.raises(RuntimeError, match="already resolved"):
                resolve_approval(db, "test-approval-1", "rejected")


class TestCheckAndResolveAtomicity:
    """Test check-and-resolve atomicity — verify within single transaction."""

    def test_check_and_resolve_not_atomic(self, tmp_path: Any) -> None:
        """Current implementation: check and resolve are NOT atomic."""
        db = _make_db(tmp_path)
        errors: list[Exception] = []

        def resolve():
            try:
                resolve_approval(db, "test-approval-1", "approved")
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=resolve)
        t2 = threading.Thread(target=resolve)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        # The race condition means at least one will fail
        assert len(errors) >= 1

    def test_check_and_resolve_with_delay_gap(self, tmp_path: Any) -> None:
        """Simulate gap between check and resolve by reading manually."""
        db = _make_db(tmp_path)
        conn = sqlite3.connect(db.path)
        row = conn.execute(
            "SELECT status FROM approvals WHERE approval_id=?", ("test-approval-1",)
        ).fetchone()
        assert row["status"] == "pending"

        # Simulate a delay between check and resolve
        time.sleep(0.01)

        # Now resolve — should succeed since no other thread modified it
        resolve_approval(db, "test-approval-1", "approved")
        conn.close()


class TestAlreadyResolvedClarity:
    """Test already-resolved clarity — verify clear message vs 'not found'."""

    def test_already_resolved_returns_clear_message(self, tmp_path: Any) -> None:
        """Already-resolved should return 'already resolved' not 'not found'."""
        db = _make_db(tmp_path)
        resolve_approval(db, "test-approval-1", "approved")

        with pytest.raises(RuntimeError, match="already resolved") as exc_info:
            resolve_approval(db, "test-approval-1", "rejected")

        assert "already resolved" in str(exc_info.value)
        assert "not found" not in str(exc_info.value).lower()

    def test_not_found_returns_different_message(self, tmp_path: Any) -> None:
        """Non-existent approval should return 'not found' not 'already resolved'."""
        db = _make_db(tmp_path)

        with pytest.raises(RuntimeError, match="not found") as exc_info:
            resolve_approval(db, "nonexistent-approval", "approved")

        assert "not found" in str(exc_info.value)
        assert "already resolved" not in str(exc_info.value).lower()

    def test_rejected_approval_returns_already_resolved(self, tmp_path: Any) -> None:
        """Rejected approval should also return 'already resolved'."""
        db = _make_db(tmp_path)
        resolve_approval(db, "test-approval-1", "rejected")

        with pytest.raises(RuntimeError, match="already resolved") as exc_info:
            resolve_approval(db, "test-approval-1", "approved")

        assert "already resolved" in str(exc_info.value)
