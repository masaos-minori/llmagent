"""tests/test_command_registry_consistency.py
Validate CommandDef/handler consistency for all built-in slash commands.
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from agent.commands.command_defs_list import _COMMANDS
from agent.commands.registry import CommandRegistry


@pytest.fixture()
def registry() -> CommandRegistry:
    ctx = MagicMock()
    out = SimpleNamespace(
        write=lambda msg: None,
        write_error=lambda msg: None,
        write_validation_error=lambda msg: None,
    )
    return CommandRegistry(ctx=ctx, out=out)


class TestCommandRegistryConsistency:
    def test_all_handlers_exist_on_registry(self, registry: CommandRegistry) -> None:
        missing = [
            cmd.handler for cmd in _COMMANDS if not hasattr(registry, cmd.handler)
        ]
        assert missing == [], f"Handlers missing from CommandRegistry: {missing}"

    def test_async_handlers_are_coroutines(self, registry: CommandRegistry) -> None:
        errors = []
        for cmd in _COMMANDS:
            if cmd.is_async and hasattr(registry, cmd.handler):
                fn = getattr(registry, cmd.handler)
                if not inspect.iscoroutinefunction(fn):
                    errors.append(cmd.handler)
        assert errors == [], f"Expected coroutines but got sync: {errors}"

    def test_sync_handlers_are_not_coroutines(self, registry: CommandRegistry) -> None:
        errors = []
        for cmd in _COMMANDS:
            if not cmd.is_async and hasattr(registry, cmd.handler):
                fn = getattr(registry, cmd.handler)
                if inspect.iscoroutinefunction(fn):
                    errors.append(cmd.handler)
        assert errors == [], f"Expected sync but got coroutines: {errors}"

    def test_exact_handlers_have_no_required_params(
        self, registry: CommandRegistry
    ) -> None:
        errors = []
        for cmd in _COMMANDS:
            if not cmd.prefix and hasattr(registry, cmd.handler):
                fn = getattr(registry, cmd.handler)
                sig = inspect.signature(fn)
                required = [
                    p
                    for p in sig.parameters.values()
                    if p.kind
                    in (
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        inspect.Parameter.POSITIONAL_ONLY,
                    )
                    and p.default is inspect.Parameter.empty
                ]
                if required:
                    errors.append(
                        f"{cmd.handler}: required params {[p.name for p in required]}"
                    )
        assert errors == [], f"Exact-match handlers with required params: {errors}"

    def test_prefix_handlers_accept_args_param(self, registry: CommandRegistry) -> None:
        errors = []
        for cmd in _COMMANDS:
            if cmd.prefix and hasattr(registry, cmd.handler):
                fn = getattr(registry, cmd.handler)
                sig = inspect.signature(fn)
                positional = [
                    p
                    for p in sig.parameters.values()
                    if p.kind
                    in (
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        inspect.Parameter.POSITIONAL_ONLY,
                        inspect.Parameter.VAR_POSITIONAL,
                    )
                ]
                if not positional:
                    errors.append(cmd.handler)
        assert errors == [], f"Prefix handlers missing positional param: {errors}"
