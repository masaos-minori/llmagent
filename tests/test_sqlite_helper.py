"""tests/test_sqlite_helper.py
Unit tests for SQLiteHelper target-aware DB path selection.
"""

from unittest.mock import patch

import pytest
from db.config import DbConfig
from db.helper import SQLiteHelper

_MOCK_CFG = DbConfig(
    rag_db_path="/opt/llm/db/rag.sqlite",
    session_db_path="/opt/llm/db/session.sqlite",
    sqlite_vec_so="/opt/llm/sqlite-vec/vec0.so",
    sqlite_timeout=30,
    sqlite_busy_timeout_ms=30000,
    embedding_dims=384,
)


def _patch_config():
    """Return a context manager that patches build_db_config for SQLiteHelper."""
    return patch("db.helper.build_db_config", return_value=_MOCK_CFG)


class TestSQLiteHelperTarget:
    def test_default_target_is_rag(self) -> None:
        with _patch_config():
            db = SQLiteHelper()
        assert db._target == "rag"

    def test_explicit_rag_target(self) -> None:
        with _patch_config():
            db = SQLiteHelper("rag")
        assert db._target == "rag"

    def test_explicit_session_target(self) -> None:
        with _patch_config():
            db = SQLiteHelper("session")
        assert db._target == "session"

    def test_invalid_target_raises(self) -> None:
        with pytest.raises(
            ValueError, match="target must be 'rag', 'session', or 'workflow'"
        ):
            SQLiteHelper("invalid")

    def test_db_path_returns_rag_path(self) -> None:
        with _patch_config():
            db = SQLiteHelper("rag")
        assert db.DB_PATH == "/opt/llm/db/rag.sqlite"

    def test_db_path_returns_session_path(self) -> None:
        with _patch_config():
            db = SQLiteHelper("session")
        assert db.DB_PATH == "/opt/llm/db/session.sqlite"

    def test_conn_is_none_before_open(self) -> None:
        with _patch_config():
            db = SQLiteHelper("rag")
        assert db.conn is None

    def test_close_is_safe_when_not_open(self) -> None:
        with _patch_config():
            db = SQLiteHelper("session")
        db.close()  # must not raise

    def test_invalid_target_empty_string(self) -> None:
        with pytest.raises(
            ValueError, match="target must be 'rag', 'session', or 'workflow'"
        ):
            SQLiteHelper("")

    def test_config_load_failure_raises_runtime_error(self) -> None:
        with patch("db.helper.build_db_config", side_effect=ValueError("bad config")):
            with pytest.raises(RuntimeError, match="DbConfig load failed"):
                SQLiteHelper("rag")

    def test_default_load_vec_rag(self) -> None:
        with _patch_config():
            db = SQLiteHelper("rag")
        assert db._default_load_vec is True

    def test_default_load_vec_session(self) -> None:
        with _patch_config():
            db = SQLiteHelper("session")
        assert db._default_load_vec is False
