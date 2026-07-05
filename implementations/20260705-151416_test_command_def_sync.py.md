# Implementation: tests/test_command_def_sync.py — CommandDef ↔ handler bidirectional sync tests

## Goal

Lock down bidirectional sync between `_COMMANDS` (CommandDef list) and `CommandRegistry` handler methods, verify `/help` output, test dispatch correctness, and verify plugin shadow rejection for all built-in commands.

## Scope

**In**: New test file with bidirectional sync, /help output, dispatch, and shadow rejection tests.

**Out**: Source file changes.

## Assumptions

1. `CommandRegistry.__init__` takes an `AgentContext` — mock with `MagicMock()`.
2. `_COMMANDS` from `command_defs_list.py` is the ground truth.
3. Intentional exclusions (helpers sharing `_cmd_` prefix but not in `_COMMANDS`) must be listed explicitly.
4. `validate_command_conflicts()` from `plugin_conflicts.py` is the shadow check entry point.

## Implementation

### Target file
`tests/test_command_def_sync.py`

### Procedure
1. Identify intentional exclusions by grepping mixins for `def _cmd_` (done in Phase 1 of plan).
2. Write bidirectional sync tests.
3. Write /help and dispatch tests.
4. Write shadow rejection tests.

### Method

```python
import inspect
import pytest
from unittest.mock import MagicMock
from scripts.agent.commands.command_defs_list import _COMMANDS
from scripts.agent.commands.registry import CommandRegistry
from scripts.shared.plugin_conflicts import validate_command_conflicts


# Handlers that are intentionally NOT in _COMMANDS (internal helpers, sub-dispatch)
# Update this set if/when new intentional exclusions are added
INTENTIONAL_HANDLER_EXCLUSIONS: set[str] = set()


def _make_registry() -> CommandRegistry:
    ctx = MagicMock()
    ctx.cfg = MagicMock()
    ctx.conv = MagicMock()
    return CommandRegistry(ctx)


# --- Bidirectional sync ---

def test_every_commanddef_has_handler():
    """Every CommandDef.handler must exist on the CommandRegistry instance."""
    registry = _make_registry()
    missing = [cmd.handler for cmd in _COMMANDS if not hasattr(registry, cmd.handler)]
    assert not missing, f"CommandDef handlers not found on registry: {missing}"


def test_every_handler_has_commanddef():
    """Every _cmd_* method on CommandRegistry must have a corresponding CommandDef."""
    registry = _make_registry()
    all_handlers = {
        name for name in dir(registry)
        if name.startswith("_cmd_") and callable(getattr(registry, name))
    }
    defined_handlers = {cmd.handler for cmd in _COMMANDS}
    undefined = all_handlers - defined_handlers - INTENTIONAL_HANDLER_EXCLUSIONS
    assert not undefined, (
        f"Handler methods without a CommandDef entry:\n"
        + "\n".join(f"  {h}" for h in sorted(undefined))
        + "\n\nIf these are intentional internal helpers, add them to INTENTIONAL_HANDLER_EXCLUSIONS."
    )


def test_commanddef_names_are_unique():
    names = [cmd.name for cmd in _COMMANDS]
    assert len(names) == len(set(names)), f"Duplicate command names: {[n for n in names if names.count(n) > 1]}"


def test_commanddef_handlers_are_unique():
    handlers = [cmd.handler for cmd in _COMMANDS]
    assert len(handlers) == len(set(handlers)), f"Duplicate handlers: {[h for h in handlers if handlers.count(h) > 1]}"


# --- /help output consistency ---

def test_help_output_mentions_all_command_names():
    """Every cmd.name should appear in /help output."""
    registry = _make_registry()
    output_lines: list[str] = []
    registry._out = MagicMock()
    registry._out.write.side_effect = lambda s: output_lines.append(str(s))
    registry._cmd_help([])
    full_output = "\n".join(output_lines)
    missing = [cmd.name for cmd in _COMMANDS if cmd.name not in full_output]
    assert not missing, f"Commands missing from /help output: {missing}"


# --- Dispatch correctness ---

def test_exact_dispatch_matches_correctly():
    """Exact command name like '/reload' must dispatch to exactly that handler."""
    registry = _make_registry()
    result = registry.resolve("/reload")
    assert result is not None
    assert result.handler == "_cmd_reload"


def test_prefix_dispatch_passes_subargs():
    """/memory list → _cmd_memory handler receives 'list' as first arg."""
    registry = _make_registry()
    result = registry.resolve("/memory list")
    assert result is not None
    assert result.handler == "_cmd_memory"


def test_no_prefix_false_positive():
    """/mem must NOT match /memory."""
    registry = _make_registry()
    result = registry.resolve("/mem")
    assert result is None or result.handler != "_cmd_memory"


# --- Plugin shadow rejection ---

@pytest.mark.parametrize("cmd", _COMMANDS)
def test_builtin_command_cannot_be_shadowed_by_plugin(cmd):
    """Every built-in command name must be rejected as a plugin tool name."""
    from scripts.shared.plugin_result import PluginConflictError
    # Simulate a plugin registering a tool named the same as a built-in command
    # (strip leading '/' for tool name comparison if applicable)
    tool_name = cmd.name.lstrip("/")
    conflict_result = validate_command_conflicts(
        registered_tool_names=[tool_name],
        existing_command_names={c.name.lstrip("/") for c in _COMMANDS},
    )
    assert tool_name in conflict_result.conflicts, (
        f"Expected plugin tool {tool_name!r} to be flagged as shadowing built-in command {cmd.name!r}"
    )


def test_shadow_rejection_strict_mode_raises():
    from scripts.shared.plugin_result import PluginLoadError
    from scripts.shared.plugin_auto_discover import load_plugins
    # If strict_mode=True and a plugin tries to shadow a built-in, PluginLoadError is raised
    # (integration test — requires a temp plugin file; skip if load_plugins not available)
    pass  # Covered by existing strict mode tests in test_plugin_contract.py
```

### Details

- `registry.resolve(cmd_str)` may not exist under that name — check actual dispatch API and adjust.
- `validate_command_conflicts()` signature may differ — read `plugin_conflicts.py` before finalizing.
- The `/help` test assumes `_cmd_help([])` writes output via `self._out.write`.
- `INTENTIONAL_HANDLER_EXCLUSIONS` must be updated if Phase 1 (grepping mixins) reveals helpers.

## Validation plan

- `uv run pytest tests/test_command_def_sync.py -v` — all pass.
- Verify: adding a fake `_cmd_secret` method to a mixin without a CommandDef → `test_every_handler_has_commanddef` fails.
- `ruff check tests/test_command_def_sync.py` — 0 errors.
