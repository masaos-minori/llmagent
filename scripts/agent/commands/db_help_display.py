"""help_display.py — Database help display logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent.commands.mixin_base import MixinBase

# DbHelpDisplay is a mixin that provides help display methods for /db commands.


class DbHelpDisplay:
    """Provides help table display methods for /db subcommands."""

    def _db_help(self) -> None:
        """Print a help table for /db subcommands."""
        rows = [
            ["rag stats", "RAG", "", "Document/chunk counts"],
            ["rag urls", "RAG", "--lang --limit", "List document URLs"],
            ["rag clean", "RAG", "<url>", "Delete a document"],
            ["rag rebuild-fts", "RAG", "", "Rebuild FTS5 index"],
            ["rag vec-rebuild", "RAG", "", "Rebuild vector index"],
            [
                "rag reconcile-url",
                "RAG",
                "<url>",
                "Rebuild FTS/vec for a single URL",
            ],
            [
                "rag recover",
                "RAG",
                "[backup-path]",
                "(admin) Integrity check / restore",
            ],
            ["rag consistency", "RAG", "", "Chunks/FTS/vec sync check"],
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

    def _db_help_rag(self) -> None:
        """Print help for /db rag subcommands."""
        rows = [
            ["stats", "", "Document/chunk counts"],
            ["urls", "--lang --limit", "List document URLs"],
            ["clean", "<url>", "Delete a document"],
            ["rebuild-fts", "", "Rebuild FTS5 index"],
            ["vec-rebuild", "", "Rebuild vector index"],
            ["reconcile-url", "<url>", "Rebuild FTS/vec for a single URL"],
            ["recover", "[backup-path]", "(admin) Integrity check / restore"],
            ["consistency", "", "Chunks/FTS/vec sync check"],
        ]
        self._out.write_table(
            ["Subcommand (/db rag ...)", "Arguments", "Description"],
            rows,
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
