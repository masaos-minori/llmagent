#!/usr/bin/env python3
"""Tests for CommandRegistry._dispatch_plugin() word-boundary matching."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import shared.plugin_registry as plugin_registry
from agent.commands.registry import CommandRegistry


@pytest.fixture(autouse=True)
def reset_registry() -> None:
    plugin_registry._reset_for_testing()
    yield
    plugin_registry._reset_for_testing()


@pytest.fixture
def registry() -> CommandRegistry:
    return CommandRegistry(MagicMock())


class TestDispatchPluginBoundary:
    @pytest.mark.asyncio
    async def test_prefix_exact_match(self, registry: CommandRegistry) -> None:
        captured: dict[str, str] = {}

        @plugin_registry.register_command("/foo", prefix=True)
        def foo_handler(ctx: object, args: str) -> None:
            captured["args"] = args

        result = await registry._dispatch_plugin("/foo")
        assert result is True
        assert captured["args"] == ""

    @pytest.mark.asyncio
    async def test_prefix_with_space_args(self, registry: CommandRegistry) -> None:
        captured: dict[str, str] = {}

        @plugin_registry.register_command("/foo", prefix=True)
        def foo_handler(ctx: object, args: str) -> None:
            captured["args"] = args

        result = await registry._dispatch_plugin("/foo bar")
        assert result is True
        assert captured["args"] == "bar"

    @pytest.mark.asyncio
    async def test_prefix_with_extra_spaces(self, registry: CommandRegistry) -> None:
        captured: dict[str, str] = {}

        @plugin_registry.register_command("/foo", prefix=True)
        def foo_handler(ctx: object, args: str) -> None:
            captured["args"] = args

        result = await registry._dispatch_plugin("/foo  bar")
        assert result is True
        assert captured["args"] == "bar"

    @pytest.mark.asyncio
    async def test_prefix_false_positive_guard(self, registry: CommandRegistry) -> None:
        called: dict[str, bool] = {}

        @plugin_registry.register_command("/foo", prefix=True)
        def foo_handler(ctx: object, args: str) -> None:
            called["invoked"] = True

        result = await registry._dispatch_plugin("/foobar")
        assert result is False
        assert "invoked" not in called

    @pytest.mark.asyncio
    async def test_exact_command_match(self, registry: CommandRegistry) -> None:
        called: dict[str, bool] = {}

        @plugin_registry.register_command("/exact")
        def exact_handler(ctx: object, args: str) -> None:
            called["invoked"] = True

        result = await registry._dispatch_plugin("/exact")
        assert result is True
        assert called.get("invoked") is True

    @pytest.mark.asyncio
    async def test_exact_command_with_trailing_text(
        self, registry: CommandRegistry
    ) -> None:
        called: dict[str, bool] = {}

        @plugin_registry.register_command("/exact")
        def exact_handler(ctx: object, args: str) -> None:
            called["invoked"] = True

        result = await registry._dispatch_plugin("/exact bar")
        assert result is False
        assert "invoked" not in called

    @pytest.mark.asyncio
    async def test_unknown_command(self, registry: CommandRegistry) -> None:
        result = await registry._dispatch_plugin("/unknown")
        assert result is False
