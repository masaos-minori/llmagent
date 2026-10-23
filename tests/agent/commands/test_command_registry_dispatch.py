#!/usr/bin/env python3
"""Tests for CommandRegistry.dispatch() args stripping and command-boundary error surface."""

from __future__ import annotations

import logging
import sqlite3
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.commands.exceptions import UnknownPresetError
from agent.commands.registry import CommandRegistry


@pytest.fixture
def registry() -> CommandRegistry:
    out = SimpleNamespace(
        write=MagicMock(),
        write_table=MagicMock(),
        write_error=MagicMock(),
        write_validation_error=MagicMock(),
        write_fatal=MagicMock(),
    )
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


async def test_dispatch_runtime_error_surfaces_as_command_error(
    registry: CommandRegistry,
) -> None:
    out = cast(MagicMock, registry._out)
    setattr(registry, "_cmd_mcp", AsyncMock(side_effect=RuntimeError("boom")))
    result = await registry.dispatch("/mcp extra")
    assert result is True
    # A non-domain handler error renders via write_error() -> [error], never [fatal].
    assert out.write_error.called
    assert not out.write_validation_error.called
    out.write_fatal.assert_not_called()


async def test_dispatch_validation_error_uses_usage_tag(
    registry: CommandRegistry,
) -> None:
    out = cast(MagicMock, registry._out)
    setattr(
        registry,
        "_cmd_mcp",
        AsyncMock(side_effect=UnknownPresetError("gold", ("silver",))),
    )
    result = await registry.dispatch("/mcp extra")
    assert result is True
    # A CommandValidationError renders via write_validation_error() -> [usage].
    assert out.write_validation_error.called
    assert not out.write_error.called
    out.write_fatal.assert_not_called()


async def test_dispatch_sqlite_error_states_partial_effect(
    registry: CommandRegistry,
) -> None:
    out = cast(MagicMock, registry._out)
    setattr(
        registry,
        "_cmd_mcp",
        AsyncMock(side_effect=sqlite3.OperationalError("disk I/O error")),
    )
    result = await registry.dispatch("/mcp extra")
    assert result is True
    out_calls = [c.args[0] for c in out.write_error.call_args_list]
    assert any("/mcp" in msg and "partial" in msg for msg in out_calls)
    out.write_fatal.assert_not_called()


async def test_dispatch_logs_the_command_error(
    registry: CommandRegistry, caplog: pytest.LogCaptureFixture
) -> None:
    out = cast(MagicMock, registry._out)
    setattr(registry, "_cmd_mcp", AsyncMock(side_effect=RuntimeError("boom")))
    with caplog.at_level(logging.ERROR):
        result = await registry.dispatch("/mcp extra")
    assert result is True
    assert any("/mcp" in rec.getMessage() for rec in caplog.records)
    assert out.write_error.called
