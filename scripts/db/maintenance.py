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
  Before schema change  : rotate_all_dbs()  # archives rag, session, and workflow
  On startup warning    : recover_corruption()
"""

import logging
import sqlite3
from dataclasses import dataclass
from enum import StrEnum

from shared.config_loader import ConfigLoader

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
        """Construct from agent.toml values; raises on config load failure."""
        cfg = ConfigLoader().load("agent.toml")
        return cls(
            max_sessions=int(cfg.get("sqlite_retention_max_sessions", 100)),
            max_age_days=int(cfg.get("sqlite_retention_max_age_days", 90)),
        )


# ── Maintenance operations ─────────────────────────────────────────────────────


def checkpoint_wal(db: SQLiteHelper, mode: str | None = None) -> WalCheckpointCounts:
    """Flush the WAL file and return checkpoint counters; mode defaults to sqlite_wal_checkpoint_mode (TRUNCATE); raises ValueError for unknown mode."""
    if mode is None:
        cfg = ConfigLoader().load("agent.toml")
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
