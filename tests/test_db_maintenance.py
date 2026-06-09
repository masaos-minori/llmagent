"""tests/test_db_maintenance.py
Unit tests for db_maintenance: purge_old_sessions, rotate_*_db, checkpoint_wal, vacuum_db.
"""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from db.config import DbConfig
from db.helper import SQLiteHelper
from db.maintenance import (
    RecoveryResult,
    RetentionConfig,
    checkpoint_wal,
    purge_old_sessions,
    recover_corruption,
    rotate_rag_db,
    rotate_session_db,
    vacuum_db,
)

# Minimal session schema for purge tests (no vec0 dependency).
_SESSION_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _make_db_cfg(
    tmp_path, rag_name="rag.sqlite", session_name="session.sqlite", **kwargs
):
    """Return a mock DbConfig pointing to tmp_path files (bypasses path validation)."""
    from unittest.mock import MagicMock

    cfg = MagicMock(spec=DbConfig)
    cfg.rag_db_path = str(tmp_path / rag_name)
    cfg.session_db_path = str(tmp_path / session_name)
    cfg.sqlite_vec_so = "/fake/vec0.so"
    cfg.embed_url = "http://127.0.0.1:8003/embedding"
    return cfg


class _FakeDB:
    """Minimal SQLiteHelper drop-in backed by in-memory SQLite for purge tests."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn: sqlite3.Connection | None = conn

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        assert self.conn is not None
        return self.conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        assert self.conn is not None
        return self.conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        assert self.conn is not None
        self.conn.commit()


def _make_session_db(sessions: list[tuple[str, str]]) -> _FakeDB:
    """Create an in-memory DB with given (title, created_at) session rows."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SESSION_SCHEMA)
    for title, created_at in sessions:
        conn.execute(
            "INSERT INTO sessions (title, created_at) VALUES (?, ?)",
            (title, created_at),
        )
    conn.commit()
    return _FakeDB(conn)


# ── RetentionConfig ────────────────────────────────────────────────────────────


class TestRetentionConfig:
    def test_defaults(self) -> None:
        cfg = RetentionConfig()
        assert cfg.max_sessions == 100
        assert cfg.max_age_days == 90

    def test_custom_values(self) -> None:
        cfg = RetentionConfig(max_sessions=5, max_age_days=7)
        assert cfg.max_sessions == 5
        assert cfg.max_age_days == 7


# ── purge_old_sessions ─────────────────────────────────────────────────────────


class TestPurgeOldSessions:
    def test_no_deletions_when_within_limits(self) -> None:
        db = _make_session_db(
            [("s1", "2099-01-01 00:00:00"), ("s2", "2099-01-02 00:00:00")]
        )
        cfg = RetentionConfig(max_sessions=10, max_age_days=0)
        result = purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        assert result == {"age_deleted": 0, "count_deleted": 0}

    def test_age_based_deletion(self) -> None:
        # One very old session, one recent
        db = _make_session_db(
            [
                ("old", "2000-01-01 00:00:00"),
                ("new", "2099-01-01 00:00:00"),
            ]
        )
        cfg = RetentionConfig(max_sessions=100, max_age_days=1)
        result = purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        assert result["age_deleted"] == 1
        assert result["count_deleted"] == 0

    def test_count_based_deletion(self) -> None:
        # 5 sessions, keep only 2 most recent
        db = _make_session_db(
            [
                ("s1", "2020-01-01 00:00:00"),
                ("s2", "2020-01-02 00:00:00"),
                ("s3", "2020-01-03 00:00:00"),
                ("s4", "2020-01-04 00:00:00"),
                ("s5", "2020-01-05 00:00:00"),
            ]
        )
        cfg = RetentionConfig(max_sessions=2, max_age_days=0)
        result = purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        assert result["count_deleted"] == 3
        # Verify only 2 rows remain
        assert db.conn is not None
        rows = db.conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        assert rows == 2

    def test_age_zero_skips_age_check(self) -> None:
        db = _make_session_db([("old", "2000-01-01 00:00:00")])
        cfg = RetentionConfig(max_sessions=100, max_age_days=0)
        result = purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        assert result["age_deleted"] == 0

    def test_cascade_deletes_messages(self) -> None:
        db = _make_session_db(
            [
                ("s1", "2000-01-01 00:00:00"),
                ("s2", "2099-01-01 00:00:00"),
            ]
        )
        assert db.conn is not None
        # Insert a message for the old session
        sid = db.conn.execute(
            "SELECT session_id FROM sessions WHERE title='s1'"
        ).fetchone()[0]
        db.conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, 'user', 'hi')",
            (sid,),
        )
        db.conn.commit()
        cfg = RetentionConfig(max_sessions=100, max_age_days=1)
        purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        count = db.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        assert count == 0


# ── rotate_rag_db / rotate_session_db ─────────────────────────────────────────


class TestRotateDb:
    def test_rotate_rag_db_creates_archive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db_file = tmp_path / "rag.sqlite"
        db_file.write_bytes(b"fake-db-content")
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.maintenance.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        dest = rotate_rag_db(archive_dir=archive_dir)

        assert dest.exists()
        assert dest.name.startswith("rag_")
        assert dest.suffix == ".sqlite"
        assert dest.read_bytes() == b"fake-db-content"

    def test_rotate_session_db_creates_archive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db_file = tmp_path / "session.sqlite"
        db_file.write_bytes(b"session-content")
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.maintenance.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        dest = rotate_session_db(archive_dir=archive_dir)

        assert dest.exists()
        assert dest.name.startswith("session_")

    def test_rotate_rag_db_copies_wal_side_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db_file = tmp_path / "rag.sqlite"
        db_file.write_bytes(b"db")
        wal_file = tmp_path / "rag.sqlite-wal"
        wal_file.write_bytes(b"wal-data")
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.maintenance.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        dest = rotate_rag_db(archive_dir=archive_dir)
        wal_dest = archive_dir / (dest.name + "-wal")
        assert wal_dest.exists()

    def test_rotate_rag_db_missing_file_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "db.maintenance.build_db_config",
            lambda: _make_db_cfg(tmp_path, rag_name="missing.sqlite"),
        )
        with pytest.raises(FileNotFoundError):
            rotate_rag_db(archive_dir=tmp_path / "archive")


# ── checkpoint_wal / vacuum_db ─────────────────────────────────────────────────


class TestCheckpointAndVacuum:
    def _make_mock_db(self, checkpoint_return: dict | None = None) -> MagicMock:
        mock = MagicMock(spec=SQLiteHelper)
        if checkpoint_return is not None:
            mock.checkpoint.return_value = checkpoint_return
        return mock

    def test_checkpoint_wal_uses_mode(self) -> None:
        mock_db = self._make_mock_db(
            {"busy": 0, "pages_in_wal": 0, "pages_checkpointed": 0}
        )
        result = checkpoint_wal(mock_db, mode="FULL")
        mock_db.checkpoint.assert_called_once_with("FULL")
        assert result["busy"] == 0

    def test_checkpoint_wal_default_mode_from_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import db.maintenance as db_maintenance

        monkeypatch.setattr(
            db_maintenance.ConfigLoader,
            "load",
            lambda self, _: {"sqlite_wal_checkpoint_mode": "PASSIVE"},
        )
        mock_db = self._make_mock_db(
            {"busy": 0, "pages_in_wal": 0, "pages_checkpointed": 0}
        )
        checkpoint_wal(mock_db)
        mock_db.checkpoint.assert_called_once_with("PASSIVE")

    def test_vacuum_db_delegates(self) -> None:
        mock_db = self._make_mock_db()
        vacuum_db(mock_db)
        mock_db.vacuum.assert_called_once()


# ── prune_old_memories ────────────────────────────────────────────────────────


class TestPruneOldMemories:
    def _make_db(
        self,
        fetchall_return: list,
        rowcount: int = 0,
    ) -> MagicMock:
        mock = MagicMock(spec=SQLiteHelper)
        mock.fetchall.return_value = fetchall_return
        cur_mock = MagicMock()
        cur_mock.rowcount = rowcount
        mock.execute.return_value = cur_mock
        return mock

    def test_no_old_memories_returns_zero(self) -> None:
        from db.maintenance import prune_old_memories

        mock_db = self._make_db(fetchall_return=[])
        result = prune_old_memories(mock_db, older_than_days=30)
        assert result == 0
        mock_db.execute.assert_not_called()

    def test_deletes_old_memories_and_fts(self) -> None:
        from db.maintenance import prune_old_memories

        mid = "abc-uuid"
        mock_db = self._make_db(
            fetchall_return=[(mid,)],
            rowcount=1,
        )
        result = prune_old_memories(mock_db, older_than_days=30)

        assert result == 1
        # memories テーブルと memories_fts テーブルから削除されること
        calls = [str(c) for c in mock_db.execute.call_args_list]
        assert any("DELETE FROM memories WHERE" in c for c in calls)
        assert any("DELETE FROM memories_fts" in c for c in calls)
        mock_db.commit.assert_called_once()

    def test_memories_vec_exception_is_suppressed(self) -> None:
        from db.maintenance import prune_old_memories

        mid = "abc-uuid"
        mock_db = self._make_db(
            fetchall_return=[(mid,)],
            rowcount=1,
        )
        # memories_vec の削除で例外が発生しても suppress されること
        mock_db.execute.side_effect = [
            MagicMock(rowcount=1),  # DELETE FROM memories
            MagicMock(),  # DELETE FROM memories_fts
            Exception("no vec table"),  # DELETE FROM memories_vec
        ]
        result = prune_old_memories(mock_db, older_than_days=30)
        assert result == 1  # 例外があっても rowcount は使われる


# ── recover_corruption ─────────────────────────────────────────────────────────


class TestRecoverCorruption:
    @pytest.fixture(autouse=True)
    def _patch_build_db_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Patch build_db_config so recover_corruption does not need real config."""
        monkeypatch.setattr(
            "db.maintenance.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

    def test_db_conn_none_raises_runtime_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """db.conn が None のとき RuntimeError が発生し RecoveryResult(success=False) が返ること。"""
        from unittest.mock import MagicMock, patch

        mock_db = MagicMock()
        mock_db.conn = None

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("db.maintenance.SQLiteHelper") as mock_helper_cls:
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption()

        assert isinstance(result, RecoveryResult)
        assert result.success is False

    def test_dry_run_returns_recovery_result(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """dry_run=True のとき変更なしで RecoveryResult が返ること。"""
        from unittest.mock import MagicMock, patch

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = ("ok",)
        mock_db = MagicMock()
        mock_db.conn = mock_conn

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("db.maintenance.SQLiteHelper") as mock_helper_cls:
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption(dry_run=True)

        assert isinstance(result, RecoveryResult)
        assert result.dry_run is True
        assert result.success is True
        assert result.action == "vacuum"

    def test_dry_run_integrity_failure(self) -> None:
        """dry_run=True with integrity failure returns error."""
        from unittest.mock import MagicMock, patch

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = ("some error",)
        mock_db = MagicMock()
        mock_db.conn = mock_conn

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("db.maintenance.SQLiteHelper") as mock_helper_cls:
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption(dry_run=True)

        assert result.success is False
        assert result.dry_run is True
        assert "integrity check failed" in result.detail

    def test_vacuum_path(self) -> None:
        """Integrity ok, not dry_run -> vacuum."""
        from unittest.mock import MagicMock, patch

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = ("ok",)
        mock_db = MagicMock()
        mock_db.conn = mock_conn

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("db.maintenance.SQLiteHelper") as mock_helper_cls:
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption()

        assert result.success is True
        assert result.action == "vacuum"
        mock_db.vacuum.assert_called_once()

    def test_no_backup_path_returns_no_backup(self) -> None:
        """Integrity fail, no backup_path -> no_backup."""
        from unittest.mock import MagicMock, patch

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = ("corrupt",)
        mock_db = MagicMock()
        mock_db.conn = mock_conn

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("db.maintenance.SQLiteHelper") as mock_helper_cls:
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption(backup_path=None)
        assert result.success is False
        assert result.action == "no_backup"

    def test_backup_not_found_returns_no_backup(self) -> None:
        """Backup file missing -> no_backup."""
        from unittest.mock import MagicMock, patch

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = ("corrupt",)
        mock_db = MagicMock()
        mock_db.conn = mock_conn

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("db.maintenance.SQLiteHelper") as mock_helper_cls:
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption(backup_path="/nonexistent/backup.sqlite")
        assert result.success is False
        assert result.action == "no_backup"
        assert "backup not found" in result.detail

    def test_restore_from_backup(self, tmp_path: Path) -> None:
        """Integrity fail, valid backup -> restored."""
        from unittest.mock import MagicMock, patch

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = ("corrupt",)
        mock_db = MagicMock()
        mock_db.conn = mock_conn

        db_file = tmp_path / "rag.sqlite"
        db_file.write_text("corrupt db")
        backup_file = tmp_path / "backup.sqlite"
        backup_file.write_text("backup content")

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("db.maintenance.SQLiteHelper") as mock_helper_cls:
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption(backup_path=str(backup_file))

        assert result.success is True
        assert result.action == "restored"
        assert db_file.read_text() == "backup content"

    def test_os_error_during_recovery(self, tmp_path: Path) -> None:
        """OSError during file copy -> error."""
        from unittest.mock import MagicMock, patch

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = ("corrupt",)
        mock_db = MagicMock()
        mock_db.conn = mock_conn

        db_file = tmp_path / "rag.sqlite"
        db_file.write_text("corrupt db")
        backup_file = tmp_path / "backup.sqlite"
        backup_file.write_text("backup")

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with (
            patch("db.maintenance.SQLiteHelper") as mock_helper_cls,
            patch("db.maintenance.shutil.copy2", side_effect=OSError("disk full")),
        ):
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption(backup_path=str(backup_file))
        assert result.success is False
        assert result.action == "error"

    def test_open_db_exception_returns_error(self) -> None:
        """Exception during DB open -> error."""
        from unittest.mock import MagicMock, patch

        mock_helper = MagicMock()
        mock_helper.open.side_effect = Exception("cannot open")

        with patch("db.maintenance.SQLiteHelper", return_value=mock_helper):
            result = recover_corruption()
        assert result.success is False
        assert result.action == "error"
