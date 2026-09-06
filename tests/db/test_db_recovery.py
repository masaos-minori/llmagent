from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.db.config import DbConfig
from scripts.db.recovery import DbCondition, recover_corruption


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
    ):
        result = recover_corruption(target="workflow")

        assert result.success is False
        assert result.action == "no_recovery_allowed"
        assert result.detail and "Automatic recovery is prohibited" in result.detail


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

        mock_integrity.assert_called_once_with(mock_db_cfg.workflow_db_path, "workflow")
        assert result.success is False
        assert result.action == "no_recovery_allowed"


def test_recover_eventbus_uses_correct_db_path(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.CORRUPTION, "corruption error"),
    ) as mock_integrity:
        result = recover_corruption(target="eventbus")

        mock_integrity.assert_called_once_with(mock_db_cfg.eventbus_db_path, "eventbus")
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
