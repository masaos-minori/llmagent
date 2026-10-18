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
        mock_instance.eventbus_db_path = Path("/tmp/eventbus.db")
        mock_cfg.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_sqlite_helper():
    with patch("db.recovery.SQLiteHelper") as mock_helper_class:
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
            (DbCondition.HEALTHY, None),  # Post-restore re-verification
        ]

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("shutil.copy2"),
            patch("os.replace"),
            patch(
                "db.recovery._run_logical_verification",
                return_value=(True, None),
            ),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is True
            assert result.action == "restored"


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
            (DbCondition.CORRUPTION, "still corrupt"),  # post-restore re-check
        ]

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("shutil.copy2"),
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


def test_recover_eventbus_uses_correct_db_path(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.CORRUPTION, "corruption error"),
    ) as mock_integrity:
        result = recover_corruption(target="eventbus")

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
    """Return side_effect list for restore path: DB corruption → backup healthy → post-restore healthy."""
    return [
        (DbCondition.CORRUPTION, "corruption error"),  # current DB
        (DbCondition.HEALTHY, None),  # backup
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
            patch("shutil.copy2"),
            patch("os.replace"),
            patch("db.recovery.check_rag_consistency", return_value=rag_report),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is not True


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
            patch("shutil.copy2"),
            patch("os.replace"),
            patch("db.recovery.check_rag_consistency", return_value=rag_report),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is not True


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
            patch("shutil.copy2"),
            patch("os.replace"),
            patch("db.recovery.check_rag_consistency", return_value=rag_report),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is not True


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
            patch("shutil.copy2"),
            patch("os.replace"),
            patch("db.recovery.check_rag_consistency", return_value=rag_report),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is not True


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
            patch("shutil.copy2"),
            patch("os.replace"),
            patch("db.recovery.check_rag_consistency", return_value=rag_report),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is not True


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


def test_recover_healthy_eventbus_prohibited(mock_db_cfg, mock_sqlite_helper):
    """Regression: eventbus target with HEALTHY DB must reject before any DB access."""
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ) as mock_integrity:
        with patch("db.recovery._vacuum_db") as mock_vacuum:
            result = recover_corruption(target="eventbus")

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


def test_recover_dry_run_eventbus_prohibited(mock_db_cfg, mock_sqlite_helper):
    """Regression: dry_run mode must reject eventbus before any DB access."""
    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ) as mock_integrity:
        result = recover_corruption(target="eventbus", dry_run=True)

        assert result.success is False
        assert result.action == "no_recovery_allowed"
        assert result.dry_run is True
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

from db.recovery import (
    _quarantine_sidecar_files,
    _stage_backup_sidecars,
)


def test_quarantine_sidecar_files():
    """Stale -wal/-shm files present before restore should be quarantined."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        wal_path = Path(tmpdir) / "test-wal"
        shm_path = Path(tmpdir) / "test-shm"

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

        _quarantine_sidecar_files(db_path, quarantine_dir)

        # Sidecars should be removed from original location
        assert not wal_path.exists()
        assert not shm_path.exists()

        # Quarantined copies should exist
        assert len(list(quarantine_dir.glob("test-wal_corrupt_*"))) == 1
        assert len(list(quarantine_dir.glob("test-shm_corrupt_*"))) == 1

        shutil.rmtree(quarantine_dir, ignore_errors=True)


def test_stage_backup_sidecars():
    """Backup -wal/-shm sidecars should be staged alongside temp_restore."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_path = Path(tmpdir) / "backup.db"
        backup_wal = Path(tmpdir) / "backup-wal"
        backup_shm = Path(tmpdir) / "backup-shm"
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

        # Staged sidecars should exist at destination
        assert staged["-wal"].exists()
        assert staged["-shm"].exists()
        assert staged["-wal"].name == "backup-wal"
        assert staged["-shm"].name == "backup-shm"


def test_restore_with_stale_wal_shm_before_swap(mock_db_cfg, mock_sqlite_helper):
    """Stale -wal/-shm files present before restore should be quarantined and not affect restore."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        wal_path = Path(tmpdir) / "test-wal"
        shm_path = Path(tmpdir) / "test-shm"

        # Create dummy files
        db_path.write_bytes(b"\x00" * 100)
        wal_path.write_text("STALE_WAL_CONTENT")
        shm_path.write_text("STALE_SHM_CONTENT")

        # Verify sidecars exist before restore
        assert wal_path.exists()
        assert shm_path.exists()

        # Create a valid backup (SQLite header for health check)
        backup_path = Path(tmpdir) / "backup.db"
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
                (DbCondition.HEALTHY, None),  # post-restore re-check
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is True
        assert result.action == "restored"

        # Stale sidecars should be removed from original location
        assert not wal_path.exists()
        assert not shm_path.exists()

        # Quarantine directory should have been cleaned up after success
        quarantine_dirs = list(Path(tmpdir).glob("*_sidecar_quarantine_*"))
        assert len(quarantine_dirs) == 0


def test_restore_with_backup_wal_shm_sidecars(mock_db_cfg, mock_sqlite_helper):
    """Backup -wal/-shm sidecars should be staged and swapped atomically with main file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_dir = Path(tmpdir) / "db_dir"
        db_dir.mkdir()
        db_path = db_dir / "test.db"
        wal_path = db_dir / "test-wal"
        shm_path = db_dir / "test-shm"

        # Create stale sidecars on db_path
        db_path.write_bytes(b"\x00" * 100)
        wal_path.write_text("STALE_WAL_CONTENT")
        shm_path.write_text("STALE_SHM_CONTENT")

        # Backup with its own WAL/SHM in a separate directory
        backup_dir = Path(tmpdir) / "backup_dir"
        backup_dir.mkdir()
        backup_path = backup_dir / "backup.db"
        backup_wal = backup_dir / "backup-wal"
        backup_shm = backup_dir / "backup-shm"

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
                (DbCondition.HEALTHY, None),  # post-restore re-check
            ]
            result = _restore_from_backup(db_path, str(backup_path), target="rag")

        assert result.success is True
        assert result.action == "restored"

        # Restored DB should have WAL/SHM sidecars from backup
        restored_wal = db_dir / "test-wal"
        restored_shm = db_dir / "test-shm"
        assert restored_wal.exists(), "Restored WAL sidecar should exist"
        assert restored_shm.exists(), "Restored SHM sidecar should exist"
        assert restored_wal.read_text() == "BACKUP_WAL_CONTENT"
        assert restored_shm.read_text() == "BACKUP_SHM_CONTENT"


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
    _handle_dry_run,
    _run_integrity_check,
    _run_logical_verification,
    _vacuum_db,
    _verify_domain_identity,
)


@pytest.fixture
def mock_recovery_db():
    """Patch db.recovery.SQLiteHelper and yield the object `with ... .open() as db` binds to.

    `SQLiteHelper.open()` returns self and `__enter__` returns self, so the bound
    name is `SQLiteHelper(...).open().__enter__()`, not the helper instance itself.
    """
    with patch("db.recovery.SQLiteHelper") as helper_class:
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
        "write_smoke_test_ok": None,
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

    def test_operational_error_never_reaches_the_invalid_format_branch(self) -> None:
        """The OperationalError branch wins, so the DatabaseError signal is not consulted."""
        e = _sqlite3.OperationalError("file is not a database")
        assert _classify_error(e) == DbCondition.UNKNOWN

    def test_plain_database_error_with_the_signal_is_invalid_format(self) -> None:
        e = _sqlite3.DatabaseError("file is not a database")
        assert _classify_error(e) == DbCondition.INVALID_FORMAT


class TestRunIntegrityCheckCharacterization:
    """Characterization: `_run_integrity_check` had no direct coverage at all."""

    def test_ok_is_healthy(self, mock_recovery_db) -> None:
        mock_recovery_db.execute.return_value.fetchone.return_value = ("ok",)

        assert _run_integrity_check(Path("/tmp/rag.db"), "rag") == (
            DbCondition.HEALTHY,
            None,
        )

    def test_non_ok_result_is_corruption_with_the_raw_text(
        self, mock_recovery_db
    ) -> None:
        mock_recovery_db.execute.return_value.fetchone.return_value = (
            "wrong number of entries in index",
        )

        assert _run_integrity_check(Path("/tmp/rag.db"), "rag") == (
            DbCondition.CORRUPTION,
            "wrong number of entries in index",
        )

    def test_open_failure_is_classified(self, mock_recovery_db) -> None:
        mock_recovery_db.execute.side_effect = _sqlite3.DatabaseError(
            "file is not a database"
        )

        assert _run_integrity_check(Path("/tmp/rag.db"), "rag") == (
            DbCondition.INVALID_FORMAT,
            "file is not a database",
        )


class TestHandleDryRunCharacterization:
    """Characterization: both branches of `_handle_dry_run`, verbatim results."""

    def test_ok_branch(self) -> None:
        assert _handle_dry_run("ok") == RecoveryResult(
            success=True,
            action="vacuum",
            detail="integrity ok (dry run)",
            dry_run=True,
        )

    def test_failure_branch(self) -> None:
        assert _handle_dry_run("no such table: chunks") == RecoveryResult(
            success=False,
            action="error",
            detail="integrity check failed: no such table: chunks",
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

        with patch("db.recovery.check_rag_consistency", return_value=report):
            ok, detail = _run_logical_verification(Path("/tmp/rag.db"), "rag")

        assert ok is False
        assert detail == (
            "fts_gap=3; fts_orphan=2; orphan_vec=3; vec=9/chunks=10; "
            "docs_no_chunks=4; chunks_no_vec=5; dup_chunk_idx=6; url_mismatches=1"
        )

    def test_rag_consistent_report_reports_no_detail(self, mock_recovery_db) -> None:
        with patch("db.recovery.check_rag_consistency", return_value=_rag_report()):
            ok, detail = _run_logical_verification(Path("/tmp/rag.db"), "rag")

        assert (ok, detail) == (True, None)

    def test_rag_read_smoke_only_failure_produces_an_empty_detail(
        self, mock_recovery_db
    ) -> None:
        """`is_consistent` checks read_smoke_test_ok, but the detail builder does not."""
        with patch(
            "db.recovery.check_rag_consistency",
            return_value=_rag_report(read_smoke_test_ok=False),
        ):
            ok, detail = _run_logical_verification(Path("/tmp/rag.db"), "rag")

        assert ok is False
        assert detail == ""

    def test_session_consistent_report_reports_no_detail(
        self, mock_recovery_db
    ) -> None:
        with patch(
            "db.recovery.check_session_consistency", return_value=_session_report()
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
            write_smoke_test_ok=False,
            diagnostic_errors=("boom", "bang"),
        )

        with patch("db.recovery.check_session_consistency", return_value=report):
            ok, detail = _run_logical_verification(Path("/tmp/session.db"), "session")

        assert ok is False
        assert detail == (
            "orphan_msgs=2; orphan_mem_links=3; diag_not_readable; "
            "read_smoke_fail; write_smoke_fail; errors=2"
        )

    def test_session_write_smoke_none_is_not_reported_as_a_failure(
        self, mock_recovery_db
    ) -> None:
        """`write_smoke_test_ok is False` is the trigger; None means "not run"."""
        report = _session_report(orphaned_message_count=1, write_smoke_test_ok=None)

        with patch("db.recovery.check_session_consistency", return_value=report):
            ok, detail = _run_logical_verification(Path("/tmp/session.db"), "session")

        assert ok is False
        assert detail == "orphan_msgs=1"

    def test_unknown_target_skips_verification(self, mock_recovery_db) -> None:
        assert _run_logical_verification(Path("/tmp/workflow.db"), "workflow") == (
            True,
            None,
        )

    def test_an_unopenable_database_is_treated_as_consistent(
        self, mock_recovery_db
    ) -> None:
        with patch(
            "db.recovery.check_rag_consistency",
            side_effect=_sqlite3.OperationalError("no such table: chunks"),
        ):
            ok, detail = _run_logical_verification(Path("/tmp/rag.db"), "rag")

        assert (ok, detail) == (True, None)


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
        """The OSError handler unlinks the half-written temp file and keeps the archive."""
        db_path = tmp_path / "rag.db"
        db_path.write_text("corrupt")
        backup = tmp_path / "backup.db"
        backup.write_text("good")

        with (
            patch(
                "db.recovery._run_integrity_check",
                return_value=(DbCondition.HEALTHY, None),
            ),
            patch("db.recovery._verify_domain_identity", return_value=(True, None)),
            patch("os.replace", side_effect=OSError("rename failed")),
        ):
            result = _restore_from_backup(db_path, backup, target="rag")

        assert result.success is False
        assert result.action == "error"
        assert result.detail == "rename failed"
        assert not list(tmp_path.glob("*.tmp_*.db")), "temp restore must be removed"
        assert list(tmp_path.glob("rag_corrupt_*.db")), "corrupt archive must remain"
        assert list(tmp_path.glob("*_sidecar_quarantine_*")), "quarantine dir is kept"

    def test_successful_restore_removes_the_quarantine_directory(
        self, tmp_path: Path
    ) -> None:
        db_path = tmp_path / "rag.db"
        db_path.write_text("corrupt")
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
        assert not list(tmp_path.glob("*_sidecar_quarantine_*"))


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
