"""scripts/agent/commands/db_session_ops.py — Session database operation handlers.

Each operation takes the job's cancellation event and returns its result object;
none of them emits the success line. The caller reports the job id and the terminal
state from that result, so an interrupted run cannot print success (REQ-004).
`health` stays read-only and returns its measurements unchanged.
"""

from __future__ import annotations

import threading

from agent.commands.exceptions import CommandValidationError
from agent.commands.output_port import OutputPort
from agent.commands.utils import parse_command_args, parse_int_arg
from agent.context import AgentContext
from agent.services.db_maintenance_service import DbMaintenanceService
from agent.services.models import (
    DbCheckpointResult,
    DbHealth,
    DbPurgeResult,
    DbRecoverResult,
    DbVacuumResult,
)


class DbSessionOps:
    """Handles session database operations: health, checkpoint, vacuum, purge, recover."""

    def __init__(self, ctx: AgentContext, out: OutputPort) -> None:
        """Initialize the database session operations handler with context and output port."""
        self._ctx = ctx
        self._out = out
        self._service: DbMaintenanceService | None = None

    def _service_for_call(self) -> DbMaintenanceService:
        """Return the service instance this handler keeps, so one instance carries every run."""
        if self._service is None:
            self._service = DbMaintenanceService(
                self._ctx.cfg.db, self._ctx.cfg.maintenance
            )
        return self._service

    def health(self) -> DbHealth:
        """Return DB health metrics: integrity, size. Read-only, no writer slot."""
        return self._service_for_call().health()

    def checkpoint(
        self, mode: str | None, *, stop: threading.Event | None = None
    ) -> DbCheckpointResult:
        """Run WAL checkpoint. mode: PASSIVE|FULL|RESTART|TRUNCATE (default from config)."""
        return self._service_for_call().checkpoint(mode, stop=stop)

    def vacuum(self, *, stop: threading.Event | None = None) -> DbVacuumResult:
        """Run VACUUM to rebuild the DB file and reclaim free pages."""
        return self._service_for_call().vacuum(stop=stop)

    def purge(self, rest: str, *, stop: threading.Event | None = None) -> DbPurgeResult:
        """Purge old sessions. Options: --max-sessions N --max-age-days N"""
        parsed = parse_command_args(rest.split())
        try:
            max_sessions = parse_int_arg(
                parsed.flags.get("max-sessions"),
                usage="/session purge …",
                minimum=1,
            )
            max_age_days = parse_int_arg(
                parsed.flags.get("max-age-days"),
                usage="/session purge …",
                minimum=0,
            )
        except CommandValidationError:
            self._out.write_validation_error("/session purge …")
            return DbPurgeResult(sessions_removed=0)
        return self._service_for_call().purge(
            max_sessions,
            max_age_days,
            current_session_id=self._ctx.session.session_id,
            stop=stop,
        )

    def recover(
        self, backup_path: str | None, *, stop: threading.Event | None = None
    ) -> DbRecoverResult:
        """Run integrity check on session.sqlite; restore from backup_path if corruption found."""
        return self._service_for_call().recover_session(backup_path, stop=stop)
