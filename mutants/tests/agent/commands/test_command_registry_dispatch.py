#!/usr/bin/env python3
"""Tests for CommandRegistry.dispatch() args stripping behavior."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.commands.registry import CommandRegistry


@pytest.fixture
def registry() -> CommandRegistry:
    out = SimpleNamespace(write=MagicMock(), write_table=MagicMock())
    return CommandRegistry(MagicMock(), out)


@pytest.mark.parametrize(
    "input_line, expected_args",
    [
        ("/mcp", ""),
    ],
)
async def test_builtin_dispatch_strips_args(
    registry: CommandRegistry,
    input_line: str,
    expected_args: str,
) -> None:
    handler_name = "_cmd_mcp"
    mock = AsyncMock()
    setattr(registry, handler_name, mock)
    await registry.dispatch(input_line)
    mock.assert_called_once_with(expected_args)
