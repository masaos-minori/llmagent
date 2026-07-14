"""help_display.py — Database help display logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.commands.output_port import OutputPort

# DbHelpDisplay is a mixin that provides help display methods for /db commands.


class DbHelpDisplay:
    """Provides help table display methods for /db subcommands."""

    _out: OutputPort  # provided by MixinBase via MRO

    def _db_help(self) -> None:
        """Print a help table for /db subcommands."""
        rows = [
            ["session stats", "Session", "", "Session/message counts"],
            ["session health", "Session", "", "(admin) Integrity check / size"],
            ["session checkpoint", "Session", "[MODE]", "(admin) WAL checkpoint"],
            ["session vacuum", "Session", "", "(admin) Reclaim free pages"],
            [
                "session purge",
                "Session",
                "--max-sessions N\n--max-age-days N",
                "(admin) Purge old sessions",
            ],
            [
                "session recover",
                "Session",
                "[backup-path]",
                "(admin) Integrity check / restore",
            ],
        ]
        self._out.write_table(
            ["Subcommand", "Target DB", "Arguments", "Description"],
            rows,
        )
        self._out.write(
            "Note: /db does not expose direct workflow maintenance commands; workflow state is managed by the WorkflowEngine."
        )

    def _db_help_session(self) -> None:
        """Print help for /db session subcommands."""
        rows = [
            ["stats", "", "Session/message counts"],
            ["health", "", "(admin) Integrity check / size"],
            ["checkpoint", "[MODE]", "(admin) WAL checkpoint"],
            ["vacuum", "", "(admin) Reclaim free pages"],
            [
                "purge",
                "--max-sessions N\n--max-age-days N",
                "(admin) Purge old sessions",
            ],
            ["recover", "[backup-path]", "(admin) Integrity check / restore"],
        ]
        self._out.write_table(
            ["Subcommand (/db session ...)", "Arguments", "Description"],
            rows,
        )
