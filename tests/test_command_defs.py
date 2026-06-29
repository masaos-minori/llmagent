"""
tests/test_command_defs.py
Unit tests for agent/commands/command_defs.py.
"""

from __future__ import annotations

from agent.commands.command_defs import _COMMANDS, CommandDef, SubcommandSpec


class TestCommandDef:
    def test_dataclass_fields(self) -> None:
        cmd = CommandDef(
            name="/test",
            prefix=False,
            is_async=True,
            handler="_cmd_test",
            help="Test command",
        )
        assert cmd.name == "/test"
        assert cmd.prefix is False
        assert cmd.is_async is True
        assert cmd.handler == "_cmd_test"
        assert cmd.help == "Test command"
        assert cmd.subcommands == []

    def test_subcommands_default_empty(self) -> None:
        cmd = CommandDef("/x", False, False, "_cmd_x", "desc")
        assert cmd.subcommands == []

    def test_subcommands_set(self) -> None:
        subs = [
            SubcommandSpec("list", "List items"),
            SubcommandSpec("show", "Show item"),
        ]
        cmd = CommandDef("/x", True, False, "_cmd_x", "desc", subcommands=subs)
        assert len(cmd.subcommands) == 2
        assert cmd.subcommands[0].name == "list"


class TestSubcommandSpec:
    def test_fields(self) -> None:
        spec = SubcommandSpec(name="list", help="List all")
        assert spec.name == "list"
        assert spec.help == "List all"


class TestCommandsList:
    def test_commands_non_empty(self) -> None:
        assert len(_COMMANDS) > 0

    def test_all_names_start_with_slash(self) -> None:
        for cmd in _COMMANDS:
            assert cmd.name.startswith("/"), f"{cmd.name} must start with /"

    def test_all_handlers_non_empty(self) -> None:
        for cmd in _COMMANDS:
            assert cmd.handler, f"{cmd.name} missing handler"

    def test_all_help_non_empty(self) -> None:
        for cmd in _COMMANDS:
            assert cmd.help, f"{cmd.name} missing help"

    def test_no_duplicate_names(self) -> None:
        names = [cmd.name for cmd in _COMMANDS]
        assert len(names) == len(set(names)), "Duplicate command names found"

    def test_known_commands_present(self) -> None:
        names = {cmd.name for cmd in _COMMANDS}
        for expected in ("/help", "/config", "/mcp", "/db", "/memory"):
            assert expected in names, f"Expected {expected} in _COMMANDS"

    def test_async_commands_have_async_flag(self) -> None:
        async_names = {cmd.name for cmd in _COMMANDS if cmd.is_async}
        assert "/compact" in async_names
        assert "/mcp" in async_names

    def test_prefix_commands_have_prefix_flag(self) -> None:
        prefix_names = {cmd.name for cmd in _COMMANDS if cmd.prefix}
        for name in ("/mcp", "/session", "/db"):
            assert name in prefix_names, f"{name} should be prefix command"

    def test_exact_commands_no_prefix_flag(self) -> None:
        exact_names = {cmd.name for cmd in _COMMANDS if not cmd.prefix}
        assert "/help" in exact_names
        assert "/config" in exact_names
