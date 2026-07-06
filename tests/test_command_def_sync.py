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
        "_cmd_db_rag",
        "_cmd_db_session",
        "_cmd_mcp_status",
        "_cmd_mdq_get",
        "_cmd_mdq_grep",
        "_cmd_mdq_index",
        "_cmd_mdq_outline",
        "_cmd_mdq_refresh",
        "_cmd_mdq_search",
        "_cmd_mdq_status",
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


# --- CommandDef metadata integrity ---


def test_all_commands_have_nonempty_help() -> None:
    for cmd in _COMMANDS:
        assert cmd.help, f"CommandDef {cmd.name!r} has empty help text"


def test_all_command_names_start_with_slash() -> None:
    for cmd in _COMMANDS:
        assert cmd.name.startswith("/"), f"CommandDef {cmd.name!r} must start with '/'"
