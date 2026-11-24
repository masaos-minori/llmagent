"""scripts/agent/services/db_maintenance_service.py

DbMaintenanceService — maintenance operations on session.sqlite only.
"""

from __future__ import annotations

import threading
from dataclasses import replace

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
        """
        effective = mode or self._maintenance.wal_checkpoint_mode
        with SQLiteHelper("session", db_config=self._db_config).open(
            write_mode=True
        ) as db:
            counts = checkpoint_wal(db, self._maintenance, effective, stop=stop)
        return DbCheckpointResult(
            mode=effective,
            pages_written=counts.pages_checkpointed,
            interrupted=counts.interrupted,
        )

    def vacuum(self, *, stop: threading.Event | None = None) -> DbVacuumResult:
        """Run VACUUM on session.sqlite and report the run as the primitive measured it."""
        with SQLiteHelper("session", db_config=self._db_config).open(
            write_mode=True
        ) as db:
            raw = vacuum_db(db, stop=stop)
        return DbVacuumResult(
            mode=raw.mode.value,
            interrupted=raw.interrupted,
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
        """
        cfg = _resolve_retention(self._maintenance, max_sessions, max_age_days)
        with SQLiteHelper("session", db_config=self._db_config).open(
            write_mode=True
        ) as db:
            raw = purge_old_sessions(
                db, cfg, keep_session_id=current_session_id, stop=stop
            )
        data = raw.data or {}
        return DbPurgeResult(
            sessions_removed=data.get("age_deleted", 0) + data.get("count_deleted", 0),
            kept_active_session=data.get("kept_active_session"),
            interrupted=raw.interrupted,
        )

    def recover_session(
        self, backup_path: str | None, *, stop: threading.Event | None = None
    ) -> DbRecoverResult:
        """Run integrity check on session.sqlite; restore from backup_path if corruption found."""
        raw = recover_corruption(self._db_config, backup_path, target="session")
        return DbRecoverResult(
            integrity_ok=raw.success,
            recovered=raw.action == "restored",
            detail=raw.detail or "",
            logical_ok=raw.logical_ok,
            interrupted=bool(stop is not None and stop.is_set()),
        )


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
