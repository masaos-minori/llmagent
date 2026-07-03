#!/usr/bin/env python3
"""shared/plugin_result.py — Plugin loading result types."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PluginFailure:
    path: str
    error: str


@dataclass(frozen=True)
class PluginLoadResult:
    loaded_count: int
    failed: tuple[PluginFailure, ...]
    tool_conflicts_shadowed: int = 0
    tool_conflicts_allowed: int = 0
    command_shadows_rejected: int = 0


class PluginLoadError(RuntimeError):
    """Raised in strict mode when one or more plugins fail to load."""
