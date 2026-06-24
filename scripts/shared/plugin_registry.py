#!/usr/bin/env python3
"""plugin_registry.py
Plugin registration decorators and auto-discovery for Agent extensions.

Three extension points are provided:

  @register_command("/name", prefix=False)
      Add a new slash command.  Handler receives (ctx, args) and may be sync
      or async.  prefix=True allows the command to receive trailing text.

  @register_tool("tool_name")
      Register a local Python async function as a tool handler.  Bypasses
      MCP routing entirely; ToolExecutor calls the function directly.

  @register_pipeline_stage(when="post")
      Hook into the RAG pipeline after cross-encoder reranking.  Handler
      receives (hits, query) and returns the (possibly modified) hits list.

Plugins are plain *.py files placed in the plugins/ directory.  Call
load_plugins(plugin_dir) at startup to import them; each file's
@register_* decorators execute at import time.

Example plugin (plugins/my_plugin.py):

    from shared.plugin_registry import register_command, register_tool

    @register_command("/ping")
    async def cmd_ping(ctx, args: str) -> None:
        print("pong")

    @register_tool("echo")
    async def tool_echo(args: dict) -> tuple[str, bool]:
        return str(args.get("text", "")), False
"""

from __future__ import annotations

import asyncio
import importlib.util
import logging
import typing
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, TypeVar, runtime_checkable

from rag.types import RagHit

logger = logging.getLogger(__name__)

_F = TypeVar("_F", bound=Callable[..., Any])


@runtime_checkable
class PipelineHook(Protocol):
    """Post-rerank pipeline hook contract.

    Input:  list[RagHit] + query str
    Output: list[RagHit] (modified or filtered)
    strict=True:  exception propagates; pipeline fails
    strict=False: exception logged as WARNING; original hits returned
    """
    async def __call__(self, hits: list[RagHit], query: str) -> list[RagHit]: ...

# Type alias for registered tool handlers: async function (args dict) → (output, is_error)
ToolHandler = Callable[[dict[str, Any]], Awaitable[tuple[str, bool]]]

# ── Internal registries ───────────────────────────────────────────────────────

# Stores (handler, is_prefix, module_name) per command name.
_commands: dict[str, tuple[Callable[..., Any], bool, str]] = {}
# Stores (handler, module_name) per tool name.
_tools: dict[str, tuple[Callable[..., Any], str]] = {}
_pipeline_post: list[PipelineHook] = []

# Set by load_plugins() around each exec_module() call so that decorators can
# record the originating module name without an explicit parameter.
_current_loading_module: str = ""

# Registered builtin command names for conflict detection.
# Populated by agent/factory.py at startup via register_builtin_commands().
_builtin_command_names: frozenset[str] = frozenset()


# ── Decorators ────────────────────────────────────────────────────────────────


def register_command(name: str, *, prefix: bool = False) -> Callable[[_F], _F]:
    """Register a slash-command plugin; name includes the leading slash; prefix=True allows trailing args."""

    def decorator(fn: _F) -> _F:
        _commands[name] = (fn, prefix, _current_loading_module)
        logger.debug("[plugin] command registered: %s", name)
        return fn

    return decorator


def register_tool(name: str) -> Callable[[_F], _F]:
    """Register a local async function as a tool handler; bypasses MCP entirely."""

    def decorator(fn: _F) -> _F:
        _tools[name] = (fn, _current_loading_module)
        hints = typing.get_type_hints(fn)
        return_hint = hints.get("return")
        if return_hint is None:
            logger.warning(
                "[plugin] warn: tool '%s' missing return type annotation", name
            )
        elif return_hint != tuple[str, bool]:
            logger.warning(
                "[plugin] warn: tool '%s' expected return type 'tuple[str, bool]', got %s",
                name,
                return_hint,
            )
        logger.debug("[plugin] tool registered: %s", name)
        return fn

    return decorator


def register_pipeline_stage(*, when: str = "post") -> Callable[[_F], _F]:
    """Register a RAG pipeline stage hook; when='post' is called after cross-encoder rerank."""
    if when != "post":
        raise ValueError(
            f"Unsupported pipeline stage position: {when!r}. Only 'post' is supported.",
        )

    def decorator(fn: _F) -> _F:
        _pipeline_post.append(fn)
        logger.debug("Pipeline post-stage registered: %r", fn.__name__)
        return fn

    return decorator


def get_pipeline_post_stages() -> list[PipelineHook]:
    """Return a snapshot of all registered post-rerank pipeline stage hooks."""
    return list(_pipeline_post)


# ── Accessors ─────────────────────────────────────────────────────────────────


def get_command(name: str) -> tuple[Callable[..., Any], bool] | None:
    """Return (handler, is_prefix) for the registered command, or None."""
    entry = _commands.get(name)
    if entry is None:
        return None
    fn, prefix, _mod = entry
    return (fn, prefix)


def iter_commands() -> dict[str, tuple[Callable[..., Any], bool]]:
    """Return a snapshot of all registered plugin commands."""
    return {name: (fn, prefix) for name, (fn, prefix, _mod) in _commands.items()}


def get_tool(name: str) -> Callable[..., Any] | None:
    """Return the registered local tool handler, or None."""
    entry = _tools.get(name)
    if entry is None:
        return None
    fn, _mod = entry
    return fn


def iter_tools() -> dict[str, Callable[..., Any]]:
    """Return a snapshot of all registered plugin tools."""
    return {name: fn for name, (fn, _mod) in _tools.items()}


def get_pipeline_post_stages() -> list[Callable[..., Any]]:
    """Return a snapshot of all registered post-rerank pipeline stage hooks."""
    return list(_pipeline_post)


def register_builtin_commands(names: frozenset[str]) -> None:
    """Register built-in command names for conflict detection during plugin loading.

    Called by the agent layer at startup to provide the set of builtin command
    names.  This avoids a direct import from agent to shared, preserving the
    import architecture constraint (shared must not import from agent).
    """
    global _builtin_command_names
    _builtin_command_names = names


async def run_pipeline_stages(
    hooks: list[PipelineHook],
    hits: list[RagHit],
    query: str,
    *,
    strict: bool = False,
) -> list[RagHit]:
    """Execute all registered post-rerank hooks with error isolation.

    Iterates hooks; calls each hook with (hits, query).
    Supports both sync and async hooks (detected via asyncio.iscoroutinefunction).
    Failed hooks are logged and skipped; strict=True re-raises the first failure.
    Returns the (possibly modified) hits list.
    """
    for hook in hooks:
        try:
            if asyncio.iscoroutinefunction(hook):
                result = await hook(hits, query)
            else:
                result = hook(hits, query)
            if result is not None:
                hits = result
        except Exception as exc:  # noqa: BLE001 — plugin hook may raise any exception type
            msg = (
                f'Plugin hook "{hook.__name__}" failed on query "{query[:60]}": '
                f"{type(exc).__name__}: {exc}"
            )
            if strict:
                logger.error(msg)
                raise
            logger.warning(msg)
    return hits


# ── Plugin load result types ─────────────────────────────────────────────────


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
    command_shadows: int = 0


class PluginLoadError(RuntimeError):
    """Raised in strict mode when one or more plugins fail to load."""


# ── Plugin auto-discovery ─────────────────────────────────────────────────────


def _validate_tool_conflicts(
    known_tools: frozenset[str],
    override_policy: str,
    strict_mode: bool = False,
) -> tuple[int, int, list[str]]:
    """Validate plugin tools against known MCP tool names.

    Returns (shadowed_count, allowed_count, strict_rejected_names).
    """
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


def _validate_command_conflicts(strict_mode: bool = False) -> int:
    """Warn when a plugin command shadows a built-in command name.

    Uses names registered via register_builtin_commands(). Returns the number
    of shadowed commands.
    """
    if not _builtin_command_names:
        return 0

    shadowed_count = 0
    for name in list(_commands.keys()):
        if name in _builtin_command_names:
            _fn, _prefix, module_name = _commands[name]
            shadowed_count += 1
            logger.info(
                "[plugin] command shadow: '%s' in '%s' shadows built-in",
                name,
                module_name,
            )
            if strict_mode:
                logger.error(
                    "[plugin] command shadow: '%s' in '%s' shadows built-in (strict mode)",
                    name,
                    module_name,
                )
    if shadowed_count:
        logger.info("[plugin] command shadows: %d", shadowed_count)
    return shadowed_count


def load_plugins(
    plugin_dir: str | Path,
    *,
    known_tools: frozenset[str] = frozenset(),
    override_policy: str = "reject",
    strict_mode: bool = False,
) -> PluginLoadResult:
    """Import all *.py files from plugin_dir; returns PluginLoadResult with success/failure details.

    When *strict_mode* is True, all plugins are attempted first, then a single
    PluginLoadError is raised with aggregated failure details (rather than
    stopping on the first failure).

    When *known_tools* is non-empty and *override_policy* is ``"reject"``,
    plugin tools that conflict with known MCP tools are removed after loading
    (not the entire directory -- other plugins continue loading).
    """
    global _current_loading_module

    plugin_path = Path(plugin_dir)
    if not plugin_path.is_dir():
        logger.debug("Plugin dir not found, skipping: %s", plugin_dir)
        return PluginLoadResult(loaded_count=0, failed=())

    loaded = 0
    failures: list[PluginFailure] = []
    for py_file in sorted(plugin_path.glob("*.py")):
        _current_loading_module = py_file.stem
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
            _current_loading_module = ""

    logger.info("[plugin] loaded=%d, skipped=%d", loaded, len(failures))

    # Run conflict validation after all modules are loaded
    shadowed, allowed, strict_rejected = _validate_tool_conflicts(
        known_tools, override_policy, strict_mode
    )
    cmd_shadows = _validate_command_conflicts(strict_mode)

    if strict_mode and (failures or strict_rejected):
        parts: list[str] = []
        if failures:
            details = "; ".join(f.error for f in failures)
            parts.append(f"Plugin load failed ({len(failures)} error(s)): {details}")
        if strict_rejected:
            parts.append(
                f"Tool MCP conflicts rejected: {', '.join(strict_rejected)}"
            )
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


# ── Test helper ───────────────────────────────────────────────────────────────


_last_load_result: PluginLoadResult | None = None


def get_last_load_result() -> PluginLoadResult | None:
    """Return the most recent PluginLoadResult, or None before first load."""
    return _last_load_result


def _set_last_load_result(result: PluginLoadResult) -> None:
    global _last_load_result
    _last_load_result = result


def _reset_for_testing() -> None:
    """Clear all registries.  Call from test setUp / pytest fixtures only."""
    global _current_loading_module, _builtin_command_names, _last_load_result
    _commands.clear()
    _tools.clear()
    _pipeline_post.clear()
    _builtin_command_names = frozenset()
    _current_loading_module = ""
    _last_load_result = None
