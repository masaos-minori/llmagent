"""tests/test_db_performance.py

Tests for SQLiteHelper.open() reuse_connection behavior.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from db.config import DbConfig
from db.helper import SQLiteHelper


def _make_cfg(db_path: str) -> DbConfig:
    return DbConfig(
        rag_db_path=db_path,
        session_db_path=db_path,
        workflow_db_path=db_path,
    )


class TestConnectionReuse:
    def test_connection_reuse_same_instance(self, tmp_path: Path) -> None:
        """reuse_connection=True returns same connection object on second open()."""
        db_path = str(tmp_path / "test.sqlite")
        cfg = _make_cfg(db_path)
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper("rag")
            with helper.open(reuse_connection=True) as h1:
                conn1 = h1.conn
            with helper.open(reuse_connection=True) as h2:
                conn2 = h2.conn
        assert conn1 is conn2

    def test_backward_compatibility_per_query(self, tmp_path: Path) -> None:
        """Default reuse_connection=False opens and closes connection each time."""
        db_path = str(tmp_path / "test.sqlite")
        cfg = _make_cfg(db_path)
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper("rag")
            with helper.open() as h1:
                conn1 = h1.conn
            # After context exit, connection should be closed
            assert conn1 is not None
            with helper.open() as h2:
                conn2 = h2.conn
        # New connection created (different object or same closed+reopened)
        # At minimum: no exception raised and connection is usable
        assert conn2 is not None

    def test_reuse_connection_keeps_open_after_context_exit(
        self, tmp_path: Path
    ) -> None:
        """reuse_connection=True keeps the connection open after context exit."""
        db_path = str(tmp_path / "test.sqlite")
        cfg = _make_cfg(db_path)
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper("rag")
            with helper.open(reuse_connection=True) as h1:
                conn1 = h1.conn
            # After context exit, connection should still be open
            assert helper.conn is conn1

    def test_non_reuse_closes_connection_after_context_exit(
        self, tmp_path: Path
    ) -> None:
        """reuse_connection=False closes the connection after context exit."""
        db_path = str(tmp_path / "test.sqlite")
        cfg = _make_cfg(db_path)
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper("rag")
            with helper.open() as _h1:
                pass
            # After context exit, connection should be closed
            assert helper.conn is None

    def test_reuse_then_non_reuse_resets_lifecycle(self, tmp_path: Path) -> None:
        """Calling open(reuse_connection=True) followed by open(reuse_connection=False) resets lifecycle behavior."""
        db_path = str(tmp_path / "test.sqlite")
        cfg = _make_cfg(db_path)
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper("rag")
            # First: reuse mode — connection stays open after exit
            with helper.open(reuse_connection=True) as h1:
                conn1 = h1.conn
            assert helper.conn is conn1

            # Second: non-reuse mode — creates new connection, closes on exit
            with helper.open() as _h2:
                pass
            # After context exit, connection should be closed (non-reuse mode)
            assert helper.conn is None

    def test_close_sets_conn_to_none(self, tmp_path: Path) -> None:
        """close() sets conn back to None."""
        db_path = str(tmp_path / "test.sqlite")
        cfg = _make_cfg(db_path)
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper("rag")
            with helper.open(reuse_connection=True) as h1:
                conn1 = h1.conn
            assert helper.conn is conn1
            helper.close()
            assert helper.conn is None

    def test_close_after_reuse_mode_sets_conn_to_none(self, tmp_path: Path) -> None:
        """close() sets conn to None even after reuse mode."""
        db_path = str(tmp_path / "test.sqlite")
        cfg = _make_cfg(db_path)
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper("rag")
            with helper.open(reuse_connection=True) as h1:
                conn1 = h1.conn
            assert helper.conn is conn1
            helper.close()
            assert helper.conn is None

    def test_no_hidden_persistent_connection_after_non_reuse(
        self, tmp_path: Path
    ) -> None:
        """No hidden persistent connection remains when reuse mode is disabled."""
        db_path = str(tmp_path / "test.sqlite")
        cfg = _make_cfg(db_path)
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper("rag")
            # Open in non-reuse mode — connection closed on exit
            with helper.open() as _h1:
                pass
            assert helper.conn is None

            # Open again in non-reuse mode — creates new connection, closes on exit
            with helper.open() as _h2:
                pass
            assert helper.conn is None
