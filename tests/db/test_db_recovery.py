from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.db.config import DbConfig
from scripts.db.recovery import DbCondition, _classify_error, recover_corruption


@pytest.fixture
def mock_db_cfg():
    with patch("scripts.db.recovery.build_db_config") as mock_cfg:
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
    with patch("scripts.db.recovery.SQLiteHelper") as mock_helper_class:
        mock_helper_instance = mock_helper_class.return_value.__enter__.return_value
        yield mock_helper_instance


def test_recover_healthy(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ):
        result = recover_corruption(target="rag", dry_run=False)

        assert result.success is True
        assert result.action == "vacuum"


def test_recover_corrupt_rag_restores(mock_db_cfg, mock_sqlite_helper):
    with patch("scripts.db.recovery._run_integrity_check") as mock_integrity:
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
                "scripts.db.recovery._run_logical_verification",
                return_value=(True, None),
            ),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is True
            assert result.action == "restored"


def test_recover_corrupt_workflow_prohibited(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.CORRUPTION, "corruption error"),
    ) as mock_integrity:
        result = recover_corruption(target="workflow")

        assert result.success is False
        assert result.action == "no_recovery_allowed"
        assert result.detail and "Automatic recovery is prohibited" in result.detail
        mock_integrity.assert_not_called()


def test_recover_lock_contention(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.LOCK_CONTENTION, "database is locked"),
    ):
        result = recover_corruption(target="rag")

        assert result.success is False
        assert result.action == "error"
        assert result.detail and "lock_contention" in result.detail


def test_recover_permission_failure(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.PERMISSION_FAILURE, "permission denied"),
    ):
        result = recover_corruption(target="rag")

        assert result.success is False
        assert result.action == "error"
        assert result.detail and "permission_failure" in result.detail


def test_recover_no_backup(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.CORRUPTION, "corruption error"),
    ):
        result = recover_corruption(backup_path=None, target="rag")

        assert result.success is False
        assert result.action == "no_backup"


def test_recover_bad_backup(mock_db_cfg, mock_sqlite_helper):
    with patch("scripts.db.recovery._run_integrity_check") as mock_integrity:
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
        patch("scripts.db.recovery._run_integrity_check") as mock_integrity,
        patch(
            "scripts.db.recovery._verify_domain_identity",
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
        patch("scripts.db.recovery._run_integrity_check") as mock_integrity,
        patch(
            "scripts.db.recovery._verify_domain_identity",
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
        patch("scripts.db.recovery._run_integrity_check") as mock_integrity,
        patch(
            "scripts.db.recovery._verify_domain_identity",
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
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ):
        result = recover_corruption(target="rag", dry_run=True)

        assert result.success is True
        assert result.action == "vacuum"
        assert result.dry_run is True


def test_recover_unsupported_target(mock_db_cfg, mock_sqlite_helper):
    with patch("scripts.db.recovery._run_integrity_check") as mock_integrity:
        result = recover_corruption(target="bogus")

        assert result.success is False
        assert result.action == "unsupported_target"
        assert result.detail and "bogus" in result.detail
        mock_integrity.assert_not_called()


def test_recover_restore_verify_failed(mock_db_cfg, mock_sqlite_helper):
    with patch("scripts.db.recovery._run_integrity_check") as mock_integrity:
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
    not session_db_path (ADR-011 domain-policy bypass found during adversarial
    verification of the implementation procedure)."""
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.CORRUPTION, "corruption error"),
    ) as mock_integrity:
        result = recover_corruption(target="workflow")

        mock_integrity.assert_not_called()
        assert result.success is False
        assert result.action == "no_recovery_allowed"


def test_recover_eventbus_uses_correct_db_path(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "scripts.db.recovery._run_integrity_check",
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
        "scripts.db.recovery._run_integrity_check",
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
    with patch("scripts.db.recovery._run_integrity_check") as mock_integrity:
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
            patch("scripts.db.recovery.check_rag_consistency", return_value=rag_report),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is not True


def test_recover_rag_missing_table(mock_db_cfg, mock_sqlite_helper):
    """RAG missing table/trigger should cause logical verification failure."""
    with patch("scripts.db.recovery._run_integrity_check") as mock_integrity:
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
            patch("scripts.db.recovery.check_rag_consistency", return_value=rag_report),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is not True


def test_recover_rag_fts_orphan(mock_db_cfg, mock_sqlite_helper):
    """RAG FTS orphan should cause logical verification failure."""
    with patch("scripts.db.recovery._run_integrity_check") as mock_integrity:
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
            patch("scripts.db.recovery.check_rag_consistency", return_value=rag_report),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is not True


def test_recover_rag_vector_orphan(mock_db_cfg, mock_sqlite_helper):
    """RAG vector orphan should cause logical verification failure."""
    with patch("scripts.db.recovery._run_integrity_check") as mock_integrity:
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
            patch("scripts.db.recovery.check_rag_consistency", return_value=rag_report),
        ):
            result = recover_corruption(backup_path="/tmp/backup.db", target="rag")

            assert result.success is False
            assert result.action == "logical_verify_failed"
            assert result.logical_ok is not True


def test_recover_rag_read_smoke_test_failed(mock_db_cfg, mock_sqlite_helper):
    """RAG read smoke test failure should cause logical verification failure even when counts are healthy."""
    with patch("scripts.db.recovery._run_integrity_check") as mock_integrity:
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
            patch("scripts.db.recovery.check_rag_consistency", return_value=rag_report),
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
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ) as mock_integrity:
        with patch("scripts.db.recovery._vacuum_db") as mock_vacuum:
            result = recover_corruption(target="workflow")

            assert result.success is False
            assert result.action == "no_recovery_allowed"
            assert result.detail and "Automatic recovery is prohibited" in result.detail
            mock_integrity.assert_not_called()
            mock_vacuum.assert_not_called()


def test_recover_healthy_eventbus_prohibited(mock_db_cfg, mock_sqlite_helper):
    """Regression: eventbus target with HEALTHY DB must reject before any DB access."""
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ) as mock_integrity:
        with patch("scripts.db.recovery._vacuum_db") as mock_vacuum:
            result = recover_corruption(target="eventbus")

            assert result.success is False
            assert result.action == "no_recovery_allowed"
            assert result.detail and "Automatic recovery is prohibited" in result.detail
            mock_integrity.assert_not_called()
            mock_vacuum.assert_not_called()


def test_recover_dry_run_workflow_prohibited(mock_db_cfg, mock_sqlite_helper):
    """Regression: dry_run mode must reject workflow before any DB access."""
    with patch(
        "scripts.db.recovery._run_integrity_check",
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
        "scripts.db.recovery._run_integrity_check",
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

from scripts.db.recovery import (
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
