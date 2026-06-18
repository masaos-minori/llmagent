#!/usr/bin/env python3
"""db/maintenance.py
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
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from shared.config_loader import ConfigLoader

from db.config import build_db_config
from db.helper import SQLiteHelper
from db.models import PurgeCounts, WalCheckpointCounts
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
        """Construct from common.toml values; raises on config load failure."""
        cfg = ConfigLoader().load_all()
        return cls(
            max_sessions=int(cfg.get("sqlite_retention_max_sessions", 100)),
            max_age_days=int(cfg.get("sqlite_retention_max_age_days", 90)),
        )


@dataclass(frozen=True)
class RagConsistencyReport:
    """Counts from chunks, chunks_fts, and chunks_vec for consistency verification."""

    chunks: int
    fts: int
    vec: int
    orphan_vec_count: int
    fts_gap: int  # chunks - fts; 0 = consistent


@dataclass(frozen=True)
class RecoveryResult:
    """Structured result of a corruption recovery attempt."""

    success: bool
    action: str
    detail: str | None = None
    dry_run: bool = False


# ── Maintenance operations ─────────────────────────────────────────────────────


def checkpoint_wal(db: SQLiteHelper, mode: str | None = None) -> WalCheckpointCounts:
    """Flush the WAL file and return checkpoint counters; mode defaults to sqlite_wal_checkpoint_mode (TRUNCATE); raises ValueError for unknown mode."""
    if mode is None:
        cfg = ConfigLoader().load_all()
        mode = cfg.get("sqlite_wal_checkpoint_mode", "TRUNCATE").upper()
    return db.checkpoint(mode)


def vacuum_db(db: SQLiteHelper) -> None:
    """Run VACUUM to rebuild the DB file and reclaim freed pages; cannot run inside a transaction; requires ~2× DB size in free disk space."""
    db.vacuum()


def purge_old_sessions(
    db: SQLiteHelper,
    cfg: RetentionConfig | None = None,
) -> PurgeCounts:
    """Delete sessions exceeding the retention policy (age-based then count-based); CASCADE removes messages; returns PurgeCounts(age_deleted, count_deleted)."""
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
                "Retention: removed %s sessions older than %s days",
                age_deleted,
                cfg.max_age_days,
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
            "Retention: removed %s sessions beyond limit of %s",
            count_deleted,
            cfg.max_sessions,
        )

    db.commit()
    return PurgeCounts(age_deleted=age_deleted, count_deleted=count_deleted)


def prune_old_memories(db: SQLiteHelper, older_than_days: int) -> int:
    """Delete memories older than older_than_days via SQLiteMemoryDeleteStore; return count deleted."""
    store = SQLiteMemoryDeleteStore(db)
    result = store.delete_memories_before(older_than_days)
    logger.info(
        "prune_old_memories: removed %s entries older than %s days",
        result.deleted,
        older_than_days,
    )
    return result.deleted


def _archive_db_file(db_path: Path, archive_dir: str | Path | None) -> Path:
    """Create a WAL-consistent backup of db_path using the SQLite online backup API."""
    if not db_path.exists():
        raise FileNotFoundError(f"DB file not found: {db_path}")

    if archive_dir is None:
        cfg = ConfigLoader().load_all()
        archive_dir = cfg.get("sqlite_archive_dir", "/opt/llm/db/archive")

    dest_dir = Path(archive_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")  # noqa: UP017
    dest = dest_dir / f"{db_path.stem}_{ts}{db_path.suffix}"

    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(dest))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    size = dest.stat().st_size
    logger.info("DB archived: %s (%s bytes)", dest, size)
    return dest


def rotate_rag_db(archive_dir: str | Path | None = None) -> Path:
    """Archive rag.sqlite to archive_dir with a timestamp suffix; returns the archive path."""
    db_cfg = build_db_config()
    return _archive_db_file(Path(db_cfg.rag_db_path), archive_dir)


def rotate_session_db(archive_dir: str | Path | None = None) -> Path:
    """Archive session.sqlite to archive_dir with a timestamp suffix; returns the archive path."""
    db_cfg = build_db_config()
    return _archive_db_file(Path(db_cfg.session_db_path), archive_dir)


def rotate_db(archive_dir: str | Path | None = None) -> tuple[Path, Path]:
    """Archive both rag.sqlite and session.sqlite; returns (rag_archive_path, session_archive_path)."""
    rag_dest = rotate_rag_db(archive_dir)
    ses_dest = rotate_session_db(archive_dir)
    return rag_dest, ses_dest


def _run_integrity_check(
    db_path: Path, target: str = "rag"
) -> tuple[str | None, str | None]:
    """Open DB and run PRAGMA integrity_check; returns (check_result, error_detail).

    Returns (None, error_detail) if the DB cannot be opened.
    """
    try:
        with SQLiteHelper(target).open() as db:
            result: str = db.conn.execute("PRAGMA integrity_check").fetchone()[0]  # type: ignore[union-attr]  # conn is set by open()
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


def check_rag_consistency(db: SQLiteHelper) -> RagConsistencyReport:
    """Return row counts from chunks, chunks_fts, and chunks_vec for consistency verification.

    All queries are read-only. Orphan vec rows are chunk_id values in chunks_vec
    with no matching row in chunks (possible when the chunks_vec_ad trigger fails).
    """
    chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    fts = db.execute("SELECT COUNT(*) FROM chunks_fts_docsize").fetchone()[0]
    vec = db.execute("SELECT COUNT(*) FROM chunks_vec").fetchone()[0]
    orphan_vec_count = db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
    ).fetchone()[0]
    return RagConsistencyReport(
        chunks=chunks,
        fts=fts,
        vec=vec,
        orphan_vec_count=orphan_vec_count,
        fts_gap=chunks - fts,
    )


def is_consistent(report: RagConsistencyReport) -> bool:
    """Return True when fts_gap == 0, orphan_vec_count == 0, and vec == chunks."""
    return (
        report.fts_gap == 0
        and report.orphan_vec_count == 0
        and report.vec == report.chunks
    )


def summarize_issues(report: RagConsistencyReport) -> list[str]:
    """Return human-readable descriptions of any consistency issues found in report."""
    issues: list[str] = []
    if report.fts_gap != 0:
        issues.append(
            f"FTS gap: chunks={report.chunks}, fts={report.fts}, gap={report.fts_gap}"
        )
    if report.orphan_vec_count > 0:
        issues.append(
            f"Orphan vec rows: {report.orphan_vec_count} chunk_id(s) not in chunks"
        )
    if report.vec != report.chunks:
        issues.append(f"Vec count mismatch: chunks={report.chunks}, vec={report.vec}")
    return issues
