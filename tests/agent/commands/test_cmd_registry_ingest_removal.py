"""tests/test_cmd_registry_ingest_removal.py

Tests that the removed `/ingest`, `/rag`, and standalone `/export` commands are
no longer dispatched, while `/compact` and `/mdq` remain functional and `/export`
is documented as a `/session` subcommand.
"""

from __future__ import annotations

from agent.commands.registry import _COMMANDS


class TestIngestRagCommandsRemoved:
    def test_ingest_not_in_built_in_commands(self) -> None:
        """Verify /ingest is NOT in the built-in command registry."""
        ingest_cmds = [c for c in _COMMANDS if c.name == "/ingest"]
        assert len(ingest_cmds) == 0, (
            "/ingest should not be registered as a built-in command"
        )

    def test_rag_not_in_built_in_commands(self) -> None:
        """Verify /rag is NOT in the built-in command registry."""
        rag_cmds = [c for c in _COMMANDS if c.name == "/rag"]
        assert len(rag_cmds) == 0, "/rag should not be registered"

    def test_export_not_registered_as_standalone(self) -> None:
        """Verify /export is no longer a standalone command (folded into /session)."""
        export_cmds = [c for c in _COMMANDS if c.name == "/export"]
        assert len(export_cmds) == 0, (
            "/export should not be registered as a standalone command"
        )

    def test_session_help_mentions_export(self) -> None:
        """Verify /session's CommandDef help text documents the export subcommand."""
        session_cmds = [c for c in _COMMANDS if c.name == "/session"]
        assert len(session_cmds) == 1, "/session should be registered"
        assert "export" in session_cmds[0].help

    def test_compact_still_registered(self) -> None:
        """Verify /compact is still in the built-in command registry."""
        compact_cmds = [c for c in _COMMANDS if c.name == "/compact"]
        assert len(compact_cmds) == 1, "/compact should still be registered"
