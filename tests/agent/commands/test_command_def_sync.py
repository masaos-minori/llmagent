"""tests/test_command_def_sync.py
Bidirectional sync tests for CommandDef ↔ CommandRegistry handler mapping.

Verifies:
- Every CommandDef.handler exists on the registry
- Every _cmd_* method has a CommandDef (with intentional exclusions listed)
- /help output mentions all command names
- Dispatch correctness
"""

from __future__ import annotations

from unittest.mock import MagicMock

from agent.commands.command_defs_list import _COMMANDS
from agent.commands.registry import CommandRegistry

# Internal sub-dispatch helpers intentionally absent from _COMMANDS
INTENTIONAL_HANDLER_EXCLUSIONS: frozenset[str] = frozenset(
    {
        "_cmd_mcp_status",
        "_cmd_mcp_tools",
    }
)


def _make_registry() -> CommandRegistry:
    ctx = MagicMock()
    ctx.cfg.tool.tool_definitions = []
    ctx.cfg.llm.llm_url = ""
    ctx.session.session_id = ""
    out = MagicMock()
    return CommandRegistry(ctx, out)


# --- Bidirectional sync ---


def test_every_commanddef_has_handler() -> None:
    registry = _make_registry()
    missing = [cmd.handler for cmd in _COMMANDS if not hasattr(registry, cmd.handler)]
    assert not missing, f"CommandDef handlers not found on registry: {missing}"


def test_every_handler_has_commanddef() -> None:
    registry = _make_registry()
    all_handlers = {
        name
        for name in dir(registry)
        if name.startswith("_cmd_") and callable(getattr(registry, name))
    }
    defined_handlers = {cmd.handler for cmd in _COMMANDS}
    undefined = all_handlers - defined_handlers - INTENTIONAL_HANDLER_EXCLUSIONS
    assert not undefined, (
        "Handler methods without a CommandDef entry:\n"
        + "\n".join(f"  {h}" for h in sorted(undefined))
        + "\n\nIf intentional, add to INTENTIONAL_HANDLER_EXCLUSIONS."
    )


def test_commanddef_names_are_unique() -> None:
    names = [cmd.name for cmd in _COMMANDS]
    duplicates = [n for n in set(names) if names.count(n) > 1]
    assert len(names) == len(set(names)), f"Duplicate command names: {duplicates}"


def test_commanddef_handlers_are_unique() -> None:
    handlers = [cmd.handler for cmd in _COMMANDS]
    duplicates = [h for h in set(handlers) if handlers.count(h) > 1]
    assert len(handlers) == len(set(handlers)), f"Duplicate handlers: {duplicates}"


# --- /help output consistency ---


def test_help_output_mentions_all_command_names() -> None:
    registry = _make_registry()
    output_lines: list[str] = []
    registry._out = MagicMock()
    registry._out.write.side_effect = lambda s: output_lines.append(str(s))
    registry._cmd_help()
    full_output = "\n".join(output_lines)
    missing = [cmd.name for cmd in _COMMANDS if cmd.name not in full_output]
    assert not missing, f"Commands missing from /help output: {missing}"


# --- Handler lookup correctness ---


def test_get_handler_exact_match() -> None:
    registry = _make_registry()
    reload_cmd = next((c for c in _COMMANDS if c.name == "/reload"), None)
    assert reload_cmd is not None, "/reload not found in _COMMANDS"
    handler = registry._get_handler(reload_cmd)
    assert callable(handler)


def test_get_handler_prefix_command() -> None:
    registry = _make_registry()
    memory_cmd = next((c for c in _COMMANDS if c.name == "/memory"), None)
    assert memory_cmd is not None, "/memory not found in _COMMANDS"
    assert memory_cmd.prefix is True
    handler = registry._get_handler(memory_cmd)
    assert callable(handler)


# --- Async dispatch ---


async def test_dispatch_help_returns_true() -> None:
    registry = _make_registry()
    result = await registry.dispatch("/help")
    assert result is True


async def test_dispatch_unknown_returns_false() -> None:
    registry = _make_registry()
    result = await registry.dispatch("/nonexistent_xyz_abc_command")
    assert result is False


async def test_dispatch_empty_returns_false() -> None:
    registry = _make_registry()
    result = await registry.dispatch("")
    assert result is False


async def test_dispatch_exact_match_async_command_is_awaited() -> None:
    """dispatch() awaits the handler for an exact-match, is_async CommandDef (e.g. /compact)."""
    from unittest.mock import AsyncMock

    registry = _make_registry()
    compact_cmd = next((c for c in _COMMANDS if c.name == "/compact"), None)
    assert compact_cmd is not None, "/compact not found in _COMMANDS"
    assert compact_cmd.prefix is False
    assert compact_cmd.is_async is True
    registry._cmd_compact = AsyncMock()  # type: ignore[method-assign] — intentional test-only monkeypatch of a bound method

    result = await registry.dispatch("/compact")

    assert result is True
    registry._cmd_compact.assert_awaited_once_with()


# --- CommandDef metadata integrity ---


def test_all_commands_have_nonempty_help() -> None:
    for cmd in _COMMANDS:
        assert cmd.help, f"CommandDef {cmd.name!r} has empty help text"


def test_all_command_names_start_with_slash() -> None:
    for cmd in _COMMANDS:
        assert cmd.name.startswith("/"), f"CommandDef {cmd.name!r} must start with '/'"


# --- Subcommand / argument contract sync (GV-023) ---


def _handler_source(handler: str) -> str:
    import inspect

    return inspect.getsource(getattr(CommandRegistry, handler))


def test_every_registered_subcommand_is_handled_by_its_handler() -> None:
    """Each SubcommandSpec name appears as a string literal in its handler source."""
    missing: list[str] = []
    for cmd in _COMMANDS:
        if not cmd.subcommands:
            continue
        source = _handler_source(cmd.handler)
        for sub in cmd.subcommands:
            if f'"{sub.name}"' not in source:
                missing.append(f"{cmd.name} {sub.name}")
    assert not missing, f"Registered subcommands not handled: {missing}"


def test_mcp_registered_subcommands_equal_the_handler_valid_set() -> None:
    import asyncio

    import pytest
    from agent.commands.exceptions import UnknownSubcommandError

    registry = _make_registry()
    with pytest.raises(UnknownSubcommandError) as exc_info:
        asyncio.run(registry._cmd_mcp("no-such-subcommand"))
    mcp = next(c for c in _COMMANDS if c.name == "/mcp")
    assert set(exc_info.value.valid) == {s.name for s in mcp.subcommands}


def test_memory_registered_subcommands_equal_the_handler_valid_set() -> None:
    import pytest
    from agent.commands.exceptions import UnknownSubcommandError

    registry = _make_registry()
    registry._ctx.services_required.memory = MagicMock()
    with pytest.raises(UnknownSubcommandError) as exc_info:
        registry._cmd_memory("no-such-subcommand")
    memory = next(c for c in _COMMANDS if c.name == "/memory")
    # "status" is handled before the dispatch table, so it is not in `valid`.
    registered = {s.name for s in memory.subcommands} - {"status"}
    assert set(exc_info.value.valid) == registered


def test_prefix_help_names_every_registered_subcommand() -> None:
    """The one-line /help text of a command lists each of its subcommand names."""
    stale: list[str] = []
    for cmd in _COMMANDS:
        stale.extend(
            f"{cmd.name} {sub.name}"
            for sub in cmd.subcommands
            if sub.name not in cmd.help
        )
    assert not stale, f"/help text omits registered subcommands: {stale}"


def test_usage_lines_render_required_and_optional_arguments() -> None:
    from agent.commands.command_defs import ArgSpec, format_usage

    assert format_usage("/x", "go", (ArgSpec("id", required=True), ArgSpec("n"))) == (
        "/x go <id> [n]"
    )
    assert format_usage("/x", "", ()) == "/x"
