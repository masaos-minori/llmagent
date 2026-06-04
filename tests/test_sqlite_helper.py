"""tests/test_sqlite_helper.py
Unit tests for SQLiteHelper target-aware DB path selection.
"""

import pytest
from db.helper import SQLiteHelper


class TestSQLiteHelperTarget:
    def test_default_target_is_rag(self) -> None:
        db = SQLiteHelper()
        assert db._target == "rag"

    def test_explicit_rag_target(self) -> None:
        db = SQLiteHelper("rag")
        assert db._target == "rag"

    def test_explicit_session_target(self) -> None:
        db = SQLiteHelper("session")
        assert db._target == "session"

    def test_invalid_target_raises(self) -> None:
        with pytest.raises(ValueError, match="target must be 'rag' or 'session'"):
            SQLiteHelper("invalid")

    def test_db_path_returns_rag_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(SQLiteHelper, "_RAG_PATH", "/opt/llm/db/rag.sqlite")
        monkeypatch.setattr(SQLiteHelper, "_SESSION_PATH", "/opt/llm/db/session.sqlite")
        monkeypatch.setattr(SQLiteHelper, "_config_loaded", True)
        assert SQLiteHelper("rag").DB_PATH == "/opt/llm/db/rag.sqlite"

    def test_db_path_returns_session_path(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(SQLiteHelper, "_RAG_PATH", "/opt/llm/db/rag.sqlite")
        monkeypatch.setattr(SQLiteHelper, "_SESSION_PATH", "/opt/llm/db/session.sqlite")
        monkeypatch.setattr(SQLiteHelper, "_config_loaded", True)
        assert SQLiteHelper("session").DB_PATH == "/opt/llm/db/session.sqlite"

    def test_conn_is_none_before_open(self) -> None:
        db = SQLiteHelper("rag")
        assert db.conn is None

    def test_close_is_safe_when_not_open(self) -> None:
        db = SQLiteHelper("session")
        db.close()  # must not raise

    def test_invalid_target_empty_string(self) -> None:
        with pytest.raises(ValueError, match="target must be 'rag' or 'session'"):
            SQLiteHelper("")
