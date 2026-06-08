#!/usr/bin/env python3
"""db_maintenance.py
SQLite operational maintenance: WAL checkpoint, VACUUM, DB rotation,
session retention, and corruption recovery.

All functions take an open SQLiteHelper instance or operate directly on the
DB file path loaded from config.  None of them modify the SQLiteHelper class —
they encode policy decisions that sit above the connection layer.

Typical maintenance schedule:
  After large ingestion : checkpoint_wal(db, "TRUNCATE")
  Weekly                : vacuum_db(db)
  Weekly                : purge_old_sessions(db, cfg)
  Before schema change  : rotate_db()
  On startup warning    : recover_corruption()
"""

import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from shared.config_loader import ConfigLoader

from db.helper import SQLiteHelper
from db.store import SQLiteMemoryDeleteStore

logger = logging.getLogger(__name__)


# ── Policy dataclasses ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RetentionConfig:
    """Session retention policy: max_sessions keeps most-recent N sessions; max_age_days deletes sessions older than N days (0=disabled)."""

    max_sessions: int = 100
    max_age_days: int = 90

    @classmethod
    def from_config(cls) -> "RetentionConfig":
        """Construct from common.toml values."""
        try:
            cfg = ConfigLoader().load("common.toml")
        except Exception as e:
            logger.warning(f"Config load failed: {e}")
            cfg = {}
        return cls(
            max_sessions=int(cfg.get("sqlite_retention_max_sessions", 100)),
            max_age_days=int(cfg.get("sqlite_retention_max_age_days", 90)),
        )


@dataclass(frozen=True)
class RecoveryResult:
    """Structured result of a corruption recovery attempt."""

    success: bool
    action: str
    detail: str | None = None
    dry_run: bool = False


# ── Maintenance operations ─────────────────────────────────────────────────────


def checkpoint_wal(db: SQLiteHelper, mode: str | None = None) -> dict[str, int]:
    """Flush the WAL file and return checkpoint counters; mode defaults to sqlite_wal_checkpoint_mode (TRUNCATE); raises ValueError for unknown mode."""
    if mode is None:
        try:
            cfg = ConfigLoader().load("common.toml")
        except Exception as e:
            logger.warning(f"Config load failed: {e}")
            cfg = {}
        mode = cfg.get("sqlite_wal_checkpoint_mode", "TRUNCATE").upper()
    return db.checkpoint(mode)


def vacuum_db(db: SQLiteHelper) -> None:
    """Run VACUUM to rebuild the DB file and reclaim freed pages; cannot run inside a transaction; requires ~2× DB size in free disk space."""
    db.vacuum()


def purge_old_sessions(
    db: SQLiteHelper,
    cfg: RetentionConfig | None = None,
) -> dict[str, int]:
    """Delete sessions exceeding the retention policy (age-based then count-based); CASCADE removes messages; returns {age_deleted, count_deleted}."""
    if cfg is None:
        cfg = RetentionConfig.from_config()

    age_deleted = 0
    count_deleted = 0

    if cfg.max_age_days > 0:
        cur = db.execute(
            "DELETE FROM sessions WHERE created_at < datetime('now', ?)",
            (f"-{cfg.max_age_days} days",),
        )
        age_deleted = cur.rowcount
        if age_deleted:
            logger.info(
                f"Retention: removed {age_deleted} sessions"
                f" older than {cfg.max_age_days} days",
            )

    rows = db.fetchall("SELECT session_id FROM sessions ORDER BY created_at DESC")
    if len(rows) > cfg.max_sessions:
        to_delete = [row[0] for row in rows[cfg.max_sessions :]]
        placeholders = ",".join("?" * len(to_delete))
        cur = db.execute(
            f"DELETE FROM sessions WHERE session_id IN ({placeholders})",  # nosec B608 — placeholders is "?" * n, not user input
            tuple(to_delete),
        )
        count_deleted = cur.rowcount
        logger.info(
            f"Retention: removed {count_deleted} sessions"
            f" beyond limit of {cfg.max_sessions}",
        )

    db.commit()
    return {"age_deleted": age_deleted, "count_deleted": count_deleted}


def prune_old_memories(db: SQLiteHelper, older_than_days: int) -> int:
    """Delete memories older than older_than_days via SQLiteMemoryDeleteStore; return count deleted."""
    store = SQLiteMemoryDeleteStore(db)
    result = store.delete_memories_before(older_than_days)
    if result.vec_skipped:
        logger.warning(
            "prune_old_memories: memories_vec deletion failed",
            extra={"error": result.vec_error, "days": older_than_days},
        )
    logger.info(
        f"prune_old_memories: removed {result.deleted} entries"
        f" older than {older_than_days} days",
    )
    return result.deleted


def _archive_db_file(db_path: Path, archive_dir: str | Path | None) -> Path:
    """Copy a single DB file (plus WAL/SHM side-files) to the archive directory."""
    if not db_path.exists():
        raise FileNotFoundError(f"DB file not found: {db_path}")

    if archive_dir is None:
        try:
            cfg = ConfigLoader().load("common.toml")
        except Exception:
            cfg = {}
        archive_dir = cfg.get("sqlite_archive_dir", "/opt/llm/db/archive")

    dest_dir = Path(archive_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"{db_path.stem}_{ts}{db_path.suffix}"
    shutil.copy2(db_path, dest)

    for side_ext in ("-wal", "-shm"):
        side = Path(str(db_path) + side_ext)
        if side.exists():
            shutil.copy2(side, dest_dir / (dest.name + side_ext))

    size = dest.stat().st_size
    logger.info(f"DB rotated: {dest} ({size:,} bytes)")
    return dest


def rotate_rag_db(archive_dir: str | Path | None = None) -> Path:
    """Archive rag.sqlite to archive_dir with a timestamp suffix; returns the archive path."""
    SQLiteHelper._ensure_config()
    return _archive_db_file(Path(SQLiteHelper._RAG_PATH), archive_dir)


def rotate_session_db(archive_dir: str | Path | None = None) -> Path:
    """Archive session.sqlite to archive_dir with a timestamp suffix; returns the archive path."""
    SQLiteHelper._ensure_config()
    return _archive_db_file(Path(SQLiteHelper._SESSION_PATH), archive_dir)


def rotate_db(archive_dir: str | Path | None = None) -> tuple[Path, Path]:
    """Archive both rag.sqlite and session.sqlite; returns (rag_archive_path, session_archive_path)."""
    rag_dest = rotate_rag_db(archive_dir)
    ses_dest = rotate_session_db(archive_dir)
    return rag_dest, ses_dest


def _run_integrity_check(db_path: Path) -> tuple[str | None, str | None]:
    """Open DB and run PRAGMA integrity_check; returns (check_result, error_detail).

    Returns (None, error_detail) if the DB cannot be opened.
    """
    try:
        with SQLiteHelper("rag").open() as db:
            if db.conn is None:
                raise RuntimeError("DB connection not established after open()")
            result: str = db.conn.execute("PRAGMA integrity_check").fetchone()[0]
            return result, None
    except Exception as e:
        logger.error(f"Cannot open DB for integrity check: {e}")
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


def _vacuum_db() -> RecoveryResult:
    """Run VACUUM and return result."""
    logger.info("Integrity check passed; running VACUUM")
    try:
        with SQLiteHelper("rag").open(write_mode=True) as db:
            db.vacuum()
    except Exception as e:
        logger.warning(f"VACUUM after integrity check failed: {e}")
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
        logger.error(f"Backup not found: {backup}")
        return RecoveryResult(
            success=False, action="no_backup", detail=f"backup not found: {backup}"
        )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    corrupt_archive = db_path.with_name(f"{db_path.stem}_corrupt_{ts}{db_path.suffix}")
    try:
        shutil.copy2(db_path, corrupt_archive)
        logger.info(f"Corrupt DB archived: {corrupt_archive}")
        shutil.copy2(backup, db_path)
        logger.info(f"DB restored from backup: {backup}")
        return RecoveryResult(success=True, action="restored", detail=str(backup))
    except OSError as e:
        logger.error(f"Recovery failed: {e}")
        return RecoveryResult(success=False, action="error", detail=str(e))


def recover_corruption(
    backup_path: str | Path | None = None,
    *,
    dry_run: bool = False,
) -> RecoveryResult:
    """Detect and recover from corruption in rag.sqlite; returns RecoveryResult with action and detail.

    action values:
      "vacuum"    — integrity ok; VACUUM executed (or skipped in dry_run)
      "restored"  — integrity failed; DB restored from backup_path
      "no_backup" — integrity failed; no usable backup_path
      "error"     — could not open DB or OS-level failure
    """
    SQLiteHelper._ensure_config()
    db_path = Path(SQLiteHelper._RAG_PATH)

    check_result, error_detail = _run_integrity_check(db_path)
    if check_result is None:
        return RecoveryResult(
            success=False, action="error", detail=error_detail, dry_run=dry_run
        )

    if dry_run:
        return _handle_dry_run(check_result)

    if check_result == "ok":
        return _vacuum_db()

    logger.error(f"Integrity check failed: {check_result}")
    return _restore_from_backup(db_path, backup_path)
