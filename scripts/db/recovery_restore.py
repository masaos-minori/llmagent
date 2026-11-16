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
from collections.abc import Sequence
from pathlib import Path

from db.config import format_timestamp, resolve_unique_path

logger = logging.getLogger(__name__)


def build_restore_paths(db_path: Path) -> tuple[Path, Path, Path]:
    """Build the collision-safe names for one recovery's working files.

    Returns ``(corrupt_archive, temp_restore, sidecar_quarantine_dir)`` built
    from a single ``format_timestamp()`` call: ``{stem}_corrupt_{ts}{suffix}``
    and ``{stem}.tmp_{ts}{suffix}`` in the database's directory, and
    ``{stem}_sidecar_quarantine_{ts}`` beside it. Each candidate goes through
    ``resolve_unique_path``, so a same-second second recovery cannot overwrite
    the first one's forensic copies. Directory creation stays with the caller.
    """
    ts = format_timestamp()
    return (
        resolve_unique_path(
            db_path.with_name(f"{db_path.stem}_corrupt_{ts}{db_path.suffix}")
        ),
        resolve_unique_path(
            db_path.with_name(f"{db_path.stem}.tmp_{ts}{db_path.suffix}")
        ),
        resolve_unique_path(db_path.parent / f"{db_path.stem}_sidecar_quarantine_{ts}"),
    )


def _quarantine_sidecar_files(
    db_path: Path, quarantine_dir: Path
) -> list[tuple[Path, Path]]:
    """Quarantine pre-existing -wal/-shm sidecar files associated with db_path.

    Sidecar names resolve from the full database filename:
    ``rag.sqlite`` -> ``rag.sqlite-wal`` / ``rag.sqlite-shm``. Fail-closed: a quarantine copy/unlink failure raises OSError so the caller
    reports a failed recovery instead of proceeding without the sidecar; a failure
    partway through first moves the already-recorded sidecars back (see
    `_restore_quarantine_sidecars`), so records are never lost mid-quarantine.

    The directory is created only when a sidecar actually quarantines, so a
    sidecar-free restore leaves no empty directory behind. Returns the quarantine
    records (live name -> quarantine path) in quarantine order so a caller can
    move each entry back byte-identically on a failure path (REQ-001).
    """
    ts = int(time.time())
    records: list[tuple[Path, Path]] = []
    try:
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(db_path) + suffix)
            if sidecar.exists():
                quarantine_dir.mkdir(parents=True, exist_ok=True)
                quarantine_path = resolve_unique_path(
                    quarantine_dir / f"{db_path.name}{suffix}_corrupt_{ts}"
                )
                shutil.copy2(sidecar, quarantine_path)
                sidecar.unlink()
                records.append((sidecar, quarantine_path))
    except OSError:
        # Mid-quarantine failure: move the already-recorded sidecars back before
        # raising, so a staging failure never strands a recorded sidecar in the
        # quarantine directory (the caller never sees records it cannot reassemble).
        try:
            _restore_quarantine_sidecars(records, quarantine_dir)
        except OSError as restore_exc:
            logger.error(
                "Failed to restore quarantined sidecars after a mid-quarantine failure: %s",
                restore_exc,
            )
        raise
    return records


def _restore_quarantine_sidecars(
    records: Sequence[tuple[Path, Path]], quarantine_dir: Path | None
) -> None:
    """Move quarantined original sidecars back to their live names (AC-1).

    Each recorded (live name -> quarantine path) pair is moved back with
    shutil.move, byte-identically; a move failure propagates like staging, so a
    partial reassembly never reports preserved_original. Once every recorded pair
    is back, the emptied quarantine directory is rmdir'd (guarded and logged —
    rmdir never deletes a non-empty directory), keeping the recorded invariant
    that a quarantine directory exists only while it holds entries. Empty
    records are a no-op, so sidecar-free restores pass quarantine_dir=None
    safely.
    """
    if not records:
        return
    for live_path, quarantine_path in records:
        shutil.move(str(quarantine_path), str(live_path))
    if quarantine_dir is not None:
        try:
            quarantine_dir.rmdir()
        except OSError as exc:
            logger.error(
                "Failed to remove emptied quarantine directory %s: %s",
                quarantine_dir,
                exc,
            )


def _retain_quarantine_archive(quarantine_dir: Path) -> None:
    """Log the quarantine archive retained after a successful restore (REQ-003).

    The directory and its copies stay as a forensic archive; removal is
    delegated to the operator-side artifact retention issue. After the
    deferred mkdir it only exists when something was quarantined.
    """
    if quarantine_dir.exists():
        logger.info("Quarantine archive retained: %s", quarantine_dir)


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
) -> tuple[dict[str, Path], list[tuple[Path, Path]]]:
    """Quarantine sidecars, archive the corrupt DB, and stage the candidate unit.

    Steps 2-4 of the restore. Staging only: the candidate — the backup
    plus its -wal/-shm sidecars named after temp_restore — is staged but NOT
    activated; db.recovery verifies it before swapping it into place. Returns the
    staged sidecar paths keyed by suffix and the quarantine records (live name ->
    quarantine path) for the caller's failure-path reassembly.
    Filesystem failures are raised for the caller's cleanup handler, which owns
    the half-written temp file.
    """
    # 2. Quarantine pre-existing -wal/-shm sidecar files on the target path
    # (the helper creates the directory only when something quarantines).
    quarantine_records = _quarantine_sidecar_files(db_path, quarantine_dir)

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
    return staged, quarantine_records
