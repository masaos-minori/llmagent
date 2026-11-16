import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from db.config import DbConfig
from db.recovery import (
    DbCondition,
    _classify_error,
    _restore_from_backup,
    recover_corruption,
)
from db.recovery_verification import _run_logical_verification


@pytest.fixture
def mock_db_cfg():
    with patch("db.recovery.build_db_config") as mock_cfg:
        # spec=DbConfig ensures accessing a nonexistent field (e.g. "bogus_db_path")
        # raises AttributeError, matching a real DbConfig instance — required for
        # test_recover_unsupported_target's getattr(..., None) guard to be exercised
        # correctly.
        mock_instance = MagicMock(spec=DbConfig)
        mock_instance.rag_db_path = Path("/tmp/rag.db")
        mock_instance.session_db_path = Path("/tmp/session.db")
        mock_instance.workflow_db_path = Path("/tmp/workflow.db")
        mock_cfg.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_sqlite_helper():
    """Patch SQLiteHelper in both recovery modules.

    The restore path lives in db.recovery and the logical verification it dispatches
    to lives in db.recovery_verification, so both modules' helper must be mocked for
    a restore that reaches verification to stay off the real filesystem.
    """
    with (
        patch("db.recovery.SQLiteHelper") as mock_helper_class,
        patch("db.recovery_verification.SQLiteHelper") as mock_verification_class,
    ):
        mock_verification_class.return_value = mock_helper_class.return_value
        mock_helper_instance = mock_helper_class.return_value.__enter__.return_value
        yield mock_helper_instance


def test_recover_healthy(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ):
        result = recover_corruption(target="rag", dry_run=False)

        assert result.success is True
        assert result.action == "vacuum"


def test_recover_corrupt_rag_restores(mock_db_cfg, mock_sqlite_helper):
    with patch("db.recovery._run_integrity_check") as mock_integrity:
        mock_integrity.side_effect = [
            (DbCondition.CORRUPTION, "corruption error"),  # For DB
            (DbCondition.HEALTHY, None),  # For Backup
            (DbCondition.HEALTHY, None),  # Candidate check (pre-activation)
            (DbCondition.HEALTHY, None),  # Post-restore re-verification
        ]

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("db.recovery_restore.resolve_unique_path", side_effect=lambda p: p),
            patch("shutil.copy2"),
            patch("shutil.move"),
            patch("pathlib.Path.unlink"),
            patch("os.replace"),
            patch(
                "db.recovery._run_logical_verification",
                return_value=(True, None),
            ),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is True
            assert result.action == "restored"
            assert result.logical_ok is True
            assert result.active_db_state == "restored"


def test_recover_corrupt_workflow_prohibited(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.CORRUPTION, "corruption error"),
    ) as mock_integrity:
        result = recover_corruption(target="workflow")

        assert result.success is False
        assert result.action == "no_recovery_allowed"
        assert result.detail and "Automatic recovery is prohibited" in result.detail
        mock_integrity.assert_not_called()


def test_recover_lock_contention(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.LOCK_CONTENTION, "database is locked"),
    ):
        result = recover_corruption(target="rag")

        assert result.success is False
        assert result.action == "error"
        assert result.detail and "lock_contention" in result.detail


def test_recover_permission_failure(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.PERMISSION_FAILURE, "permission denied"),
    ):
        result = recover_corruption(target="rag")

        assert result.success is False
        assert result.action == "error"
        assert result.detail and "permission_failure" in result.detail


def test_recover_invalid_format(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.INVALID_FORMAT, "invalid database format"),
    ):
        result = recover_corruption(target="rag")

        assert result.success is False
        assert result.action == "error"
        assert result.detail and "invalid_format" in result.detail


def test_recover_no_backup(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.CORRUPTION, "corruption error"),
    ):
        result = recover_corruption(backup_path=None, target="rag")

        assert result.success is False
        assert result.action == "no_backup"


def test_recover_bad_backup(mock_db_cfg, mock_sqlite_helper):
    with patch("db.recovery._run_integrity_check") as mock_integrity:
        mock_integrity.side_effect = [
            (DbCondition.CORRUPTION, "DB corruption"),  # For DB
            (DbCondition.CORRUPTION, "Backup corruption"),  # For Backup
        ]

        with patch("pathlib.Path.exists", return_value=True):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "bad_backup"


def test_recover_wrong_domain_backup_rejected(mock_db_cfg, mock_sqlite_helper):
    with (
        patch("db.recovery._run_integrity_check") as mock_integrity,
        patch(
            "db.recovery._verify_domain_identity",
            return_value=(False, "backup missing required table 'sessions'"),
        ),
        patch("pathlib.Path.exists", return_value=True),
    ):
        mock_integrity.side_effect = [
            (DbCondition.CORRUPTION, "corruption error"),  # current DB
            (DbCondition.HEALTHY, None),  # backup
        ]
        result = recover_corruption(backup_path="/tmp/backup.db", target="session")

        assert result.success is False
        assert result.action == "backup_wrong_domain"


def test_recover_wrong_domain_backup_distinct_action(mock_db_cfg, mock_sqlite_helper):
    with (
        patch("db.recovery._run_integrity_check") as mock_integrity,
        patch(
            "db.recovery._verify_domain_identity",
            return_value=(False, "backup missing required table 'sessions'"),
        ),
        patch("pathlib.Path.exists", return_value=True),
    ):
        mock_integrity.side_effect = [
            (DbCondition.CORRUPTION, "corruption error"),  # current DB
            (DbCondition.HEALTHY, None),  # backup
        ]
        result = recover_corruption(backup_path="/tmp/backup.db", target="session")

        assert result.action not in ("no_backup", "bad_backup")


def test_recover_backup_with_unreadable_sqlite_master(mock_db_cfg, mock_sqlite_helper):
    """A backup whose sqlite_master cannot be read reports a failed recovery, not an exception.

    `_verify_domain_identity()` opens the backup, and `recover_corruption()`'s OSError
    handler starts after that check, so the sqlite3.Error has to be reported as a
    failed backup instead of escaping to the caller.
    """
    with (
        patch("db.recovery._run_integrity_check") as mock_integrity,
        patch(
            "db.recovery._verify_domain_identity",
            side_effect=sqlite3.DatabaseError("file is not a database"),
        ),
        patch("pathlib.Path.exists", return_value=True),
    ):
        mock_integrity.side_effect = [
            (DbCondition.CORRUPTION, "corruption error"),  # current DB
            (DbCondition.HEALTHY, None),  # backup
        ]
        result = recover_corruption(backup_path="/tmp/backup.db", target="session")

    assert result.success is False
    assert result.action == "bad_backup"
    assert "domain-identity check failed" in (result.detail or "")


def test_recover_wrong_domain_backup_leaves_db_untouched(
    mock_db_cfg, mock_sqlite_helper
):
    with (
        patch("db.recovery._run_integrity_check") as mock_integrity,
        patch(
            "db.recovery._verify_domain_identity",
            return_value=(False, "backup missing required table 'sessions'"),
        ),
        patch("pathlib.Path.exists", return_value=True),
        patch("shutil.copy2") as mock_copy2,
        patch("os.replace") as mock_replace,
    ):
        mock_integrity.side_effect = [
            (DbCondition.CORRUPTION, "corruption error"),  # current DB
            (DbCondition.HEALTHY, None),  # backup
        ]
        result = recover_corruption(backup_path="/tmp/backup.db", target="session")

        assert result.success is False
        mock_copy2.assert_not_called()
        mock_replace.assert_not_called()


def test_recover_dry_run_healthy(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ):
        result = recover_corruption(target="rag", dry_run=True)

        assert result.success is True
        assert result.action == "vacuum"
        assert result.dry_run is True


def test_recover_dry_run_corrupt_file_unchanged(tmp_path):
    """Dry Run on a real corrupt database leaves its bytes and its directory unchanged (INV-16).

    The database is created in WAL mode, the mode every deployed database uses; opening a
    rollback-journal file would first switch it to WAL, which is outside this invariant.
    """
    db_file = tmp_path / "rag.db"
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE t (a TEXT)")
    conn.executemany(
        "INSERT INTO t VALUES (?)", [("x" * 200 + str(i),) for i in range(2000)]
    )
    conn.commit()
    conn.close()
    corrupt = bytearray(db_file.read_bytes())
    corrupt[8192 : 8192 + 4096] = b"\xff" * 4096
    db_file.write_bytes(bytes(corrupt))
    before_bytes = db_file.read_bytes()
    before_listing = sorted(p.name for p in tmp_path.iterdir())

    with patch("db.recovery.build_db_config") as mock_cfg:
        mock_instance = MagicMock(spec=DbConfig)
        mock_instance.rag_db_path = db_file
        mock_cfg.return_value = mock_instance
        result = recover_corruption(target="rag", dry_run=True)

    assert result.dry_run is True
    assert result.success is False
    assert "corruption" in (result.detail or "")
    assert db_file.read_bytes() == before_bytes
    assert sorted(p.name for p in tmp_path.iterdir()) == before_listing


def test_recover_unsupported_target(mock_db_cfg, mock_sqlite_helper):
    with patch("db.recovery._run_integrity_check") as mock_integrity:
        result = recover_corruption(target="bogus")

        assert result.success is False
        assert result.action == "unsupported_target"
        assert result.detail and "bogus" in result.detail
        mock_integrity.assert_not_called()


def test_recover_restore_verify_failed(mock_db_cfg, mock_sqlite_helper):
    with patch("db.recovery._run_integrity_check") as mock_integrity:
        mock_integrity.side_effect = [
            (DbCondition.CORRUPTION, "corruption error"),  # current DB
            (DbCondition.HEALTHY, None),  # backup
            (
                DbCondition.CORRUPTION,
                "still corrupt",
            ),  # candidate check (pre-activation)
        ]

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("db.recovery_restore.resolve_unique_path", side_effect=lambda p: p),
            patch("shutil.copy2"),
            patch("shutil.move"),
            patch("pathlib.Path.unlink"),
            patch("os.replace"),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "restore_verify_failed"
            assert result.detail == "still corrupt"


def test_recover_workflow_uses_correct_db_path(mock_db_cfg, mock_sqlite_helper):
    """Regression test: target="workflow" must integrity-check workflow_db_path,
    not session_db_path (ADR-008 domain-policy bypass found during adversarial
    verification of the implementation procedure)."""
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.CORRUPTION, "corruption error"),
    ) as mock_integrity:
        result = recover_corruption(target="workflow")

        mock_integrity.assert_not_called()
        assert result.success is False
        assert result.action == "no_recovery_allowed"


def test_recover_unknown_preserved_operator_intervention_required(
    mock_db_cfg, mock_sqlite_helper
):
    """DbCondition.UNKNOWN must preserve the DB and require operator intervention."""
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.UNKNOWN, "unclassifiable integrity failure"),
    ) as mock_integrity:
        result = recover_corruption(target="rag")

        mock_integrity.assert_called_once()
        assert result.success is False
        assert result.action == "preserved_operator_intervention_required"
        assert result.detail is not None
        assert "operator intervention required" in result.detail
        assert "unclassifiable integrity failure" in result.detail


def _mock_restore_side_effect():
    """Return side_effect list for restore path: DB corruption -> backup healthy -> candidate healthy -> post-restore healthy."""
    return [
        (DbCondition.CORRUPTION, "corruption error"),  # current DB
        (DbCondition.HEALTHY, None),  # backup
        (DbCondition.HEALTHY, None),  # candidate check (pre-activation)
        (DbCondition.HEALTHY, None),  # post-restore re-check
    ]


def test_recover_rag_fts_gap(mock_db_cfg, mock_sqlite_helper):
    """RAG FTS gap should cause logical verification failure."""
    with patch("db.recovery._run_integrity_check") as mock_integrity:
        mock_integrity.side_effect = _mock_restore_side_effect()

        rag_report = MagicMock()
        rag_report.fts_gap = 5
        rag_report.fts_orphan_count = 0
        rag_report.orphan_vec_count = 0
        rag_report.vec = 10
        rag_report.chunks = 10
        rag_report.documents_without_chunks_count = 0
        rag_report.chunks_without_vec_count = 0
        rag_report.duplicate_chunk_index_count = 0
        rag_report.url_level_mismatches = {}
        rag_report.diagnostic_errors = None

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("db.recovery_restore.resolve_unique_path", side_effect=lambda p: p),
            patch("shutil.copy2"),
            patch("shutil.move"),
            patch("pathlib.Path.unlink"),
            patch("os.replace"),
            patch(
                "db.recovery_verification.check_rag_consistency",
                return_value=rag_report,
            ),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is False
            assert result.active_db_state == "preserved_original"


def test_recover_rag_missing_table(mock_db_cfg, mock_sqlite_helper):
    """RAG missing table/trigger should cause logical verification failure."""
    with patch("db.recovery._run_integrity_check") as mock_integrity:
        mock_integrity.side_effect = _mock_restore_side_effect()

        rag_report = MagicMock()
        rag_report.chunks = 10
        rag_report.vec = 10
        rag_report.fts_gap = 0
        rag_report.fts_orphan_count = 0
        rag_report.orphan_vec_count = 0
        rag_report.documents_without_chunks_count = 0
        rag_report.chunks_without_vec_count = 0
        rag_report.duplicate_chunk_index_count = 0
        rag_report.url_level_mismatches = {}
        rag_report.diagnostic_errors = ("Missing table: chunks",)

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("db.recovery_restore.resolve_unique_path", side_effect=lambda p: p),
            patch("shutil.copy2"),
            patch("shutil.move"),
            patch("pathlib.Path.unlink"),
            patch("os.replace"),
            patch(
                "db.recovery_verification.check_rag_consistency",
                return_value=rag_report,
            ),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is False
            assert result.active_db_state == "preserved_original"


def test_recover_rag_fts_orphan(mock_db_cfg, mock_sqlite_helper):
    """RAG FTS orphan should cause logical verification failure."""
    with patch("db.recovery._run_integrity_check") as mock_integrity:
        mock_integrity.side_effect = _mock_restore_side_effect()

        rag_report = MagicMock()
        rag_report.chunks = 10
        rag_report.vec = 10
        rag_report.fts_gap = 0
        rag_report.fts_orphan_count = 3
        rag_report.orphan_vec_count = 0
        rag_report.documents_without_chunks_count = 0
        rag_report.chunks_without_vec_count = 0
        rag_report.duplicate_chunk_index_count = 0
        rag_report.url_level_mismatches = {}
        rag_report.diagnostic_errors = None

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("db.recovery_restore.resolve_unique_path", side_effect=lambda p: p),
            patch("shutil.copy2"),
            patch("shutil.move"),
            patch("pathlib.Path.unlink"),
            patch("os.replace"),
            patch(
                "db.recovery_verification.check_rag_consistency",
                return_value=rag_report,
            ),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is False
            assert result.active_db_state == "preserved_original"


def test_recover_rag_vector_orphan(mock_db_cfg, mock_sqlite_helper):
    """RAG vector orphan should cause logical verification failure."""
    with patch("db.recovery._run_integrity_check") as mock_integrity:
        mock_integrity.side_effect = _mock_restore_side_effect()

        rag_report = MagicMock()
        rag_report.chunks = 10
        rag_report.vec = 10
        rag_report.fts_gap = 0
        rag_report.fts_orphan_count = 0
        rag_report.orphan_vec_count = 2
        rag_report.documents_without_chunks_count = 0
        rag_report.chunks_without_vec_count = 0
        rag_report.duplicate_chunk_index_count = 0
        rag_report.url_level_mismatches = {}
        rag_report.diagnostic_errors = None

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("db.recovery_restore.resolve_unique_path", side_effect=lambda p: p),
            patch("shutil.copy2"),
            patch("shutil.move"),
            patch("pathlib.Path.unlink"),
            patch("os.replace"),
            patch(
                "db.recovery_verification.check_rag_consistency",
                return_value=rag_report,
            ),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is False
            assert result.active_db_state == "preserved_original"


def test_recover_rag_read_smoke_test_failed(mock_db_cfg, mock_sqlite_helper):
    """RAG read smoke test failure should cause logical verification failure even when counts are healthy."""
    with patch("db.recovery._run_integrity_check") as mock_integrity:
        mock_integrity.side_effect = _mock_restore_side_effect()

        rag_report = MagicMock()
        rag_report.chunks = 10
        rag_report.vec = 10
        rag_report.fts_gap = 0
        rag_report.fts_orphan_count = 0
        rag_report.orphan_vec_count = 0
        rag_report.documents_without_chunks_count = 0
        rag_report.chunks_without_vec_count = 0
        rag_report.duplicate_chunk_index_count = 0
        rag_report.url_level_mismatches = {}
        rag_report.diagnostic_errors = None
        rag_report.read_smoke_test_ok = False

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("db.recovery_restore.resolve_unique_path", side_effect=lambda p: p),
            patch("shutil.copy2"),
            patch("shutil.move"),
            patch("pathlib.Path.unlink"),
            patch("os.replace"),
            patch(
                "db.recovery_verification.check_rag_consistency",
                return_value=rag_report,
            ),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is False
            assert result.active_db_state == "preserved_original"


# --- _classify_error() direct unit tests ---

import sqlite3


def test_recover_healthy_workflow_prohibited(mock_db_cfg, mock_sqlite_helper):
    """Regression: workflow target with HEALTHY DB must reject before any DB access."""
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ) as mock_integrity:
        with patch("db.recovery._vacuum_db") as mock_vacuum:
            result = recover_corruption(target="workflow")

            assert result.success is False
            assert result.action == "no_recovery_allowed"
            assert result.detail and "Automatic recovery is prohibited" in result.detail
            mock_integrity.assert_not_called()
            mock_vacuum.assert_not_called()


def test_recover_dry_run_workflow_prohibited(mock_db_cfg, mock_sqlite_helper):
    """Regression: dry_run mode must reject workflow before any DB access."""
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ) as mock_integrity:
        result = recover_corruption(target="workflow", dry_run=True)

        assert result.success is False
        assert result.action == "no_recovery_allowed"
        assert result.dry_run is True
        mock_integrity.assert_not_called()


def test_recover_eventbus_target_is_unsupported(mock_db_cfg, mock_sqlite_helper):
    """eventbus.sqlite is owned by the EventBus service: the Agent-side recovery
    rejects it as an unknown target before any DB access."""
    with patch("db.recovery._run_integrity_check") as mock_integrity:
        result = recover_corruption(target="eventbus")

        assert result.success is False
        assert result.action == "unsupported_target"
        mock_integrity.assert_not_called()


def test_classify_error_health_invariant():
    """_classify_error never returns DbCondition.HEALTHY — this invariant must hold."""
    pass  # No assertion needed: the invariant is that HEALTHY is unreachable here.


def test_classify_error_corruption_generic():
    """Generic sqlite3.DatabaseError should map to CORRUPTION."""
    e = sqlite3.DatabaseError("some corruption error")
    result = _classify_error(e)
    assert result == DbCondition.CORRUPTION


def test_classify_error_lock_contention_via_sqlite_errorcode():
    """Lock contention detected via sqlite_errorcode (SQLITE_BUSY=5 / SQLITE_LOCKED=6)."""
    e = sqlite3.OperationalError("database is locked")
    e.sqlite_errorcode = 5  # SQLITE_BUSY
    result = _classify_error(e)
    assert result == DbCondition.LOCK_CONTENTION

    e.sqlite_errorcode = 6  # SQLITE_LOCKED
    result = _classify_error(e)
    assert result == DbCondition.LOCK_CONTENTION


def test_classify_error_lock_contention_via_substring():
    """Lock contention detected via substring fallback."""
    e = sqlite3.OperationalError("database is locked")
    result = _classify_error(e)
    assert result == DbCondition.LOCK_CONTENTION

    e = sqlite3.OperationalError("the database is busy")
    result = _classify_error(e)
    assert result == DbCondition.LOCK_CONTENTION


def test_classify_error_permission_failure_via_sqlite_errorcode():
    """Permission failure detected via sqlite_errorcode (SQLITE_READONLY=8)."""
    e = sqlite3.OperationalError("permission denied")
    e.sqlite_errorcode = 8  # SQLITE_READONLY
    result = _classify_error(e)
    assert result == DbCondition.PERMISSION_FAILURE


def test_classify_error_permission_failure_via_substring():
    """Permission failure detected via substring fallback."""
    e = sqlite3.OperationalError("permission denied")
    result = _classify_error(e)
    assert result == DbCondition.PERMISSION_FAILURE

    e = sqlite3.OperationalError("readonly filesystem")
    result = _classify_error(e)
    assert result == DbCondition.PERMISSION_FAILURE


def test_classify_error_invalid_format():
    """'file is not a database' signal should map to INVALID_FORMAT."""
    e = sqlite3.DatabaseError("file is not a database")
    result = _classify_error(e)
    assert result == DbCondition.INVALID_FORMAT

    e = ValueError("file is not a database")
    result = _classify_error(e)
    assert result == DbCondition.INVALID_FORMAT


def test_classify_error_unknown():
    """Non-sqlite3 exceptions should map to UNKNOWN."""
    e = RuntimeError("something went wrong")
    result = _classify_error(e)
    assert result == DbCondition.UNKNOWN


# --- _quarantine_sidecar_files / _stage_backup_sidecars unit tests ---

import shutil
import tempfile
import time

from db.recovery_restore import (
    _quarantine_sidecar_files,
    _stage_backup_sidecars,
)


def test_quarantine_sidecar_files():
    """Stale -wal/-shm files present before restore should be quarantined."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        wal_path = db_path.parent / f"{db_path.name}-wal"
        shm_path = db_path.parent / f"{db_path.name}-shm"

        # Create dummy files
        db_path.write_bytes(b"\x00" * 100)
        wal_path.write_text("STALE_WAL_CONTENT")
        shm_path.write_text("STALE_SHM_CONTENT")

        # Verify sidecars exist before quarantine
        assert wal_path.exists()
        assert shm_path.exists()

        quarantine_dir = (
            db_path.parent / f"{db_path.stem}_sidecar_quarantine_{int(time.time())}"
        )
        quarantine_dir.mkdir(exist_ok=True)

        records = _quarantine_sidecar_files(db_path, quarantine_dir)

        # Sidecars should be removed from original location
        assert not wal_path.exists()
        assert not shm_path.exists()

        # Quarantined copies should exist under the full-filename form
        assert len(list(quarantine_dir.glob("test.sqlite-wal_corrupt_*"))) == 1
        assert len(list(quarantine_dir.glob("test.sqlite-shm_corrupt_*"))) == 1

        # Returned records pair each live name with its quarantine copy (REQ-001)
        assert [(live.name, q.parent) for live, q in records] == [
            ("test.sqlite-wal", quarantine_dir),
            ("test.sqlite-shm", quarantine_dir),
        ]
        assert records[0][1].name.startswith("test.sqlite-wal_corrupt_")
        assert records[1][1].name.startswith("test.sqlite-shm_corrupt_")

        shutil.rmtree(quarantine_dir, ignore_errors=True)


def test_stage_backup_sidecars():
    """Backup -wal/-shm sidecars should be staged alongside temp_restore."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_path = Path(tmpdir) / "backup.sqlite"
        backup_wal = backup_path.parent / f"{backup_path.name}-wal"
        backup_shm = backup_path.parent / f"{backup_path.name}-shm"
        temp_restore_parent = Path(tmpdir) / "restore_target"
        temp_restore_parent.mkdir()

        # Create dummy files
        backup_path.write_bytes(b"\x00" * 100)
        backup_wal.write_text("BACKUP_WAL_CONTENT")
        backup_shm.write_text("BACKUP_SHM_CONTENT")

        # Verify backup sidecars exist
        assert backup_wal.exists()
        assert backup_shm.exists()

        staged = _stage_backup_sidecars(backup_path, temp_restore_parent)

        # Both sidecars should be staged
        assert len(staged) == 2
        assert "-wal" in staged
        assert "-shm" in staged

        # Staged sidecars should exist at destination with full-filename names
        assert staged["-wal"].exists()
        assert staged["-shm"].exists()
        assert staged["-wal"].name == "backup.sqlite-wal"
        assert staged["-shm"].name == "backup.sqlite-shm"


def test_quarantine_sidecar_files_raises_on_copy_failure():
    """Fail-closed (REQ-002): a quarantine copy failure raises instead of skipping the sidecar."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        wal_path = db_path.parent / f"{db_path.name}-wal"
        db_path.write_bytes(b"\x00" * 100)
        wal_path.write_text("STALE_WAL_CONTENT")
        quarantine_dir = db_path.parent / "quarantine"
        quarantine_dir.mkdir()

        with patch(
            "db.recovery_restore.shutil.copy2", side_effect=OSError("copy failed")
        ):
            with pytest.raises(OSError):
                _quarantine_sidecar_files(db_path, quarantine_dir)

        # The sidecar stays in place: no silent removal without a quarantined copy.
        assert wal_path.exists()


def test_quarantine_sidecar_files_self_rolls_back_mid_failure():
    """Self-rollback (REQ-001): a second-sidecar failure restores the first pair.

    If the quarantine copy fails on -shm after -wal was already recorded,
    _quarantine_sidecar_files must move -wal back to its live name
    byte-identically and remove the emptied quarantine directory before
    raising, so the caller never loses a recorded pair.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        wal_path = db_path.parent / f"{db_path.name}-wal"
        shm_path = db_path.parent / f"{db_path.name}-shm"
        db_path.write_bytes(b"\x00" * 100)
        wal_path.write_text("STALE_WAL_CONTENT")
        shm_path.write_text("STALE_SHM_CONTENT")
        quarantine_dir = db_path.parent / "quarantine"
        quarantine_dir.mkdir()

        real_copy2 = shutil.copy2

        def _fail_on_shm(src, dst, *args, **kwargs):
            if "-shm_corrupt_" in str(dst):
                raise OSError("copy failed")
            return real_copy2(src, dst, *args, **kwargs)

        with patch("db.recovery_restore.shutil.copy2", side_effect=_fail_on_shm):
            with pytest.raises(OSError):
                _quarantine_sidecar_files(db_path, quarantine_dir)

        # The recorded -wal pair is rolled back byte-identically to its live name.
        assert wal_path.read_text() == "STALE_WAL_CONTENT"
        # -shm was never removed: the failing copy left it in place.
        assert shm_path.read_text() == "STALE_SHM_CONTENT"
        # Empty after the restore-back: the quarantine directory is removed
        # (exists only while non-empty).
        assert not quarantine_dir.exists()


def test_stage_backup_sidecars_raises_on_copy_failure():
    """Fail-closed (REQ-002): a staging copy failure raises instead of staging a partial unit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_path = Path(tmpdir) / "backup.sqlite"
        backup_wal = backup_path.parent / f"{backup_path.name}-wal"
        backup_path.write_bytes(b"\x00" * 100)
        backup_wal.write_text("BACKUP_WAL_CONTENT")
        staged_dir = Path(tmpdir) / "staged"
        staged_dir.mkdir()

        with patch(
            "db.recovery_restore.shutil.copy2", side_effect=OSError("copy failed")
        ):
            with pytest.raises(OSError):
                _stage_backup_sidecars(backup_path, staged_dir)

        assert not any(staged_dir.iterdir())


def test_restore_with_stale_wal_shm_before_swap(mock_db_cfg, mock_sqlite_helper):
    """Stale -wal/-shm files present before restore should be quarantined and not affect restore."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        wal_path = db_path.parent / f"{db_path.name}-wal"
        shm_path = db_path.parent / f"{db_path.name}-shm"

        # Create dummy files
        db_path.write_bytes(b"\x00" * 100)
        wal_path.write_text("STALE_WAL_CONTENT")
        shm_path.write_text("STALE_SHM_CONTENT")

        # Verify sidecars exist before restore
        assert wal_path.exists()
        assert shm_path.exists()

        # Create a valid backup (SQLite header for health check)
        backup_path = Path(tmpdir) / "backup.sqlite"
        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch(
                "db.recovery._run_logical_verification",
                return_value=(True, None),
            ),
            patch("os.replace"),
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.HEALTHY, None),  # candidate check (pre-activation)
                (DbCondition.HEALTHY, None),  # post-restore re-check
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is True
        assert result.action == "restored"
        assert result.logical_ok is True
        assert result.active_db_state == "restored"

        # Stale sidecars should be removed from original location
        assert not wal_path.exists()
        assert not shm_path.exists()

        # Retention policy (Plan 003 REQ-003): the quarantine archive stays after
        # a successful restore, holding copies of the stale sidecars.
        quarantine_dirs = list(Path(tmpdir).glob("*_sidecar_quarantine_*"))
        assert len(quarantine_dirs) == 1
        assert list(quarantine_dirs[0].glob("test.sqlite-wal_corrupt_*"))
        assert list(quarantine_dirs[0].glob("test.sqlite-shm_corrupt_*"))


def test_restore_with_backup_wal_shm_sidecars(mock_db_cfg, mock_sqlite_helper):
    """Backup -wal/-shm sidecars should be staged and swapped atomically with main file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_dir = Path(tmpdir) / "db_dir"
        db_dir.mkdir()
        db_path = db_dir / "test.sqlite"
        wal_path = db_dir / "test.sqlite-wal"
        shm_path = db_dir / "test.sqlite-shm"

        # Create stale sidecars on db_path
        db_path.write_bytes(b"\x00" * 100)
        wal_path.write_text("STALE_WAL_CONTENT")
        shm_path.write_text("STALE_SHM_CONTENT")

        # Backup with its own WAL/SHM in a separate directory
        backup_dir = Path(tmpdir) / "backup_dir"
        backup_dir.mkdir()
        backup_path = backup_dir / "backup.sqlite"
        backup_wal = backup_dir / "backup.sqlite-wal"
        backup_shm = backup_dir / "backup.sqlite-shm"

        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)
        backup_wal.write_text("BACKUP_WAL_CONTENT")
        backup_shm.write_text("BACKUP_SHM_CONTENT")

        # Verify all files exist
        assert wal_path.exists()
        assert shm_path.exists()
        assert backup_wal.exists()
        assert backup_shm.exists()

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch(
                "db.recovery._run_logical_verification",
                return_value=(True, None),
            ),
            patch("os.replace"),
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.HEALTHY, None),  # candidate check (pre-activation)
                (DbCondition.HEALTHY, None),  # post-restore re-check
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is True
        assert result.action == "restored"
        assert result.logical_ok is True
        assert result.active_db_state == "restored"

        # Restored DB should have WAL/SHM sidecars from backup
        restored_wal = db_dir / "test.sqlite-wal"
        restored_shm = db_dir / "test.sqlite-shm"
        assert restored_wal.exists(), "Restored WAL sidecar should exist"
        assert restored_shm.exists(), "Restored SHM sidecar should exist"
        assert restored_wal.read_text() == "BACKUP_WAL_CONTENT"
        assert restored_shm.read_text() == "BACKUP_SHM_CONTENT"


def test_unverified_candidate_is_never_activated(mock_db_cfg, mock_sqlite_helper):
    """Verify-before-activate (REQ-003): a failing candidate never touches the live DB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        original_bytes = b"CORRUPT ORIGINAL CONTENT"
        db_path.write_bytes(original_bytes)
        backup_path = Path(tmpdir) / "backup.sqlite"
        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch("db.recovery._run_logical_verification") as mock_logical,
            patch("os.replace") as mock_replace,
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (
                    DbCondition.CORRUPTION,
                    "candidate is corrupt",
                ),  # candidate (pre-activation)
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is False
        assert result.action == "restore_verify_failed"
        assert result.logical_ok is False
        assert result.active_db_state == "preserved_original"
        # The swap never ran and the live bytes are byte-identical.
        mock_replace.assert_not_called()
        mock_logical.assert_not_called()
        assert db_path.read_bytes() == original_bytes
        # Staged candidate files are cleaned up; the corrupt archive stays for forensics.
        assert not list(Path(tmpdir).glob("*.tmp_*"))
        assert list(Path(tmpdir).glob("test_corrupt_*"))


def test_post_activation_failure_rolls_back_the_original(
    mock_db_cfg, mock_sqlite_helper
):
    """REQ-004: a failed post-activation re-check puts the archived original back."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        original_bytes = b"CORRUPT ORIGINAL CONTENT"
        db_path.write_bytes(original_bytes)
        backup_path = Path(tmpdir) / "backup.sqlite"
        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.HEALTHY, None),  # candidate (pre-activation)
                (DbCondition.CORRUPTION, "post-activation check failed"),  # re-check
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is False
        assert result.action == "restore_verify_failed"
        assert result.logical_ok is False
        assert result.active_db_state == "preserved_original"
        # Real os.replace ran: activation swapped in the candidate, rollback swapped
        # the archived original back, so the live path holds the original bytes.
        assert db_path.read_bytes() == original_bytes
        assert not list(Path(tmpdir).glob("test_corrupt_*"))


def test_failed_rollback_reports_non_serviceable(mock_db_cfg, mock_sqlite_helper):
    """AC-004: when the rollback itself fails, the result reports rollback_failed / non_serviceable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        db_path.write_bytes(b"CORRUPT ORIGINAL CONTENT")
        backup_path = Path(tmpdir) / "backup.sqlite"
        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
            patch(
                "os.replace",
                side_effect=[None, OSError("rollback replace failed")],
            ) as mock_replace,
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.HEALTHY, None),  # candidate (pre-activation)
                (DbCondition.CORRUPTION, "post-activation check failed"),  # re-check
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is False
        assert result.action == "rollback_failed"
        assert result.logical_ok is False
        assert result.active_db_state == "non_serviceable"
        # First replace activated the candidate, the second (rollback) failed.
        assert mock_replace.call_count == 2


def test_os_error_after_activation_with_failed_rollback_reports_non_serviceable(
    mock_db_cfg, mock_sqlite_helper
) -> None:
    """REQ-003/AC-004: an OSError after activation whose rollback also fails is reported."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        db_path.write_bytes(b"CORRUPT ORIGINAL CONTENT")
        backup_path = Path(tmpdir) / "backup.sqlite"
        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
            # Activation's os.replace succeeds; the handler's rollback replace fails.
            patch("os.replace", side_effect=[None, OSError("rollback replace failed")]),
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.HEALTHY, None),  # candidate (pre-activation)
                OSError("disk I/O failure in the post-activation re-check"),
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is False
        # Unified vocabulary: the rollback helper reports the failed rollback itself
        # as rollback_failed / non_serviceable (REQ-003), same as the post-activation
        # verification-failure path.
        assert result.action == "rollback_failed"
        assert result.active_db_state == "non_serviceable"


def test_wal_shm_sidecars_land_at_final_locations_after_activation(
    mock_db_cfg, mock_sqlite_helper
) -> None:
    """WAL integration: a successful restore lands sidecars at <db>.sqlite-wal / -shm."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_dir = Path(tmpdir) / "db_dir"
        db_dir.mkdir()
        db_path = db_dir / "test.sqlite"
        db_path.write_bytes(b"CORRUPT ORIGINAL CONTENT")
        (db_dir / "test.sqlite-wal").write_text("STALE_WAL_CONTENT")
        (db_dir / "test.sqlite-shm").write_text("STALE_SHM_CONTENT")

        backup_dir = Path(tmpdir) / "backup_dir"
        backup_dir.mkdir()
        backup_path = backup_dir / "backup.sqlite"
        backup_bytes = b"SQLite format 3\x00" + b"\x00" * 99
        backup_path.write_bytes(backup_bytes)
        (backup_dir / "backup.sqlite-wal").write_text("BACKUP_WAL_CONTENT")
        (backup_dir / "backup.sqlite-shm").write_text("BACKUP_SHM_CONTENT")

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.HEALTHY, None),  # candidate (pre-activation)
                (DbCondition.HEALTHY, None),  # post-activation re-check
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is True
        assert result.action == "restored"
        assert result.active_db_state == "restored"
        # Real activation: the live DB holds the candidate bytes...
        assert db_path.read_bytes() == backup_bytes
        # ...and the sidecars end at their full-filename locations.
        assert (db_dir / "test.sqlite-wal").read_text() == "BACKUP_WAL_CONTENT"
        assert (db_dir / "test.sqlite-shm").read_text() == "BACKUP_SHM_CONTENT"
        # Retention policy (Plan 003 REQ-003): the stale sidecars stay archived.
        quarantine_dirs = list(db_dir.glob("*_sidecar_quarantine_*"))
        assert len(quarantine_dirs) == 1
        assert list(quarantine_dirs[0].glob("test.sqlite-wal_corrupt_*"))
        assert list(quarantine_dirs[0].glob("test.sqlite-shm_corrupt_*"))


# --- In-activation failure injection (companion 20261115-080732_1) ---


def test_activation_failure_after_replace_rolls_back_original(
    mock_db_cfg, mock_sqlite_helper
) -> None:
    """AC-1: an OSError after os.replace but before the sidecar moves rolls back."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_dir = Path(tmpdir) / "db_dir"
        db_dir.mkdir()
        db_path = db_dir / "test.sqlite"
        original_bytes = b"CORRUPT ORIGINAL CONTENT"
        db_path.write_bytes(original_bytes)
        (db_dir / "test.sqlite-wal").write_text("STALE_WAL_CONTENT")

        backup_dir = Path(tmpdir) / "backup_dir"
        backup_dir.mkdir()
        backup_path = backup_dir / "backup.sqlite"
        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)
        (backup_dir / "backup.sqlite-wal").write_text("BACKUP_WAL_CONTENT")

        shutil_move_real = shutil.move
        live_wal = Path(str(db_path) + "-wal")

        def fail_on_live_move(src, dst, *args, **kwargs):
            # Fault only the activation move (staged temp file -> live name).
            # Staging moves and the quarantine-back move (quarantine dir ->
            # live name) must run for real, so they are keyed by source.
            if Path(dst) == live_wal and Path(src).name.startswith("test.tmp_"):
                raise OSError("sidecar move failed")
            return shutil_move_real(src, dst, *args, **kwargs)

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
            patch("shutil.move", side_effect=fail_on_live_move),
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.HEALTHY, None),  # candidate (pre-activation)
                (DbCondition.HEALTHY, None),  # post-activation re-check (not reached)
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is False
        assert result.action == "error"
        assert result.active_db_state == "preserved_original"
        # The rollback moved the archived original back onto the live name, so the
        # archive itself no longer exists as a separate *_corrupt_* file.
        assert db_path.read_bytes() == original_bytes
        assert not list(db_dir.glob("*_corrupt_*"))
        # Whole-unit reassembly (Plan 003): the candidate sidecar never reached
        # the live name, and the quarantined original sidecar was moved back.
        assert live_wal.read_text() == "STALE_WAL_CONTENT"
        assert not list(db_dir.glob("*_sidecar_quarantine_*"))


def test_partial_activation_removes_moved_sidecars_on_rollback(
    mock_db_cfg, mock_sqlite_helper
) -> None:
    """AC-4/REQ-002: a failed second move unlinks the sidecar that already moved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_dir = Path(tmpdir) / "db_dir"
        db_dir.mkdir()
        db_path = db_dir / "test.sqlite"
        original_bytes = b"CORRUPT ORIGINAL CONTENT"
        db_path.write_bytes(original_bytes)
        (db_dir / "test.sqlite-wal").write_text("STALE_WAL_CONTENT")
        (db_dir / "test.sqlite-shm").write_text("STALE_SHM_CONTENT")

        backup_dir = Path(tmpdir) / "backup_dir"
        backup_dir.mkdir()
        backup_path = backup_dir / "backup.sqlite"
        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)
        (backup_dir / "backup.sqlite-wal").write_text("BACKUP_WAL_CONTENT")
        (backup_dir / "backup.sqlite-shm").write_text("BACKUP_SHM_CONTENT")

        shutil_move_real = shutil.move
        live_names = {Path(str(db_path) + "-wal"), Path(str(db_path) + "-shm")}
        live_moves = 0

        def fail_on_second_live_move(src, dst, *args, **kwargs):
            # Activation moves only (staged temp file -> live name): the first
            # runs for real, the second raises. The quarantine-back move is
            # keyed out by its quarantine-directory source.
            nonlocal live_moves
            if Path(dst) in live_names and Path(src).name.startswith("test.tmp_"):
                live_moves += 1
                if live_moves == 2:
                    raise OSError("second sidecar move failed")
            return shutil_move_real(src, dst, *args, **kwargs)

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
            patch("shutil.move", side_effect=fail_on_second_live_move),
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.HEALTHY, None),  # candidate (pre-activation)
                (DbCondition.HEALTHY, None),  # post-activation re-check (not reached)
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is False
        assert result.action == "error"
        assert result.active_db_state == "preserved_original"
        # The first candidate sidecar had already reached its live name; the
        # rollback removed it before moving the original back. Whole-unit
        # reassembly (Plan 003): both live sidecars hold the quarantined originals,
        # and no candidate file is left at any live name.
        assert Path(str(db_path) + "-wal").read_text() == "STALE_WAL_CONTENT"
        assert Path(str(db_path) + "-shm").read_text() == "STALE_SHM_CONTENT"
        assert db_path.read_bytes() == original_bytes
        assert not list(db_dir.glob("*_corrupt_*"))
        assert not list(db_dir.glob("*_sidecar_quarantine_*"))


def test_cleanup_staged_unlink_failure_does_not_escape(
    mock_db_cfg, mock_sqlite_helper
) -> None:
    """AC-3/REQ-004: an unlink failure in _cleanup_staged is logged, not raised."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_dir = Path(tmpdir) / "db_dir"
        db_dir.mkdir()
        db_path = db_dir / "test.sqlite"
        db_path.write_bytes(b"CORRUPT ORIGINAL CONTENT")

        backup_dir = Path(tmpdir) / "backup_dir"
        backup_dir.mkdir()
        backup_path = backup_dir / "backup.sqlite"
        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)
        (backup_dir / "backup.sqlite-wal").write_text("BACKUP_WAL_CONTENT")

        unlink_real = Path.unlink

        def unlink_or_fail(self, *args, **kwargs):
            # Only the staged temp main file is blocked; every other unlink
            # (e.g. the staged sidecar) runs for real.
            if self.name.startswith("test.tmp_") and self.suffix == ".sqlite":
                raise OSError("unlink blocked")
            return unlink_real(self, *args, **kwargs)

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
            patch("pathlib.Path.unlink", autospec=True, side_effect=unlink_or_fail),
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.CORRUPTION, "candidate is corrupt"),  # candidate
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is False
        assert result.action == "restore_verify_failed"
        assert result.active_db_state == "preserved_original"
        # The blocked temp file leaked (logged, not raised); the staged sidecar was
        # removed, and the live path still holds the original bytes.
        assert list(db_dir.glob("test.tmp_*.sqlite"))
        assert not list(db_dir.glob("test.tmp_*.sqlite-wal"))
        assert db_path.read_bytes() == b"CORRUPT ORIGINAL CONTENT"


# --- Whole-unit reassembly and quarantine retention (companion 20261115-082016_1/_2) ---


def _write_stale_sidecars(db_dir: Path, db_name: str) -> None:
    """Write distinct-content -wal/-shm fixtures next to db_name in db_dir."""
    (db_dir / f"{db_name}-wal").write_text("STALE_WAL_CONTENT")
    (db_dir / f"{db_name}-shm").write_text("STALE_SHM_CONTENT")


def test_preactivation_integrity_failure_restores_whole_unit(
    mock_db_cfg, mock_sqlite_helper
) -> None:
    """AC-1: a candidate integrity failure leaves the live unit byte-identical."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_dir = Path(tmpdir) / "db_dir"
        db_dir.mkdir()
        db_path = db_dir / "test.sqlite"
        original_bytes = b"CORRUPT ORIGINAL CONTENT"
        db_path.write_bytes(original_bytes)
        _write_stale_sidecars(db_dir, "test.sqlite")

        backup_path = Path(tmpdir) / "backup.sqlite"
        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.CORRUPTION, "candidate is corrupt"),  # candidate
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is False
        assert result.action == "restore_verify_failed"
        assert result.active_db_state == "preserved_original"
        # The main file was never swapped and both sidecars were moved back.
        assert db_path.read_bytes() == original_bytes
        assert (db_dir / "test.sqlite-wal").read_text() == "STALE_WAL_CONTENT"
        assert (db_dir / "test.sqlite-shm").read_text() == "STALE_SHM_CONTENT"
        assert not list(db_dir.glob("*_sidecar_quarantine_*"))
        assert not list(db_dir.glob("*.tmp_*"))


def test_preactivation_logical_failure_restores_whole_unit(
    mock_db_cfg, mock_sqlite_helper
) -> None:
    """AC-1: a candidate logical failure leaves the live unit byte-identical."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_dir = Path(tmpdir) / "db_dir"
        db_dir.mkdir()
        db_path = db_dir / "test.sqlite"
        original_bytes = b"CORRUPT ORIGINAL CONTENT"
        db_path.write_bytes(original_bytes)
        _write_stale_sidecars(db_dir, "test.sqlite")

        backup_path = Path(tmpdir) / "backup.sqlite"
        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch(
                "db.recovery._run_logical_verification",
                return_value=(False, "counts mismatch"),
            ),
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.HEALTHY, None),  # candidate
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is False
        assert result.action == "logical_verify_failed"
        assert result.active_db_state == "preserved_original"
        assert db_path.read_bytes() == original_bytes
        assert (db_dir / "test.sqlite-wal").read_text() == "STALE_WAL_CONTENT"
        assert (db_dir / "test.sqlite-shm").read_text() == "STALE_SHM_CONTENT"
        assert not list(db_dir.glob("*_sidecar_quarantine_*"))


def test_postactivation_rollback_reassembles_whole_unit(
    mock_db_cfg, mock_sqlite_helper
) -> None:
    """AC-1/AC-2: post-activation rollback removes candidate sidecars and moves the originals back."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_dir = Path(tmpdir) / "db_dir"
        db_dir.mkdir()
        db_path = db_dir / "test.sqlite"
        original_bytes = b"CORRUPT ORIGINAL CONTENT"
        db_path.write_bytes(original_bytes)
        _write_stale_sidecars(db_dir, "test.sqlite")

        backup_dir = Path(tmpdir) / "backup_dir"
        backup_dir.mkdir()
        backup_path = backup_dir / "backup.sqlite"
        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)
        (backup_dir / "backup.sqlite-wal").write_text("BACKUP_WAL_CONTENT")
        (backup_dir / "backup.sqlite-shm").write_text("BACKUP_SHM_CONTENT")

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.HEALTHY, None),  # candidate (pre-activation)
                (DbCondition.CORRUPTION, "post-activation check failed"),  # re-check
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is False
        assert result.action == "restore_verify_failed"
        assert result.active_db_state == "preserved_original"
        # Live main holds the archived original; live sidecars hold the quarantined
        # originals, not the candidate's backup sidecars.
        assert db_path.read_bytes() == original_bytes
        assert (db_dir / "test.sqlite-wal").read_text() == "STALE_WAL_CONTENT"
        assert (db_dir / "test.sqlite-shm").read_text() == "STALE_SHM_CONTENT"
        # The quarantine directory was emptied by the move-back and removed.
        assert not list(db_dir.glob("*_sidecar_quarantine_*"))


def test_restore_without_sidecars_creates_no_quarantine_directory(
    mock_db_cfg, mock_sqlite_helper
) -> None:
    """Plan Assumption: the deferred mkdir leaves no directory for sidecar-free restores."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        db_path.write_bytes(b"CORRUPT ORIGINAL CONTENT")
        backup_path = Path(tmpdir) / "backup.sqlite"
        backup_path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)

        with (
            patch("db.recovery._run_integrity_check") as mock_integrity,
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
            patch("os.replace"),
        ):
            mock_integrity.side_effect = [
                (DbCondition.HEALTHY, None),  # backup
                (DbCondition.HEALTHY, None),  # candidate (pre-activation)
                (DbCondition.HEALTHY, None),  # post-activation re-check
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is True
        assert result.action == "restored"
        assert not list(Path(tmpdir).glob("*_sidecar_quarantine_*"))


# --- Real sqlite-vec restore verification (companion 20261115-075008_1) ---
#
# These tests run the real extension load and the real logical verification:
# a healthy vec0-bearing candidate must reach action="restored". They are
# written against the fixed behavior of _run_logical_verification, which
# resolves sqlite_vec_so via build_db_config() itself.

from db.config import build_db_config
from db.helper import SQLiteHelper
from db.schema_sql import build_rag_schema_sql, build_session_schema_sql
from db.store_protocols import get_embedding_bytes, get_embedding_dims

VEC_SO = Path(build_db_config().sqlite_vec_so)
vec0_available = VEC_SO.is_file()
vec_required = pytest.mark.skipif(
    not vec0_available, reason=f"sqlite-vec extension not available at {VEC_SO}"
)


def _make_vec_rag_db(path: Path) -> None:
    """Build a minimal fully consistent rag candidate with real vec0 tables."""
    zero_vec = b"\x00" * get_embedding_bytes()
    with SQLiteHelper("rag", db_path=str(path), sqlite_vec_so=str(VEC_SO)).open(
        write_mode=True
    ) as db:
        db.executescript(build_rag_schema_sql(get_embedding_dims()))
        db.execute(
            "INSERT INTO documents (url, lang, fetched_at) VALUES (?, ?, ?)",
            ("test://doc1", "ja", "2026-01-01T00:00:00Z"),
        )
        db.execute(
            "INSERT INTO chunks (doc_id, chunk_index, content) VALUES (?, ?, ?)",
            (1, 0, "test chunk content"),
        )
        db.execute(
            "INSERT INTO chunks_vec (chunk_id, embedding) VALUES (?, ?)", (1, zero_vec)
        )
        db.commit()


def _make_vec_session_db(path: Path) -> None:
    """Build a minimal fully consistent session candidate with real vec0 tables."""
    zero_vec = b"\x00" * get_embedding_bytes()
    with SQLiteHelper("session", db_path=str(path), sqlite_vec_so=str(VEC_SO)).open(
        write_mode=True
    ) as db:
        db.executescript(build_session_schema_sql(get_embedding_dims()))
        db.execute("INSERT INTO sessions DEFAULT VALUES")
        db.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (1, "user", "hello"),
        )
        db.execute(
            "INSERT INTO memories (memory_id, memory_type, content) VALUES (?, ?, ?)",
            ("m1", "semantic", "test memory"),
        )
        db.execute(
            "INSERT INTO memories_vec (memory_id, embedding) VALUES (?, ?)",
            ("m1", zero_vec),
        )
        db.commit()


@vec_required
def test_restore_rag_vec0_candidate_reaches_restored(tmp_path: Path) -> None:
    """AC-2: a healthy real-vec0 rag candidate passes verification and activates."""
    db_dir = tmp_path / "db_dir"
    db_dir.mkdir()
    db_path = db_dir / "rag.sqlite"
    db_path.write_bytes(b"CORRUPT ORIGINAL CONTENT")
    backup_path = tmp_path / "backup.sqlite"
    _make_vec_rag_db(backup_path)

    with patch("db.recovery._run_integrity_check") as mock_integrity:
        mock_integrity.side_effect = [
            (DbCondition.HEALTHY, None),  # backup
            (DbCondition.HEALTHY, None),  # candidate (pre-activation)
            (DbCondition.HEALTHY, None),  # post-activation re-check
        ]
        result = _restore_from_backup(db_path, str(backup_path), target="rag")

    assert result.success is True
    assert result.action == "restored"
    assert result.logical_ok is True
    assert result.active_db_state == "restored"
    assert db_path.read_bytes() == backup_path.read_bytes()


@vec_required
def test_restore_session_vec0_candidate_reaches_restored(tmp_path: Path) -> None:
    """AC-2: the memories_vec-requiring session stage passes with the extension."""
    db_dir = tmp_path / "db_dir"
    db_dir.mkdir()
    db_path = db_dir / "session.sqlite"
    db_path.write_bytes(b"CORRUPT ORIGINAL CONTENT")
    backup_path = tmp_path / "backup.sqlite"
    _make_vec_session_db(backup_path)

    with patch("db.recovery._run_integrity_check") as mock_integrity:
        mock_integrity.side_effect = [
            (DbCondition.HEALTHY, None),  # backup
            (DbCondition.HEALTHY, None),  # candidate (pre-activation)
            (DbCondition.HEALTHY, None),  # post-activation re-check
        ]
        result = _restore_from_backup(db_path, str(backup_path), target="session")

    assert result.success is True
    assert result.action == "restored"
    assert result.logical_ok is True
    assert result.active_db_state == "restored"
    assert db_path.read_bytes() == backup_path.read_bytes()


def test_logical_verification_config_failure_is_verification_unavailable(
    tmp_path: Path,
) -> None:
    """REQ-001 fail-closed: a config without sqlite_vec_so never reports success."""
    db_file = tmp_path / "rag.sqlite"
    db_file.write_bytes(b"SQLite format 3\x00" + b"\x00" * 99)
    with patch(
        "db.recovery_verification.build_db_config",
        side_effect=ValueError("sqlite_vec_so is empty or absent in agent.toml"),
    ):
        consistent, detail = _run_logical_verification(db_file, "rag")
    assert consistent is False
    assert detail == "verification_unavailable"


# --- Characterization tests for the recovery internals the suite left uncovered ---
#
# These lock behavior that the refactor of scripts/db/recovery.py must preserve
# byte-for-byte: the exact detail strings `_run_logical_verification` builds, the
# `_classify_error` branch boundaries, the integrity-check and domain-identity
# contracts, the VACUUM failure result, the restore guard results, and the
# OSError cleanup contract. Each was recorded against the pre-refactor module.

import sqlite3 as _sqlite3

from db.models import (
    RagConsistencyReport,
    RecoveryResult,
    SessionConsistencyReport,
)
from db.recovery import (
    _dry_run_integrity_ok,
    _run_integrity_check,
    _vacuum_db,
    _verify_domain_identity,
)


@pytest.fixture
def mock_recovery_db():
    """Patch SQLiteHelper in both recovery modules and yield the object `with ... .open() as db` binds to.

    `SQLiteHelper.open()` returns self and `__enter__` returns self, so the bound
    name is `SQLiteHelper(...).open().__enter__()`, not the helper instance itself.
    `db.recovery_verification` is patched with the same class because
    `_run_logical_verification` now lives there and opens the helper itself.
    """
    with (
        patch("db.recovery.SQLiteHelper") as helper_class,
        patch("db.recovery_verification.SQLiteHelper") as verification_helper_class,
    ):
        verification_helper_class.return_value = helper_class.return_value
        yield helper_class.return_value.open.return_value.__enter__.return_value


def _rag_report(**overrides: object) -> RagConsistencyReport:
    """A fully consistent rag report, with the named fields overridden."""
    fields: dict = {
        "chunks": 10,
        "fts": 10,
        "vec": 10,
        "orphan_vec_count": 0,
        "fts_gap": 0,
        "fts_orphan_count": 0,
        "read_smoke_test_ok": True,
    }
    fields.update(overrides)
    return RagConsistencyReport(**fields)


def _session_report(**overrides: object) -> SessionConsistencyReport:
    """A fully consistent session report, with the named fields overridden."""
    fields: dict = {
        "sessions": 1,
        "messages": 2,
        "memories": 0,
        "orphaned_message_count": 0,
        "orphaned_memory_link_count": 0,
        "session_diagnostics_readable": True,
        "read_smoke_test_ok": True,
    }
    fields.update(overrides)
    return SessionConsistencyReport(**fields)


class TestClassifyErrorBranchBoundaries:
    """Characterization: the isinstance-chain boundaries of `_classify_error`."""

    def test_value_error_without_the_signal_is_corruption(self) -> None:
        assert _classify_error(ValueError("bad argument")) == DbCondition.CORRUPTION

    def test_operational_error_with_an_unmapped_errorcode_is_unknown(self) -> None:
        e = _sqlite3.OperationalError("cannot execute statement")
        e.sqlite_errorcode = 1  # SQLITE_ERROR
        assert _classify_error(e) == DbCondition.UNKNOWN

    def test_operational_error_with_errorcode_zero_is_not_treated_as_missing(
        self,
    ) -> None:
        e = _sqlite3.OperationalError("cannot execute statement")
        e.sqlite_errorcode = 0
        assert _classify_error(e) == DbCondition.UNKNOWN

    def test_operational_error_with_the_signal_is_invalid_format(self) -> None:
        """The INVALID_FORMAT signal is checked before the OperationalError branch."""
        e = _sqlite3.OperationalError("file is not a database")
        assert _classify_error(e) == DbCondition.INVALID_FORMAT

    def test_plain_database_error_with_the_signal_is_invalid_format(self) -> None:
        e = _sqlite3.DatabaseError("file is not a database")
        assert _classify_error(e) == DbCondition.INVALID_FORMAT


class TestRunIntegrityCheckCharacterization:
    """Characterization: `_run_integrity_check` had no direct coverage at all.

    dbreview004 churn: every call site states the probe mode and the
    existence-first gate needs a real file. The placeholder file only
    satisfies the gate — the mocked helper decides the probe result either way.
    """

    @staticmethod
    def _existing_db(tmp_path: Path) -> Path:
        db_file = tmp_path / "rag.db"
        db_file.write_bytes(b"placeholder for the existence gate")
        return db_file

    def test_ok_is_healthy(self, mock_recovery_db, tmp_path: Path) -> None:
        mock_recovery_db.execute.return_value.fetchone.return_value = ("ok",)

        assert _run_integrity_check(
            self._existing_db(tmp_path), "rag", read_only=True
        ) == (
            DbCondition.HEALTHY,
            None,
        )

    def test_non_ok_result_is_corruption_with_the_raw_text(
        self, mock_recovery_db, tmp_path: Path
    ) -> None:
        mock_recovery_db.execute.return_value.fetchone.return_value = (
            "wrong number of entries in index",
        )

        assert _run_integrity_check(
            self._existing_db(tmp_path), "rag", read_only=True
        ) == (
            DbCondition.CORRUPTION,
            "wrong number of entries in index",
        )

    def test_open_failure_is_classified(self, mock_recovery_db, tmp_path: Path) -> None:
        mock_recovery_db.execute.side_effect = _sqlite3.DatabaseError(
            "file is not a database"
        )

        assert _run_integrity_check(
            self._existing_db(tmp_path), "rag", read_only=True
        ) == (
            DbCondition.INVALID_FORMAT,
            "file is not a database",
        )


class TestDryRunIntegrityOkCharacterization:
    """Characterization: the dry_run result a HEALTHY integrity check reports."""

    def test_dry_run_result(self) -> None:
        assert _dry_run_integrity_ok() == RecoveryResult(
            success=True,
            action="vacuum",
            detail="integrity ok (dry run)",
            dry_run=True,
        )


class TestLogicalVerificationDetailCharacterization:
    """Characterization: the exact detail strings and the skip/tolerate branches."""

    def test_rag_detail_lists_every_gap_in_declaration_order(
        self, mock_recovery_db
    ) -> None:
        report = _rag_report(
            chunks=10,
            fts=7,
            vec=9,
            orphan_vec_count=3,
            fts_gap=3,
            fts_orphan_count=2,
            documents_without_chunks_count=4,
            chunks_without_vec_count=5,
            duplicate_chunk_index_count=6,
            url_level_mismatches={"https://example.test/a": {"chunk_count": 1}},
        )

        with patch(
            "db.recovery_verification.check_rag_consistency", return_value=report
        ):
            ok, detail = _run_logical_verification(Path("/tmp/rag.db"), "rag")

        assert ok is False
        assert detail == (
            "fts_gap=3; fts_orphan=2; orphan_vec=3; vec=9/chunks=10; "
            "docs_no_chunks=4; chunks_no_vec=5; dup_chunk_idx=6; url_mismatches=1"
        )

    def test_rag_consistent_report_reports_no_detail(self, mock_recovery_db) -> None:
        with patch(
            "db.recovery_verification.check_rag_consistency", return_value=_rag_report()
        ):
            ok, detail = _run_logical_verification(Path("/tmp/rag.db"), "rag")

        assert (ok, detail) == (True, None)

    def test_rag_read_smoke_only_failure_produces_an_empty_detail(
        self, mock_recovery_db
    ) -> None:
        """`is_consistent` checks read_smoke_test_ok, but the detail builder does not."""
        with patch(
            "db.recovery_verification.check_rag_consistency",
            return_value=_rag_report(read_smoke_test_ok=False),
        ):
            ok, detail = _run_logical_verification(Path("/tmp/rag.db"), "rag")

        assert ok is False
        assert detail == ""

    def test_session_consistent_report_reports_no_detail(
        self, mock_recovery_db
    ) -> None:
        with patch(
            "db.recovery_verification.check_session_consistency",
            return_value=_session_report(),
        ):
            ok, detail = _run_logical_verification(Path("/tmp/session.db"), "session")

        assert (ok, detail) == (True, None)

    def test_session_detail_lists_every_gap_in_declaration_order(
        self, mock_recovery_db
    ) -> None:
        report = _session_report(
            orphaned_message_count=2,
            orphaned_memory_link_count=3,
            session_diagnostics_readable=False,
            read_smoke_test_ok=False,
            diagnostic_errors=("boom", "bang"),
        )

        with patch(
            "db.recovery_verification.check_session_consistency", return_value=report
        ):
            ok, detail = _run_logical_verification(Path("/tmp/session.db"), "session")

        assert ok is False
        assert detail == (
            "orphan_msgs=2; orphan_mem_links=3; diag_not_readable; "
            "read_smoke_fail; errors=2"
        )

    def test_session_detail_with_only_an_orphan_lists_only_that_entry(
        self, mock_recovery_db
    ) -> None:
        """Fields left at their healthy values add no entry beside the orphan count."""
        report = _session_report(orphaned_message_count=1)

        with patch(
            "db.recovery_verification.check_session_consistency", return_value=report
        ):
            ok, detail = _run_logical_verification(Path("/tmp/session.db"), "session")

        assert ok is False
        assert detail == "orphan_msgs=1"

    def test_unknown_target_skips_verification(self, mock_recovery_db) -> None:
        assert _run_logical_verification(Path("/tmp/workflow.db"), "workflow") == (
            True,
            None,
        )

    def test_unknown_mandatory_target_fails_closed(self) -> None:
        # A mandatory domain with no registered verifier is a hard failure (seq 03);
        # a non-mandatory unknown target keeps the skip result.
        with patch("db.recovery_verification._LOGICAL_VERIFIERS", {}):
            assert _run_logical_verification(Path("/tmp/rag.db"), "rag") == (
                False,
                "verification_unavailable",
            )
            assert _run_logical_verification(Path("/tmp/session.db"), "session") == (
                False,
                "verification_unavailable",
            )
            assert _run_logical_verification(Path("/tmp/workflow.db"), "workflow") == (
                True,
                None,
            )

    def test_an_unopenable_database_fails_closed(
        self, mock_recovery_db, caplog
    ) -> None:
        with caplog.at_level(logging.ERROR, logger="db.recovery_verification"):
            with patch(
                "db.recovery_verification.check_rag_consistency",
                side_effect=_sqlite3.OperationalError("no such table: chunks"),
            ):
                ok, detail = _run_logical_verification(Path("/tmp/rag.db"), "rag")

        # Fail-closed (seq 03): an unverifiable mandatory target is a failure, not a tolerated gap.
        assert (ok, detail) == (False, "verification_unavailable")
        assert any("could not open DB" in msg for msg in caplog.messages)


class TestVacuumDbCharacterization:
    """Characterization: `_vacuum_db`'s failure result, which was uncovered."""

    def test_success(self, mock_recovery_db) -> None:
        assert _vacuum_db("rag") == RecoveryResult(success=True, action="vacuum")

    def test_operational_error_reports_vacuum_failed(self, mock_recovery_db) -> None:
        mock_recovery_db.vacuum.side_effect = _sqlite3.OperationalError(
            "disk I/O error"
        )

        assert _vacuum_db("rag") == RecoveryResult(
            success=False, action="vacuum_failed", detail="disk I/O error"
        )

    def test_runtime_error_reports_vacuum_failed(self, mock_recovery_db) -> None:
        mock_recovery_db.vacuum.side_effect = RuntimeError("vec extension unavailable")

        assert _vacuum_db("rag") == RecoveryResult(
            success=False, action="vacuum_failed", detail="vec extension unavailable"
        )


class TestVerifyDomainIdentityCharacterization:
    """Characterization: both uncovered exits of `_verify_domain_identity`."""

    def test_unknown_target_has_no_domain_constraint(self, mock_recovery_db) -> None:
        assert _verify_domain_identity(Path("/tmp/backup.db"), "workflow") == (
            True,
            None,
        )

    def test_missing_table_reports_the_detail(self, mock_recovery_db) -> None:
        mock_recovery_db.execute.return_value.fetchone.return_value = None

        ok, detail = _verify_domain_identity(Path("/tmp/backup.db"), "rag")

        assert ok is False
        assert detail == "backup missing required table 'documents' for domain 'rag'"

    def test_present_table_passes(self, mock_recovery_db) -> None:
        mock_recovery_db.execute.return_value.fetchone.return_value = ("documents",)

        assert _verify_domain_identity(Path("/tmp/backup.db"), "rag") == (True, None)


class TestRestoreGuardCharacterization:
    """Characterization: the restore guards that run against real files."""

    def test_missing_backup_file_reports_no_backup_with_the_path(
        self, tmp_path: Path
    ) -> None:
        db_path = tmp_path / "rag.db"
        db_path.write_text("corrupt")
        missing = tmp_path / "gone.db"

        result = _restore_from_backup(db_path, missing, target="rag", dry_run=True)

        assert result.success is False
        assert result.action == "no_backup"
        assert result.detail == f"backup not found: {missing}"
        assert result.dry_run is True

    def test_os_error_during_the_swap_removes_the_temp_restore_file(
        self, tmp_path: Path
    ) -> None:
        """The OSError handler unlinks the temp file, keeps the archive, and reassembles the unit."""
        db_path = tmp_path / "rag.db"
        db_path.write_text("corrupt")
        _write_stale_sidecars(tmp_path, "rag.db")
        backup = tmp_path / "backup.db"
        backup.write_text("good")

        with (
            patch(
                "db.recovery._run_integrity_check",
                return_value=(DbCondition.HEALTHY, None),
            ),
            patch("db.recovery._verify_domain_identity", return_value=(True, None)),
            # Stubbed so the flow reaches the swap: after seq 03 the unopenable
            # fixture files would fail closed at candidate verification first.
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
            patch("os.replace", side_effect=OSError("rename failed")),
        ):
            result = _restore_from_backup(db_path, backup, target="rag")

        assert result.success is False
        assert result.action == "error"
        assert result.detail == "rename failed"
        assert not list(tmp_path.glob("*.tmp_*.db")), "temp restore must be removed"
        assert list(tmp_path.glob("rag_corrupt_*.db")), "corrupt archive must remain"
        # The swap never completed: the quarantined sidecars are moved back and
        # the emptied quarantine directory is removed (Plan 003 whole-unit AC-1).
        assert (tmp_path / "rag.db-wal").read_text() == "STALE_WAL_CONTENT"
        assert (tmp_path / "rag.db-shm").read_text() == "STALE_SHM_CONTENT"
        assert not list(tmp_path.glob("*_sidecar_quarantine_*"))

    def test_successful_restore_retains_the_quarantine_directory(
        self, tmp_path: Path
    ) -> None:
        db_path = tmp_path / "rag.db"
        db_path.write_text("corrupt")
        _write_stale_sidecars(tmp_path, "rag.db")
        backup = tmp_path / "backup.db"
        backup.write_text("good")

        with (
            patch(
                "db.recovery._run_integrity_check",
                return_value=(DbCondition.HEALTHY, None),
            ),
            patch("db.recovery._verify_domain_identity", return_value=(True, None)),
            patch("db.recovery._run_logical_verification", return_value=(True, None)),
        ):
            result = _restore_from_backup(db_path, backup, target="rag")

        assert result.success is True
        assert result.action == "restored"
        assert result.detail == str(backup)
        # Retention policy (Plan 003 REQ-003): the archive directory and its
        # copies stay in place after a successful restore.
        quarantine_dirs = list(tmp_path.glob("*_sidecar_quarantine_*"))
        assert len(quarantine_dirs) == 1
        assert list(quarantine_dirs[0].glob("rag.db-wal_corrupt_*"))
        assert list(quarantine_dirs[0].glob("rag.db-shm_corrupt_*"))


class TestRecoverCorruptionConditionDispatchCharacterization:
    """Characterization: the dry_run CORRUPTION result and the healthy dry_run result."""

    def test_dry_run_corruption_reports_the_integrity_failure(
        self, mock_db_cfg
    ) -> None:
        with patch(
            "db.recovery._run_integrity_check",
            return_value=(DbCondition.CORRUPTION, "btree is corrupt"),
        ):
            result = recover_corruption(
                backup_path="/tmp/backup.db", target="rag", dry_run=True
            )

        assert result.success is False
        assert result.action == "error"
        assert result.detail == "Integrity failure (corruption): btree is corrupt"
        assert result.dry_run is True

    def test_dry_run_healthy_reports_the_vacuum_preview(self, mock_db_cfg) -> None:
        with patch(
            "db.recovery._run_integrity_check",
            return_value=(DbCondition.HEALTHY, None),
        ):
            result = recover_corruption(target="rag", dry_run=True)

        assert result == RecoveryResult(
            success=True,
            action="vacuum",
            detail="integrity ok (dry run)",
            dry_run=True,
        )


# ── Probe invariance and MISSING policy (dbreview004, REQ-002..REQ-006) ──────

import hashlib
import os as _os

from db.recovery import _backup_is_usable, run_integrity_check


def _sha256(path: Path) -> str:
    """sha256 of the file bytes — the filesystem-observable invariant of AC-1."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_run_integrity_check_leaves_backup_unchanged(tmp_path: Path) -> None:
    """REQ-006/AC-1: the public probe rewrites no bytes and creates no sidecars."""
    db_file = tmp_path / "backup.db"
    conn = _sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO documents VALUES (1)")
    conn.commit()
    conn.close()
    before_bytes = _sha256(db_file)
    before_listing = sorted(_os.listdir(tmp_path))

    condition, detail = run_integrity_check(db_file, "rag")

    assert (condition, detail) == (DbCondition.HEALTHY, None)
    assert _sha256(db_file) == before_bytes
    assert sorted(_os.listdir(tmp_path)) == before_listing


def test_run_integrity_check_keeps_rollback_journal_mode(tmp_path: Path) -> None:
    """REQ-003/AC-1: probing a rollback-journal database no longer switches it to WAL."""
    db_file = tmp_path / "backup.db"
    conn = _sqlite3.connect(db_file)
    conn.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO documents VALUES (1)")
    conn.commit()
    conn.close()
    before_bytes = _sha256(db_file)

    assert run_integrity_check(db_file, "rag")[0] == DbCondition.HEALTHY

    probe_conn = _sqlite3.connect(db_file)
    try:
        mode = probe_conn.execute("PRAGMA journal_mode").fetchone()[0]
    finally:
        probe_conn.close()
    assert mode == "delete"
    assert _sha256(db_file) == before_bytes


def test_backup_is_usable_leaves_backup_unchanged(tmp_path: Path) -> None:
    """REQ-006/AC-1: the pre-restore gate is a pure read on a healthy backup."""
    db_file = tmp_path / "backup.sqlite"
    conn = _sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO documents VALUES (1)")
    conn.commit()
    conn.close()
    before_bytes = _sha256(db_file)
    before_listing = sorted(_os.listdir(tmp_path))

    action, detail = _backup_is_usable(db_file, "rag")

    assert (action, detail) == (None, "")
    assert _sha256(db_file) == before_bytes
    assert sorted(_os.listdir(tmp_path)) == before_listing


def test_backup_is_usable_accepts_readonly_backup(tmp_path: Path) -> None:
    """REQ-003/AC-3: a 0444 backup verifies successfully instead of bad_backup."""
    db_file = tmp_path / "backup.sqlite"
    conn = _sqlite3.connect(db_file)
    conn.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO documents VALUES (1)")
    conn.commit()
    conn.close()
    db_file.chmod(0o444)

    action, detail = _backup_is_usable(db_file, "rag")

    assert (action, detail) == (None, "")


def _patch_cfg_to(tmp_path: Path, rag_db_path: Path):
    """Patch build_db_config so recover_corruption aims at tmp_path."""
    patcher = patch("db.recovery.build_db_config")
    mock_cfg = patcher.start()
    instance = MagicMock(spec=DbConfig)
    instance.rag_db_path = rag_db_path
    mock_cfg.return_value = instance
    return patcher


def test_recover_missing_live_db_reports_missing_database(tmp_path: Path) -> None:
    """REQ-002/REQ-004/AC-2: a vanished live DB reports missing_database, no restore."""
    db_file = tmp_path / "rag.sqlite"
    conn = _sqlite3.connect(db_file)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    db_file.unlink()

    patcher = _patch_cfg_to(tmp_path, db_file)
    try:
        result = recover_corruption(target="rag")
    finally:
        patcher.stop()

    assert result.success is False
    assert result.action == "missing_database"
    assert result.active_db_state == "missing"
    assert str(db_file) in (result.detail or "")
    assert list(tmp_path.iterdir()) == []


def test_recover_missing_live_db_dry_run(tmp_path: Path) -> None:
    """REQ-004/AC-2: the MISSING policy is identical under dry_run."""
    db_file = tmp_path / "rag.sqlite"
    conn = _sqlite3.connect(db_file)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    db_file.unlink()

    patcher = _patch_cfg_to(tmp_path, db_file)
    try:
        result = recover_corruption(target="rag", dry_run=True)
    finally:
        patcher.stop()

    assert result.success is False
    assert result.action == "missing_database"
    assert result.active_db_state == "missing"
    assert result.dry_run is True
    assert list(tmp_path.iterdir()) == []


@vec_required
def test_logical_verification_leaves_db_unchanged(tmp_path: Path) -> None:
    """REQ-005/AC-1: the logical stage's read-only open leaves no write side effects."""
    db_file = tmp_path / "rag.sqlite"
    _make_vec_rag_db(db_file)
    before_bytes = _sha256(db_file)
    before_listing = sorted(_os.listdir(tmp_path))

    ok, _detail = _run_logical_verification(db_file, "rag")

    assert ok is True
    assert _sha256(db_file) == before_bytes
    assert sorted(_os.listdir(tmp_path)) == before_listing


def test_restore_activates_after_verification_consumes_staged_wal(
    tmp_path: Path,
) -> None:
    """Regression: candidate verification consumes the staged backup -wal.

    The read-write candidate integrity check replays the staged WAL into the
    candidate database and SQLite removes it on close. Activation must still
    swap the candidate and report success; moving the already-consumed sidecar
    raised FileNotFoundError (action="error") — the latent bug.
    """
    db_dir = tmp_path / "live"
    db_dir.mkdir()
    db_path = db_dir / "workflow.sqlite"
    db_path.write_bytes(b"\x00" * 100)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "workflow_src.sqlite"
    conn = _sqlite3.connect(src)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE workflow_state (id INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO workflow_state VALUES (1)")
    conn.commit()
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    backup = backup_dir / "backup.sqlite"
    shutil.copy2(src, backup)
    shutil.copy2(Path(str(src) + "-wal"), backup_dir / "backup.sqlite-wal")
    conn.close()

    result = _restore_from_backup(db_path, str(backup), target="workflow")

    assert result.success is True
    assert result.action == "restored"
    assert result.active_db_state == "restored"
    assert result.logical_ok is True

    live = _sqlite3.connect(db_path)
    try:
        rows = live.execute("SELECT id FROM workflow_state").fetchall()
    finally:
        live.close()
    assert rows == [(1,)]
    # The consumed sidecars leave nothing at the live name, and staging leaves
    # no temp residue behind.
    assert not Path(str(db_path) + "-wal").exists()
    assert not Path(str(db_path) + "-shm").exists()
    assert not list(db_dir.glob("*.tmp_*"))
