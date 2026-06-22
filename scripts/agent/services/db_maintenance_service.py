"""agent/services/db_maintenance_service.py
DbMaintenanceService — maintenance operations on session.sqlite only.

Extracted from cmd_db._DbMixin so the DB logic can be tested
independently of the REPL command layer.
"""

from __future__ import annotations

from typing import Any

from db.helper import SQLiteHelper
from db.maintenance import (
    RetentionConfig,
    checkpoint_wal,
    purge_old_sessions,
    recover_corruption,
    vacuum_db,
)

from agent.services.models import (
    DbCheckpointResult,
    DbHealth,
    DbPurgeResult,
    DbRecoverResult,
    DbStats,
)


class DbMaintenanceService:
    """Wraps maintenance operations on session.sqlite only."""

    def stats(self) -> DbStats:
        """Return session/message counts from session.sqlite."""
        with SQLiteHelper("session").open(row_factory=True) as db:
            sessions = self._count_table(db, "sessions")
            messages = self._count_table(db, "messages")
        return DbStats(docs=0, chunks=0, sessions=sessions, messages=messages)

    @staticmethod
    def _count_table(db: Any, table: str) -> int:
        """Return row count for a single table."""
        return int(db.fetchall(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"])  # nosec B608 — table is always a hardcoded name, never user input

    def health(self) -> DbHealth:
        """Return DB health metrics from session.sqlite."""
        with SQLiteHelper("session").open() as db:
            raw = db.health_check()
        return DbHealth(
            integrity_ok=raw.integrity == "ok",
            wal_pages=0,
            size_bytes=raw.db_size_bytes,
        )

    def checkpoint(self, mode: str | None) -> DbCheckpointResult:
        """Run WAL checkpoint on session.sqlite."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            raw = checkpoint_wal(db, mode)
        return DbCheckpointResult(
            mode=mode or "TRUNCATE",
            pages_written=raw.pages_checkpointed,
        )

    def vacuum(self) -> None:
        """Run VACUUM on session.sqlite."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            vacuum_db(db)

    def purge(
        self, max_sessions: int | None, max_age_days: int | None
    ) -> DbPurgeResult:
        """Purge old sessions per retention config."""
        cfg = _build_retention_config(max_sessions, max_age_days)
        with SQLiteHelper("session").open(write_mode=True) as db:
            raw = purge_old_sessions(db, cfg)
        data = raw.data or {}
        return DbPurgeResult(
            sessions_removed=data.get("age_deleted", 0) + data.get("count_deleted", 0),
        )

    def recover_session(self, backup_path: str | None) -> DbRecoverResult:
        """Run integrity check on session.sqlite; restore from backup_path if corruption found."""
        raw = recover_corruption(backup_path, target="session")
        return DbRecoverResult(
            integrity_ok=raw.success,
            recovered=raw.action == "restored",
            detail=raw.detail or "",
        )


def _build_retention_config(
    max_sessions: int | None, max_age_days: int | None
) -> RetentionConfig | None:
    """Build a RetentionConfig from optional parameters."""
    kwargs: dict[str, int] = {}
    if max_sessions is not None:
        kwargs["max_sessions"] = max_sessions
    if max_age_days is not None:
        kwargs["max_age_days"] = max_age_days
    return RetentionConfig(**kwargs) if kwargs else None
