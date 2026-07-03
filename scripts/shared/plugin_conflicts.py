#!/usr/bin/env python3
"""shared/plugin_conflicts.py — Plugin conflict validation helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.plugin_registries import (  # noqa: F401
        _builtin_command_names,
        _commands,
        _tools,
    )

logger = logging.getLogger(__name__)


def validate_tool_conflicts(
    known_tools: frozenset[str],
    override_policy: str,
    strict_mode: bool = False,
) -> tuple[int, int, list[str]]:
    """Validate plugin tools against known MCP tool names.

    Returns (shadowed_count, allowed_count, strict_rejected_names).
    """
    from shared.plugin_registries import _tools  # noqa: PLC0415 — break circular import

    if not known_tools:
        return (0, 0, [])

    shadowed_count = 0
    allowed_count = 0
    strict_rejected: list[str] = []
    for tool_name in list(_tools.keys()):
        if tool_name in known_tools:
            _fn, module_name = _tools[tool_name]
            if override_policy == "allow":
                allowed_count += 1
                logger.info(
                    "[plugin] conflict: tool '%s' in '%s' shadows MCP tool — allowed",
                    tool_name,
                    module_name,
                )
            else:
                del _tools[tool_name]
                shadowed_count += 1
                if strict_mode:
                    strict_rejected.append(tool_name)
                logger.info(
                    "[plugin] conflict: tool '%s' in '%s' shadows MCP tool — rejected",
                    tool_name,
                    module_name,
                )
    if shadowed_count or allowed_count:
        logger.info(
            "[plugin] tool conflicts: shadowed=%d, allowed=%d",
            shadowed_count,
            allowed_count,
        )
    return (shadowed_count, allowed_count, strict_rejected)


def validate_command_conflicts(strict_mode: bool = False) -> tuple[int, list[str]]:
    """Reject plugin commands that shadow a built-in command name.

    Uses names registered via register_builtin_commands(). Removes shadowed
    commands from _commands and returns (shadowed_count, strict_rejected_names).
    """
    from shared.plugin_registries import (  # noqa: PLC0415 — break circular import
        _builtin_command_names,
        _commands,
    )

    if not _builtin_command_names[0]:
        return (0, [])

    shadowed_count = 0
    strict_rejected: list[str] = []
    for name in list(_commands.keys()):
        if name in _builtin_command_names[0]:
            _fn, _prefix, module_name = _commands[name]
            del _commands[name]
            shadowed_count += 1
            if strict_mode:
                strict_rejected.append(name)
            logger.info(
                "[plugin] command shadow rejected: '%s' in '%s' shadows built-in",
                name,
                module_name,
            )
    if shadowed_count:
        logger.info("[plugin] command shadows rejected: %d", shadowed_count)
    return (shadowed_count, strict_rejected)
