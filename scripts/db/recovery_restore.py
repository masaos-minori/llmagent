#!/usr/bin/env python3
"""scripts/db/recovery_restore.py — Filesystem execution of a corruption restore.

Owns the file operations a restore performs: resolve the backup candidate, quarantine
and stage the -wal/-shm sidecars, and archive the corrupt DB. Staging is separate from
activation: db.recovery verifies the staged candidate before swapping it into
place. Condition classification, the physical integrity check, and the RecoveryResult
policy stay in db.recovery, which calls these helpers; the logical consistency checks
that run after a restore live in db.recovery_verification.

ADR-008 recovery policy: restore file staging used by db.recovery.recover_corruption.
"""

import logging
import shutil
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def _quarantine_sidecar_files(db_path: Path, quarantine_dir: Path) -> None:
    """Quarantine pre-existing -wal/-shm sidecar files associated with db_path.

    Sidecar names resolve from the full database filename:
    ``rag.sqlite`` -> ``rag.sqlite-wal`` / ``rag.sqlite-shm``. Fail-closed: a quarantine copy/unlink failure raises OSError so the caller
    reports a failed recovery instead of proceeding without the sidecar.
    """
    ts = int(time.time())
    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(db_path) + suffix)
        if sidecar.exists():
            quarantine_path = quarantine_dir / f"{db_path.name}{suffix}_corrupt_{ts}"
            shutil.copy2(sidecar, quarantine_path)
            sidecar.unlink()


def _stage_backup_sidecars(
    backup_path: Path, temp_restore_dir: Path
) -> dict[str, Path]:
    """Stage -wal/-shm sidecars from backup_path alongside temp_restore.

    Sidecar names resolve from the full backup filename:
    ``backup.sqlite`` -> ``backup.sqlite-wal`` / ``backup.sqlite-shm``.
    """
    staged: dict[str, Path] = {}
    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(backup_path) + suffix)
        if sidecar.exists():
            dest = temp_restore_dir / f"{backup_path.name}{suffix}"
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
) -> dict[str, Path]:
    """Quarantine sidecars, archive the corrupt DB, and stage the candidate unit.

    Steps 2-4 of the restore. Staging only: the candidate — the backup
    plus its -wal/-shm sidecars named after temp_restore — is staged but NOT
    activated; db.recovery verifies it before swapping it into place. Returns the
    staged sidecar paths keyed by suffix for the caller's activation step.
    Filesystem failures are raised for the caller's cleanup handler, which owns
    the half-written temp file.
    """
    # 2. Quarantine pre-existing -wal/-shm sidecar files on the target path
    quarantine_dir.mkdir(exist_ok=True)
    _quarantine_sidecar_files(db_path, quarantine_dir)

    # 3. Archive current corrupt DB (if it exists)
    if db_path.exists():
        shutil.copy2(db_path, corrupt_archive)
        logger.info("Corrupt DB archived: %s", corrupt_archive)

    # 4. Stage the candidate unit: copy the backup and move its sidecars under
    # the temp_restore names so verification sees the complete unit.
    # Fail-closed: a move failure raises; the caller's OSError
    # handler reports the failed recovery.
    shutil.copy2(backup, temp_restore)
    staged: dict[str, Path] = {}
    for suffix, staged_path in _stage_backup_sidecars(
        backup, temp_restore.parent
    ).items():
        dest = Path(str(temp_restore) + suffix)
        shutil.move(staged_path, dest)
        staged[suffix] = dest
    return staged
