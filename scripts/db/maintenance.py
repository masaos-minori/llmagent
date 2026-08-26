#!/usr/bin/env python3
"""scripts/db/maintenance.py

SQLite operational maintenance: WAL checkpoint, VACUUM, DB rotation,
session retention, and corruption recovery.

All functions take an open SQLiteHelper instance or operate directly on the
DB file path loaded from config.  None of them modify the SQLiteHelper class —
they encode policy decisions that sit above the connection layer.

Typical maintenance schedule:
  After large ingestion : checkpoint_wal(db, "TRUNCATE")
  Weekly                : vacuum_db(db)
  Weekly                : purge_old_sessions(db, cfg)
  Weekly                : purge_corrupt_archives()
  Before schema change  : rotate_all_dbs()  # archives rag, session, workflow, and eventbus
  On startup warning    : recover_corruption()
"""

import logging
import sqlite3
import time
from dataclasses import dataclass
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
    """Mode controlling how database maintenance operations handle errors."""

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


# ── Error handling helper ──────────────────────────────────────────────────────


def _handle_maintenance_error(
    exc: Exception,
    action: str,
    mode: MaintenanceMode,
    *,
    extra_data: dict | None = None,
) -> MaintenanceResult:
    """Handle an error from a maintenance operation.

    Returns a MaintenanceResult(success=False) in BEST_EFFORT mode,
    or re-raises the exception in STRICT mode.
    """
    logger.error("%s failed: %s", action, exc)
    if mode == MaintenanceMode.STRICT:
        raise
    return MaintenanceResult(
        success=False,
        action=f"{action}_failed",
        mode=mode,
        detail=str(exc),
        data=extra_data,
    )


# ── Config loading helper ──────────────────────────────────────────────────────


def _load_agent_config():
    """Load agent.toml — shared entry point for maintenance-related config keys."""
    return ConfigLoader().load("agent.toml")


# ── Policy dataclasses ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RetentionConfig:
    """Session retention policy: max_sessions keeps most-recent N sessions; max_age_days deletes sessions older than N days (0=disabled)."""

    max_sessions: int = 100
    max_age_days: int = 90

    @classmethod
    def from_config(cls) -> "RetentionConfig":
        """Construct from agent.toml values; raises on config load failure."""
        cfg = _load_agent_config()
        return cls(
            max_sessions=int(cfg.get("sqlite_retention_max_sessions", 100)),
            max_age_days=int(cfg.get("sqlite_retention_max_age_days", 90)),
        )


@dataclass(frozen=True)
class CorruptArchiveRetentionConfig:
    """Retention policy for timestamped *_corrupt_* archive files created by
    db.recovery._restore_from_backup() before restoring; max_files keeps the
    most-recent N archives per source database; max_age_days deletes archives
    older than N days (0=disabled)."""

    max_files: int = 10
    max_age_days: int = 30

    @classmethod
    def from_config(cls) -> "CorruptArchiveRetentionConfig":
        """Construct from agent.toml values; raises on config load failure."""
        cfg = _load_agent_config()
        return cls(
            max_files=int(cfg.get("sqlite_corrupt_archive_max_files", 10)),
            max_age_days=int(cfg.get("sqlite_corrupt_archive_max_age_days", 30)),
        )


# ── Maintenance operations ─────────────────────────────────────────────────────


def checkpoint_wal(db: SQLiteHelper, mode: str | None = None) -> WalCheckpointCounts:
    """Flush the WAL file and return checkpoint counters; mode defaults to sqlite_wal_checkpoint_mode (TRUNCATE); raises ValueError for unknown mode."""
    if mode is None:
        cfg = _load_agent_config()
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
        return _handle_maintenance_error(e, "vacuum", mode)


def _delete_sessions_by_age(db: SQLiteHelper, max_age_days: int) -> int:
    """Delete sessions older than max_age_days; returns rows deleted (0 if disabled)."""
    if max_age_days <= 0:
        return 0
    cur = db.execute(
        "DELETE FROM sessions WHERE created_at < datetime('now', ?)",
        (f"-{max_age_days} days",),
    )
    deleted = cur.rowcount
    if deleted:
        logger.info(
            "Retention: removed %s sessions older than %s days",
            deleted,
            max_age_days,
        )
    return deleted


def _delete_sessions_beyond_limit(db: SQLiteHelper, max_sessions: int) -> int:
    """Delete sessions beyond the max_sessions most-recent limit; returns rows deleted."""
    rows = db.fetchall("SELECT session_id FROM sessions ORDER BY created_at DESC")
    if len(rows) <= max_sessions:
        return 0
    to_delete = [row[0] for row in rows[max_sessions:]]
    placeholders = ",".join("?" * len(to_delete))
    cur = db.execute(
        f"DELETE FROM sessions WHERE session_id IN ({placeholders})",  # nosec B608 — placeholders is "?" * n, not user input
        tuple(to_delete),
    )
    deleted = cur.rowcount
    logger.info(
        "Retention: removed %s sessions beyond limit of %s",
        deleted,
        max_sessions,
    )
    return deleted


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
        age_deleted = _delete_sessions_by_age(db, cfg.max_age_days)
        count_deleted = _delete_sessions_beyond_limit(db, cfg.max_sessions)

        db.commit()
        return MaintenanceResult(
            success=True,
            action="purge",
            mode=mode,
            data={"age_deleted": age_deleted, "count_deleted": count_deleted},
        )
    except sqlite3.Error as e:
        return _handle_maintenance_error(
            e,
            "purge",
            mode,
            extra_data={"age_deleted": age_deleted, "count_deleted": count_deleted},
        )


def _delete_corrupt_archives_by_age(
    archive_dir: Path, pattern: str, max_age_days: int
) -> int:
    """Delete archives matching pattern under archive_dir older than max_age_days;
    returns count deleted (0 if disabled)."""
    if max_age_days <= 0:
        return 0
    threshold = time.time() - max_age_days * 86400
    deleted = 0
    for path in archive_dir.glob(pattern):
        if path.stat().st_mtime < threshold:
            path.unlink()
            deleted += 1
    if deleted:
        logger.info(
            "Retention: removed %s corrupt archives older than %s days",
            deleted,
            max_age_days,
        )
    return deleted


def _delete_corrupt_archives_beyond_limit(
    archive_dir: Path, pattern: str, max_files: int
) -> int:
    """Delete archives matching pattern under archive_dir beyond the max_files
    most-recent limit; returns count deleted."""
    paths = sorted(
        archive_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if len(paths) <= max_files:
        return 0
    to_delete = paths[max_files:]
    for path in to_delete:
        path.unlink()
    deleted = len(to_delete)
    logger.info(
        "Retention: removed %s corrupt archives beyond limit of %s",
        deleted,
        max_files,
    )
    return deleted


def purge_corrupt_archives(
    cfg: CorruptArchiveRetentionConfig | None = None,
    mode: MaintenanceMode = MaintenanceMode.STRICT,
) -> MaintenanceResult:
    """Delete timestamped *_corrupt_* archive files (created by
    db.recovery._restore_from_backup()) exceeding the retention policy
    (age-based then count-based), applied independently per source database.

    In STRICT mode (default), raises on filesystem errors.
    In BEST_EFFORT mode, returns MaintenanceResult with partial counts on error.
    """
    if cfg is None:
        cfg = CorruptArchiveRetentionConfig.from_config()

    age_deleted = 0
    count_deleted = 0

    try:
        db_cfg = build_db_config()
        for raw_path in (db_cfg.rag_db_path, db_cfg.session_db_path):
            db_path = Path(raw_path)
            archive_dir = db_path.parent
            pattern = f"{db_path.stem}_corrupt_*{db_path.suffix}"
            age_deleted += _delete_corrupt_archives_by_age(
                archive_dir, pattern, cfg.max_age_days
            )
            count_deleted += _delete_corrupt_archives_beyond_limit(
                archive_dir, pattern, cfg.max_files
            )

        return MaintenanceResult(
            success=True,
            action="purge_corrupt_archives",
            mode=mode,
            data={"age_deleted": age_deleted, "count_deleted": count_deleted},
        )
    except OSError as e:
        return _handle_maintenance_error(
            e,
            "purge_corrupt_archives",
            mode,
            extra_data={"age_deleted": age_deleted, "count_deleted": count_deleted},
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
        return _handle_maintenance_error(e, "prune", mode)
