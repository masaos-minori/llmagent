#!/usr/bin/env python3
"""
db_maintenance.py
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

logger = logging.getLogger(__name__)

_cfg: dict | None = None


def _get_cfg() -> dict:
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("common.toml")
        except Exception as e:
            logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


# ── Policy dataclass ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RetentionConfig:
    """Session retention policy parameters.

    max_sessions: keep this many most-recent sessions; delete older ones.
    max_age_days: delete sessions created before this many days ago (0 = disabled).
    """

    max_sessions: int = 100
    max_age_days: int = 90

    @classmethod
    def from_config(cls) -> "RetentionConfig":
        """Construct from common.toml values."""
        cfg = _get_cfg()
        return cls(
            max_sessions=int(cfg.get("sqlite_retention_max_sessions", 100)),
            max_age_days=int(cfg.get("sqlite_retention_max_age_days", 90)),
        )


# ── Maintenance operations ─────────────────────────────────────────────────────


def checkpoint_wal(db: SQLiteHelper, mode: str | None = None) -> dict[str, int]:
    """Flush the WAL file and return checkpoint counters.

    mode defaults to sqlite_wal_checkpoint_mode from common.toml (TRUNCATE).
    Valid values: PASSIVE, FULL, RESTART, TRUNCATE.

    Returns {"busy": 0|1, "pages_in_wal": n, "pages_checkpointed": n}.
    Raises ValueError for an unrecognised mode.
    """
    if mode is None:
        mode = _get_cfg().get("sqlite_wal_checkpoint_mode", "TRUNCATE").upper()
    return db.checkpoint(mode)


def vacuum_db(db: SQLiteHelper) -> None:
    """Run VACUUM to rebuild the DB file and reclaim freed pages.

    Cannot run inside a transaction; call on a freshly opened connection
    before any writes.  Requires ~2× DB size in free disk space.
    """
    db.vacuum()


def purge_old_sessions(
    db: SQLiteHelper, cfg: RetentionConfig | None = None
) -> dict[str, int]:
    """Delete sessions that exceed the retention policy.

    Applies two independent rules in sequence:
    1. Age-based: delete sessions created more than cfg.max_age_days days ago.
    2. Count-based: if more than cfg.max_sessions rows remain, delete the oldest.

    ON DELETE CASCADE removes messages automatically.
    Returns {"age_deleted": n, "count_deleted": n}.
    db must be opened on session.sqlite (SQLiteHelper("session")).
    """
    if cfg is None:
        cfg = RetentionConfig.from_config()

    assert db.conn is not None, "DB not open"
    age_deleted = 0
    count_deleted = 0

    if cfg.max_age_days > 0:
        cur = db.conn.execute(
            "DELETE FROM sessions WHERE created_at < datetime('now', ?)",
            (f"-{cfg.max_age_days} days",),
        )
        age_deleted = cur.rowcount
        if age_deleted:
            logger.info(
                f"Retention: removed {age_deleted} sessions"
                f" older than {cfg.max_age_days} days"
            )

    rows = db.conn.execute(
        "SELECT session_id FROM sessions ORDER BY created_at DESC"
    ).fetchall()
    if len(rows) > cfg.max_sessions:
        to_delete = [row[0] for row in rows[cfg.max_sessions :]]
        placeholders = ",".join("?" * len(to_delete))
        cur = db.conn.execute(
            f"DELETE FROM sessions WHERE session_id IN ({placeholders})",
            to_delete,
        )
        count_deleted = cur.rowcount
        logger.info(
            f"Retention: removed {count_deleted} sessions"
            f" beyond limit of {cfg.max_sessions}"
        )

    db.conn.commit()
    return {"age_deleted": age_deleted, "count_deleted": count_deleted}


def _archive_db_file(db_path: Path, archive_dir: str | Path | None) -> Path:
    """Copy a single DB file (plus WAL/SHM side-files) to the archive directory."""
    if not db_path.exists():
        raise FileNotFoundError(f"DB file not found: {db_path}")

    if archive_dir is None:
        archive_dir = _get_cfg().get("sqlite_archive_dir", "/opt/llm/db/archive")

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
    """Archive rag.sqlite to archive_dir with a timestamp suffix.

    Returns the path of the created archive file.
    """
    SQLiteHelper._ensure_config()
    return _archive_db_file(Path(SQLiteHelper._RAG_PATH), archive_dir)


def rotate_session_db(archive_dir: str | Path | None = None) -> Path:
    """Archive session.sqlite to archive_dir with a timestamp suffix.

    Returns the path of the created archive file.
    """
    SQLiteHelper._ensure_config()
    return _archive_db_file(Path(SQLiteHelper._SESSION_PATH), archive_dir)


def rotate_db(archive_dir: str | Path | None = None) -> tuple[Path, Path]:
    """Archive both rag.sqlite and session.sqlite.

    Returns (rag_archive_path, session_archive_path).
    """
    rag_dest = rotate_rag_db(archive_dir)
    ses_dest = rotate_session_db(archive_dir)
    return rag_dest, ses_dest


def recover_corruption(backup_path: str | Path | None = None) -> bool:
    """Detect and recover from corruption in rag.sqlite.

    Recovery procedure:
    1. Run PRAGMA integrity_check (full scan).
    2. If the check passes: run VACUUM to defragment, then return True.
    3. If the check fails and backup_path is given:
       a. Archive the corrupt file with a timestamp suffix.
       b. Copy backup_path over DB_PATH.
       c. Return True on success, False on any OS error.
    4. If the check fails and no backup is given: log the error, return False.
    """
    SQLiteHelper._ensure_config()
    db_path = Path(SQLiteHelper._RAG_PATH)

    try:
        with SQLiteHelper("rag").open() as db:
            assert db.conn is not None
            result = db.conn.execute("PRAGMA integrity_check").fetchone()[0]
    except Exception as e:
        logger.error(f"Cannot open DB for integrity check: {e}")
        return False

    if result == "ok":
        logger.info("Integrity check passed; running VACUUM")
        try:
            with SQLiteHelper("rag").open(write_mode=True) as db:
                db.vacuum()
        except Exception as e:
            logger.warning(f"VACUUM after integrity check failed: {e}")
        return True

    logger.error(f"Integrity check failed: {result}")

    if backup_path is None:
        logger.error("No backup_path provided — manual recovery required")
        return False

    backup = Path(backup_path)
    if not backup.exists():
        logger.error(f"Backup not found: {backup}")
        return False

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    corrupt_archive = db_path.with_name(f"{db_path.stem}_corrupt_{ts}{db_path.suffix}")
    try:
        shutil.copy2(db_path, corrupt_archive)
        logger.info(f"Corrupt DB archived: {corrupt_archive}")
        shutil.copy2(backup, db_path)
        logger.info(f"DB restored from backup: {backup}")
        return True
    except OSError as e:
        logger.error(f"Recovery failed: {e}")
        return False
