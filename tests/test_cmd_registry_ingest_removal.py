"""tests/test_cmd_registry_ingest_removal.py

Tests that the removed `/ingest` command is no longer dispatched,
while `/rag`, `/export`, and `/compact` remain functional.
"""

from __future__ import annotations

from agent.commands.registry import _COMMANDS


class TestIngestCommandRemoved:
    def test_ingest_not_in_built_in_commands(self) -> None:
        """Verify /ingest is NOT in the built-in command registry."""
        ingest_cmds = [c for c in _COMMANDS if c.name == "/ingest"]
        assert len(ingest_cmds) == 0, "/ingest should not be registered as a built-in command"

    def test_rag_still_registered(self) -> None:
        """Verify /rag is still in the built-in command registry."""
        rag_cmds = [c for c in _COMMANDS if c.name == "/rag"]
        assert len(rag_cmds) == 1, "/rag should still be registered"
        assert rag_cmds[0].prefix is True

    def test_export_still_registered(self) -> None:
        """Verify /export is still in the built-in command registry."""
        export_cmds = [c for c in _COMMANDS if c.name == "/export"]
        assert len(export_cmds) == 1, "/export should still be registered"
        assert export_cmds[0].prefix is True

    def test_compact_still_registered(self) -> None:
        """Verify /compact is still in the built-in command registry."""
        compact_cmds = [c for c in _COMMANDS if c.name == "/compact"]
        assert len(compact_cmds) == 1, "/compact should still be registered"
