#!/usr/bin/env python3
"""scripts/db/recovery_restore.py — Filesystem execution of a corruption restore.

Owns the file operations a restore performs: resolve the backup candidate, quarantine
and stage the -wal/-shm sidecars, archive the corrupt DB, and swap the backup into
place. Condition classification, the integrity/logical checks, and the RecoveryResult
policy stay in db.recovery, which calls these helpers.

ADR-008 recovery policy: restore file staging used by db.recovery.recover_corruption().
"""

import logging
import os
import shutil
import time
from pathlib import Path

logger = logging.getLogger(__name__)


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


def _resolve_backup(backup_path: str | Path | None) -> tuple[Path | None, str]:
    """Return (backup, detail) for the two backup-availability guards.

    backup is None when no usable backup exists, and detail then carries the message
    the no_backup result reports. The two failure modes log differently, so the
    logging stays here rather than being reconstructed by the caller.
    """
    if backup_path is None:
        logger.error("No backup_path provided — manual recovery required")
        return None, "no backup_path provided"

    backup = Path(backup_path)
    if not backup.exists():
        logger.error("Backup not found: %s", backup)
        return None, f"backup not found: {backup}"

    return backup, ""


def _stage_restore(
    db_path: Path,
    backup: Path,
    corrupt_archive: Path,
    temp_restore: Path,
    quarantine_dir: Path,
) -> None:
    """Quarantine sidecars, archive the corrupt DB, and swap the backup into place.

    Steps 2-4a of the restore. Filesystem failures are raised for the caller's
    cleanup handler, which owns the half-written temp file.
    """
    # 2. Quarantine pre-existing -wal/-shm sidecar files on the target path
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
