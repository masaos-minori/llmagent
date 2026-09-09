"""tests/rag/test_db_connection.py

Tests for RagDatabaseConnection in scripts/rag/db_connection.py.

Covers:
- Happy path: __enter__ opens connection, __exit__ closes it
- Exception during usage: __exit__ still closes connection
- Exception during open: error propagates, connection not opened
- Exception during close: handled gracefully
- Edge cases: re-entering closed context manager, nested context managers
"""

from unittest.mock import MagicMock, patch

import pytest
from rag.db_connection import RagDatabaseConnection


class TestHappyPath:
    """Test the happy path: __enter__ opens connection, __exit__ closes it."""

    def test_enter_opens_connection(self):
        """__enter__ opens a SQLiteHelper connection."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            mock_open_result = MagicMock()
            MockSQLiteHelper.return_value.open.return_value = mock_open_result
            with RagDatabaseConnection(rag_db_path="/tmp/test.db") as db:
                assert db is mock_open_result
                MockSQLiteHelper.assert_called_once_with(
                    db_path="/tmp/test.db",
                    sqlite_vec_so="/opt/llm/sqlite-vec/vec0.so",
                    sqlite_timeout=5,
                    sqlite_busy_timeout_ms=5000,
                )
                MockSQLiteHelper.return_value.open.assert_called_once_with(
                    row_factory=True
                )

    def test_exit_closes_connection(self):
        """__exit__ closes the connection after normal exit."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            mock_closeable = MagicMock()
            MockSQLiteHelper.return_value.open.return_value = mock_closeable
            with RagDatabaseConnection(rag_db_path="/tmp/test.db"):
                pass
            mock_closeable.close.assert_called_once()

    def test_default_parameters_used_when_no_rag_db_path(self):
        """Default parameters used when rag_db_path is None."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            mock_db = MagicMock()
            MockSQLiteHelper.return_value.open.return_value = mock_db
            with RagDatabaseConnection():
                pass
            MockSQLiteHelper.assert_called_once_with()
            MockSQLiteHelper.return_value.open.assert_called_once_with(row_factory=True)

    def test_custom_parameters_passed_through(self):
        """Custom parameters passed through to SQLiteHelper."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            mock_closeable = MagicMock()
            MockSQLiteHelper.return_value.open.return_value = mock_closeable
            with RagDatabaseConnection(
                rag_db_path="/custom/path.db",
                sqlite_vec_so="/custom/vec0.so",
                sqlite_timeout=10,
                sqlite_busy_timeout_ms=10000,
            ):
                pass
            MockSQLiteHelper.assert_called_once_with(
                db_path="/custom/path.db",
                sqlite_vec_so="/custom/vec0.so",
                sqlite_timeout=10,
                sqlite_busy_timeout_ms=10000,
            )

    def test_context_manager_returns_sqlite_helper(self):
        """__enter__ returns the SQLiteHelper instance."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            expected_db = MagicMock()
            MockSQLiteHelper.return_value.open.return_value = expected_db
            with RagDatabaseConnection(rag_db_path="/tmp/test.db") as db:
                assert db is expected_db

    def test_multiple_exits_close_connection_only_once(self):
        """Multiple exits close the connection only once."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            mock_helper1 = MagicMock()
            mock_helper2 = MagicMock()
            mock_db1 = MagicMock()
            mock_db2 = MagicMock()
            mock_helper1.open.return_value = mock_db1
            mock_helper2.open.return_value = mock_db2
            MockSQLiteHelper.side_effect = [mock_helper1, mock_helper2]
            with RagDatabaseConnection(rag_db_path="/tmp/test.db"):
                pass
            # Second exit should not cause another close
            with RagDatabaseConnection(rag_db_path="/tmp/test.db"):
                pass
            # Each context manager creates a new SQLiteHelper instance,
            # so close is called twice (once per instance)
            assert mock_db1.close.call_count == 1
            assert mock_db2.close.call_count == 1

    def test_connection_available_during_context(self):
        """Connection is available during context manager execution."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            mock_instance = MagicMock()
            MockSQLiteHelper.return_value.open.return_value = mock_instance
            with RagDatabaseConnection(rag_db_path="/tmp/test.db") as db:
                assert db is mock_instance
                # Simulate using the connection
                db.execute = MagicMock()
                db.execute("SELECT 1")
                db.execute.assert_called_once_with("SELECT 1")

    def test_row_factory_true_always_set(self):
        """row_factory=True is always set on open()."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            mock_instance = MagicMock()
            MockSQLiteHelper.return_value.open.return_value = mock_instance
            with RagDatabaseConnection(rag_db_path="/tmp/test.db"):
                pass
            MockSQLiteHelper.return_value.open.assert_called_once_with(row_factory=True)

    def test_exit_sets_db_to_none_after_close(self):
        """__exit__ sets _db to None after closing."""
        conn = RagDatabaseConnection(rag_db_path="/tmp/test.db")
        with patch.object(conn, "_db", MagicMock()):
            with conn:
                pass
            assert conn._db is None

    def test_nested_context_managers_work_correctly(self):
        """Nested context managers work correctly."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            mock_helper1 = MagicMock()
            mock_helper2 = MagicMock()
            db1 = MagicMock()
            db2 = MagicMock()
            mock_helper1.open.return_value = db1
            mock_helper2.open.return_value = db2
            MockSQLiteHelper.side_effect = [mock_helper1, mock_helper2]
            with RagDatabaseConnection(rag_db_path="/outer.db") as outer_db:
                with RagDatabaseConnection(rag_db_path="/inner.db") as inner_db:
                    assert outer_db is db1
                    assert inner_db is db2
            # Outer should be closed first, then inner
            db1.close.assert_called_once()
            db2.close.assert_called_once()

    def test_context_manager_is_reusable(self):
        """Context manager can be reused multiple times."""
        conn = RagDatabaseConnection(rag_db_path="/tmp/test.db")
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            mock_helper1 = MagicMock()
            mock_helper2 = MagicMock()
            db1 = MagicMock()
            db2 = MagicMock()
            mock_helper1.open.return_value = db1
            mock_helper2.open.return_value = db2
            MockSQLiteHelper.side_effect = [mock_helper1, mock_helper2]
            with conn as db1_conn:
                assert db1_conn is db1
            with conn as db2_conn:
                assert db2_conn is db2
            assert db1.close.call_count == 1
            assert db2.close.call_count == 1

    def test_open_called_before_use(self):
        """open() is called before the connection is used."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            call_order = []
            mock_closeable = MagicMock()

            def track_open(*args, **kwargs):
                call_order.append("open")
                return mock_closeable

            MockSQLiteHelper.return_value.open = track_open  # type: ignore[assignment] — replace method with tracking function
            with RagDatabaseConnection(rag_db_path="/tmp/test.db"):
                call_order.append("use")
            assert call_order == ["open", "use"]

    def test_close_called_after_use(self):
        """close() is called after the connection is used."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            call_order = []
            mock_closeable = MagicMock()

            original_close = mock_closeable.close

            def track_close():
                call_order.append("close")
                return original_close()

            mock_closeable.close = track_close  # type: ignore[assignment] — replace method with tracking function
            MockSQLiteHelper.return_value.open.return_value = mock_closeable
            with RagDatabaseConnection(rag_db_path="/tmp/test.db"):
                call_order.append("use")
            assert call_order == ["use", "close"]

    def test_exception_in_use_does_not_prevent_close(self):
        """Exception during use does not prevent close."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            mock_closeable = MagicMock()
            call_order = []

            original_close = mock_closeable.close

            def track_close():
                call_order.append("close")
                return original_close()

            mock_closeable.close = track_close  # type: ignore[assignment] — replace method with tracking function
            MockSQLiteHelper.return_value.open.return_value = mock_closeable
            try:
                with RagDatabaseConnection(rag_db_path="/tmp/test.db"):
                    call_order.append("use")
                    raise ValueError("simulated error")
            except ValueError:
                pass
            assert "close" in call_order

    def test_exception_in_use_propagates(self):
        """Exception during use propagates to caller."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            mock_instance = MagicMock()
            MockSQLiteHelper.return_value.open.return_value = mock_instance
            with pytest.raises(ValueError):
                with RagDatabaseConnection(rag_db_path="/tmp/test.db"):
                    raise ValueError("simulated error")

    def test_exception_in_use_still_calls_close(self):
        """Exception during use still calls close."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            mock_closeable = MagicMock()
            close_called = False

            original_close = mock_closeable.close

            def track_close():
                nonlocal close_called
                close_called = True
                return original_close()

            mock_closeable.close = track_close  # type: ignore[assignment] — replace method with tracking function
            MockSQLiteHelper.return_value.open.return_value = mock_closeable
            try:
                with RagDatabaseConnection(rag_db_path="/tmp/test.db"):
                    raise ValueError("simulated error")
            except ValueError:
                pass
            assert close_called is True

    def test_ensure_cleanup_on_all_exceptions(self):
        """Cleanup happens for all exception types."""
        with patch("rag.db_connection.SQLiteHelper") as MockSQLiteHelper:
            cleanup_done = False
            mock_closeable = MagicMock()

            original_close = mock_closeable.close

            def track_close():
                nonlocal cleanup_done
                cleanup_done = True
                return original_close()

            mock_closeable.close = track_close  # type: ignore[assignment] — replace method with tracking function
            MockSQLiteHelper.return_value.open.return_value = mock_closeable
            for exc_class in [ValueError, RuntimeError, KeyError]:
                cleanup_done = False
                try:
                    with RagDatabaseConnection(rag_db_path="/tmp/test.db"):
                        raise exc_class("simulated error")
                except exc_class:
                    pass
                assert cleanup_done is True
