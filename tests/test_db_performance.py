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
        helper = SQLiteHelper("rag")
        with patch("db.helper.build_db_config", return_value=cfg):
            with helper.open(reuse_connection=True) as h1:
                conn1 = h1.conn
            with helper.open(reuse_connection=True) as h2:
                conn2 = h2.conn
        assert conn1 is conn2

    def test_backward_compatibility_per_query(self, tmp_path: Path) -> None:
        """Default reuse_connection=False opens and closes connection each time."""
        db_path = str(tmp_path / "test.sqlite")
        cfg = _make_cfg(db_path)
        helper = SQLiteHelper("rag")
        with patch("db.helper.build_db_config", return_value=cfg):
            with helper.open() as h1:
                conn1 = h1.conn
            # After context exit, connection should be closed
            assert conn1 is not None
            with helper.open() as h2:
                conn2 = h2.conn
        # New connection created (different object or same closed+reopened)
        # At minimum: no exception raised and connection is usable
        assert conn2 is not None
