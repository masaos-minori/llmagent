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


class TestRemovedSkillCommand:
    """Verify /skill is not registered as a built-in command."""

    def test_skill_not_in_registry(self) -> None:
        """/skill is not registered as a built-in command."""
        from agent.commands.registry import _COMMANDS

        command_names = {cmd.name for cmd in _COMMANDS}
        assert "/skill" not in command_names, (
            "/skill should not be a registered command"
        )


class TestRemovedMdqCommand:
    """Verify /mdq is not registered as a built-in command."""

    def test_mdq_not_in_registry(self) -> None:
        """/mdq is not registered as a built-in command."""
        from agent.commands.registry import _COMMANDS

        command_names = {cmd.name for cmd in _COMMANDS}
        assert "/mdq" not in command_names, "/mdq should not be a registered command"


class TestRemovedApproveCommand:
    """Verify /approve is not registered as a built-in command."""

    def test_approve_not_in_registry(self) -> None:
        """/approve is not registered as a built-in command."""
        from agent.commands.registry import _COMMANDS

        command_names = {cmd.name for cmd in _COMMANDS}
        assert "/approve" not in command_names, (
            "/approve should not be a registered command"
        )


class TestRemovedRejectCommand:
    """Verify /reject is not registered as a built-in command."""

    def test_reject_not_in_registry(self) -> None:
        """/reject is not registered as a built-in command."""
        from agent.commands.registry import _COMMANDS

        command_names = {cmd.name for cmd in _COMMANDS}
        assert "/reject" not in command_names, (
            "/reject should not be a registered command"
        )
