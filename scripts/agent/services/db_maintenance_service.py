"""scripts/agent/services/db_maintenance_service.py

DbMaintenanceService — maintenance operations on session.sqlite only.

Each write operation measures its own postcondition after the run, so the result it
returns is the measured outcome and not the attempt (REQ-004).
"""

from __future__ import annotations

import threading
from dataclasses import replace
from pathlib import Path

from db.config import DbConfig
from db.helper import SQLiteHelper
from db.maintenance import (
    DbMaintenanceConfig,
    RetentionConfig,
    checkpoint_wal,
    purge_old_sessions,
    vacuum_db,
)
from db.recovery import recover_corruption
from shared.db_maintenance import count_table

from agent.services.models import (
    DbCheckpointResult,
    DbHealth,
    DbPurgeResult,
    DbRecoverResult,
    DbStats,
    DbVacuumResult,
)


class DbMaintenanceService:
    """Wraps maintenance operations on session.sqlite only."""

    def __init__(self, db_config: DbConfig, maintenance: DbMaintenanceConfig) -> None:
        """Accepts the typed configurations supplied by the process that owns the file.

        `db_config` resolves the database path and `maintenance` supplies the
        checkpoint and retention policy. This service reads no configuration file.
        """
        self._db_config = db_config
        self._maintenance = maintenance

    def stats(self) -> DbStats:
        """Return session/message counts from session.sqlite."""
        with SQLiteHelper("session", db_config=self._db_config).open(
            row_factory=True
        ) as db:
            sessions = count_table(db, "sessions")
            messages = count_table(db, "messages")
        return DbStats(docs=0, chunks=0, sessions=sessions, messages=messages)

    def health(self) -> DbHealth:
        """Return DB health metrics from session.sqlite."""
        with SQLiteHelper("session", db_config=self._db_config).open() as db:
            raw = db.health_check()
        return DbHealth(
            integrity_ok=raw.integrity == "ok",
            wal_pages=0,
            size_bytes=raw.db_size_bytes,
        )

    def checkpoint(
        self, mode: str | None, *, stop: threading.Event | None = None
    ) -> DbCheckpointResult:
        """Run WAL checkpoint on session.sqlite and return the measured outcome.

        `stop` is the job's cancellation event, forwarded to the primitive; the
        wrapper decides nothing about it (REQ-002).

        The postcondition re-measures `journal_mode` and the WAL size after the run, so a
        run that did not drain the WAL is reported unverified rather than as a success
        (REQ-004). A stopped run carries no postcondition values.
        """
        effective = mode or self._maintenance.wal_checkpoint_mode
        with SQLiteHelper("session", db_config=self._db_config).open(
            write_mode=True
        ) as db:
            counts = checkpoint_wal(db, self._maintenance, effective, stop=stop)
            if counts.interrupted:
                return DbCheckpointResult(
                    mode=effective,
                    pages_written=counts.pages_checkpointed,
                    interrupted=True,
                )
            journal_mode = _pragma_text(db, "PRAGMA journal_mode")
            wal_size = _file_size(f"{self._db_config.session_db_path}-wal")
        return DbCheckpointResult(
            mode=effective,
            pages_written=counts.pages_checkpointed,
            journal_mode=journal_mode,
            wal_size_bytes=wal_size,
            verified=journal_mode == "wal" and wal_size == 0,
        )

    def vacuum(self, *, stop: threading.Event | None = None) -> DbVacuumResult:
        """Run VACUUM on session.sqlite and report the run as the primitive measured it.

        The postcondition re-measures `page_count` after the run and reports the delta; the
        run is verified only when the postcondition shows nothing left to reclaim (REQ-004).
        A stopped run reports the pre-run state, not a partial delta.
        """
        with SQLiteHelper("session", db_config=self._db_config).open(
            write_mode=True
        ) as db:
            before = _pragma_int(db, "PRAGMA page_count")
            raw = vacuum_db(db, stop=stop)
            if raw.interrupted:
                return DbVacuumResult(mode=raw.mode.value, interrupted=True)
            after = _pragma_int(db, "PRAGMA page_count")
            freelist = _pragma_int(db, "PRAGMA freelist_count")
        return DbVacuumResult(
            mode=raw.mode.value,
            verified=raw.success and freelist == 0,
            page_count_before=before,
            page_count_after=after,
            pages_reclaimed=before - after,
        )

    def purge(
        self,
        max_sessions: int | None,
        max_age_days: int | None,
        *,
        current_session_id: int | None = None,
        stop: threading.Event | None = None,
    ) -> DbPurgeResult:
        """Purge old sessions per retention config; optionally guard the active session.

        `stop` is the job's cancellation event, forwarded to the primitive (REQ-002).

        The postcondition re-counts the rows after the commit and compares them with the
        rows the run reported as removed, so a run that did not re-count is not verified
        (REQ-004).
        """
        cfg = _resolve_retention(self._maintenance, max_sessions, max_age_days)
        with SQLiteHelper("session", db_config=self._db_config).open(
            write_mode=True, row_factory=True
        ) as db:
            before = count_table(db, "sessions")
            raw = purge_old_sessions(
                db, cfg, keep_session_id=current_session_id, stop=stop
            )
            data = raw.data or {}
            removed = data.get("age_deleted", 0) + data.get("count_deleted", 0)
            if raw.interrupted:
                return DbPurgeResult(
                    sessions_removed=removed,
                    kept_active_session=data.get("kept_active_session"),
                    interrupted=True,
                )
            after = count_table(db, "sessions")
        return DbPurgeResult(
            sessions_removed=removed,
            kept_active_session=data.get("kept_active_session"),
            verified=after == before - removed,
            rows_before=before,
            rows_after=after,
        )

    def recover_session(
        self, backup_path: str | None, *, stop: threading.Event | None = None
    ) -> DbRecoverResult:
        """Run integrity check on session.sqlite; restore from backup_path if corruption found.

        The recovery result is not taken as proof on its own: the integrity check is re-run
        against the file after the run, and the run is verified only when that re-check
        passes (REQ-004). A stopped run reports no postcondition.
        """
        raw = recover_corruption(self._db_config, backup_path, target="session")
        interrupted = bool(stop is not None and stop.is_set())
        if interrupted:
            return DbRecoverResult(
                integrity_ok=raw.success,
                recovered=raw.action == "restored",
                detail=raw.detail or "",
                logical_ok=raw.logical_ok,
                interrupted=True,
            )
        with SQLiteHelper("session", db_config=self._db_config).open() as db:
            post_check = _pragma_text(db, "PRAGMA quick_check")
        return DbRecoverResult(
            integrity_ok=raw.success,
            recovered=raw.action == "restored",
            detail=raw.detail or "",
            logical_ok=raw.logical_ok,
            verified=raw.success and post_check == "ok",
            post_check=post_check,
        )


def _pragma_text(db: SQLiteHelper, sql: str) -> str:
    """Read one PRAGMA value from the open connection, as the postcondition measured it."""
    row = db.execute(sql).fetchone()
    return str(row[0]) if row is not None else ""


def _pragma_int(db: SQLiteHelper, sql: str) -> int:
    """Read one PRAGMA value from the open connection as an integer."""
    row = db.execute(sql).fetchone()
    return int(row[0]) if row is not None else 0


def _file_size(path: str) -> int:
    """Return the size of a file; a missing file is 0, which is a drained WAL."""
    try:
        return Path(path).stat().st_size
    except OSError:
        return 0


def _resolve_retention(
    maintenance: DbMaintenanceConfig,
    max_sessions: int | None,
    max_age_days: int | None,
) -> RetentionConfig:
    """Build the RetentionConfig to use for one purge call.

    The typed maintenance configuration supplies the policy; a per-call override
    replaces only the field the caller passed. This is the shape the caller that
    owns the configuration must provide now that `purge_old_sessions()` takes a
    typed configuration instead of loading one.
    """
    cfg = RetentionConfig.from_typed(maintenance)
    kwargs: dict[str, int] = {}
    if max_sessions is not None:
        kwargs["max_sessions"] = max_sessions
    if max_age_days is not None:
        kwargs["max_age_days"] = max_age_days
    return replace(cfg, **kwargs) if kwargs else cfg
