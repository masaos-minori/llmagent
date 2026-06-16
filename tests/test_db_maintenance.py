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
        assert result.age_deleted == 0
        assert result.count_deleted == 0

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
        assert result.age_deleted == 1
        assert result.count_deleted == 0

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
        assert result.count_deleted == 3
        # Verify only 2 rows remain
        assert db.conn is not None
        rows = db.conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        assert rows == 2

    def test_age_zero_skips_age_check(self) -> None:
        db = _make_session_db([("old", "2000-01-01 00:00:00")])
        cfg = RetentionConfig(max_sessions=100, max_age_days=0)
        result = purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        assert result.age_deleted == 0

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
    def _make_real_sqlite(self, path: Path) -> None:
        """Create a minimal valid SQLite database file."""
        import sqlite3

        conn = sqlite3.connect(str(path))
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

    def test_rotate_rag_db_creates_archive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db_file = tmp_path / "rag.sqlite"
        self._make_real_sqlite(db_file)
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.maintenance.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        dest = rotate_rag_db(archive_dir=archive_dir)

        assert dest.exists()
        assert dest.name.startswith("rag_")
        assert dest.suffix == ".sqlite"
        # Verify the backup is a valid SQLite DB
        import sqlite3 as _s

        conn = _s.connect(str(dest))
        assert conn.execute("SELECT name FROM sqlite_master").fetchall() is not None
        conn.close()

    def test_rotate_session_db_creates_archive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db_file = tmp_path / "session.sqlite"
        self._make_real_sqlite(db_file)
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.maintenance.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        dest = rotate_session_db(archive_dir=archive_dir)

        assert dest.exists()
        assert dest.name.startswith("session_")

    def test_rotate_rag_db_backup_api_is_wal_safe(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The backup API integrates WAL data automatically; no separate WAL file copy needed.
        db_file = tmp_path / "rag.sqlite"
        self._make_real_sqlite(db_file)
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.maintenance.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        dest = rotate_rag_db(archive_dir=archive_dir)
        # Backup destination must be a valid SQLite database (no "file is not a database").
        import sqlite3 as _s

        conn = _s.connect(str(dest))
        conn.execute("PRAGMA integrity_check")
        conn.close()

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
    def _make_mock_db(self, checkpoint_return: object = None) -> MagicMock:
        from db.models import WalCheckpointCounts as _WCC

        mock = MagicMock(spec=SQLiteHelper)
        if checkpoint_return is not None:
            mock.checkpoint.return_value = checkpoint_return
        else:
            mock.checkpoint.return_value = _WCC(
                busy=0, log_size=0, pages_checkpointed=0
            )
        return mock

    def test_checkpoint_wal_uses_mode(self) -> None:
        from db.models import WalCheckpointCounts as _WCC

        mock_db = self._make_mock_db(_WCC(busy=0, log_size=0, pages_checkpointed=0))
        result = checkpoint_wal(mock_db, mode="FULL")
        mock_db.checkpoint.assert_called_once_with("FULL")
        assert result.busy == 0

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

    def test_memories_vec_exception_raises(self) -> None:
        from db.maintenance import prune_old_memories

        mid = "abc-uuid"
        mock_db = self._make_db(
            fetchall_return=[(mid,)],
            rowcount=1,
        )
        # memories_vec deletion failure propagates (fail-fast)
        mock_db.execute.side_effect = [
            MagicMock(rowcount=1),  # DELETE FROM memories
            MagicMock(),  # DELETE FROM memories_fts
            Exception("no vec table"),  # DELETE FROM memories_vec — must raise
        ]
        with pytest.raises(Exception, match="no vec table"):
            prune_old_memories(mock_db, older_than_days=30)


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
        """open() が RuntimeError を上げるとき RecoveryResult(success=False) が返ること。"""
        from unittest.mock import patch

        with patch("db.maintenance.SQLiteHelper") as mock_helper_cls:
            mock_helper_cls.return_value.open.side_effect = RuntimeError(
                "conn not open"
            )
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
        """OperationalError during DB open -> error."""
        import sqlite3 as _sqlite3
        from unittest.mock import MagicMock, patch

        mock_helper = MagicMock()
        mock_helper.open.side_effect = _sqlite3.OperationalError("cannot open")

        with patch("db.maintenance.SQLiteHelper", return_value=mock_helper):
            result = recover_corruption()
        assert result.success is False
        assert result.action == "error"


# ── DbMaintenanceService document methods ──────────────────────────────────────


class TestDbMaintenanceServiceDocuments:
    """Tests for list_documents and delete_document methods."""

    def _make_rag_db(self, tmp_path: Path) -> sqlite3.Connection:
        """Create a minimal rag.sqlite with documents, chunks, chunks_vec tables."""
        conn = sqlite3.connect(str(tmp_path / "rag.sqlite"))
        conn.executescript("""
            CREATE TABLE documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                lang TEXT,
                fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
                chunking_strategy TEXT NOT NULL DEFAULT 'text'
            );
            CREATE TABLE chunks (
                chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL REFERENCES documents(doc_id),
                content TEXT NOT NULL
            );
            CREATE TABLE chunks_vec (
                chunk_id INTEGER PRIMARY KEY,
                embedding BLOB NOT NULL,
                FOREIGN KEY(chunk_id) REFERENCES chunks(chunk_id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        return conn

    def test_list_documents_returns_correct_shape(self, tmp_path: Path) -> None:
        """list_documents() returns dicts with all expected keys including chunking_strategy."""
        from unittest.mock import patch

        from agent.services.db_maintenance_service import DbMaintenanceService

        conn = self._make_rag_db(tmp_path)
        conn.execute(
            "INSERT INTO documents (url, title, lang, fetched_at, chunking_strategy) "
            "VALUES ('https://example.com/1', 'Doc 1', 'ja', '2026-01-01 00:00:00', 'markdown')"
        )
        conn.execute("INSERT INTO chunks (doc_id, content) VALUES (1, 'content 1')")
        conn.execute(
            "INSERT INTO chunks_vec (chunk_id, embedding) VALUES (1, X'00112233')"
        )
        conn.commit()

        with patch("agent.services.db_maintenance_service.SQLiteHelper") as mock_cls:
            mock_helper = MagicMock()
            mock_cls.return_value.open.return_value.__enter__ = MagicMock(
                return_value=mock_helper
            )
            mock_cls.return_value.open.return_value.__exit__ = MagicMock(
                return_value=False
            )
            mock_helper.fetchall.return_value = [
                {
                    "url": "https://example.com/1",
                    "title": "Doc 1",
                    "lang": "ja",
                    "fetched_at": "2026-01-01 00:00:00",
                    "chunking_strategy": "markdown",
                    "n": 1,
                }
            ]

            result = DbMaintenanceService().list_documents()

        assert len(result) == 1
        assert result[0]["url"] == "https://example.com/1"
        assert result[0]["title"] == "Doc 1"
        assert result[0]["lang"] == "ja"
        assert result[0]["chunking_strategy"] == "markdown"
        assert result[0]["chunk_count"] == 1

    def test_list_documents_empty_returns_empty_list(self, tmp_path: Path) -> None:
        """list_documents() on empty DB returns empty list."""
        from unittest.mock import MagicMock, patch

        from agent.services.db_maintenance_service import DbMaintenanceService

        with patch("agent.services.db_maintenance_service.SQLiteHelper") as mock_cls:
            mock_helper = MagicMock()
            mock_cls.return_value.open.return_value.__enter__ = MagicMock(
                return_value=mock_helper
            )
            mock_cls.return_value.open.return_value.__exit__ = MagicMock(
                return_value=False
            )
            mock_helper.fetchall.return_value = []

            result = DbMaintenanceService().list_documents()

        assert result == []

    def test_delete_document_returns_true_when_exists(self, tmp_path: Path) -> None:
        """delete_document() returns True when URL exists and deletes all related rows."""
        from unittest.mock import MagicMock, patch

        from agent.services.db_maintenance_service import DbMaintenanceService

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = (42,)  # doc_id
        mock_db = MagicMock()
        mock_db.conn = mock_conn

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("agent.services.db_maintenance_service.SQLiteHelper") as mock_cls:
            mock_cls.return_value.open.return_value = FakeContext()
            result = DbMaintenanceService().delete_document("https://example.com/1")

        assert result is True
        # Verify all DELETE statements were executed
        delete_calls = [str(c) for c in mock_db.execute.call_args_list]
        assert any("DELETE FROM chunks_vec" in c for c in delete_calls)
        assert any("DELETE FROM documents WHERE doc_id" in c for c in delete_calls)
        mock_db.commit.assert_called_once()

    def test_delete_document_returns_false_when_not_found(self, tmp_path: Path) -> None:
        """delete_document() returns False when URL does not exist."""
        from unittest.mock import MagicMock, patch

        from agent.services.db_maintenance_service import DbMaintenanceService

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # no doc found
        mock_db = MagicMock()
        mock_db.execute.return_value = mock_cursor

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("agent.services.db_maintenance_service.SQLiteHelper") as mock_cls:
            mock_cls.return_value.open.return_value = FakeContext()
            result = DbMaintenanceService().delete_document("https://nonexistent.com/")

        assert result is False
        # No DELETE statements should be executed when doc not found
        delete_calls = [str(c) for c in mock_db.execute.call_args_list]
        assert not any("DELETE" in c for c in delete_calls)

    def test_delete_document_cascades_from_chunks_vec(self, tmp_path: Path) -> None:
        """delete_document() executes chunks_vec DELETE before documents DELETE."""
        from unittest.mock import MagicMock, patch

        from agent.services.db_maintenance_service import DbMaintenanceService

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = (99,)  # doc_id
        mock_db = MagicMock()
        mock_db.conn = mock_conn

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("agent.services.db_maintenance_service.SQLiteHelper") as mock_cls:
            mock_cls.return_value.open.return_value = FakeContext()
            DbMaintenanceService().delete_document("https://example.com/1")

        # Verify chunks_vec deletion happens before documents deletion
        delete_calls = [str(c) for c in mock_db.execute.call_args_list]
        vec_idx = next(i for i, c in enumerate(delete_calls) if "chunks_vec" in c)
        doc_idx = next(
            i for i, c in enumerate(delete_calls) if "documents WHERE doc_id" in c
        )
        assert vec_idx < doc_idx, "chunks_vec DELETE must precede documents DELETE"

    def test_list_documents_filters_by_lang(self, tmp_path: Path) -> None:
        """list_documents(lang='ja') returns only Japanese documents."""
        from unittest.mock import MagicMock, patch

        from agent.services.db_maintenance_service import DbMaintenanceService

        with patch("agent.services.db_maintenance_service.SQLiteHelper") as mock_cls:
            mock_helper = MagicMock()
            mock_cls.return_value.open.return_value.__enter__ = MagicMock(
                return_value=mock_helper
            )
            mock_cls.return_value.open.return_value.__exit__ = MagicMock(
                return_value=False
            )
            mock_helper.fetchall.return_value = [
                {
                    "url": "https://example.com/ja",
                    "title": "Japanese Doc",
                    "lang": "ja",
                    "fetched_at": "2026-01-01 00:00:00",
                    "chunking_strategy": "text",
                    "n": 3,
                }
            ]

            result = DbMaintenanceService().list_documents(lang="ja")

        assert len(result) == 1
        assert result[0]["lang"] == "ja"
        # Verify WHERE clause was added
        call_args = mock_cls.return_value.open.return_value.__enter__.return_value.fetchall.call_args
        sql_used = call_args[0][0]
        assert "WHERE d.lang = ?" in sql_used
