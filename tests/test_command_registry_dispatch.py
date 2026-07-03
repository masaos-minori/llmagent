#!/usr/bin/env python3
"""Tests for CommandRegistry.dispatch() args stripping behavior."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import shared.plugin_registry as plugin_registry
from agent.commands.registry import CommandRegistry


@pytest.fixture
def registry() -> CommandRegistry:
    out = SimpleNamespace(write=MagicMock(), write_table=MagicMock())
    return CommandRegistry(MagicMock(), out)


@pytest.fixture(autouse=True)
def reset_plugins() -> None:
    plugin_registry._reset_for_testing()
    yield
    plugin_registry._reset_for_testing()


@pytest.mark.parametrize(
    "input_line, expected_args",
    [
        ("/db help", "help"),
        ("/db  help", "help"),
        ("/mcp", ""),
        ("/db", ""),
    ],
)
async def test_builtin_dispatch_strips_args(
    registry: CommandRegistry,
    input_line: str,
    expected_args: str,
) -> None:
    handler_name = "_cmd_db" if input_line.startswith("/db") else "_cmd_mcp"
    mock = AsyncMock()
    setattr(registry, handler_name, mock)
    await registry.dispatch(input_line)
    mock.assert_called_once_with(expected_args)


async def test_plugin_dispatch_strips_args(registry: CommandRegistry) -> None:
    captured: dict[str, str] = {}

    @plugin_registry.register_command("/myplugin", prefix=True)
    def handler(ctx: object, args: str) -> None:
        captured["args"] = args

    await registry.dispatch("/myplugin  value")
    assert captured.get("args") == "value"
