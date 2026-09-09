#!/usr/bin/env python3
"""scripts/db/recovery.py — Corruption recovery operations."""

import logging
import os
import shutil
import sqlite3
import time
from enum import StrEnum
from pathlib import Path

from db.config import build_db_config, format_timestamp
from db.helper import SQLiteHelper
from db.models import RecoveryResult
from db.rag_consistency import check_rag_consistency
from db.rag_consistency import is_consistent as rag_is_consistent
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


def _classify_error(e: Exception) -> DbCondition:
    """Classify a caught exception into a DbCondition.

    Uses sqlite_errorcode where available (Python 3.14+), falling back to
    substring matching for conditions not covered by error codes.
    Priority: lock/permission via error code > INVALID_FORMAT via message >
    CORRUPTION > UNKNOWN.
    """
    if isinstance(e, sqlite3.OperationalError):
        # Lock/permission conditions: prefer error code over substring matching
        errcode = getattr(e, "sqlite_errorcode", None)
        if errcode is not None:
            if errcode in (5, 6):  # SQLITE_BUSY / SQLITE_LOCKED
                return DbCondition.LOCK_CONTENTION
            if errcode == 8:  # SQLITE_READONLY
                return DbCondition.PERMISSION_FAILURE
        # Substring fallback for lock/permission conditions
        msg = str(e).lower()
        if "database is locked" in msg or "busy" in msg:
            return DbCondition.LOCK_CONTENTION
        if "permission denied" in msg or "readonly" in msg:
            return DbCondition.PERMISSION_FAILURE
    elif isinstance(e, sqlite3.DatabaseError):
        # INVALID_FORMAT: "file is not a database" signal from SQLite C library
        if "file is not a database" in str(e):
            return DbCondition.INVALID_FORMAT
        return DbCondition.CORRUPTION
    elif isinstance(e, ValueError):
        # Same INVALID_FORMAT signal applies to ValueError
        if "file is not a database" in str(e):
            return DbCondition.INVALID_FORMAT
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


def _handle_dry_run(check_result: str) -> RecoveryResult:
    """Return appropriate RecoveryResult for dry_run mode."""
    if check_result == "ok":
        return RecoveryResult(
            success=True,
            action="vacuum",
            detail="integrity ok (dry run)",
            dry_run=True,
        )
    return RecoveryResult(
        success=False,
        action="error",
        detail=f"integrity check failed: {check_result}",
        dry_run=True,
    )


def _run_logical_verification(db_path: Path, target: str) -> tuple[bool, str | None]:
    """Run logical consistency verification on the restored database.

    Returns (consistent, detail_string) — detail contains a short summary
    of counts/identifiers only (no row content), matching REQ-010/AC-7.
    """
    try:
        with SQLiteHelper(target, db_path=str(db_path)).open() as db:
            if target == "rag":
                report = check_rag_consistency(db)
                consistent = rag_is_consistent(report)
                if not consistent:
                    parts: list[str] = []
                    if report.fts_gap > 0:
                        parts.append(f"fts_gap={report.fts_gap}")
                    if report.fts_orphan_count > 0:
                        parts.append(f"fts_orphan={report.fts_orphan_count}")
                    if report.orphan_vec_count > 0:
                        parts.append(f"orphan_vec={report.orphan_vec_count}")
                    if report.vec != report.chunks:
                        parts.append(f"vec={report.vec}/chunks={report.chunks}")
                    if report.documents_without_chunks_count > 0:
                        parts.append(
                            f"docs_no_chunks={report.documents_without_chunks_count}"
                        )
                    if report.chunks_without_vec_count > 0:
                        parts.append(f"chunks_no_vec={report.chunks_without_vec_count}")
                    if report.duplicate_chunk_index_count > 0:
                        parts.append(
                            f"dup_chunk_idx={report.duplicate_chunk_index_count}"
                        )
                    if report.url_level_mismatches:
                        parts.append(
                            f"url_mismatches={len(report.url_level_mismatches)}"
                        )
                    detail = "; ".join(parts)
                else:
                    detail = None
            elif target == "session":
                session_report = check_session_consistency(db)
                consistent = session_is_consistent(session_report)
                if not consistent:
                    session_parts: list[str] = []
                    if session_report.orphaned_message_count > 0:
                        session_parts.append(
                            f"orphan_msgs={session_report.orphaned_message_count}"
                        )
                    if session_report.orphaned_memory_link_count > 0:
                        session_parts.append(
                            f"orphan_mem_links={session_report.orphaned_memory_link_count}"
                        )
                    if not session_report.session_diagnostics_readable:
                        session_parts.append("diag_not_readable")
                    if not session_report.read_smoke_test_ok:
                        session_parts.append("read_smoke_fail")
                    if session_report.write_smoke_test_ok is False:
                        session_parts.append("write_smoke_fail")
                    if session_report.diagnostic_errors:
                        session_parts.append(
                            f"errors={len(session_report.diagnostic_errors)}"
                        )
                    detail = "; ".join(session_parts)
                else:
                    detail = None
            else:
                # Unknown target — skip logical verification
                return True, None
    except sqlite3.Error as e:
        logger.warning("Logical verification could not open DB: %s", e)
        return True, None
    return consistent, detail


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


def _quarantine_sidecar_files(db_path: Path, quarantine_dir: Path) -> None:
    """Quarantine pre-existing -wal/-shm sidecar files associated with db_path."""
    stem = db_path.stem
    ts = int(time.time())
    for suffix in ("-wal", "-shm"):
        sidecar = db_path.parent / f"{stem}{suffix}"
        if sidecar.exists():
            quarantine_name = f"{stem}{suffix}_corrupt_{ts}"
            quarantine_path = quarantine_dir / quarantine_name
            try:
                shutil.copy2(sidecar, quarantine_path)
                sidecar.unlink()
            except OSError:
                logger.warning(
                    "Failed to quarantine sidecar file %s; proceeding without it",
                    sidecar,
                )


def _stage_backup_sidecars(
    backup_path: Path, temp_restore_dir: Path
) -> dict[str, Path]:
    """Stage -wal/-shm sidecars from backup_path alongside temp_restore."""
    stem = backup_path.stem
    staged: dict[str, Path] = {}
    for suffix in ("-wal", "-shm"):
        sidecar = backup_path.parent / f"{stem}{suffix}"
        if sidecar.exists():
            dest = temp_restore_dir / f"{stem}{suffix}"
            shutil.copy2(sidecar, dest)
            staged[suffix] = dest
    return staged


def _restore_from_backup(
    db_path: Path,
    backup_path: str | Path | None,
    target: str = "rag",
    dry_run: bool = False,
) -> RecoveryResult:
    """Restore DB from backup; returns RecoveryResult."""
    if backup_path is None:
        logger.error("No backup_path provided — manual recovery required")
        return RecoveryResult(
            success=False,
            action="no_backup",
            detail="no backup_path provided",
            dry_run=dry_run,
        )

    backup = Path(backup_path)
    if not backup.exists():
        logger.error("Backup not found: %s", backup)
        return RecoveryResult(
            success=False,
            action="no_backup",
            detail=f"backup not found: {backup}",
            dry_run=dry_run,
        )

    # 1. Verify backup integrity
    integrity_condition, integrity_error = _run_integrity_check(backup, target)
    if integrity_condition != DbCondition.HEALTHY:
        err = integrity_error or f"backup integrity check failed: {integrity_condition}"
        logger.error("Backup is also corrupt: %s", err)
        return RecoveryResult(
            success=False, action="bad_backup", detail=err, dry_run=dry_run
        )

    domain_ok, domain_error = _verify_domain_identity(backup, target)
    if not domain_ok:
        err = domain_error or f"backup failed domain-identity check for target={target}"
        logger.error("Backup belongs to a different persistence domain: %s", err)
        return RecoveryResult(
            success=False, action="backup_wrong_domain", detail=err, dry_run=dry_run
        )

    ts = format_timestamp()
    corrupt_archive = db_path.with_name(f"{db_path.stem}_corrupt_{ts}{db_path.suffix}")
    temp_restore = db_path.with_name(f"{db_path.stem}.tmp_{ts}{db_path.suffix}")

    try:
        # 2. Quarantine pre-existing -wal/-shm sidecar files on the target path
        quarantine_dir = db_path.parent / f"{db_path.stem}_sidecar_quarantine_{ts}"
        quarantine_dir.mkdir(exist_ok=True)
        _quarantine_sidecar_files(db_path, quarantine_dir)

        # 3. Archive current corrupt DB (if it exists)
        if db_path.exists():
            shutil.copy2(db_path, corrupt_archive)
            logger.info("Corrupt DB archived: %s", corrupt_archive)

        # 4. Atomic restore: copy backup + sidecars to temp, then rename
        shutil.copy2(backup, temp_restore)
        staged = _stage_backup_sidecars(backup, temp_restore.parent)
        for suffix, staged_path in staged.items():
            dest = temp_restore.parent / f"{temp_restore.stem}{suffix}"
            shutil.copy2(staged_path, dest)
        os.replace(temp_restore, db_path)

        # 4a. Rename staged -wal/-shm files to final locations alongside db_path
        for suffix, staged_path in staged.items():
            final_path = db_path.parent / f"{db_path.stem}{suffix}"
            try:
                shutil.move(staged_path, final_path)
            except OSError:
                logger.warning(
                    "Failed to move staged sidecar %s to %s; proceeding without it",
                    staged_path,
                    final_path,
                )

        # 4. Re-verify the restored database before reporting success
        post_condition, post_detail = _run_integrity_check(db_path, target)
        if post_condition != DbCondition.HEALTHY:
            detail = (
                post_detail
                or f"post-restore integrity check failed: {post_condition.value}"
            )
            logger.error("Post-restore integrity check failed: %s", detail)
            return RecoveryResult(
                success=False,
                action="restore_verify_failed",
                detail=detail,
                dry_run=dry_run,
            )

        # 5. Logical-verification stage (between physical re-check and success)
        logical_ok, logical_detail = _run_logical_verification(db_path, target)
        if not logical_ok:
            err_detail = logical_detail or f"logical verification failed: {target}"
            logger.error("Post-restore logical verification failed: %s", err_detail)
            return RecoveryResult(
                success=False,
                action="logical_verify_failed",
                detail=err_detail,
                dry_run=dry_run,
            )

        logger.info("DB restored from backup: %s", backup)
        # Cleanup quarantine directory after successful restore
        if quarantine_dir.exists():
            shutil.rmtree(quarantine_dir, ignore_errors=True)
        return RecoveryResult(
            success=True, action="restored", detail=str(backup), dry_run=dry_run
        )
    except OSError as e:
        logger.error("Recovery failed: %s", e)
        if temp_restore.exists():
            temp_restore.unlink()
        return RecoveryResult(
            success=False, action="error", detail=str(e), dry_run=dry_run
        )


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
        # ADR-011 Requirement #6: workflow/eventbus require explicit decision
        return RecoveryResult(
            success=False,
            action="no_recovery_allowed",
            detail=f"Automatic recovery is prohibited for {target}. Manual intervention required.",
            dry_run=dry_run,
        )

    db_path = Path(target_db_path)
    condition, detail = _run_integrity_check(db_path, target)
    if condition == DbCondition.HEALTHY:
        if dry_run:
            return _handle_dry_run("ok")
        return _vacuum_db(target)

    if condition in (
        DbCondition.LOCK_CONTENTION,
        DbCondition.PERMISSION_FAILURE,
        DbCondition.INVALID_FORMAT,
    ):
        return RecoveryResult(
            success=False,
            action="error",
            detail=f"{condition.value}: {detail}",
            dry_run=dry_run,
        )

    if condition == DbCondition.UNKNOWN:
        return RecoveryResult(
            success=False,
            action="preserved_operator_intervention_required",
            detail=f"Unknown integrity-check failure ({detail}): operator intervention required",
            dry_run=dry_run,
        )

    # It's CORRUPTION
    if dry_run:
        return RecoveryResult(
            success=False,
            action="error",
            detail=f"Integrity failure ({condition.value}): {detail}",
            dry_run=True,
        )

    # For rag and session, we attempt restoration
    return _restore_from_backup(db_path, backup_path, target=target, dry_run=dry_run)
