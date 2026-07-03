#!/usr/bin/env python3
"""shared/plugin_registries.py — Internal registries for plugin command/tool/pipeline hooks."""

from __future__ import annotations

import typing
from collections.abc import Callable

from shared.types import RagHit

_F = typing.TypeVar("_F", bound=Callable[..., typing.Any])


# Type alias for registered tool handlers: async function (args dict) → (output, is_error)
ToolHandler = Callable[[dict[typing.Any, typing.Any]], typing.Awaitable[tuple[str, bool]]]

# ── Internal registries ───────────────────────────────────────────────────────

# Stores (handler, is_prefix, module_name) per command name. Cleared only by _reset_for_testing().
_commands: dict[str, tuple[Callable[..., typing.Any], bool, str]] = {}
# Stores (handler, module_name) per tool name. Cleared only by _reset_for_testing().
_tools: dict[str, tuple[Callable[..., typing.Any], str]] = {}
# Pipeline hooks registered via @register_pipeline_stage(when="post"). Cleared only by _reset_for_testing().
_pipeline_post: list[RagHit] = []

# Mutable wrappers for values that need to be shared across modules (immutable types
# like str/frozenset can't be updated in-place, so we use mutable containers).
_current_loading_module: typing.MutableSequence[str] = [""]  # type: ignore[misc] — mutable list
_builtin_command_names: typing.MutableSequence[frozenset[str]] = [frozenset()]  # type: ignore[misc] — mutable list
