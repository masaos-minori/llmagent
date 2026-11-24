"""
tests/test_command_defs.py
Unit tests for agent/commands/command_defs.py.
"""

from __future__ import annotations

from agent.commands.command_defs import CommandDef, SubcommandSpec
from agent.commands.command_defs_list import _COMMANDS


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
        for expected in ("/help", "/config", "/mcp", "/memory", "/jobs"):
            assert expected in names, f"Expected {expected} in _COMMANDS"

    def test_job_command_subcommand_contract(self) -> None:
        """Row 9: `/jobs` is registered as a top-level command with status and cancel.

        The definition is the source of truth for the registered set and for the
        completion candidates, so the subcommands and their required id argument are
        asserted here rather than in the handler (REQ-001, REQ-010).
        """
        jobs = next((cmd for cmd in _COMMANDS if cmd.name == "/jobs"), None)
        assert jobs is not None, "/jobs must be registered in _COMMANDS"
        assert jobs.prefix is True
        assert jobs.handler == "_cmd_jobs"
        assert [spec.name for spec in jobs.subcommands] == ["status", "cancel"]
        for spec in jobs.subcommands:
            assert [arg.token for arg in spec.args] == ["id"]
            assert spec.args[0].required is True
            assert spec.args[0].render() == "<id>"
        # The usage lines the contract checker requires in a chapter document.
        assert jobs.usages() == ["/jobs status <id>", "/jobs cancel <id>"]

    def test_session_vector_subcommand_names_the_prune_operation(self) -> None:
        """Row 9, Phase 6: the vector subcommand is registered only under the prune name.

        The definition is the source of the registered set and of the completion
        candidates, so the retired rebuild name must not resolve here (REQ-007, AC-8).
        """
        session = next(cmd for cmd in _COMMANDS if cmd.name == "/session")
        specs = {spec.name: spec for spec in session.subcommands}

        assert "rag-prune-vec" in specs
        assert "rag-rebuild-vec" not in specs
        assert "orphan" in specs["rag-prune-vec"].help
        # The FTS subcommand performs a rebuild, so its name is unchanged.
        assert specs["rag-rebuild-fts"].help == "Rebuild chunks_fts"
        assert "/session rag-prune-vec" in session.usages()

    def test_async_commands_have_async_flag(self) -> None:
        async_names = {cmd.name for cmd in _COMMANDS if cmd.is_async}
        assert "/compact" in async_names
        assert "/mcp" in async_names

    def test_prefix_commands_have_prefix_flag(self) -> None:
        prefix_names = {cmd.name for cmd in _COMMANDS if cmd.prefix}
        for name in ("/mcp", "/session"):
            assert name in prefix_names, f"{name} should be prefix command"

    def test_exact_commands_no_prefix_flag(self) -> None:
        exact_names = {cmd.name for cmd in _COMMANDS if not cmd.prefix}
        assert "/help" in exact_names
        assert "/config" in exact_names
