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
            # Skip removed sections
            if "removed" in line.lower() and ("### /" in line or "## /" in line):
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
        docs_files = [
            ROOT / "docs" / "05_agent_01_system-overview.md",
            ROOT / "docs" / "05_agent_07_cli-and-commands.md",
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

    def test_db_commands_in_registry(self) -> None:
        """/db is registered as a built-in command."""
        registered = self.get_registered_commands()
        assert "/db" in registered, "/db should be registered"

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
