"""stats_display.py — Database stats display logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.commands.output_port import OutputPort

from agent.services.db_maintenance_service import DbMaintenanceService


class DbStatsDisplay:
    """Provides stats display methods for /db subcommands."""

    _out: OutputPort  # provided by MixinBase via MRO

    def _db_stats(self) -> None:
        """Print session/message counts from the Session database."""
        result = DbMaintenanceService().stats()
        self._out.write_kv(
            [
                ("sessions", f"{result.sessions:,}"),
                ("messages", f"{result.messages:,}"),
                ("target", "Session"),
            ]
        )

    def _db_session_stats(self) -> None:
        """Print session/message counts from the Session database."""
        result = DbMaintenanceService().stats()
        self._out.write_kv(
            [
                ("sessions", f"{result.sessions:,}"),
                ("messages", f"{result.messages:,}"),
                ("target", "Session"),
            ]
        )
