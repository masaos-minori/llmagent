#!/usr/bin/env python3
"""scripts/db/recovery.py — Corruption recovery operations."""

import logging
import os
import shutil
import sqlite3
from enum import StrEnum
from pathlib import Path

from db.config import build_db_config, format_timestamp
from db.helper import SQLiteHelper
from db.models import RecoveryResult

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
    """Classify a caught exception into a DbCondition."""
    if isinstance(e, sqlite3.OperationalError):
        msg = str(e).lower()
        if "database is locked" in msg or "busy" in msg:
            return DbCondition.LOCK_CONTENTION
        if "permission denied" in msg or "readonly" in msg:
            return DbCondition.PERMISSION_FAILURE
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


def _restore_from_backup(
    db_path: Path, backup_path: str | Path | None, dry_run: bool = False
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
    integrity_condition, integrity_error = _run_integrity_check(backup, target="rag")
    if integrity_condition != DbCondition.HEALTHY:
        err = integrity_error or f"backup integrity check failed: {integrity_condition}"
        logger.error("Backup is also corrupt: %s", err)
        return RecoveryResult(
            success=False, action="bad_backup", detail=err, dry_run=dry_run
        )

    ts = format_timestamp()
    corrupt_archive = db_path.with_name(f"{db_path.stem}_corrupt_{ts}{db_path.suffix}")
    temp_restore = db_path.with_name(f"{db_path.stem}.tmp_{ts}{db_path.suffix}")

    try:
        # 2. Archive current corrupt DB (if it exists)
        if db_path.exists():
            shutil.copy2(db_path, corrupt_archive)
            logger.info("Corrupt DB archived: %s", corrupt_archive)

        # 3. Atomic restore: copy backup to temp, then rename
        shutil.copy2(backup, temp_restore)
        os.replace(temp_restore, db_path)

        logger.info("DB restored from backup: %s", backup)
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
      "vacuum"        — integrity ok; VACUUM executed (or skipped in dry_run)
      "vacuum_failed" — integrity ok but VACUUM raised
      "restored"      — integrity failed; DB restored from backup_path
      "no_backup"     — integrity failed; no usable backup_path
      "error"         — could not open DB or OS-level failure
    """
    db_cfg = build_db_config()
    db_path = Path(db_cfg.rag_db_path if target == "rag" else db_cfg.session_db_path)

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

    # It's CORRUPTION or UNKNOWN
    if dry_run:
        return RecoveryResult(
            success=False,
            action="error",
            detail=f"Integrity failure ({condition.value}): {detail}",
            dry_run=True,
        )

    # Domain policy check
    if target in ("workflow", "eventbus"):
        # ADR-011 Requirement #6: workflow/eventbus require explicit decision
        return RecoveryResult(
            success=False,
            action="no_recovery_allowed",
            detail=f"Automatic recovery is prohibited for {target}. Manual intervention required.",
            dry_run=dry_run,
        )

    # For rag and session, we attempt restoration
    return _restore_from_backup(db_path, backup_path, dry_run=dry_run)
