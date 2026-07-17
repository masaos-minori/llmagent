"""tests/docs/test_command_docs_sync.py
Docs test: ensure active command docs match registered command surface.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


class TestCommandDocsSync:
    """Ensure active command docs don't reference unregistered commands."""

    def get_registered_commands(self) -> set[str]:
        """Get all registered built-in command names."""
        from agent.commands.registry import _COMMANDS

        return {cmd.name for cmd in _COMMANDS}

    def _get_active_command_refs_from_docs(self, filepath: Path) -> set[str]:
        """Extract ALL command references from a doc file (both registered and unregistered)."""
        if not filepath.exists():
            return set()

        content = filepath.read_text(encoding="utf-8")

        found: list[str] = []
        for line in content.splitlines():
            # Skip removed-command sections/headings ...
            if "removed" in line.lower() and ("### /" in line or "## /" in line):
                continue
            # ... and prose lines explicitly marking a command as historical
            # ("旧" = "former") -- the doc set's established convention for
            # describing migrated/deprecated commands (see e.g.
            # 05_agent_07_08's "旧`/db session <subcmd>`...へ移管された").
            if "旧" in line:
                continue
            # Match command references like /mcp, /db, /debug, etc.
            matches = re.findall(
                r"/(?:mcp|db|debug|audit|memory|mdq|rag|plugin)\b", line
            )
            for m in matches:
                found.append(m)

        return set(found)

    def test_active_docs_match_registered_commands(self) -> None:
        """Active command docs only reference registered commands."""
        # docs/05_agent_07_cli-and-commands.md was split into the 11
        # 05_agent_07_NN_* files below; check the full active set rather than
        # the removed monolith (which silently skipped this check entirely,
        # since .exists() was False for every doc it should have covered).
        docs_files = [
            ROOT / "docs" / "05_agent_01_system-overview.md",
            ROOT / "docs" / "05_agent_07_01_cli-and-commands-cli-reference.md",
            ROOT / "docs" / "05_agent_07_02_cli-and-commands-cliview.md",
            ROOT / "docs" / "05_agent_07_03_cli-and-commands-command-registry.md",
            ROOT / "docs" / "05_agent_07_04_cli-and-commands-purpose.md",
            ROOT / "docs" / "05_agent_07_05_cli-and-commands-repl-io.md",
            ROOT / "docs" / "05_agent_07_06_cli-and-commands-hot-reload.md",
            # 05_agent_07_07 (migration-notes) intentionally excluded: its entire
            # purpose is documenting removed commands (e.g. /db) as a historical
            # record, not describing current active command surface.
            ROOT
            / "docs"
            / "05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md",
            ROOT
            / "docs"
            / "05_agent_07_09_cli-and-commands-slash-commands-context-db.md",
            ROOT
            / "docs"
            / "05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md",
            ROOT
            / "docs"
            / "05_agent_07_11_cli-and-commands-slash-commands-memory-other.md",
        ]

        for filepath in docs_files:
            if not filepath.exists():
                continue
            all_refs = self._get_active_command_refs_from_docs(filepath)
            unregistered = all_refs - self.get_registered_commands()
            assert not unregistered, (
                f"{filepath} contains unregistered command references: {sorted(unregistered)}"
            )

    def test_mcp_commands_in_registry(self) -> None:
        """/mcp is registered as a built-in command."""
        registered = self.get_registered_commands()
        assert "/mcp" in registered, "/mcp should be registered"

    def test_db_commands_not_in_registry(self) -> None:
        """/db is no longer registered as a built-in command."""
        registered = self.get_registered_commands()
        assert "/db" not in registered, "/db should not be registered"

    def test_debug_commands_in_registry(self) -> None:
        """/debug is registered as a built-in command."""
        registered = self.get_registered_commands()
        assert "/debug" in registered, "/debug should be registered"

    def test_audit_commands_in_registry(self) -> None:
        """/audit is registered as a built-in command."""
        registered = self.get_registered_commands()
        assert "/audit" in registered, "/audit should be registered"

    def test_memory_commands_in_registry(self) -> None:
        """/memory is registered as a built-in command."""
        registered = self.get_registered_commands()
        assert "/memory" in registered, "/memory should be registered"

    def test_mdq_commands_in_registry(self) -> None:
        """/mdq is registered as a built-in command."""
        registered = self.get_registered_commands()
        assert "/mdq" in registered, "/mdq should be registered"

    def test_plugin_commands_in_registry(self) -> None:
        """/plugin is registered as a built-in command."""
        registered = self.get_registered_commands()
        assert "/plugin" in registered, "/plugin should be registered"
