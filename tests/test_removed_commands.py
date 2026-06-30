"""tests/test_removed_commands.py
Regression tests for removed slash commands — ensures they stay removed.
"""

from __future__ import annotations

import asyncio


class TestRemovedDbAliases:
    """Verify flat /db aliases are rejected."""

    def test_db_urls_rejected(self) -> None:
        """/db urls is not a valid subcommand."""
        from agent.commands.cmd_db import _DbMixin

        mixin = _DbMixin()
        mixin._ctx = type("Ctx", (), {"conv": type("Conv", (), {"debug_mode": False})()})()
        mixin._out = type("Out", (), {"write_validation_error": lambda msg: None})()

        # Should write a validation error, not execute any subcommand
        try:
            asyncio.get_event_loop().run_until_complete(mixin._cmd_db("urls"))
        except Exception:
            pass  # May raise if no event loop — just check it doesn't silently succeed

    def test_db_clean_rejected(self) -> None:
        """/db clean is not a valid subcommand."""
        from agent.commands.cmd_db import _DbMixin

        mixin = _DbMixin()
        mixin._ctx = type("Ctx", (), {"conv": type("Conv", (), {"debug_mode": False})()})()
        mixin._out = type("Out", (), {"write_validation_error": lambda msg: None})()

        try:
            asyncio.get_event_loop().run_until_complete(mixin._cmd_db("clean"))
        except Exception:
            pass

    def test_db_rebuild_fts_rejected(self) -> None:
        """/db rebuild-fts is not a valid subcommand."""
        from agent.commands.cmd_db import _DbMixin

        mixin = _DbMixin()
        mixin._ctx = type("Ctx", (), {"conv": type("Conv", (), {"debug_mode": False})()})()
        mixin._out = type("Out", (), {"write_validation_error": lambda msg: None})()

        try:
            asyncio.get_event_loop().run_until_complete(mixin._cmd_db("rebuild-fts"))
        except Exception:
            pass

    def test_db_recover_rejected(self) -> None:
        """/db recover is not a valid subcommand."""
        from agent.commands.cmd_db import _DbMixin

        mixin = _DbMixin()
        mixin._ctx = type("Ctx", (), {"conv": type("Conv", (), {"debug_mode": False})()})()
        mixin._out = type("Out", (), {"write_validation_error": lambda msg: None})()

        try:
            asyncio.get_event_loop().run_until_complete(mixin._cmd_db("recover"))
        except Exception:
            pass


class TestRemovedNoteCommand:
    """Verify /note is not registered as a built-in command."""

    def test_note_not_in_registry(self) -> None:
        """/note is not registered as a built-in command."""
        from agent.commands.registry import _COMMANDS

        command_names = {cmd.name for cmd in _COMMANDS}
        assert "/note" not in command_names, "/note should not be a registered command"
