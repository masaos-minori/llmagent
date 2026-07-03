#!/usr/bin/env python3
"""db/recovery.py — Corruption recovery operations."""

import logging
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from db.config import build_db_config
from db.helper import SQLiteHelper
from db.models import RecoveryResult

logger = logging.getLogger(__name__)


def _run_integrity_check(
    db_path: Path, target: str = "rag"
) -> tuple[str | None, str | None]:
    """Open DB and run PRAGMA integrity_check; returns (check_result, error_detail).

    Returns (None, error_detail) if the DB cannot be opened.
    """
    try:
        with SQLiteHelper(target).open() as db:
            cursor = db.execute("PRAGMA integrity_check")
            result = str(cursor.fetchone()[0])
            return result, None
    except (sqlite3.OperationalError, ValueError, RuntimeError) as e:
        logger.error("Cannot open DB for integrity check: %s", e)
        return None, str(e)


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
    db_path: Path, backup_path: str | Path | None
) -> RecoveryResult:
    """Restore DB from backup; returns RecoveryResult."""
    if backup_path is None:
        logger.error("No backup_path provided — manual recovery required")
        return RecoveryResult(
            success=False, action="no_backup", detail="no backup_path provided"
        )

    backup = Path(backup_path)
    if not backup.exists():
        logger.error("Backup not found: %s", backup)
        return RecoveryResult(
            success=False, action="no_backup", detail=f"backup not found: {backup}"
        )

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")  # noqa: UP017
    corrupt_archive = db_path.with_name(f"{db_path.stem}_corrupt_{ts}{db_path.suffix}")
    try:
        shutil.copy2(db_path, corrupt_archive)
        logger.info("Corrupt DB archived: %s", corrupt_archive)
        shutil.copy2(backup, db_path)
        logger.info("DB restored from backup: %s", backup)
        return RecoveryResult(success=True, action="restored", detail=str(backup))
    except OSError as e:
        logger.error("Recovery failed: %s", e)
        return RecoveryResult(success=False, action="error", detail=str(e))


def recover_corruption(
    backup_path: str | Path | None = None,
    *,
    target: str = "rag",
    dry_run: bool = False,
) -> RecoveryResult:
    """Detect and recover from corruption in the target DB; returns RecoveryResult.

    target: "rag" (default) or "session".
    action values:
      "vacuum"        — integrity ok; VACUUM executed (or skipped in dry_run)
      "vacuum_failed" — integrity ok but VACUUM raised
      "restored"      — integrity failed; DB restored from backup_path
      "no_backup"     — integrity failed; no usable backup_path
      "error"         — could not open DB or OS-level failure
    """
    db_cfg = build_db_config()
    db_path = Path(db_cfg.rag_db_path if target == "rag" else db_cfg.session_db_path)

    check_result, error_detail = _run_integrity_check(db_path, target)
    if check_result is None:
        return RecoveryResult(
            success=False, action="error", detail=error_detail, dry_run=dry_run
        )

    if dry_run:
        return _handle_dry_run(check_result)

    if check_result == "ok":
        return _vacuum_db(target)

    logger.error("Integrity check failed: %s", check_result)
    return _restore_from_backup(db_path, backup_path)
