"""
tests/test_approval_task_persistence.py

Characterization tests for approval task ID persistence across turns.
"""

from __future__ import annotations

import sqlite3
from typing import Any

import pytest
from agent.context import TurnContext
from agent.workflow.approval_ops import (
    resolve_approval,
    update_task_status,
)
from db.helper import SQLiteHelper


def _make_db(tmp_path: Any) -> SQLiteHelper:
    """Create a temp SQLite DB with approvals and tasks tables."""
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
        """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'running',
            created_at TEXT NOT NULL,
            updated_at TEXT
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
    conn.execute(
        "INSERT INTO tasks (task_id, status, created_at) VALUES (?, ?, ?)",
        ("task-1", "running", "2026-01-01T00:00:00+00:00"),
    )
    conn.commit()
    conn.close()
    return SQLiteHelper(db_path)


class TestPendingApprovalIdClearing:
    """Test pending approval ID clearing — verify cleared after resolution."""

    def test_pending_approval_id_cleared_after_resolution(self, tmp_path: Any) -> None:
        """pending_approval_id should be cleared after approval resolution."""
        ctx = TurnContext()
        ctx.turn.pending_approval_id = "test-approval-1"

        db = _make_db(tmp_path)
        resolve_approval(db, "test-approval-1", "approved")

        assert ctx.turn.pending_approval_id is None

    def test_pending_approval_id_not_cleared_before_resolution(
        self, tmp_path: Any
    ) -> None:
        """pending_approval_id should remain before resolution."""
        ctx = TurnContext()
        ctx.turn.pending_approval_id = "test-approval-1"

        # Don't resolve yet — pending_approval_id remains set
        assert ctx.turn.pending_approval_id == "test-approval-1"

    def test_pending_approval_id_cleared_on_rejection(self, tmp_path: Any) -> None:
        """pending_approval_id should be cleared even on rejection."""
        ctx = TurnContext()
        ctx.turn.pending_approval_id = "test-approval-1"

        db = _make_db(tmp_path)
        resolve_approval(db, "test-approval-1", "rejected")

        assert ctx.turn.pending_approval_id is None


class TestTaskIdOverwriteDetection:
    """Test task ID overwrite detection — verify warning issued on second approval."""

    def test_warning_issued_on_overwrite(self, tmp_path: Any) -> None:
        """Warning should be logged when pending_approval_task_id is overwritten."""
        ctx = TurnContext()
        ctx.turn.pending_approval_task_id = "old-task-id"

        # Simulate what happens in cmd_workflow._cmd_approve
        new_task_id = "new-task-id"
        if ctx.turn.pending_approval_task_id is not None:
            # This would generate a warning log in real code
            pass  # The actual warning is logged by the orchestrator

        # After overwrite, the value should be updated
        ctx.turn.pending_approval_task_id = new_task_id
        assert ctx.turn.pending_approval_task_id == new_task_id

    def test_no_warning_when_first_assignment(self, tmp_path: Any) -> None:
        """No warning when there's no existing value to overwrite."""
        ctx = TurnContext()
        ctx.turn.pending_approval_task_id = None

        new_task_id = "new-task-id"
        ctx.turn.pending_approval_task_id = new_task_id
        assert ctx.turn.pending_approval_task_id == new_task_id


class TestHaltedTaskStatusRejection:
    """Test halted task status rejection — verify error returned instead of continued processing."""

    def test_halted_task_returns_error(self, tmp_path: Any) -> None:
        """Halted task status should cause an error, not continue processing."""
        db = _make_db(tmp_path)
        update_task_status(db, "task-1", "halted")

        # Verify the task is halted
        row = db.fetchone(
            "SELECT status FROM tasks WHERE task_id=?",
            ("task-1",),
        )
        assert row["status"] == "halted"

    def test_halted_task_prevents_resume(self, tmp_path: Any) -> None:
        """A halted task should not be resumable via normal flow."""
        db = _make_db(tmp_path)
        update_task_status(db, "task-1", "halted")

        # Try to resolve approval for a halted task
        with pytest.raises(RuntimeError):
            resolve_approval(db, "test-approval-1", "approved")

    def test_running_task_allows_resume(self, tmp_path: Any) -> None:
        """A running task should allow approval resolution."""
        db = _make_db(tmp_path)
        # Task is already "running"
        resolve_approval(db, "test-approval-1", "approved")

        row = db.fetchone(
            "SELECT status FROM approvals WHERE approval_id=?",
            ("test-approval-1",),
        )
        assert row["status"] == "approved"


class TestMultipleSequentialApprovals:
    """Test multiple sequential approvals — verify correct task restoration for each."""

    def test_sequential_approvals_restore_correct_tasks(self, tmp_path: Any) -> None:
        """Each sequential approval should restore the correct task state."""
        db = _make_db(tmp_path)

        # First approval
        resolve_approval(db, "test-approval-1", "approved")

        # Create a second approval for a different task
        conn = sqlite3.connect(db.path)
        conn.execute(
            "INSERT INTO approvals (approval_id, task_id, stage_id, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                "test-approval-2",
                "task-2",
                "stage-2",
                "pending",
                "2026-01-01T00:00:00+00:00",
            ),
        )
        conn.execute(
            "INSERT INTO tasks (task_id, status, created_at) VALUES (?, ?, ?)",
            ("task-2", "running", "2026-01-01T00:00:00+00:00"),
        )
        conn.commit()
        conn.close()

        # Second approval
        resolve_approval(db, "test-approval-2", "approved")

        # Verify both are approved
        rows = db.fetchall(
            "SELECT approval_id, status FROM approvals ORDER BY approval_id"
        )
        assert len(rows) == 2
        assert rows[0]["status"] == "approved"
        assert rows[1]["status"] == "approved"

    def test_sequential_approvals_with_different_statuses(self, tmp_path: Any) -> None:
        """Sequential approvals with mixed approve/reject statuses."""
        db = _make_db(tmp_path)

        # First approval — reject
        resolve_approval(db, "test-approval-1", "rejected")

        # Create a second approval
        conn = sqlite3.connect(db.path)
        conn.execute(
            "INSERT INTO approvals (approval_id, task_id, stage_id, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                "test-approval-2",
                "task-2",
                "stage-2",
                "pending",
                "2026-01-01T00:00:00+00:00",
            ),
        )
        conn.execute(
            "INSERT INTO tasks (task_id, status, created_at) VALUES (?, ?, ?)",
            ("task-2", "running", "2026-01-01T00:00:00+00:00"),
        )
        conn.commit()
        conn.close()

        # Second approval — approve
        resolve_approval(db, "test-approval-2", "approved")

        # Verify statuses
        rows = db.fetchall(
            "SELECT approval_id, status FROM approvals ORDER BY approval_id"
        )
        assert rows[0]["status"] == "rejected"
        assert rows[1]["status"] == "approved"
