"""tests/test_ingester_etag_guard.py
Unit tests for ETagManager.update() stale-guard logic.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from rag.ingestion.etag_manager import (
    ETagManager,
    InvalidIncomingTimestampError,
    InvalidStoredTimestampError,
)


def _make_etag_mgr(
    stored_fetched_at: str | None, doc_id: int = 42
) -> tuple[ETagManager, MagicMock]:
    db = MagicMock()
    db.fetchall.return_value = (
        [(stored_fetched_at,)] if stored_fetched_at is not None else []
    )
    return ETagManager(db, doc_id), db


class TestUpdateEtagGuard(unittest.TestCase):
    def test_newer_incoming_updates_etag(self) -> None:
        etag_mgr, db = _make_etag_mgr("2026-06-01T10:00:00")

        etag_mgr.update("etag-new", "Mon, 02 Jun 2026", "2026-06-02T10:00:00")

        db.execute.assert_called_once()
        call_args = db.execute.call_args[0]
        assert "UPDATE documents" in call_args[0]
        assert call_args[1] == (
            "etag-new",
            "Mon, 02 Jun 2026",
            "2026-06-02T10:00:00",
            42,
        )
        # Transaction ownership moved to caller; no internal commit
        db.commit.assert_not_called()

    def test_stale_incoming_skips_update(self) -> None:
        etag_mgr, db = _make_etag_mgr("2026-06-10T10:00:00")

        with patch("rag.ingestion.etag_manager.logger") as mock_logger:
            etag_mgr.update("etag-old", "Mon, 01 Jun 2026", "2026-06-01T10:00:00")

        db.execute.assert_not_called()
        db.commit.assert_not_called()
        mock_logger.info.assert_called_once()
        logged_msg = mock_logger.info.call_args[0][0]
        assert "stale" in logged_msg

    def test_empty_fetched_at_raises_value_error(self) -> None:
        etag_mgr, db = _make_etag_mgr("2026-06-10T10:00:00")

        with self.assertRaises(ValueError):
            etag_mgr.update("etag-x", "Mon, 01 Jun 2026", "")

    def test_newer_fetched_at_allows_direct_assignment(self) -> None:
        etag_mgr, db = _make_etag_mgr("2026-06-10T10:00:00")

        etag_mgr.update("etag-new", "Mon, 02 Jun 2026", "2026-06-11T10:00:00")

        db.execute.assert_called_once()
        db.commit.assert_not_called()
        sql = db.execute.call_args[0][0]
        assert "COALESCE" not in sql
        assert "fetched_at = ?" in sql

    def test_both_none_returns_early_no_db_query(self) -> None:
        from rag.ingestion.etag_manager import ETagManager

        db = MagicMock()
        etag_mgr = ETagManager(db, 42)

        etag_mgr.update(None, None, "2026-06-01T10:00:00")

        db.execute.assert_not_called()
        db.fetchall.assert_not_called()
        db.commit.assert_not_called()

    def test_datetime_comparison_with_z_suffix(self) -> None:
        """Verify timezone-aware datetime comparison handles 'Z' suffix."""
        etag_mgr, db = _make_etag_mgr("2026-06-10T10:00:00+00:00")

        with patch("rag.ingestion.etag_manager.logger") as mock_logger:
            etag_mgr.update("etag-z", "Mon, 01 Jun 2026", "2026-06-01T10:00:00Z")

        db.execute.assert_not_called()
        db.commit.assert_not_called()
        mock_logger.info.assert_called_once()
        logged_msg = mock_logger.info.call_args[0][0]
        assert "stale" in logged_msg

    def test_invalid_timestamp_raises_value_error(self) -> None:
        """Invalid timestamps should raise ValueError (fail-closed)."""
        etag_mgr, db = _make_etag_mgr("not-a-date")

        with self.assertRaises(ValueError):
            etag_mgr.update("etag-invalid", "Mon, 01 Jun 2026", "2026-06-01T10:00:00")

    def test_invalid_incoming_raises_incoming_subclass(self) -> None:
        """Invalid incoming fetched_at raises InvalidIncomingTimestampError."""
        etag_mgr, db = _make_etag_mgr("2026-06-10T10:00:00")

        with self.assertRaises(InvalidIncomingTimestampError):
            etag_mgr.update("etag-x", "Mon, 01 Jun 2026", "not-a-date")
        assert isinstance(
            InvalidIncomingTimestampError("x"), InvalidIncomingTimestampError
        )

    def test_invalid_stored_raises_stored_subclass(self) -> None:
        """Invalid stored fetched_at raises InvalidStoredTimestampError."""
        etag_mgr, db = _make_etag_mgr("not-a-date")

        with self.assertRaises(InvalidStoredTimestampError):
            etag_mgr.update("etag-x", "Mon, 01 Jun 2026", "2026-06-01T10:00:00")
