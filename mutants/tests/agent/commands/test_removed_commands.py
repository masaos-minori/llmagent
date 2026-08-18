"""tests/test_removed_commands.py
Regression tests for removed slash commands — ensures they stay removed.
"""

from __future__ import annotations


class TestRemovedDbAliases:
    """Verify flat /db aliases are not registered as commands."""

    def test_db_urls_not_registered(self) -> None:
        """/db urls is not a registered command."""
        from agent.commands.registry import _COMMANDS

        command_names = {cmd.name for cmd in _COMMANDS}
        assert "/db" not in command_names, "/db should not be a registered command"

    def test_db_clean_not_registered(self) -> None:
        """/db clean is not a registered command."""
        from agent.commands.registry import _COMMANDS

        command_names = {cmd.name for cmd in _COMMANDS}
        assert "/db" not in command_names, "/db should not be a registered command"

    def test_db_rebuild_fts_not_registered(self) -> None:
        """/db rebuild-fts is not a registered command."""
        from agent.commands.registry import _COMMANDS

        command_names = {cmd.name for cmd in _COMMANDS}
        assert "/db" not in command_names, "/db should not be a registered command"

    def test_db_recover_not_registered(self) -> None:
        """/db recover is not a registered command."""
        from agent.commands.registry import _COMMANDS

        command_names = {cmd.name for cmd in _COMMANDS}
        assert "/db" not in command_names, "/db should not be a registered command"


class TestRemovedNoteCommand:
    """Verify /note is not registered as a built-in command."""

    def test_note_not_in_registry(self) -> None:
        """/note is not registered as a built-in command."""
        from agent.commands.registry import _COMMANDS

        command_names = {cmd.name for cmd in _COMMANDS}
        assert "/note" not in command_names, "/note should not be a registered command"
