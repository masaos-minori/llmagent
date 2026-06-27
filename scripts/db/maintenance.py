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

import dataclasses
import logging
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

from shared.config_loader import ConfigLoader

from db.config import build_db_config
from db.helper import SQLiteHelper
from db.models import WalCheckpointCounts
from db.store_impl import SQLiteMemoryDeleteStore

logger = logging.getLogger(__name__)


# ── Maintenance mode and result ────────────────────────────────────────────────


class MaintenanceMode(StrEnum):
    STRICT = "strict"
    BEST_EFFORT = "best_effort"


@dataclass(frozen=True)
class MaintenanceResult:
    """Structured result of a maintenance operation.

    In STRICT mode (default), errors raise directly and this is only returned on success.
    In BEST_EFFORT mode, errors are caught and returned as success=False with detail.
    """

    success: bool
    action: str
    mode: MaintenanceMode
    detail: str | None = None
    data: dict | None = None


# ── Policy dataclasses ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RetentionConfig:
    """Session retention policy: max_sessions keeps most-recent N sessions; max_age_days deletes sessions older than N days (0=disabled)."""

    max_sessions: int = 100
    max_age_days: int = 90

    @classmethod
    def from_config(cls) -> "RetentionConfig":
        """Construct from common.toml values; raises on config load failure."""
        cfg = ConfigLoader().load("common.toml")
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
    fts_gap: int  # chunks - fts; positive = missing FTS entries
    fts_orphan_count: int  # fts - chunks; positive = extra FTS entries (data loss risk)
    embed_failed: int = 0  # embedding failures during ingestion
    issues: tuple[str, ...] = ()  # human-readable consistency issues
    # Affected identifiers (up to 10 each; None when not applicable)
    affected_chunk_ids: tuple[int, ...] | None = None  # chunk_ids missing from FTS
    affected_doc_ids: tuple[int, ...] | None = None  # doc_ids for chunks missing from FTS
    affected_orphan_chunk_ids: tuple[int, ...] | None = (
        None  # chunk_ids in vec but not chunks
    )
    affected_orphan_urls: tuple[str, ...] | None = (
        None  # URLs of docs with orphan vec rows
    )


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
        cfg = ConfigLoader().load("common.toml")
        raw_mode: str | None = cfg.get("sqlite_wal_checkpoint_mode")
        if raw_mode is None or not isinstance(raw_mode, str):
            raw_mode = "TRUNCATE"
        mode = raw_mode.upper()
    return db.checkpoint(mode)


def vacuum_db(
    db: SQLiteHelper, mode: MaintenanceMode = MaintenanceMode.STRICT
) -> MaintenanceResult:
    """Run VACUUM to rebuild the DB file and reclaim freed pages.

    In STRICT mode (default), raises on failure.
    In BEST_EFFORT mode, returns MaintenanceResult(success=False, detail=str(exc)).
    Cannot run inside a transaction; requires ~2× DB size in free disk space.
    """
    try:
        db.vacuum()
        return MaintenanceResult(success=True, action="vacuum", mode=mode)
    except (sqlite3.OperationalError, RuntimeError) as e:
        logger.error("VACUUM failed: %s", e)
        if mode == MaintenanceMode.STRICT:
            raise
        return MaintenanceResult(
            success=False, action="vacuum_failed", mode=mode, detail=str(e)
        )


def purge_old_sessions(
    db: SQLiteHelper,
    cfg: RetentionConfig | None = None,
    mode: MaintenanceMode = MaintenanceMode.STRICT,
) -> MaintenanceResult:
    """Delete sessions exceeding the retention policy (age-based then count-based).

    CASCADE removes messages. In STRICT mode (default), raises on DB errors.
    In BEST_EFFORT mode, returns MaintenanceResult with partial counts on error.
    """
    if cfg is None:
        cfg = RetentionConfig.from_config()

    age_deleted = 0
    count_deleted = 0

    try:
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
        return MaintenanceResult(
            success=True,
            action="purge",
            mode=mode,
            data={"age_deleted": age_deleted, "count_deleted": count_deleted},
        )
    except sqlite3.Error as e:
        logger.error("purge_old_sessions failed: %s", e)
        if mode == MaintenanceMode.STRICT:
            raise
        return MaintenanceResult(
            success=False,
            action="purge_failed",
            mode=mode,
            detail=str(e),
            data={"age_deleted": age_deleted, "count_deleted": count_deleted},
        )


def prune_old_memories(
    db: SQLiteHelper,
    older_than_days: int,
    mode: MaintenanceMode = MaintenanceMode.STRICT,
) -> MaintenanceResult:
    """Delete memories older than older_than_days via SQLiteMemoryDeleteStore.

    In STRICT mode (default), raises on DB errors.
    In BEST_EFFORT mode, returns MaintenanceResult(success=False, detail=str(exc)).
    """
    try:
        store = SQLiteMemoryDeleteStore(db)
        delete_result = store.delete_memories_before(older_than_days)
        logger.info(
            "prune_old_memories: removed %s entries older than %s days",
            delete_result.deleted,
            older_than_days,
        )
        return MaintenanceResult(
            success=True,
            action="prune",
            mode=mode,
            data={"deleted": delete_result.deleted},
        )
    except sqlite3.Error as e:
        logger.error("prune_old_memories failed: %s", e)
        if mode == MaintenanceMode.STRICT:
            raise
        return MaintenanceResult(
            success=False, action="prune_failed", mode=mode, detail=str(e)
        )


def _archive_db_file(db_path: Path, archive_dir: str | Path | None) -> Path:
    """Create a WAL-consistent backup of db_path using the SQLite online backup API."""
    if not db_path.exists():
        raise FileNotFoundError(f"DB file not found: {db_path}")

    if archive_dir is None:
        cfg = ConfigLoader().load("common.toml")
        raw_archive_dir: str | None = cfg.get("sqlite_archive_dir")
        if raw_archive_dir is None or not isinstance(raw_archive_dir, str):
            raw_archive_dir = "/opt/llm/db/archive"
        archive_dir = raw_archive_dir

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


def rotate_session_db(archive_dir: str | Path | None = None) -> Path:
    """Archive session.sqlite to archive_dir with a timestamp suffix; returns the archive path."""
    db_cfg = build_db_config()
    return _archive_db_file(Path(db_cfg.session_db_path), archive_dir)


def rotate_db(archive_dir: str | Path | None = None) -> tuple[Path, Path]:
    """Archive both rag.sqlite and session.sqlite; returns (rag_archive_path, session_archive_path)."""
    db_cfg = build_db_config()
    rag_dest = _archive_db_file(Path(db_cfg.rag_db_path), archive_dir)
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


def check_rag_consistency(
    db: SQLiteHelper, embed_failed: int = 0
) -> RagConsistencyReport:
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
    fts_gap = max(0, chunks - fts)
    fts_orphan_count = max(0, fts - chunks)

    # Collect affected identifiers (read-only; top 10 each)
    affected_chunk_ids: tuple[int, ...] | None = None
    affected_doc_ids: tuple[int, ...] | None = None
    affected_orphan_chunk_ids: tuple[int, ...] | None = None
    affected_orphan_urls: tuple[str, ...] | None = None
    if fts_gap > 0:
        rows = db.execute(
            "SELECT chunk_id FROM chunks"
            " WHERE chunk_id NOT IN (SELECT id FROM chunks_fts_docsize)"
            " ORDER BY chunk_id LIMIT 10"
        ).fetchall()
        affected_chunk_ids = tuple(r[0] for r in rows)
        doc_rows = db.execute(
            "SELECT c.doc_id FROM chunks c"
            " WHERE c.chunk_id NOT IN (SELECT id FROM chunks_fts_docsize)"
            " ORDER BY c.doc_id LIMIT 10"
        ).fetchall()
        affected_doc_ids = tuple(r[0] for r in doc_rows) if doc_rows else None
    if orphan_vec_count > 0:
        id_rows = db.execute(
            "SELECT chunk_id FROM chunks_vec"
            " WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
            " ORDER BY chunk_id LIMIT 10"
        ).fetchall()
        affected_orphan_chunk_ids = tuple(r[0] for r in id_rows)
        url_rows = db.execute(
            "SELECT DISTINCT d.url FROM chunks_vec cv"
            " LEFT JOIN chunks c ON cv.chunk_id = c.chunk_id"
            " LEFT JOIN documents d ON c.doc_id = d.doc_id"
            " WHERE c.chunk_id IS NULL AND d.url IS NOT NULL"
            " ORDER BY d.url LIMIT 10"
        ).fetchall()
        affected_orphan_urls = tuple(r[0] for r in url_rows) if url_rows else None

    report = RagConsistencyReport(
        chunks=chunks,
        fts=fts,
        vec=vec,
        orphan_vec_count=orphan_vec_count,
        fts_gap=fts_gap,
        fts_orphan_count=fts_orphan_count,
        embed_failed=embed_failed,
        affected_chunk_ids=affected_chunk_ids,
        affected_doc_ids=affected_doc_ids,
        affected_orphan_chunk_ids=affected_orphan_chunk_ids,
        affected_orphan_urls=affected_orphan_urls,
    )
    return dataclasses.replace(report, issues=tuple(summarize_issues(report)))


def is_consistent(report: RagConsistencyReport) -> bool:
    """Return True when fts_gap == 0, fts_orphan_count == 0, orphan_vec_count == 0, and vec == chunks."""
    return (
        report.fts_gap == 0
        and report.fts_orphan_count == 0
        and report.orphan_vec_count == 0
        and report.vec == report.chunks
    )


def summarize_issues(report: RagConsistencyReport) -> list[str]:
    """Return severity-prefixed descriptions of consistency issues with repair guidance."""
    issues: list[str] = []
    if report.fts_gap > 0:
        detail = ""
        if report.affected_doc_ids:
            ids = ", ".join(str(i) for i in report.affected_doc_ids[:10])
            truncated = " ..." if len(report.affected_doc_ids) == 10 else ""
            detail = f" Affected doc_ids: [{ids}{truncated}]."
        elif report.affected_chunk_ids:
            ids = ", ".join(str(i) for i in report.affected_chunk_ids[:10])
            truncated = " ..." if len(report.affected_chunk_ids) == 10 else ""
            detail = f" Affected chunk_ids: [{ids}{truncated}]."
        issues.append(
            f"[WARNING] FTS gap detected (chunks={report.chunks}, fts={report.fts},"
            f" gap={report.fts_gap}).{detail} Run '/db rebuild-fts' to repair."
        )
    if report.fts_orphan_count > 0:
        detail = ""
        if report.affected_doc_ids:
            ids = ", ".join(str(i) for i in report.affected_doc_ids[:10])
            truncated = " ..." if len(report.affected_doc_ids) == 10 else ""
            detail = f" Affected doc_ids: [{ids}{truncated}]."
        issues.append(
            f"[CRITICAL] FTS index has more entries than chunks"
            f" (fts={report.fts}, chunks={report.chunks}).{detail}"
            f" Run '/db rebuild-fts' immediately; orphan FTS entries indicate data loss risk."
        )
    if report.orphan_vec_count > 0:
        detail = ""
        if report.affected_orphan_urls:
            urls = ", ".join(report.affected_orphan_urls[:5])
            truncated = " ..." if len(report.affected_orphan_urls) == 10 else ""
            detail = f" Affected URLs: [{urls}{truncated}]."
        elif report.affected_orphan_chunk_ids:
            ids = ", ".join(str(i) for i in report.affected_orphan_chunk_ids[:10])
            detail = f" Affected chunk_ids: [{ids}]."
        issues.append(
            f"[CRITICAL] Orphan vec rows detected (count={report.orphan_vec_count}).{detail}"
            f" Re-run ingestion with 'ingester.py --force' for affected URLs."
        )
    if report.vec != report.chunks:
        detail = ""
        if report.affected_orphan_urls:
            urls = ", ".join(report.affected_orphan_urls[:5])
            truncated = " ..." if len(report.affected_orphan_urls) == 10 else ""
            detail = f" Affected URLs: [{urls}{truncated}]."
        elif report.affected_orphan_chunk_ids:
            ids = ", ".join(str(i) for i in report.affected_orphan_chunk_ids[:10])
            detail = f" Affected chunk_ids: [{ids}]."
        issues.append(
            f"[WARNING] Vector count mismatch (chunks={report.chunks}, vec={report.vec}).{detail}"
            f" Re-run ingestion with 'ingester.py --force' for affected URLs."
        )
    return issues
