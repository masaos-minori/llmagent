"""scripts/agent/commands/db_session_ops.py — Session database operation handlers."""

from __future__ import annotations

from agent.commands.output_port import OutputPort
from agent.commands.utils import parse_command_args
from agent.context import AgentContext
from agent.services.db_maintenance_service import DbMaintenanceService


def _parse_optional_int(raw: str | bool | None) -> int | None:
    """Parse raw as int; return None when raw is empty/falsy or not a valid integer."""
    try:
        return int(raw) if raw else None
    except (ValueError, TypeError):
        return None


class DbSessionOps:
    """Handles session database operations: health, checkpoint, vacuum, purge, recover."""

    def __init__(self, ctx: AgentContext, out: OutputPort) -> None:
        """Initialize the database session operations handler with context and output port."""
        self._ctx = ctx
        self._out = out

    def health(self) -> None:
        """Print DB health metrics: integrity, size."""
        info = DbMaintenanceService().health()
        self._out.write_kv(
            [
                ("integrity_ok", str(info.integrity_ok)),
                ("db_size", f"{info.size_bytes:,} bytes"),
                ("target", "Session"),
            ]
        )

    def checkpoint(self, mode: str | None) -> None:
        """Run WAL checkpoint. mode: PASSIVE|FULL|RESTART|TRUNCATE (default from config)."""
        result = DbMaintenanceService().checkpoint(mode)
        self._out.write_success(
            f"WAL checkpoint complete: mode={result.mode}, pages_written={result.pages_written} [Session]"
        )

    def vacuum(self) -> None:
        """Run VACUUM to rebuild the DB file and reclaim free pages."""
        DbMaintenanceService().vacuum()
        self._out.write_success("VACUUM complete. [Session]")

    def purge(self, rest: str) -> None:
        """Purge old sessions. Options: --max-sessions N --max-age-days N"""
        parsed = parse_command_args(rest.split())
        max_sessions = _parse_optional_int(parsed.flags.get("max-sessions"))
        max_age_days = _parse_optional_int(parsed.flags.get("max-age-days"))
        result = DbMaintenanceService().purge(max_sessions, max_age_days)
        self._out.write_success(
            f"Purged: {result.sessions_removed} session(s) removed [Session]"
        )

    def recover(self, backup_path: str | None) -> None:
        """Run integrity check on session.sqlite; restore from backup_path if corruption found."""
        result = DbMaintenanceService().recover_session(backup_path)
        if result.integrity_ok:
            self._out.write_success(f"Recovery succeeded: {result.detail} [Session]")
        else:
            self._out.write_no_data(f"Recovery failed: {result.detail} [Session]")
