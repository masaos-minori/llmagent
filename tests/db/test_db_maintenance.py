"""tests/test_db_maintenance.py
Unit tests for db_maintenance: purge_old_sessions, rotate_*_db, checkpoint_wal, vacuum_db.
"""

import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from db.config import DbConfig
from db.helper import SQLiteHelper
from db.maintenance import (
    CorruptArchiveRetentionConfig,
    MaintenanceMode,
    MaintenanceResult,
    RetentionConfig,
    _handle_maintenance_error,
    checkpoint_wal,
    prune_old_memories,
    purge_corrupt_archives,
    purge_old_sessions,
    vacuum_db,
)
from db.models import RecoveryResult
from db.recovery import DbCondition, recover_corruption
from db.rotation import (
    _archive_db_file,
    rotate_all_dbs,
    rotate_session_db,
    rotate_workflow_db,
)
from db.store_impl import SQLiteMemoryDeleteStore

_TEST_EMBED_URL = "http://127.0.0.1:8081/embedding"

# Minimal session schema for purge tests (no vec0 dependency).
_SESSION_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    title TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
"""


def _make_db_cfg(
    tmp_path,
    rag_name="rag.sqlite",
    session_name="session.sqlite",
    workflow_name="workflow.sqlite",
    **kwargs,
):
    """Return a mock DbConfig pointing to tmp_path files (bypasses path validation)."""
    from unittest.mock import MagicMock

    cfg = MagicMock(spec=DbConfig)
    cfg.rag_db_path = str(tmp_path / rag_name)
    cfg.session_db_path = str(tmp_path / session_name)
    cfg.workflow_db_path = str(tmp_path / workflow_name)
    cfg.sqlite_vec_so = "/opt/llm/sqlite-vec/vec0.so"
    cfg.sqlite_timeout = 30
    cfg.sqlite_busy_timeout_ms = 30000
    cfg.embed_url = _TEST_EMBED_URL
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

    @contextmanager
    def begin_immediate(self):
        """Mirror helper._begin_transaction (db/helper.py): BEGIN IMMEDIATE...COMMIT,
        rollback on any normal exception, re-raise."""
        assert self.conn is not None
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.conn.execute("COMMIT")
        except Exception:
            try:
                self.conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise


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
    def _make_real_sqlite(self, path: Path) -> None:
        """Create a minimal valid SQLite database file.

        Includes the required tables for every domain-identity check (rag needs
        ``documents``, session needs ``sessions``) so the file passes archive
        verification when archived under any target (dbmig001 row 12).
        """
        import sqlite3

        conn = sqlite3.connect(str(path))
        conn.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

    def test_no_deletions_when_within_limits(self) -> None:
        db = _make_session_db(
            [("s1", "2099-01-01T00:00:00Z"), ("s2", "2099-01-02T00:00:00Z")]
        )
        cfg = RetentionConfig(max_sessions=10, max_age_days=0)
        result = purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        assert result.success is True
        assert result.data is not None
        assert result.data["age_deleted"] == 0
        assert result.data["count_deleted"] == 0

    def test_age_based_deletion(self) -> None:
        # One very old session, one recent
        db = _make_session_db(
            [
                ("old", "2000-01-01T00:00:00Z"),
                ("new", "2099-01-01T00:00:00Z"),
            ]
        )
        cfg = RetentionConfig(max_sessions=100, max_age_days=1)
        result = purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        assert result.success is True
        assert result.data is not None
        assert result.data["age_deleted"] == 1
        assert result.data["count_deleted"] == 0

    def test_count_based_deletion(self) -> None:
        # 5 sessions, keep only 2 most recent
        db = _make_session_db(
            [
                ("s1", "2020-01-01T00:00:00Z"),
                ("s2", "2020-01-02T00:00:00Z"),
                ("s3", "2020-01-03T00:00:00Z"),
                ("s4", "2020-01-04T00:00:00Z"),
                ("s5", "2020-01-05T00:00:00Z"),
            ]
        )
        cfg = RetentionConfig(max_sessions=2, max_age_days=0)
        result = purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        assert result.success is True
        assert result.data is not None
        assert result.data["count_deleted"] == 3
        # Verify only 2 rows remain
        assert db.conn is not None
        rows = db.conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        assert rows == 2

    def test_boundary_below_max_sessions(self) -> None:
        db = _make_session_db([(f"s{i}", "2099-01-01T00:00:00Z") for i in range(9)])
        cfg = RetentionConfig(max_sessions=10, max_age_days=0)
        result = purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        assert result.success is True
        assert result.data is not None
        assert result.data["count_deleted"] == 0

    def test_boundary_at_max_sessions(self) -> None:
        db = _make_session_db([(f"s{i}", "2099-01-01T00:00:00Z") for i in range(10)])
        cfg = RetentionConfig(max_sessions=10, max_age_days=0)
        result = purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        assert result.success is True
        assert result.data is not None
        assert result.data["count_deleted"] == 0

    def test_boundary_above_max_sessions(self) -> None:
        db = _make_session_db([(f"s{i}", "2099-01-01T00:00:00Z") for i in range(11)])
        cfg = RetentionConfig(max_sessions=10, max_age_days=0)
        result = purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        assert result.success is True
        assert result.data is not None
        assert result.data["count_deleted"] == 1

    def test_age_zero_skips_age_check(self) -> None:
        db = _make_session_db([("old", "2000-01-01T00:00:00Z")])
        cfg = RetentionConfig(max_sessions=100, max_age_days=0)
        result = purge_old_sessions(db, cfg)  # type: ignore[arg-type]
        assert result.success is True
        assert result.data is not None
        assert result.data["age_deleted"] == 0

    def test_cascade_deletes_messages(self) -> None:
        db = _make_session_db(
            [
                ("s1", "2000-01-01T00:00:00Z"),
                ("s2", "2099-01-01T00:00:00Z"),
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

    def test_age_rule_keeps_active_session(self) -> None:
        db = _make_session_db(
            [
                ("active", "2000-01-01T00:00:00Z"),  # session_id 1
                ("old", "2000-01-02T00:00:00Z"),  # session_id 2
                ("new", "2099-01-01T00:00:00Z"),  # session_id 3
            ]
        )
        assert db.conn is not None
        db.conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (1, 'u', 'live')"
        )
        db.conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (2, 'u', 'gone')"
        )
        db.conn.commit()
        cfg = RetentionConfig(max_sessions=100, max_age_days=1)
        result = purge_old_sessions(db, cfg, keep_session_id=1)  # type: ignore[arg-type]
        assert result.success is True
        assert result.data is not None
        assert result.data["age_deleted"] == 1
        assert result.data["kept_active_session"] == 1
        survived = {r[0] for r in db.conn.execute("SELECT session_id FROM sessions")}
        assert survived == {1, 3}
        msgs = {r[0] for r in db.conn.execute("SELECT session_id FROM messages")}
        assert msgs == {1}  # session 2's messages cascade-deleted

    def test_count_rule_keeps_active_session(self) -> None:
        db = _make_session_db(
            [
                ("s1", "2099-01-01T00:00:00Z"),  # oldest
                ("s2", "2099-01-02T00:00:00Z"),  # active: 3rd by created_at
                ("s3", "2099-01-03T00:00:00Z"),
                ("s4", "2099-01-04T00:00:00Z"),
            ]
        )
        assert db.conn is not None
        cfg = RetentionConfig(max_sessions=2, max_age_days=0)
        result = purge_old_sessions(db, cfg, keep_session_id=2)  # type: ignore[arg-type]
        assert result.success is True
        assert result.data is not None
        assert result.data["count_deleted"] == 1  # only s1 removed
        assert result.data["kept_active_session"] == 2
        survived = {r[0] for r in db.conn.execute("SELECT session_id FROM sessions")}
        assert survived == {2, 3, 4}  # kept count exceeds max_sessions by one

    def test_absent_guard_deletes_expired_active_equivalent(self) -> None:
        db = _make_session_db(
            [
                ("active", "2000-01-01T00:00:00Z"),
                ("old", "2000-01-02T00:00:00Z"),
                ("new", "2099-01-01T00:00:00Z"),
            ]
        )
        cfg = RetentionConfig(max_sessions=100, max_age_days=1)
        result = purge_old_sessions(db, cfg)  # no guard: today's behavior
        assert result.success is True
        assert result.data is not None
        assert result.data["age_deleted"] == 2
        assert result.data["kept_active_session"] is None

    def test_guard_not_present_in_sessions_is_noop(self) -> None:
        db = _make_session_db(
            [
                ("active", "2000-01-01T00:00:00Z"),
                ("old", "2000-01-02T00:00:00Z"),
                ("new", "2099-01-01T00:00:00Z"),
            ]
        )
        cfg = RetentionConfig(max_sessions=100, max_age_days=1)
        result = purge_old_sessions(db, cfg, keep_session_id=999)  # type: ignore[arg-type]
        assert result.success is True
        assert result.data is not None
        assert result.data["age_deleted"] == 2  # identical counts to the unguarded run
        assert result.data["kept_active_session"] is None

    def test_rotate_session_db_creates_archive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db_file = tmp_path / "session.sqlite"
        self._make_real_sqlite(db_file)
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.recovery.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        dest = rotate_session_db(archive_dir=archive_dir)

        assert dest.exists()
        assert dest.name.startswith("session_")


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
            lambda self, key: {"sqlite_wal_checkpoint_mode": "PASSIVE"},
        )
        mock_db = self._make_mock_db(
            {"busy": 0, "pages_in_wal": 0, "pages_checkpointed": 0}
        )
        checkpoint_wal(mock_db)
        mock_db.checkpoint.assert_called_once_with("PASSIVE")

    def test_vacuum_db_delegates(self) -> None:
        mock_db = self._make_mock_db()
        result = vacuum_db(mock_db)
        mock_db.vacuum.assert_called_once()
        assert result.success is True
        assert result.action == "vacuum"


# ── prune_old_memories ────────────────────────────────────────────────────────


class TestPruneOldMemories:
    def _make_db(
        self,
        fetchall_return: list,
    ) -> MagicMock:
        mock = MagicMock(spec=SQLiteHelper)
        mock.fetchall.return_value = fetchall_return
        cur_mock = MagicMock()
        cur_mock.fetchall.return_value = fetchall_return  # DELETE ... RETURNING rows
        mock.execute.return_value = cur_mock
        return mock

    def test_no_old_memories_returns_zero(self) -> None:
        mock_db = self._make_db(fetchall_return=[])
        result = prune_old_memories(mock_db, older_than_days=30)
        assert result.success is True
        assert result.data is not None
        assert result.data["deleted"] == 0
        mock_db.execute.assert_not_called()

    def test_deletes_old_memories_and_fts(self) -> None:
        mid = "abc-uuid"
        mock_db = self._make_db(
            fetchall_return=[(mid,)],
        )
        result = prune_old_memories(mock_db, older_than_days=30)

        assert result.success is True
        assert result.data is not None
        assert result.data["deleted"] == 1
        assert result.data["pruned_ids"] == [mid]
        # memories テーブルと memories_fts テーブルから削除されること
        calls = [str(c) for c in mock_db.execute.call_args_list]
        assert any("DELETE FROM memories WHERE" in c for c in calls)
        assert any("DELETE FROM memories_fts" in c for c in calls)
        mock_db.begin_immediate.assert_called_once()

    def test_memories_vec_exception_raises(self) -> None:
        mid = "abc-uuid"
        mock_db = self._make_db(
            fetchall_return=[(mid,)],
        )
        # memories_vec deletion failure propagates in STRICT mode (default)
        mock_db.execute.side_effect = [
            MagicMock(fetchall=lambda: [(mid,)]),  # DELETE FROM memories ... RETURNING
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
        """Patch build_db_config so recover_corruption does not need real config.

        dbreview004 churn: the existence-first probe gate runs before any
        helper open, so the rag target file is created here. These tests mock
        the helper wholesale; the placeholder only satisfies the gate — the
        mocked helper still decides the probe result either way. Without it a
        missing file would short-circuit every case into missing_database.
        """
        monkeypatch.setattr(
            "db.recovery.build_db_config", lambda: _make_db_cfg(tmp_path)
        )
        (tmp_path / "rag.sqlite").write_bytes(b"placeholder for the existence gate")

    def test_db_conn_none_raises_runtime_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """open() が RuntimeError を上げるとき RecoveryResult(success=False) が返ること。"""
        from unittest.mock import patch

        with patch("db.recovery.SQLiteHelper") as mock_helper_cls:
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

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = ("ok",)

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("db.recovery.SQLiteHelper") as mock_helper_cls:
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption(dry_run=True)

        assert isinstance(result, RecoveryResult)
        assert result.dry_run is True
        assert result.success is True
        assert result.action == "vacuum"

    def test_dry_run_integrity_failure(self) -> None:
        """dry_run=True with integrity failure returns error."""
        from unittest.mock import MagicMock, patch

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = ("some error",)

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("db.recovery.SQLiteHelper") as mock_helper_cls:
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption(dry_run=True)

        assert result.success is False
        assert result.dry_run is True
        assert "Integrity failure" in result.detail

    def test_vacuum_path(self) -> None:
        """Integrity ok, not dry_run -> vacuum."""
        from unittest.mock import MagicMock, patch

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = ("ok",)

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("db.recovery.SQLiteHelper") as mock_helper_cls:
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

        with patch("db.recovery.SQLiteHelper") as mock_helper_cls:
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

        with patch("db.recovery.SQLiteHelper") as mock_helper_cls:
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption(backup_path="/nonexistent/backup.sqlite")
        assert result.success is False
        assert result.action == "no_backup"
        assert "backup not found" in result.detail

    def test_restore_from_backup(self, tmp_path: Path) -> None:
        """Integrity fail, valid backup -> restored."""
        from unittest.mock import MagicMock, patch

        mock_cursor = MagicMock()
        # DB check (corrupt), backup check (ok), domain-identity check
        # (required table present), candidate check (pre-activation, ok),
        # post-restore re-verification (ok).
        # _run_logical_verification() is bypassed below since it isn't
        # this test's concern (covered by tests/db/test_db_recovery.py).
        mock_cursor.fetchone.side_effect = [
            ("corrupt",),
            ("ok",),
            ("documents",),
            ("ok",),
            ("ok",),
        ]
        mock_db = MagicMock()
        mock_db.execute.return_value = mock_cursor

        db_file = tmp_path / "rag.sqlite"
        db_file.write_text("corrupt db")
        backup_file = tmp_path / "backup.sqlite"
        backup_file.write_text("backup content")

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with (
            patch("db.recovery.SQLiteHelper") as mock_helper_cls,
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
        ):
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption(backup_path=str(backup_file))

        assert result.success is True
        assert result.action == "restored"
        assert db_file.read_text() == "backup content"

    def test_os_error_during_recovery(self, tmp_path: Path) -> None:
        """OSError during file copy -> error."""
        from unittest.mock import MagicMock, patch

        mock_cursor = MagicMock()
        # DB check (corrupt), backup check (ok), domain-identity check
        # (required table present) — reached before the copy2() call below
        # ever raises.
        mock_cursor.fetchone.side_effect = [("corrupt",), ("ok",), ("documents",)]
        mock_db = MagicMock()
        mock_db.execute.return_value = mock_cursor

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
            patch("db.recovery.SQLiteHelper") as mock_helper_cls,
            patch("db.recovery.shutil.copy2", side_effect=OSError("disk full")),
        ):
            mock_helper_cls.return_value.open.return_value = FakeContext()
            result = recover_corruption(backup_path=str(backup_file))
        assert result.success is False
        assert result.action == "error"

    def test_open_db_exception_returns_error(self) -> None:
        """An unclassifiable OperationalError during DB open -> preserved,
        operator intervention required (not automatically treated as
        CORRUPTION/restorable) — see _classify_error()'s UNKNOWN fallback
        and recover_corruption()'s DbCondition.UNKNOWN branch."""
        import sqlite3 as _sqlite3
        from unittest.mock import MagicMock, patch

        mock_helper = MagicMock()
        mock_helper.open.side_effect = _sqlite3.OperationalError("cannot open")

        with patch("db.recovery.SQLiteHelper", return_value=mock_helper):
            result = recover_corruption()
        assert result.success is False
        assert result.action == "preserved_operator_intervention_required"

    def test_unsupported_target_returns_error(self) -> None:
        """target outside rag/session/workflow -> unsupported_target, no DB access."""
        from unittest.mock import patch

        with patch("db.recovery.SQLiteHelper") as mock_helper_cls:
            result = recover_corruption(target="bogus")

        assert result.success is False
        assert result.action == "unsupported_target"
        mock_helper_cls.assert_not_called()

    def test_restore_verify_failed(self, tmp_path: Path) -> None:
        """Restore succeeds but post-restore integrity check fails -> restore_verify_failed."""
        from unittest.mock import MagicMock, patch

        mock_cursor = MagicMock()
        # DB check (corrupt), backup check (ok), domain-identity check (table present),
        # candidate check (pre-activation, ok), post-restore re-check (corrupt) -> rollback.
        mock_cursor.fetchone.side_effect = [
            ("corrupt",),
            ("ok",),
            ("documents",),
            ("ok",),
            ("corrupt",),
        ]
        mock_db = MagicMock()
        mock_db.execute.return_value = mock_cursor

        db_file = tmp_path / "rag.sqlite"
        db_file.write_text("corrupt db")
        backup_file = tmp_path / "backup.sqlite"
        backup_file.write_text("backup content")

        class FakeContext:
            def __enter__(self) -> MagicMock:
                return mock_db

            def __exit__(self, *args: object) -> None:
                pass

        with patch("db.recovery.SQLiteHelper") as mock_helper_cls:
            mock_helper_cls.return_value.open.return_value = FakeContext()
            # Stubbed: the physical-branch contract is what this test exercises;
            # the unstubbed verification would fail closed on the mock files (seq 03).
            with patch(
                "db.recovery._run_logical_verification", return_value=(True, None)
            ):
                result = recover_corruption(backup_path=str(backup_file))

        assert result.success is False
        assert result.action == "restore_verify_failed"
        assert result.logical_ok is False
        assert result.active_db_state == "preserved_original"

    def test_unknown_condition_preserves_db_and_does_not_restore(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """UNKNOWN classification is preserved, not treated as CORRUPTION."""
        from unittest.mock import patch

        with patch(
            "db.recovery._run_integrity_check",
            return_value=(DbCondition.UNKNOWN, "unrecognized failure"),
        ):
            with patch("db.recovery._restore_from_backup") as mock_restore:
                result = recover_corruption(target="rag")

        mock_restore.assert_not_called()
        assert result.success is False
        assert result.action == "preserved_operator_intervention_required"
        assert "operator intervention required" in result.detail


# ── purge_corrupt_archives ──────────────────────────────────────────────────────


class TestPurgeCorruptArchives:
    @pytest.fixture(autouse=True)
    def _patch_build_db_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Patch build_db_config so purge_corrupt_archives does not need real config."""
        monkeypatch.setattr(
            "db.maintenance.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

    def _make_archive(
        self, tmp_path: Path, stem: str, suffix_ts: str, age_days: float = 0
    ) -> Path:
        path = tmp_path / f"{stem}_corrupt_{suffix_ts}.sqlite"
        path.write_text("archived corrupt db")
        if age_days:
            mtime = time.time() - age_days * 86400
            os.utime(path, (mtime, mtime))
        return path

    def test_no_deletions_when_within_limits(self, tmp_path: Path) -> None:
        self._make_archive(tmp_path, "rag", "1")
        result = purge_corrupt_archives(
            CorruptArchiveRetentionConfig(max_files=10, max_age_days=0)
        )
        assert result.success is True
        assert result.data is not None
        assert result.data["age_deleted"] == 0
        assert result.data["count_deleted"] == 0

    def test_age_based_deletion(self, tmp_path: Path) -> None:
        old = self._make_archive(tmp_path, "rag", "1", age_days=100)
        new = self._make_archive(tmp_path, "rag", "2", age_days=1)
        result = purge_corrupt_archives(
            CorruptArchiveRetentionConfig(max_files=100, max_age_days=30)
        )
        assert result.success is True
        assert result.data is not None
        assert result.data["age_deleted"] == 1
        assert result.data["count_deleted"] == 0
        assert not old.exists()
        assert new.exists()

    def test_age_zero_skips_age_check(self, tmp_path: Path) -> None:
        old = self._make_archive(tmp_path, "rag", "1", age_days=1000)
        result = purge_corrupt_archives(
            CorruptArchiveRetentionConfig(max_files=100, max_age_days=0)
        )
        assert result.data is not None
        assert result.data["age_deleted"] == 0
        assert old.exists()

    def test_count_based_deletion(self, tmp_path: Path) -> None:
        # 3 rag archives, keep only 2 most recent by mtime
        self._make_archive(tmp_path, "rag", "1", age_days=3)
        self._make_archive(tmp_path, "rag", "2", age_days=2)
        self._make_archive(tmp_path, "rag", "3", age_days=1)
        result = purge_corrupt_archives(
            CorruptArchiveRetentionConfig(max_files=2, max_age_days=0)
        )
        assert result.success is True
        assert result.data is not None
        assert result.data["count_deleted"] == 1
        remaining = list(tmp_path.glob("rag_corrupt_*.sqlite"))
        assert len(remaining) == 2

    def test_boundary_at_max_files(self, tmp_path: Path) -> None:
        self._make_archive(tmp_path, "rag", "1", age_days=2)
        self._make_archive(tmp_path, "rag", "2", age_days=1)
        result = purge_corrupt_archives(
            CorruptArchiveRetentionConfig(max_files=2, max_age_days=0)
        )
        assert result.data is not None
        assert result.data["count_deleted"] == 0

    def test_retention_applied_independently_per_database(self, tmp_path: Path) -> None:
        """A count limit hit by rag archives must not delete session archives."""
        self._make_archive(tmp_path, "rag", "1", age_days=3)
        self._make_archive(tmp_path, "rag", "2", age_days=2)
        self._make_archive(tmp_path, "rag", "3", age_days=1)
        session_archive = self._make_archive(tmp_path, "session", "1", age_days=1)
        result = purge_corrupt_archives(
            CorruptArchiveRetentionConfig(max_files=2, max_age_days=0)
        )
        assert result.data is not None
        assert result.data["count_deleted"] == 1
        assert session_archive.exists()

    def test_best_effort_returns_partial_result_on_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._make_archive(tmp_path, "rag", "1", age_days=100)

        def _raise(*args: object, **kwargs: object) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(Path, "unlink", _raise)
        result = purge_corrupt_archives(
            CorruptArchiveRetentionConfig(max_files=100, max_age_days=30),
            mode=MaintenanceMode.BEST_EFFORT,
        )
        assert result.success is False
        assert result.action == "purge_corrupt_archives_failed"
        assert result.detail is not None
        assert "disk full" in result.detail

    def test_strict_raises_on_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._make_archive(tmp_path, "rag", "1", age_days=100)

        def _raise(*args: object, **kwargs: object) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(Path, "unlink", _raise)
        with pytest.raises(OSError, match="disk full"):
            purge_corrupt_archives(
                CorruptArchiveRetentionConfig(max_files=100, max_age_days=30),
                mode=MaintenanceMode.STRICT,
            )


# ── DbCondition.UNKNOWN handling ───────────────────────────────────────────────


class TestRecoverCorruptionUnknown:
    """Tests for DbCondition.UNKNOWN handling in recover_corruption()."""

    @pytest.fixture(autouse=True)
    def _patch_build_db_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Patch build_db_config so recover_corruption does not need real config."""
        monkeypatch.setattr(
            "db.recovery.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

    def test_unknown_does_not_restore_rag_db(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify UNKNOWN classification preserves the target database and does not trigger restore.

        REQ-001: recover_corruption() MUST distinguish DbCondition.UNKNOWN from CORRUPTION
                 and NOT trigger automatic backup-restore for UNKNOWN conditions on rag targets.
        REQ-005: Tests MUST assert that an Unknown classification does not call
                 _restore_from_backup() and leaves the target database unmodified.
        """
        from unittest.mock import patch

        from db.recovery import (
            DbCondition,
            recover_corruption,
        )

        # Create a valid minimal SQLite file at the path _make_db_cfg's
        # default rag_name points to, so the unmodified-content assertion
        # below is actually checking the file recover_corruption() operates on.
        db_path = tmp_path / "rag.sqlite"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO test_table VALUES (1)")
        conn.commit()
        conn.close()

        original_content = db_path.read_bytes()

        # Patch _run_integrity_check directly (mirrors
        # TestRecoverCorruption::test_unknown_condition_preserves_db_and_does_not_restore)
        # rather than _classify_error, which is only reached from
        # _run_integrity_check's except-branch — a genuinely valid SQLite
        # file never raises, so _classify_error would never be invoked.
        with (
            patch(
                "db.recovery._run_integrity_check",
                return_value=(DbCondition.UNKNOWN, "unknown integrity error"),
            ),
            patch("db.recovery._restore_from_backup") as mock_restore,
        ):
            result = recover_corruption(target="rag")

            mock_restore.assert_not_called()
            assert result.action != "restored"
            current_content = db_path.read_bytes()
            assert current_content == original_content
            assert result.success is False


# ── MaintenanceMode ────────────────────────────────────────────────────────────


class TestMaintenanceMode:
    def test_vacuum_strict_mode_raises_on_error(self) -> None:
        mock_db = MagicMock(spec=SQLiteHelper)
        mock_db.vacuum.side_effect = sqlite3.OperationalError("disk full")
        with pytest.raises(sqlite3.OperationalError, match="disk full"):
            vacuum_db(mock_db, mode=MaintenanceMode.STRICT)

    def test_vacuum_best_effort_returns_failure_result(self) -> None:
        mock_db = MagicMock(spec=SQLiteHelper)
        mock_db.vacuum.side_effect = sqlite3.OperationalError("disk full")
        result = vacuum_db(mock_db, mode=MaintenanceMode.BEST_EFFORT)
        assert isinstance(result, MaintenanceResult)
        assert result.success is False
        assert result.action == "vacuum_failed"
        assert result.detail is not None
        assert "disk full" in result.detail
        assert result.mode == MaintenanceMode.BEST_EFFORT

    def test_vacuum_best_effort_returns_success_result(self) -> None:
        mock_db = MagicMock(spec=SQLiteHelper)
        result = vacuum_db(mock_db, mode=MaintenanceMode.BEST_EFFORT)
        assert result.success is True
        assert result.action == "vacuum"
        assert result.mode == MaintenanceMode.BEST_EFFORT

    def test_purge_best_effort_returns_failure_result_on_error(self) -> None:
        mock_db = MagicMock(spec=SQLiteHelper)
        mock_db.execute.side_effect = sqlite3.OperationalError("lock timeout")
        # max_age_days=1 triggers the age-based DELETE (execute), which raises
        result = purge_old_sessions(
            mock_db,  # type: ignore[arg-type]
            RetentionConfig(max_sessions=100, max_age_days=1),
            mode=MaintenanceMode.BEST_EFFORT,
        )
        assert isinstance(result, MaintenanceResult)
        assert result.success is False
        assert result.action == "purge_failed"
        assert result.detail is not None
        assert "lock timeout" in result.detail
        assert result.mode == MaintenanceMode.BEST_EFFORT

    def test_purge_strict_raises_on_error(self) -> None:
        mock_db = MagicMock(spec=SQLiteHelper)
        mock_db.execute.side_effect = sqlite3.OperationalError("lock timeout")
        # max_age_days=1 triggers the age-based DELETE (execute), which raises
        with pytest.raises(sqlite3.OperationalError, match="lock timeout"):
            purge_old_sessions(
                mock_db,  # type: ignore[arg-type]
                RetentionConfig(max_sessions=100, max_age_days=1),
                mode=MaintenanceMode.STRICT,
            )

    def test_prune_best_effort_returns_failure_on_error(self) -> None:
        mock_db = MagicMock(spec=SQLiteHelper)
        mock_db.fetchall.return_value = [("uuid-1",)]
        mock_db.execute.side_effect = sqlite3.OperationalError("no vec table")
        result = prune_old_memories(
            mock_db, older_than_days=30, mode=MaintenanceMode.BEST_EFFORT
        )
        assert isinstance(result, MaintenanceResult)
        assert result.success is False
        assert result.action == "prune_failed"
        assert result.detail is not None
        assert "no vec table" in result.detail
        assert result.mode == MaintenanceMode.BEST_EFFORT

    def test_prune_strict_raises_on_error(self) -> None:
        mock_db = MagicMock(spec=SQLiteHelper)
        mock_db.fetchall.return_value = [("uuid-1",)]
        mock_db.execute.side_effect = sqlite3.OperationalError("no vec table")
        with pytest.raises(Exception, match="no vec table"):
            prune_old_memories(mock_db, older_than_days=30, mode=MaintenanceMode.STRICT)


# ── rotate_workflow_db / rotate_all_dbs ────────────────────────────────────────


class TestRotateWorkflowAndAll:
    def _make_real_sqlite(self, path: Path) -> None:
        """Create a minimal valid SQLite database file.

        Includes the required tables for every domain-identity check (rag needs
        ``documents``, session needs ``sessions``) so the file passes archive
        verification when archived under any target (dbmig001 row 12).
        """
        import sqlite3

        conn = sqlite3.connect(str(path))
        conn.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

    def test_rotate_workflow_db_creates_archive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db_file = tmp_path / "workflow.sqlite"
        self._make_real_sqlite(db_file)
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.recovery.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        dest = rotate_workflow_db(archive_dir=archive_dir)

        assert dest.exists()
        assert dest.name.startswith("workflow_")

    def test_rotate_all_dbs_archives_all_three(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        rag_file = tmp_path / "rag.sqlite"
        ses_file = tmp_path / "session.sqlite"
        wf_file = tmp_path / "workflow.sqlite"
        for f in (rag_file, ses_file, wf_file):
            self._make_real_sqlite(f)
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.rotation.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        rag_dest, ses_dest, wf_dest = rotate_all_dbs(archive_dir=archive_dir)

        assert rag_dest.exists()
        assert rag_dest.name.startswith("rag_")
        assert ses_dest.exists()
        assert ses_dest.name.startswith("session_")
        assert wf_dest.exists()
        assert wf_dest.name.startswith("workflow_")

    def test_rotate_workflow_db_missing_file_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.rotation.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        with pytest.raises(FileNotFoundError, match="workflow.sqlite"):
            rotate_workflow_db(archive_dir=archive_dir)

    def test_rotate_all_dbs_missing_workflow_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        rag_file = tmp_path / "rag.sqlite"
        ses_file = tmp_path / "session.sqlite"
        for f in (rag_file, ses_file):
            self._make_real_sqlite(f)
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.rotation.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        with pytest.raises(FileNotFoundError, match="workflow.sqlite"):
            rotate_all_dbs(archive_dir=archive_dir)


# ── archive verification (dbmig001 row 12) ────────────────────────────────────


class TestArchiveVerification:
    """Every produced archive must pass integrity + domain-identity checks.

    Row 12 threads a ``target`` through ``rotation._archive_db_file`` and verifies
    the copy before returning it as a recovery point. These tests cover the
    success path, a missing-required-table (wrong-domain) source, an injected
    integrity failure, and ``rotate_all_dbs`` aborting mid-sequence.
    """

    def _make_domain_db(self, path: Path, *, with_documents: bool) -> None:
        """Create a valid SQLite file.

        rag identity requires a ``documents`` table; omitting it simulates a
        wrong-domain/corrupt source that fails verification deterministically.
        """
        conn = sqlite3.connect(str(path))
        conn.execute("CREATE TABLE sessions (id INTEGER PRIMARY KEY)")
        if with_documents:
            conn.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

    def test_verified_archive_is_healthy(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from db.recovery import run_integrity_check

        db_file = tmp_path / "rag.sqlite"
        self._make_domain_db(db_file, with_documents=True)
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.recovery.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        dest = _archive_db_file(db_file, archive_dir, target="rag")

        assert dest.exists()
        assert dest.name.startswith("rag_")
        # The returned archive is itself a healthy database.
        condition, detail = run_integrity_check(dest, "rag")
        assert condition == DbCondition.HEALTHY
        assert detail is None

    def test_missing_required_table_aborts_rotation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A rag archive missing its required table raises with the detail."""
        db_file = tmp_path / "rag.sqlite"
        self._make_domain_db(db_file, with_documents=False)
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.recovery.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        with pytest.raises(RuntimeError, match="archive verification failed"):
            _archive_db_file(db_file, archive_dir, target="rag")

    def test_injected_integrity_failure_aborts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An integrity failure aborts the rotation with an integrity detail."""
        import db.rotation as rotation

        def _fake_integrity(db_path: object, target: str = "rag") -> tuple:
            return (DbCondition.CORRUPTION, "injected malformed")

        monkeypatch.setattr(rotation, "run_integrity_check", _fake_integrity)
        db_file = tmp_path / "rag.sqlite"
        self._make_domain_db(db_file, with_documents=True)
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.recovery.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        with pytest.raises(RuntimeError, match="integrity check reported"):
            _archive_db_file(db_file, archive_dir, target="rag")

    def test_rotate_all_dbs_stops_on_middle_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failure on a middle domain aborts the sequence; later domains are
        not archived (the failed archive is left in place for forensics)."""
        import db.rotation as rotation

        real_integrity = rotation.run_integrity_check

        def _fake_integrity(db_path: object, target: str = "rag") -> tuple:
            if target == "session":
                return (DbCondition.CORRUPTION, "injected malformed")
            return real_integrity(db_path, target)

        monkeypatch.setattr(rotation, "run_integrity_check", _fake_integrity)
        for name in ("rag", "session", "workflow"):
            self._make_domain_db(
                tmp_path / f"{name}.sqlite", with_documents=(name == "rag")
            )
        archive_dir = tmp_path / "archive"
        monkeypatch.setattr(
            "db.rotation.build_db_config", lambda: _make_db_cfg(tmp_path)
        )

        with pytest.raises(RuntimeError, match="archive verification failed"):
            rotate_all_dbs(archive_dir=archive_dir)

        archives = {p.name for p in archive_dir.glob("*.sqlite")}
        # rag archived before session failed ...
        assert any(n.startswith("rag_") for n in archives)
        assert any(n.startswith("session_") for n in archives)
        # ... workflow never reached.
        assert not any(n.startswith("workflow_") for n in archives)


# ── Rotation archive invariance (dbreview004, REQ-006) ───────────────────────


def test_verify_archive_leaves_archive_unchanged(tmp_path: Path) -> None:
    """REQ-006/AC-1: rotation's archive verification is a pure read.

    _verify_archive probes through the public run_integrity_check /
    verify_domain_identity wrappers (dbreview004 made both read-only); the
    archive's bytes, file mode, and directory listing must survive it
    unchanged.
    """
    import hashlib
    import os
    import sqlite3

    from db.rotation import _verify_archive

    archive = tmp_path / "session_20260101.sqlite"
    conn = sqlite3.connect(archive)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE sessions (session_id INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO sessions DEFAULT VALUES")
    conn.commit()
    conn.close()

    before_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    before_listing = sorted(os.listdir(tmp_path))
    before_mode = archive.stat().st_mode

    _verify_archive(archive, "session")

    assert hashlib.sha256(archive.read_bytes()).hexdigest() == before_sha
    assert sorted(os.listdir(tmp_path)) == before_listing
    assert archive.stat().st_mode == before_mode


# ── Maintenance error semantics (dbreview006, REQ-006) ────────────────────────


class TestPurgeTransactionAtomicity:
    """AC-1: both purge delete rules run in one BEGIN IMMEDIATE transaction;
    a count-rule failure rolls back the age-rule deletions (REQ-001)."""

    def test_count_rule_failure_rolls_back_age_deletions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import db.maintenance as db_maintenance

        def _boom(*args: object, **kwargs: object) -> None:
            raise sqlite3.OperationalError("count rule boom")

        monkeypatch.setattr(db_maintenance, "_delete_sessions_beyond_limit", _boom)

        helper = SQLiteHelper("session", db_path=str(tmp_path / "session.sqlite"))
        with helper.open(write_mode=True) as db:
            db.executescript(_SESSION_SCHEMA)
            for i in range(5):
                db.execute(
                    "INSERT INTO sessions (title, created_at)"
                    " VALUES (?, datetime('now', '-10 days'))",
                    (f"s{i}",),
                )
            db.commit()

            result = purge_old_sessions(
                db,
                RetentionConfig(max_sessions=1, max_age_days=1),
                mode=MaintenanceMode.BEST_EFFORT,
            )

            assert result.success is False
            assert result.action == "purge_failed"
            assert result.data == {
                "age_deleted": 0,
                "count_deleted": 0,
                "kept_active_session": None,
            }
            assert db.fetchall("SELECT COUNT(*) FROM sessions")[0][0] == 5
            assert helper._require_conn().in_transaction is False


class TestVacuumDatabaseError:
    """AC-2: vacuum_db captures any sqlite3.Error, not only OperationalError (REQ-002)."""

    def _malformed(self) -> MagicMock:
        mock_db = MagicMock(spec=SQLiteHelper)
        mock_db.vacuum.side_effect = sqlite3.DatabaseError(
            "database disk image is malformed"
        )
        return mock_db

    def test_vacuum_best_effort_catches_database_error(self) -> None:
        result = vacuum_db(self._malformed(), mode=MaintenanceMode.BEST_EFFORT)
        assert isinstance(result, MaintenanceResult)
        assert result.success is False
        assert result.action == "vacuum_failed"
        assert result.detail is not None
        assert "malformed" in result.detail
        assert result.mode == MaintenanceMode.BEST_EFFORT

    def test_vacuum_strict_raises_database_error(self) -> None:
        with pytest.raises(sqlite3.DatabaseError, match="malformed"):
            vacuum_db(self._malformed(), mode=MaintenanceMode.STRICT)


class TestConfigErrorPropagation:
    """AC-3: config-load failures propagate in both modes (REQ-003)."""

    def test_purge_config_oserror_raises_in_both_modes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import db.maintenance as db_maintenance

        def _boom(self: object, key: str) -> dict:
            raise OSError("agent.toml unreadable")

        monkeypatch.setattr(db_maintenance.ConfigLoader, "load", _boom)
        mock_db = MagicMock(spec=SQLiteHelper)
        for mode in (MaintenanceMode.STRICT, MaintenanceMode.BEST_EFFORT):
            with pytest.raises(OSError, match="agent.toml unreadable"):
                # cfg=None triggers RetentionConfig.from_config (config load)
                purge_old_sessions(mock_db, mode=mode)  # type: ignore[arg-type]

    def test_archive_config_valueerror_raises_best_effort(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import db.maintenance as db_maintenance

        def _boom() -> object:
            raise ValueError("db config invalid")

        monkeypatch.setattr(db_maintenance, "build_db_config", _boom)
        with pytest.raises(ValueError, match="db config invalid"):
            purge_corrupt_archives(
                CorruptArchiveRetentionConfig(), mode=MaintenanceMode.BEST_EFFORT
            )


class TestHandleMaintenanceErrorReraise:
    """AC-4: _handle_maintenance_error re-raises the passed exception even
    when called outside any except block (REQ-004)."""

    def test_direct_call_outside_except_reraises_same_exception(self) -> None:
        exc = ValueError("x")
        with pytest.raises(ValueError) as caught:
            _handle_maintenance_error(exc, "op", MaintenanceMode.STRICT)
        assert caught.value is exc


class TestPruneIdsSource:
    """AC-5: data["pruned_ids"] is exactly the ids removed by the delete
    transaction; maintenance no longer pre-selects via collect_prunable_ids (REQ-005)."""

    def test_pruned_ids_equal_deleted_ids_and_no_preselect(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(
            """
            CREATE TABLE memories (memory_id TEXT PRIMARY KEY, updated_at TEXT,
                pinned INTEGER DEFAULT 0);
            CREATE TABLE memories_fts (memory_id TEXT);
            CREATE TABLE memories_vec (memory_id TEXT);
            CREATE TABLE memory_links (src_id TEXT, dst_id TEXT);
            """
        )
        conn.executemany(
            "INSERT INTO memories VALUES (?, datetime('now', ?), ?)",
            [("m1", "-90 days", 0), ("m2", "-90 days", 1), ("m3", "-1 days", 0)],
        )
        conn.executemany("INSERT INTO memories_fts VALUES (?)", [("m1",)])
        conn.executemany("INSERT INTO memories_vec VALUES (?)", [("m1",)])
        conn.executemany(
            "INSERT INTO memory_links VALUES (?, ?)", [("m1", "x"), ("y", "m1")]
        )
        conn.commit()

        db = _FakeDB(conn)
        with patch.object(
            SQLiteMemoryDeleteStore, "collect_prunable_ids", autospec=True
        ) as spy:
            result = prune_old_memories(db, older_than_days=30)  # type: ignore[arg-type]

        assert result.success is True
        assert result.data is not None
        pruned_ids = result.data["pruned_ids"]
        assert pruned_ids == ["m1"]
        assert result.data["deleted"] == len(pruned_ids)
        remaining = {row[0] for row in conn.execute("SELECT memory_id FROM memories")}
        assert remaining == {"m2", "m3"}
        assert conn.execute("SELECT COUNT(*) FROM memories_fts").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM memories_vec").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM memory_links").fetchone()[0] == 0
        spy.assert_not_called()


class TestRetentionConfigBoundary:
    """from_config boundary matrix: negative/bool/float/string raise key-naming ValueError; 0 loads (REQ-001/REQ-003)."""

    _RETENTION_KEYS = (
        "sqlite_retention_max_sessions",
        "sqlite_retention_max_age_days",
    )
    _ARCHIVE_KEYS = (
        "sqlite_corrupt_archive_max_files",
        "sqlite_corrupt_archive_max_age_days",
    )

    @pytest.mark.parametrize("bad", [-1, True, 1.5, "10"])
    @pytest.mark.parametrize("key", _RETENTION_KEYS + _ARCHIVE_KEYS)
    def test_invalid_value_raises_key_naming_valueerror(
        self, monkeypatch: pytest.MonkeyPatch, key: str, bad: object
    ) -> None:
        import db.maintenance as db_maintenance

        monkeypatch.setattr(
            db_maintenance.ConfigLoader, "load", lambda self, k: {key: bad}
        )
        from_config = (
            RetentionConfig.from_config
            if key in self._RETENTION_KEYS
            else CorruptArchiveRetentionConfig.from_config
        )
        with pytest.raises(ValueError, match=key):
            from_config()

    def test_zero_values_load_cleanly(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import db.maintenance as db_maintenance

        monkeypatch.setattr(
            db_maintenance.ConfigLoader,
            "load",
            lambda self, k: {
                "sqlite_retention_max_sessions": 0,
                "sqlite_retention_max_age_days": 0,
                "sqlite_corrupt_archive_max_files": 0,
                "sqlite_corrupt_archive_max_age_days": 0,
            },
        )
        assert RetentionConfig.from_config() == RetentionConfig(
            max_sessions=0, max_age_days=0
        )
        assert (
            CorruptArchiveRetentionConfig.from_config()
            == CorruptArchiveRetentionConfig(max_files=0, max_age_days=0)
        )

    def test_max_sessions_zero_keeps_all(self) -> None:
        db = _make_session_db([(f"s{i}", "2099-01-01T00:00:00Z") for i in range(11)])
        result = purge_old_sessions(
            db, RetentionConfig(max_sessions=0, max_age_days=90)
        )  # type: ignore[arg-type]
        assert result.success is True
        assert result.data is not None
        assert result.data["count_deleted"] == 0
        assert result.data["age_deleted"] == 0
        assert db.conn is not None
        assert db.conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 11

    def test_max_files_zero_keeps_all_archives(self, tmp_path: Path) -> None:
        import db.maintenance as db_maintenance

        for i in range(5):
            (tmp_path / f"rag_corrupt_{i}.sqlite").write_text("archive")
        cfg = _make_db_cfg(tmp_path)
        with patch.object(db_maintenance, "build_db_config", return_value=cfg):
            result = purge_corrupt_archives(
                CorruptArchiveRetentionConfig(max_files=0, max_age_days=0)
            )
        assert result.success is True
        assert result.data is not None
        assert result.data["count_deleted"] == 0
        assert result.data["age_deleted"] == 0
        assert len(list(tmp_path.glob("rag_corrupt_*"))) == 5


class TestRetentionHelperGuards:
    """Directly constructed negative configs raise ValueError in both modes before any deletion (REQ-001)."""

    def test_negative_session_retention_raises_in_both_modes(self) -> None:
        db = _make_session_db([("old", "2000-01-01T00:00:00Z")])
        for mode in (MaintenanceMode.STRICT, MaintenanceMode.BEST_EFFORT):
            with pytest.raises(ValueError, match="sqlite_retention_max_sessions"):
                purge_old_sessions(  # type: ignore[arg-type]
                    db, RetentionConfig(max_sessions=-1, max_age_days=0), mode
                )
            with pytest.raises(ValueError, match="sqlite_retention_max_age_days"):
                purge_old_sessions(  # type: ignore[arg-type]
                    db, RetentionConfig(max_sessions=100, max_age_days=-1), mode
                )
        assert db.conn is not None
        assert db.conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1

    def test_negative_archive_retention_raises_in_both_modes(
        self, tmp_path: Path
    ) -> None:
        import db.maintenance as db_maintenance

        cfg = _make_db_cfg(tmp_path)
        for mode in (MaintenanceMode.STRICT, MaintenanceMode.BEST_EFFORT):
            with patch.object(db_maintenance, "build_db_config", return_value=cfg):
                with pytest.raises(
                    ValueError, match="sqlite_corrupt_archive_max_files"
                ):
                    purge_corrupt_archives(
                        CorruptArchiveRetentionConfig(max_files=-1, max_age_days=0),
                        mode,
                    )
                with pytest.raises(
                    ValueError, match="sqlite_corrupt_archive_max_age_days"
                ):
                    purge_corrupt_archives(
                        CorruptArchiveRetentionConfig(max_files=10, max_age_days=-1),
                        mode,
                    )


class TestRetentionCutoffDay:
    """T/Z cutoff contract: one row 5 s past the cutoff-day boundary is deleted, one 5 s inside survives (REQ-004)."""

    def test_cutoff_day_boundary_deletes_only_the_past_row(self) -> None:
        now = datetime.now(UTC)
        past = (now - timedelta(days=1, seconds=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        inside = (now - timedelta(days=1) + timedelta(seconds=5)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        db = _make_session_db([("past", past), ("inside", inside)])
        result = purge_old_sessions(
            db, RetentionConfig(max_sessions=100, max_age_days=1)
        )  # type: ignore[arg-type]
        assert result.success is True
        assert result.data is not None
        assert result.data["age_deleted"] == 1
        assert result.data["count_deleted"] == 0
        assert db.conn is not None
        titles = {row[0] for row in db.conn.execute("SELECT title FROM sessions")}
        assert titles == {"inside"}


class TestRetentionTieOrder:
    """Equal created_at ties resolve deterministically: lowest session_id is deleted first (REQ-006)."""

    def test_equal_created_at_keeps_highest_session_ids(self) -> None:
        for _ in range(2):  # repeated for determinism
            db = _make_session_db(
                [(f"s{i}", "2099-01-01T00:00:00Z") for i in range(1, 6)]
            )
            result = purge_old_sessions(
                db, RetentionConfig(max_sessions=2, max_age_days=0)
            )  # type: ignore[arg-type]
            assert result.success is True
            assert result.data is not None
            assert result.data["count_deleted"] == 3
            assert db.conn is not None
            kept = {
                row[0] for row in db.conn.execute("SELECT session_id FROM sessions")
            }
            assert kept == {4, 5}
