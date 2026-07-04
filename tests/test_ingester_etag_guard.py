"""tests/test_ingester_etag_guard.py
Unit tests for ETagManager.update() stale-guard logic.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_etag_mgr(stored_fetched_at: str | None, doc_id: int = 42) -> object:
    from rag.ingestion.etag_manager import ETagManager

    db = MagicMock()
    db.fetchall.return_value = (
        [(stored_fetched_at,)] if stored_fetched_at is not None else []
    )
    return ETagManager(db, doc_id), db


class TestUpdateEtagGuard:
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
        db.commit.assert_called_once()

    def test_stale_incoming_skips_update(self) -> None:
        etag_mgr, db = _make_etag_mgr("2026-06-10T10:00:00")

        with patch("rag.ingestion.etag_manager.logger") as mock_logger:
            etag_mgr.update("etag-old", "Mon, 01 Jun 2026", "2026-06-01T10:00:00")

        db.execute.assert_not_called()
        db.commit.assert_not_called()
        mock_logger.info.assert_called_once()
        logged_msg = mock_logger.info.call_args[0][0]
        assert "stale" in logged_msg

    def test_missing_fetched_at_uses_coalesce_fill_only(self) -> None:
        etag_mgr, db = _make_etag_mgr("2026-06-10T10:00:00")

        etag_mgr.update("etag-x", "Mon, 01 Jun 2026", None)

        db.execute.assert_called_once()
        db.commit.assert_called_once()
        db.fetchall.assert_not_called()
        sql = db.execute.call_args[0][0]
        assert "COALESCE(etag, ?)" in sql
        assert "COALESCE(last_modified, ?)" in sql

    def test_missing_fetched_at_does_not_overwrite_existing_etag(self) -> None:
        etag_mgr, db = _make_etag_mgr("2026-06-10T10:00:00")

        etag_mgr.update("etag-stale", "Mon, 01 Jun 2026", None)

        sql = db.execute.call_args[0][0]
        assert "COALESCE(etag, ?)" in sql, (
            "Must use fill-only SQL when new_fetched_at is None"
        )

    def test_missing_fetched_at_fills_null_etag(self) -> None:
        etag_mgr, db = _make_etag_mgr(None)

        etag_mgr.update("etag-first", "Mon, 01 Jun 2026", None)

        db.execute.assert_called_once()
        sql = db.execute.call_args[0][0]
        assert "COALESCE(etag, ?)" in sql

    def test_both_none_returns_early_no_db_query(self) -> None:
        from rag.ingestion.etag_manager import ETagManager

        db = MagicMock()
        etag_mgr = ETagManager(db, 42)

        etag_mgr.update(None, None, "2026-06-01T10:00:00")

        db.execute.assert_not_called()
        db.fetchall.assert_not_called()
        db.commit.assert_not_called()
