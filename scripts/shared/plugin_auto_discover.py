#!/usr/bin/env python3
"""shared/plugin_auto_discover.py — Plugin auto-discovery and loading."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path

from shared.plugin_conflicts import validate_command_conflicts, validate_tool_conflicts
from shared.plugin_registries import (
    _builtin_command_names,
    _commands,
    _current_loading_module,
    _pipeline_post,
    _tools,
)
from shared.plugin_result import PluginFailure, PluginLoadError, PluginLoadResult

logger = logging.getLogger(__name__)


def load_plugins(
    plugin_dir: str | Path,
    *,
    known_tools: frozenset[str] = frozenset(),
    override_policy: str = "reject",
    strict_mode: bool = False,
) -> PluginLoadResult:
    """Import all *.py files from plugin_dir; returns PluginLoadResult with success/failure details.

    Intended to be called once per process at startup. Calling it multiple times
    is safe but accumulates registrations — duplicate command/tool names silently
    overwrite earlier ones. _last_load_result reflects only the most recent call.

    When *strict_mode* is True, all plugins are attempted first, then a single
    PluginLoadError is raised with aggregated failure details (rather than
    stopping on the first failure).

    When *known_tools* is non-empty and *override_policy* is ``"reject"``,
    plugin tools that conflict with known MCP tools are removed after loading
    (not the entire directory -- other plugins continue loading).
    """
    global _last_load_result

    plugin_path = Path(plugin_dir)
    if not plugin_path.is_dir():
        logger.debug("Plugin dir not found, skipping: %s", plugin_dir)
        return PluginLoadResult(loaded_count=0, failed=())

    loaded = 0
    failures: list[PluginFailure] = []
    for py_file in sorted(plugin_path.glob("*.py")):
        _current_loading_module[0] = py_file.stem
        try:
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                loaded += 1
                logger.info("[plugin] loaded: %s", py_file.name)
        except (ImportError, SyntaxError, AttributeError, RuntimeError) as e:
            error_msg = f"Plugin load failed ({py_file.name}): {type(e).__name__}: {e}"
            failures.append(PluginFailure(path=py_file.name, error=error_msg))
            logger.warning("[plugin] skipped: %s (%s)", py_file.name, type(e).__name__)
        finally:
            _current_loading_module[0] = ""

    logger.info("[plugin] loaded=%d, skipped=%d", loaded, len(failures))

    # Run conflict validation after all modules are loaded
    shadowed, allowed, strict_rejected = validate_tool_conflicts(
        known_tools, override_policy, strict_mode
    )
    cmd_shadows = validate_command_conflicts(strict_mode)

    if strict_mode and (failures or strict_rejected):
        parts: list[str] = []
        if failures:
            details = "; ".join(f.error for f in failures)
            parts.append(f"Plugin load failed ({len(failures)} error(s)): {details}")
        if strict_rejected:
            parts.append(f"Tool MCP conflicts rejected: {', '.join(strict_rejected)}")
        raise PluginLoadError("; ".join(parts))

    result = PluginLoadResult(
        loaded_count=loaded,
        failed=tuple(failures),
        tool_conflicts_shadowed=shadowed,
        tool_conflicts_allowed=allowed,
        command_shadows=cmd_shadows,
    )
    _set_last_load_result(result)
    return result


# Last load_plugins() call result; None until first load.
# Replaced (not accumulated) on each subsequent load_plugins() call.

_last_load_result: PluginLoadResult | None = None


def get_last_load_result() -> PluginLoadResult | None:
    """Return the most recent PluginLoadResult, or None before first load."""
    return _last_load_result


def _set_last_load_result(result: PluginLoadResult) -> None:
    global _last_load_result
    _last_load_result = result


def _reset_for_testing() -> None:  # type: ignore[name-defined] — mutable list assignment
    """Clear all registries. For test use only. Do not call from production code."""
    global _current_loading_module, _builtin_command_names, _last_load_result
    _commands.clear()
    _tools.clear()
    _pipeline_post.clear()
    _builtin_command_names[0] = frozenset()  # type: ignore[index] — mutable list assignment
    _current_loading_module[0] = ""  # type: ignore[index] — mutable list assignment
    _last_load_result = None
