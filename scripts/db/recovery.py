#!/usr/bin/env python3
"""scripts/db/recovery.py — Corruption recovery operations."""

import logging
import shutil
import sqlite3
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path

from db.config import build_db_config, format_timestamp
from db.helper import SQLiteHelper
from db.models import (
    RagConsistencyReport,
    RecoveryResult,
    SessionConsistencyReport,
)
from db.rag_consistency import check_rag_consistency
from db.rag_consistency import is_consistent as rag_is_consistent
from db.recovery_restore import (
    _resolve_backup,
    _stage_restore,
)
from db.session_consistency import (
    check_session_consistency,
)
from db.session_consistency import (
    is_consistent as session_is_consistent,
)

logger = logging.getLogger(__name__)


class DbCondition(StrEnum):
    """Classification of database state/failure."""

    HEALTHY = "healthy"
    CORRUPTION = "corruption"
    LOCK_CONTENTION = "lock_contention"
    PERMISSION_FAILURE = "permission_failure"
    INVALID_FORMAT = "invalid_format"
    UNKNOWN = "unknown"


# sqlite_errorcode -> condition for the failures SQLite identifies by code
# (5/6 = SQLITE_BUSY / SQLITE_LOCKED, 8 = SQLITE_READONLY).
_ERRORCODE_CONDITIONS: dict[int, DbCondition] = {
    5: DbCondition.LOCK_CONTENTION,
    6: DbCondition.LOCK_CONTENTION,
    8: DbCondition.PERMISSION_FAILURE,
}

# Message fallbacks, in priority order, for the conditions error codes do not cover.
_MESSAGE_CONDITIONS: tuple[tuple[tuple[str, ...], DbCondition], ...] = (
    (("database is locked", "busy"), DbCondition.LOCK_CONTENTION),
    (("permission denied", "readonly"), DbCondition.PERMISSION_FAILURE),
)

# Signal the SQLite C library reports when the file is not a database at all.
_INVALID_FORMAT_SIGNAL = "file is not a database"


def _classify_operational_error(e: sqlite3.OperationalError) -> DbCondition:
    """Classify an OperationalError: error code first, message substrings second."""
    errcode: int | None = getattr(e, "sqlite_errorcode", None)
    if errcode is not None and errcode in _ERRORCODE_CONDITIONS:
        return _ERRORCODE_CONDITIONS[errcode]
    msg = str(e).lower()
    for tokens, condition in _MESSAGE_CONDITIONS:
        if any(token in msg for token in tokens):
            return condition
    return DbCondition.UNKNOWN


def _classify_error(e: Exception) -> DbCondition:
    """Classify a caught exception into a DbCondition.

    Uses sqlite_errorcode where available (Python 3.14+), falling back to
    substring matching for conditions not covered by error codes.
    Priority: INVALID_FORMAT via message > lock/permission via error code >
    CORRUPTION > UNKNOWN.

    The INVALID_FORMAT signal is checked for every sqlite3 error, OperationalError
    included: SQLite raises an OperationalError when it reads the header of a file
    that is not a database, and classifying that as UNKNOWN would hide the reason
    the file cannot be opened.
    """
    if isinstance(e, (sqlite3.Error, ValueError)) and _INVALID_FORMAT_SIGNAL in str(e):
        return DbCondition.INVALID_FORMAT
    if isinstance(e, sqlite3.OperationalError):
        return _classify_operational_error(e)
    if isinstance(e, (sqlite3.DatabaseError, ValueError)):
        return DbCondition.CORRUPTION
    return DbCondition.UNKNOWN


def _run_integrity_check(
    db_path: Path, target: str = "rag"
) -> tuple[DbCondition, str | None]:
    """Open DB and run PRAGMA integrity_check; returns (condition, error_detail).

    Returns (DbCondition.HEALTHY, None) if the DB is healthy.
    """
    try:
        with SQLiteHelper(target, db_path=str(db_path)).open() as db:
            cursor = db.execute("PRAGMA integrity_check")
            result = str(cursor.fetchone()[0])
            if result == "ok":
                return DbCondition.HEALTHY, None
            else:
                return DbCondition.CORRUPTION, result
    except Exception as e:  # noqa: BLE001 — intentional broad catch for _classify_error dispatch
        return _classify_error(e), str(e)


def _dry_run_integrity_ok() -> RecoveryResult:
    """Return the dry_run result reported when the integrity check reports HEALTHY."""
    return RecoveryResult(
        success=True,
        action="vacuum",
        detail="integrity ok (dry run)",
        dry_run=True,
    )


def _failure(action: str, detail: str | None, dry_run: bool) -> RecoveryResult:
    """Build the failed RecoveryResult every recovery guard reports."""
    return RecoveryResult(success=False, action=action, detail=detail, dry_run=dry_run)


def _rag_inconsistency_detail(report: RagConsistencyReport) -> str:
    """Summarize a rag report's inconsistencies as counts/identifiers only (REQ-010/AC-7).

    Entries are listed in the order `check_rag_consistency` computes them. An empty
    string means the inconsistency came from a check this summary does not name
    (read smoke test, diagnostic errors).
    """
    mismatches = report.url_level_mismatches or {}
    entries: list[tuple[bool, str]] = [
        (report.fts_gap > 0, f"fts_gap={report.fts_gap}"),
        (report.fts_orphan_count > 0, f"fts_orphan={report.fts_orphan_count}"),
        (report.orphan_vec_count > 0, f"orphan_vec={report.orphan_vec_count}"),
        (report.vec != report.chunks, f"vec={report.vec}/chunks={report.chunks}"),
        (
            report.documents_without_chunks_count > 0,
            f"docs_no_chunks={report.documents_without_chunks_count}",
        ),
        (
            report.chunks_without_vec_count > 0,
            f"chunks_no_vec={report.chunks_without_vec_count}",
        ),
        (
            report.duplicate_chunk_index_count > 0,
            f"dup_chunk_idx={report.duplicate_chunk_index_count}",
        ),
        (bool(mismatches), f"url_mismatches={len(mismatches)}"),
    ]
    return "; ".join(text for include, text in entries if include)


def _session_inconsistency_detail(report: SessionConsistencyReport) -> str:
    """Summarize a session report's inconsistencies as counts/identifiers only (REQ-010/AC-7).

    `write_smoke_test_ok is False` is the only trigger for the write-smoke entry:
    None means the test was not run, which is not an inconsistency.
    """
    errors = report.diagnostic_errors or ()
    entries: list[tuple[bool, str]] = [
        (
            report.orphaned_message_count > 0,
            f"orphan_msgs={report.orphaned_message_count}",
        ),
        (
            report.orphaned_memory_link_count > 0,
            f"orphan_mem_links={report.orphaned_memory_link_count}",
        ),
        (not report.session_diagnostics_readable, "diag_not_readable"),
        (not report.read_smoke_test_ok, "read_smoke_fail"),
        (report.write_smoke_test_ok is False, "write_smoke_fail"),
        (bool(errors), f"errors={len(errors)}"),
    ]
    return "; ".join(text for include, text in entries if include)


def _verify_rag_logic(db: SQLiteHelper) -> tuple[bool, str | None]:
    """Return (consistent, count-only detail) for the rag domain."""
    report = check_rag_consistency(db)
    if rag_is_consistent(report):
        return True, None
    return False, _rag_inconsistency_detail(report)


def _verify_session_logic(db: SQLiteHelper) -> tuple[bool, str | None]:
    """Return (consistent, count-only detail) for the session domain."""
    report = check_session_consistency(db)
    if session_is_consistent(report):
        return True, None
    return False, _session_inconsistency_detail(report)


# Logical verifiers by target. A target missing from this table skips logical
# verification entirely: no consistency contract is defined for it.
_LOGICAL_VERIFIERS: dict[str, Callable[[SQLiteHelper], tuple[bool, str | None]]] = {
    "rag": _verify_rag_logic,
    "session": _verify_session_logic,
}


def _run_logical_verification(db_path: Path, target: str) -> tuple[bool, str | None]:
    """Run logical consistency verification on the restored database.

    Returns (consistent, detail_string) — detail contains a short summary
    of counts/identifiers only (no row content), matching REQ-010/AC-7.

    An unknown target, or a database this stage cannot open, is reported as
    consistent: a verification gap must never block a completed physical restore.
    """
    verify = _LOGICAL_VERIFIERS.get(target)
    if verify is None:
        return True, None
    try:
        with SQLiteHelper(target, db_path=str(db_path)).open() as db:
            return verify(db)
    except sqlite3.Error as e:
        logger.warning("Logical verification could not open DB: %s", e)
        return True, None


def _vacuum_db(target: str = "rag") -> RecoveryResult:
    """Run VACUUM on target DB and return result; returns success=False on failure."""
    logger.info("Integrity check passed; running VACUUM")
    try:
        with SQLiteHelper(target).open(write_mode=True) as db:
            db.vacuum()
    except (sqlite3.OperationalError, RuntimeError) as e:
        logger.error("VACUUM failed: %s", e)
        return RecoveryResult(success=False, action="vacuum_failed", detail=str(e))
    return RecoveryResult(success=True, action="vacuum")


_REQUIRED_TABLE_BY_DOMAIN: dict[str, str] = {
    "rag": "documents",
    "session": "sessions",
}


def _verify_domain_identity(backup: Path, target: str) -> tuple[bool, str | None]:
    """Verify backup contains the required table for target's domain.

    Returns (True, None) if the domain's required table is present in the backup's
    sqlite_master; (False, detail) otherwise. Unknown/unmapped targets pass through
    (no domain-identity constraint defined for them).
    """
    required_table = _REQUIRED_TABLE_BY_DOMAIN.get(target)
    if required_table is None:
        return True, None
    with SQLiteHelper(target, db_path=str(backup)).open() as db:
        cursor = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (required_table,),
        )
        if cursor.fetchone() is None:
            return False, (
                f"backup missing required table '{required_table}' for "
                f"domain '{target}'"
            )
    return True, None


def _backup_is_usable(backup: Path, target: str) -> tuple[str | None, str]:
    """Return (failed_action, detail) for the checks a backup must pass before it is copied in.

    (None, "") means the backup may replace the target database.
    """
    # 1. Verify backup integrity
    integrity_condition, integrity_error = _run_integrity_check(backup, target)
    if integrity_condition != DbCondition.HEALTHY:
        err = integrity_error or f"backup integrity check failed: {integrity_condition}"
        logger.error("Backup is also corrupt: %s", err)
        return "bad_backup", err

    try:
        domain_ok, domain_error = _verify_domain_identity(backup, target)
    except sqlite3.Error as e:
        # The check opens the backup, so a sqlite3.Error here means the backup cannot
        # be read. recover_corruption() wraps only OSError, and that try block starts
        # after this check, so an uncaught sqlite3.Error would escape to the caller
        # instead of reporting a failed recovery.
        logger.error("Backup domain-identity check failed: %s", e)
        return "bad_backup", f"domain-identity check failed: {e}"
    if not domain_ok:
        err = domain_error or f"backup failed domain-identity check for target={target}"
        logger.error("Backup belongs to a different persistence domain: %s", err)
        return "backup_wrong_domain", err

    return None, ""


def _post_restore_failure(
    db_path: Path, target: str, dry_run: bool
) -> RecoveryResult | None:
    """Return the failure result for a post-restore check, or None when both pass.

    The physical re-check runs before the logical-verification stage, which is the
    order the restore reports them in.
    """
    post_condition, post_detail = _run_integrity_check(db_path, target)
    if post_condition != DbCondition.HEALTHY:
        detail = (
            post_detail
            or f"post-restore integrity check failed: {post_condition.value}"
        )
        logger.error("Post-restore integrity check failed: %s", detail)
        return _failure("restore_verify_failed", detail, dry_run)

    logical_ok, logical_detail = _run_logical_verification(db_path, target)
    if not logical_ok:
        err_detail = logical_detail or f"logical verification failed: {target}"
        logger.error("Post-restore logical verification failed: %s", err_detail)
        return _failure("logical_verify_failed", err_detail, dry_run)

    return None


def _restore_from_backup(
    db_path: Path,
    backup_path: str | Path | None,
    target: str = "rag",
    dry_run: bool = False,
) -> RecoveryResult:
    """Restore DB from backup; returns RecoveryResult."""
    backup, detail = _resolve_backup(backup_path)
    if backup is None:
        return _failure("no_backup", detail, dry_run)

    action, detail = _backup_is_usable(backup, target)
    if action is not None:
        return _failure(action, detail, dry_run)

    ts = format_timestamp()
    corrupt_archive = db_path.with_name(f"{db_path.stem}_corrupt_{ts}{db_path.suffix}")
    temp_restore = db_path.with_name(f"{db_path.stem}.tmp_{ts}{db_path.suffix}")
    quarantine_dir = db_path.parent / f"{db_path.stem}_sidecar_quarantine_{ts}"

    try:
        _stage_restore(db_path, backup, corrupt_archive, temp_restore, quarantine_dir)

        failure = _post_restore_failure(db_path, target, dry_run)
        if failure is not None:
            return failure

        logger.info("DB restored from backup: %s", backup)
        # Cleanup quarantine directory after successful restore
        shutil.rmtree(quarantine_dir, ignore_errors=True)
        return RecoveryResult(
            success=True, action="restored", detail=str(backup), dry_run=dry_run
        )
    except OSError as e:
        logger.error("Recovery failed: %s", e)
        if temp_restore.exists():
            temp_restore.unlink()
        return _failure("error", str(e), dry_run)


# Conditions that must not trigger a restore: they report action="error" instead.
_NO_RESTORE_CONDITIONS: frozenset[DbCondition] = frozenset(
    {
        DbCondition.LOCK_CONTENTION,
        DbCondition.PERMISSION_FAILURE,
        DbCondition.INVALID_FORMAT,
    }
)


def _result_for_condition(
    condition: DbCondition, detail: str | None, target: str, dry_run: bool
) -> RecoveryResult | None:
    """Map an integrity-check condition to the result that ends recovery here.

    Returns None only for CORRUPTION: the caller owns the restore attempt.
    """
    if condition == DbCondition.HEALTHY:
        if dry_run:
            return _dry_run_integrity_ok()
        return _vacuum_db(target)

    if condition in _NO_RESTORE_CONDITIONS:
        return _failure("error", f"{condition.value}: {detail}", dry_run)

    if condition == DbCondition.UNKNOWN:
        return _failure(
            "preserved_operator_intervention_required",
            f"Unknown integrity-check failure ({detail}): operator intervention required",
            dry_run,
        )

    return None


def recover_corruption(
    backup_path: str | Path | None = None,
    *,
    target: str = "rag",
    dry_run: bool = False,
) -> RecoveryResult:
    """Detect and recover from corruption in the target DB; returns RecoveryResult.

    target: "rag" (default), "session", "workflow", or "eventbus".
    action values:
      "vacuum"                              — integrity ok; VACUUM executed (or skipped in dry_run)
      "vacuum_failed"                       — integrity ok but VACUUM raised
      "restored"                            — integrity failed; DB restored from backup_path
      "no_backup"                           — integrity failed; no usable backup_path
      "restore_verify_failed"               — restored from backup, but post-restore integrity
                                                check failed
      "logical_verify_failed"               — restored from backup, but post-restore logical
                                                verification failed
      "unsupported_target"                  — target is not one of "rag"/"session"/"workflow"/
                                                "eventbus"
      "error"                               — could not open DB or OS-level failure
      "no_recovery_allowed"                 — automatic recovery prohibited for workflow/eventbus
      "preserved_operator_intervention_required" — integrity check returned an unclassifiable result; DB preserved, operator intervention required
    """
    db_cfg = build_db_config()
    target_db_path = getattr(db_cfg, f"{target}_db_path", None)
    if target_db_path is None:
        return RecoveryResult(
            success=False,
            action="unsupported_target",
            detail=f"unsupported target: {target!r}",
            dry_run=dry_run,
        )

    # Domain policy check — moved here, before _run_integrity_check()
    if target in ("workflow", "eventbus"):
        # ADR-008 recovery policy: workflow/eventbus require an explicit operator decision
        return RecoveryResult(
            success=False,
            action="no_recovery_allowed",
            detail=f"Automatic recovery is prohibited for {target}. Manual intervention required.",
            dry_run=dry_run,
        )

    db_path = Path(target_db_path)
    condition, detail = _run_integrity_check(db_path, target)

    result = _result_for_condition(condition, detail, target, dry_run)
    if result is not None:
        return result

    # It's CORRUPTION
    if dry_run:
        return _failure(
            "error", f"Integrity failure ({condition.value}): {detail}", True
        )

    # For rag and session, we attempt restoration
    return _restore_from_backup(db_path, backup_path, target=target, dry_run=dry_run)
