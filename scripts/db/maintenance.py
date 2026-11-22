#!/usr/bin/env python3
"""scripts/db/maintenance.py

SQLite operational maintenance: WAL checkpoint, VACUUM, DB rotation,
session retention, and corruption recovery.

All functions take an open SQLiteHelper instance or operate on the DB file path
from the typed configuration supplied by the owning process.  None of them modify
the SQLiteHelper class — they encode policy decisions that sit above the
connection layer. This module reads no configuration file.

Typical maintenance schedule:
  After large ingestion : checkpoint_wal(db, "TRUNCATE")
  Weekly                : vacuum_db(db)
  Weekly                : purge_old_sessions(db, cfg)
  Weekly                : purge_corrupt_archives(cfg, db_cfg)
  Weekly                : purge_archive_artifacts()
  Before schema change  : rotate_all_dbs(db_cfg, maintenance)  # rag, session, workflow
  On startup warning    : recover_corruption(db_config, backup_path)
"""

import logging
import sqlite3
import time
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from shared.config_utils import get_str, get_typed

from db.config import DbConfig
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
        raise exc
    return MaintenanceResult(
        success=False,
        action=f"{action}_failed",
        mode=mode,
        detail=str(exc),
        data=extra_data,
    )


# ── Config helpers ─────────────────────────────────────────────────────────────


def _retention_guard(value: int, key: str) -> bool:
    """Retention-limit guard shared by the delete helpers.

    Returns True when the rule is disabled (``value == 0``); a negative value
    raises a key-naming ValueError.
    """
    if value < 0:
        raise ValueError(f"'{key}' must be >= 0, got {value}")
    return value == 0


def _non_negative_int(cfg: dict[str, Any], key: str, default: int) -> int:
    """Read an int config key via get_typed; negative values raise a key-naming ValueError."""
    value: int = get_typed(cfg, key, int, "an integer", default=default)
    _retention_guard(value, key)
    return value


# ── Typed maintenance configuration ────────────────────────────────────────────


@dataclass(frozen=True)
class DbMaintenanceConfig:
    """Typed maintenance configuration supplied by the process that owns the config file.

    Groups the checkpoint, session-retention, rotation-archive, corrupt-archive,
    drill-artifact and quarantine settings that config/agent.toml exposes as
    separate top-level keys. This module never reads a configuration file: the
    owning process supplies the mapping, which `from_mapping()` validates
    (REQ-004).

    Semantics: 0 disables the corresponding rule; negative values are rejected
    with a key-naming ValueError at construction. `archive_dir` stays empty when
    the key is absent, and `db.rotation._resolve_archive_dir()` then applies the
    documented hardcoded fallback.
    """

    wal_checkpoint_mode: str = "TRUNCATE"
    archive_dir: str = ""
    retention_max_sessions: int = 100
    retention_max_age_days: int = 90
    archive_max_files: int = 14
    archive_max_age_days: int = 30
    corrupt_archive_max_files: int = 10
    corrupt_archive_max_age_days: int = 30
    drill_artifact_max_files: int = 14
    drill_artifact_max_age_days: int = 30
    quarantine_max_files: int = 10
    quarantine_max_age_days: int = 90

    @classmethod
    def from_mapping(cls, cfg: Mapping[str, Any]) -> "DbMaintenanceConfig":
        """Build the typed configuration from the mapping supplied by the owning process.

        Wrong-typed or negative values raise a key-naming ValueError; an absent
        key falls back to the documented default.
        """
        cfg_dict = dict(cfg)
        raw_mode = cfg_dict.get("sqlite_wal_checkpoint_mode")
        if raw_mode is None or not isinstance(raw_mode, str):
            raw_mode = "TRUNCATE"
        return cls(
            wal_checkpoint_mode=raw_mode.upper(),
            archive_dir=get_str(cfg_dict, "sqlite_archive_dir", ""),
            retention_max_sessions=_non_negative_int(
                cfg_dict, "sqlite_retention_max_sessions", 100
            ),
            retention_max_age_days=_non_negative_int(
                cfg_dict, "sqlite_retention_max_age_days", 90
            ),
            archive_max_files=_non_negative_int(
                cfg_dict, "sqlite_archive_max_files", 14
            ),
            archive_max_age_days=_non_negative_int(
                cfg_dict, "sqlite_archive_max_age_days", 30
            ),
            corrupt_archive_max_files=_non_negative_int(
                cfg_dict, "sqlite_corrupt_archive_max_files", 10
            ),
            corrupt_archive_max_age_days=_non_negative_int(
                cfg_dict, "sqlite_corrupt_archive_max_age_days", 30
            ),
            drill_artifact_max_files=_non_negative_int(
                cfg_dict, "sqlite_drill_artifact_max_files", 14
            ),
            drill_artifact_max_age_days=_non_negative_int(
                cfg_dict, "sqlite_drill_artifact_max_age_days", 30
            ),
            quarantine_max_files=_non_negative_int(
                cfg_dict, "sqlite_quarantine_max_files", 10
            ),
            quarantine_max_age_days=_non_negative_int(
                cfg_dict, "sqlite_quarantine_max_age_days", 90
            ),
        )


# ── Policy dataclasses ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RetentionConfig:
    """Session retention policy: max_sessions keeps most-recent N sessions; max_age_days deletes sessions older than N days.

    Semantics: 0 disables the corresponding rule (deletes nothing); negative
    values are rejected with ValueError when the typed configuration is built and
    in the purge helpers.
    """

    max_sessions: int = 100
    max_age_days: int = 90

    @classmethod
    def from_typed(cls, m: DbMaintenanceConfig) -> "RetentionConfig":
        """Project the session-retention fields of the injected typed configuration."""
        return cls(
            max_sessions=m.retention_max_sessions,
            max_age_days=m.retention_max_age_days,
        )


@dataclass(frozen=True)
class CorruptArchiveRetentionConfig:
    """Retention policy for timestamped *_corrupt_* archive files created by
    db.recovery._restore_from_backup() before restoring; max_files keeps the
    most-recent N archives per source database; max_age_days deletes archives
    older than N days.

    Semantics: 0 disables the corresponding rule (deletes nothing); negative
    values are rejected with ValueError when the typed configuration is built and
    in the purge helpers.
    """

    max_files: int = 10
    max_age_days: int = 30

    @classmethod
    def from_typed(cls, m: DbMaintenanceConfig) -> "CorruptArchiveRetentionConfig":
        """Project the corrupt-archive fields of the injected typed configuration."""
        return cls(
            max_files=m.corrupt_archive_max_files,
            max_age_days=m.corrupt_archive_max_age_days,
        )


# ── Maintenance operations ─────────────────────────────────────────────────────


def checkpoint_wal(
    db: SQLiteHelper,
    maintenance: DbMaintenanceConfig,
    mode: str | None = None,
) -> WalCheckpointCounts:
    """Flush the WAL file and return checkpoint counters.

    `mode` overrides the default; when it is absent the mode comes from the
    injected typed configuration. Raises ValueError for an unknown mode.
    """
    if mode is None:
        mode = maintenance.wal_checkpoint_mode
    return db.checkpoint(mode)


def vacuum_db(
    db: SQLiteHelper, mode: MaintenanceMode = MaintenanceMode.STRICT
) -> MaintenanceResult:
    """Run VACUUM to rebuild the DB file and reclaim freed pages.

    In STRICT mode (default), raises on failure.
    In BEST_EFFORT mode, returns MaintenanceResult(success=False, detail=str(exc)).
    Catches any sqlite3.Error (not only OperationalError) plus RuntimeError.
    This function performs no config loading; elsewhere in this module
    config-load failures propagate in both modes.
    Cannot run inside a transaction; requires ~2× DB size in free disk space.
    """
    try:
        db.vacuum()
        return MaintenanceResult(success=True, action="vacuum", mode=mode)
    except (sqlite3.Error, RuntimeError) as e:
        return _handle_maintenance_error(e, "vacuum", mode)


def _delete_sessions_by_age(
    db: SQLiteHelper, max_age_days: int, keep_session_id: int | None = None
) -> tuple[int, bool]:
    """Delete sessions older than max_age_days; returns (rows deleted, exempted).

    When `keep_session_id` is given and that session is itself an age-rule delete
    candidate, it is exempted from deletion and `exempted` is True (0 if disabled).

    `max_age_days == 0` disables the rule; a negative value raises ValueError.
    """
    if _retention_guard(max_age_days, "sqlite_retention_max_age_days"):
        return 0, False
    if keep_session_id is None:
        cur = db.execute(
            "DELETE FROM sessions WHERE created_at < strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?)",
            (f"-{max_age_days} days",),
        )
        deleted = cur.rowcount
        if deleted:
            logger.info(
                "Retention: removed %s sessions older than %s days",
                deleted,
                max_age_days,
            )
        return deleted, False
    expired = db.fetchall(
        "SELECT 1 FROM sessions WHERE session_id = ? AND created_at < strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?)",
        (keep_session_id, f"-{max_age_days} days"),
    )
    cur = db.execute(
        "DELETE FROM sessions WHERE created_at < strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?) AND session_id != ?",
        (f"-{max_age_days} days", keep_session_id),
    )
    deleted = cur.rowcount
    if deleted:
        logger.info(
            "Retention: removed %s sessions older than %s days",
            deleted,
            max_age_days,
        )
    return deleted, bool(expired)


def _delete_sessions_beyond_limit(
    db: SQLiteHelper, max_sessions: int, keep_session_id: int | None = None
) -> tuple[int, bool]:
    """Delete sessions beyond the max_sessions most-recent limit; returns (rows deleted, exempted).

    The exempted `keep_session_id` does not consume a keep slot (kept count may
    exceed max_sessions by one).  Equal `created_at` ties resolve deterministically:
    the lowest `session_id` is deleted first.

    `max_sessions == 0` disables the rule; a negative value raises ValueError.
    """
    if _retention_guard(max_sessions, "sqlite_retention_max_sessions"):
        return 0, False
    rows = db.fetchall(
        "SELECT session_id FROM sessions ORDER BY created_at DESC, session_id DESC"
    )
    if len(rows) <= max_sessions:
        return 0, False
    candidates = [row[0] for row in rows[max_sessions:]]
    if keep_session_id is None:
        exempted = False
        to_delete = candidates
    else:
        exempted = keep_session_id in candidates
        to_delete = [sid for sid in candidates if sid != keep_session_id]
    if not to_delete:
        return 0, exempted  # guard emptied the list; IN () must not be built
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
    return deleted, exempted


def purge_old_sessions(
    db: SQLiteHelper,
    cfg: RetentionConfig,
    mode: MaintenanceMode = MaintenanceMode.STRICT,
    *,
    keep_session_id: int | None = None,
) -> MaintenanceResult:
    """Delete sessions exceeding the retention policy (age-based then count-based).

    Both delete rules run inside one BEGIN IMMEDIATE transaction: on any DB error
    the whole purge is rolled back and no partial deletions survive.

    CASCADE removes messages. In STRICT mode (default), raises on DB errors.
    In BEST_EFFORT mode, returns MaintenanceResult with zeroed counts
    (the transaction was rolled back; attempted counts are not reported).

    Negative-retention `ValueError`s raised by the delete helpers propagate in
    both modes (the transaction rolls back, so no partial deletions survive).
    `cfg` is supplied by the caller that owns the configuration; this module does
    not read a config file.

    When `keep_session_id` is given and that session was a delete candidate under at
    least one rule, it is exempted and surfaced as `data["kept_active_session"]`
    (None when nothing was exempted).
    """
    try:
        with db.begin_immediate():
            age_deleted, age_exempted = _delete_sessions_by_age(
                db, cfg.max_age_days, keep_session_id
            )
            count_deleted, count_exempted = _delete_sessions_beyond_limit(
                db, cfg.max_sessions, keep_session_id
            )
        kept = keep_session_id if (age_exempted or count_exempted) else None
        if kept is not None:
            logger.info("Retention: kept active session %s beyond retention", kept)

        return MaintenanceResult(
            success=True,
            action="purge",
            mode=mode,
            data={
                "age_deleted": age_deleted,
                "count_deleted": count_deleted,
                "kept_active_session": kept,
            },
        )
    except sqlite3.Error as e:
        return _handle_maintenance_error(
            e,
            "purge",
            mode,
            extra_data={
                "age_deleted": 0,
                "count_deleted": 0,
                "kept_active_session": None,
            },
        )


def _delete_corrupt_archives_by_age(
    archive_dir: Path, pattern: str, max_age_days: int
) -> int:
    """Delete archives matching pattern under archive_dir older than max_age_days;
    returns count deleted (0 if disabled).

    `max_age_days == 0` disables the rule; a negative value raises ValueError.
    """
    if _retention_guard(max_age_days, "sqlite_corrupt_archive_max_age_days"):
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
    most-recent limit; returns count deleted.

    `max_files == 0` disables the rule; a negative value raises ValueError.
    """
    if _retention_guard(max_files, "sqlite_corrupt_archive_max_files"):
        return 0
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
    cfg: CorruptArchiveRetentionConfig,
    db_cfg: DbConfig,
    mode: MaintenanceMode = MaintenanceMode.STRICT,
) -> MaintenanceResult:
    """Delete timestamped *_corrupt_* archive files (created by
    db.recovery._restore_from_backup()) exceeding the retention policy
    (age-based then count-based), applied independently per source database.

    In STRICT mode (default), raises on filesystem errors.
    In BEST_EFFORT mode, returns MaintenanceResult with partial counts on error.
    Negative-retention `ValueError`s raised by the delete helpers propagate in
    both modes. The typed configuration and the database paths are supplied by the
    caller that owns the configuration; this module reads no config file.
    """
    age_deleted = 0
    count_deleted = 0

    try:
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
    This function performs no config loading; elsewhere in this module
    config-load failures propagate in both modes.
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
            data={
                "deleted": delete_result.deleted,
                "pruned_ids": list(delete_result.deleted_ids),
            },
        )
    except sqlite3.Error as e:
        return _handle_maintenance_error(e, "prune", mode)
