#!/usr/bin/env python3
"""tests/test_state_store.py

Tests for StateStore CRUD operations and optimistic locking in recover_stale_attempts().
"""

import re
from unittest.mock import MagicMock

from agent.workflow.state_store import StateStore


class TestRecoverStaleAttemptsOptimisticLocking:
    """Verify the optimistic locking behavior of recover_stale_attempts()."""

    def _make_mock_db(self):
        """Create a mock SQLiteHelper with row_factory=True."""
        db = MagicMock()
        db.fetchall.return_value = []
        cursor = MagicMock()
        cursor.rowcount = 0
        db.execute.return_value = cursor
        db.commit.return_value = None
        return db

    def test_recover_single_stale_attempt(self):
        """Only the stale running attempt is recovered."""
        ss = StateStore()
        db = self._make_mock_db()

        # Mock find_stale_running_attempts to return a stale attempt
        stale_result = [
            {
                "attempt_id": "att-1",
                "started_at": "2026-08-01T10:00:00",
                "elapsed_sec": 60.0,
            }
        ]
        ss.find_stale_running_attempts = lambda _: stale_result

        cursor = MagicMock()
        cursor.rowcount = 1
        db.execute.return_value = cursor

        result = ss.recover_stale_attempts(db)

        assert result == 1
        call_args = db.execute.call_args
        assert (
            call_args[0][0]
            == "UPDATE attempts SET status='failed', ended_at=? WHERE attempt_id=? AND status='running'"
        )
        assert isinstance(call_args[0][1], tuple)
        assert len(call_args[0][1]) == 2
        iso_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
        assert re.match(iso_pattern, call_args[0][1][0]), (
            f"Expected ISO timestamp, got {call_args[0][1][0]}"
        )
        assert call_args[0][1][1] == "att-1"

    def test_recover_non_stale_attempt_not_changed(self):
        """An attempt within the grace period is not recovered."""
        ss = StateStore()
        db = self._make_mock_db()

        # No stale attempts found
        ss.find_stale_running_attempts = lambda _: []

        result = ss.recover_stale_attempts(db)

        assert result == 0
        db.execute.assert_not_called()

    def test_recover_concurrent_calls_only_one_succeeds(self):
        """Simulate contention: two stale entries for the same attempt_id, only one gets rowcount=1."""
        ss = StateStore()
        db = MagicMock()

        # Two stale entries for the same attempt — simulates two processes racing
        stale_result = [
            {
                "attempt_id": "att-1",
                "started_at": "2026-08-01T10:00:00",
                "elapsed_sec": 60.0,
            },
            {
                "attempt_id": "att-1",
                "started_at": "2026-08-01T10:00:00",
                "elapsed_sec": 60.0,
            },
        ]
        ss.find_stale_running_attempts = lambda _: stale_result

        call_count = [0]

        def execute_side_effect(sql, params):
            call_count[0] += 1
            cursor = MagicMock()
            # First caller claims the attempt (rowcount=1), second caller sees no change (rowcount=0)
            if call_count[0] == 1:
                cursor.rowcount = 1
            else:
                cursor.rowcount = 0
            return cursor

        db.execute.side_effect = execute_side_effect
        db.commit.return_value = None

        result = ss.recover_stale_attempts(db)

        # Only one stale attempt was actually claimed despite two entries
        assert result == 1
        assert db.execute.call_count == 2

    def test_recover_multiple_stale_attempts_all_claimed(self):
        """All stale attempts are recovered when no contention exists."""
        ss = StateStore()
        db = self._make_mock_db()

        stale_result = [
            {
                "attempt_id": "att-1",
                "started_at": "2026-08-01T10:00:00",
                "elapsed_sec": 60.0,
            },
            {
                "attempt_id": "att-2",
                "started_at": "2026-08-01T09:50:00",
                "elapsed_sec": 120.0,
            },
        ]
        ss.find_stale_running_attempts = lambda _: stale_result

        cursor = MagicMock()
        cursor.rowcount = 1
        db.execute.return_value = cursor

        result = ss.recover_stale_attempts(db)

        assert result == 2
        assert db.execute.call_count == 2
        db.commit.assert_called_once()

    def test_recover_mixed_stale_and_non_stale(self):
        """Only stale attempts are recovered; non-stale ones are skipped."""
        ss = StateStore()
        db = self._make_mock_db()

        stale_result = [
            {
                "attempt_id": "att-1",
                "started_at": "2026-08-01T10:00:00",
                "elapsed_sec": 60.0,
            },
        ]
        ss.find_stale_running_attempts = lambda _: stale_result

        cursor = MagicMock()
        cursor.rowcount = 1
        db.execute.return_value = cursor

        result = ss.recover_stale_attempts(db)

        assert result == 1
        assert db.execute.call_count == 1

    def test_recover_no_running_attempts(self):
        """No stale attempts found — nothing happens."""
        ss = StateStore()
        db = self._make_mock_db()

        ss.find_stale_running_attempts = lambda _: []

        result = ss.recover_stale_attempts(db)

        assert result == 0
        db.execute.assert_not_called()
        db.commit.assert_not_called()

    def test_recover_already_failed_attempt_not_double_recovered(self):
        """A stale attempt that changed to 'failed' before recovery is not counted again."""
        ss = StateStore()
        db = MagicMock()

        stale_result = [
            {
                "attempt_id": "att-1",
                "started_at": "2026-08-01T10:00:00",
                "elapsed_sec": 60.0,
            },
        ]
        ss.find_stale_running_attempts = lambda _: stale_result

        call_count = [0]

        def execute_side_effect(sql, params):
            call_count[0] += 1
            cursor = MagicMock()
            # First call: finds stale attempt, but status already changed to 'failed' by another process
            cursor.rowcount = 0
            return cursor

        db.execute.side_effect = execute_side_effect
        db.commit.return_value = None

        result = ss.recover_stale_attempts(db)

        assert result == 0

    def test_find_stale_running_attempts_skips_invalid_timestamp(self):
        """find_stale_running_attempts skips rows with unparseable started_at values."""
        ss = StateStore()
        db = MagicMock()

        # Mock fetchall to return a row with invalid timestamp
        db.fetchall.return_value = [
            {"attempt_id": "att-1", "started_at": "not-a-date"},
        ]

        stale = ss.find_stale_running_attempts(db)

        assert stale == []

    def test_recover_returns_zero_when_commit_fails_on_no_changes(self):
        """commit() is not called when there are no stale attempts at all."""
        ss = StateStore()
        db = self._make_mock_db()

        ss.find_stale_running_attempts = lambda _: []

        ss.recover_stale_attempts(db)

        db.commit.assert_not_called()
