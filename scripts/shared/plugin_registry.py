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
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

_F = TypeVar("_F", bound=Callable[..., Any])

# Type alias for registered tool handlers: async function (args dict) → (output, is_error)
ToolHandler = Callable[[dict[str, Any]], Awaitable[tuple[str, bool]]]

# ── Internal registries ───────────────────────────────────────────────────────

_commands: dict[str, tuple[Callable[..., Any], bool]] = {}
_tools: dict[str, Callable[..., Any]] = {}
_pipeline_post: list[Callable[..., Any]] = []


# ── Decorators ────────────────────────────────────────────────────────────────


def register_command(name: str, *, prefix: bool = False) -> Callable[[_F], _F]:
    """Register a slash-command plugin; name includes the leading slash; prefix=True allows trailing args."""

    def decorator(fn: _F) -> _F:
        _commands[name] = (fn, prefix)
        logger.debug("Plugin command registered: %s", name)
        return fn

    return decorator


def register_tool(name: str) -> Callable[[_F], _F]:
    """Register a local async function as a tool handler; bypasses MCP entirely."""

    def decorator(fn: _F) -> _F:
        _tools[name] = fn
        hints = typing.get_type_hints(fn)
        return_hint = hints.get("return")
        if return_hint is not None and return_hint != tuple[str, bool]:
            logger.warning(
                "Plugin tool %r: expected return type 'tuple[str, bool]', got %s",
                name,
                return_hint,
            )
        logger.debug("Plugin tool registered: %s", name)
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


# ── Accessors ─────────────────────────────────────────────────────────────────


def get_command(name: str) -> tuple[Callable[..., Any], bool] | None:
    """Return (handler, is_prefix) for the registered command, or None."""
    return _commands.get(name)


def iter_commands() -> dict[str, tuple[Callable[..., Any], bool]]:
    """Return a snapshot of all registered plugin commands."""
    return dict(_commands)


def get_tool(name: str) -> Callable[..., Any] | None:
    """Return the registered local tool handler, or None."""
    return _tools.get(name)


def iter_tools() -> dict[str, Callable[..., Any]]:
    """Return a snapshot of all registered plugin tools."""
    return dict(_tools)


def get_pipeline_post_stages() -> list[Callable[..., Any]]:
    """Return a snapshot of all registered post-rerank pipeline stage hooks."""
    return list(_pipeline_post)


async def run_pipeline_stages(
    hits: list[Any],
    query: str,
    *,
    strict: bool = False,
) -> list[Any]:
    """Execute all registered post-rerank hooks with error isolation.

    Iterates get_pipeline_post_stages(); calls each hook with (hits, query).
    Supports both sync and async hooks (detected via asyncio.iscoroutinefunction).
    Failed hooks are logged and skipped; strict=True re-raises the first failure.
    Returns the (possibly modified) hits list.
    """
    for hook in get_pipeline_post_stages():
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


# ── Plugin auto-discovery ─────────────────────────────────────────────────────


def _validate_tool_conflicts(
    known_tools: frozenset[str],
    override_policy: str,
) -> dict[str, bool]:
    """Validate plugin tools against known MCP tool names.

    Returns a dict mapping tool_name → True if the tool was removed (rejected).
    """
    if not known_tools:
        return {}

    removed: dict[str, bool] = {}
    for tool_name in list(_tools.keys()):
        if tool_name in known_tools:
            if override_policy == "allow":
                logger.warning(
                    "Plugin tool %r shadows MCP tool; override policy allows it",
                    tool_name,
                )
            else:
                del _tools[tool_name]
                removed[tool_name] = True
                logger.error(
                    "Plugin tool %r rejected: conflicts with MCP tool. "
                    "Set plugin_tool_override = true to allow.",
                    tool_name,
                )
    return removed


def _validate_command_conflicts(strict_mode: bool = False) -> dict[str, bool]:
    """Warn when a plugin command shadows a built-in command name.

    Returns a dict mapping command_name to True when shadowing was detected.
    """
    try:
        from agent.commands.command_defs import _COMMANDS  # noqa: I001 — deferred: avoid circular import at module level
    except ImportError:
        return {}

    builtin_names = frozenset(cmd.name for cmd in _COMMANDS)
    shadowed: dict[str, bool] = {}
    for name in list(_commands.keys()):
        if name in builtin_names:
            shadowed[name] = True
            msg = (
                f"Plugin command {name!r} shadows built-in command."
                " The built-in command will take precedence."
            )
            if strict_mode:
                logger.error(msg)
            else:
                logger.warning(msg)
    return shadowed


def load_plugins(
    plugin_dir: str | Path,
    *,
    known_tools: frozenset[str] = frozenset(),
    override_policy: str = "reject",
    strict_mode: bool = False,
) -> PluginLoadResult:
    """Import all *.py files from plugin_dir; returns PluginLoadResult with success/failure details.

    When *strict_mode* is True, the first plugin import failure raises
    the original exception instead of logging and continuing.

    When *known_tools* is non-empty and *override_policy* is ``"reject"``,
    plugin tools that conflict with known MCP tools are removed after loading
    (not the entire directory -- other plugins continue loading).
    """
    plugin_path = Path(plugin_dir)
    if not plugin_path.is_dir():
        logger.debug("Plugin dir not found, skipping: %s", plugin_dir)
        return PluginLoadResult(loaded_count=0, failed=())

    loaded = 0
    failures: list[PluginFailure] = []
    for py_file in sorted(plugin_path.glob("*.py")):
        try:
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                loaded += 1
                logger.info("Plugin loaded: %s", py_file.name)
        except (ImportError, SyntaxError, AttributeError, RuntimeError) as e:
            error_msg = f"Plugin load failed ({py_file.name}): {type(e).__name__}: {e}"
            failures.append(PluginFailure(path=py_file.name, error=error_msg))
            if strict_mode:
                logger.error(error_msg)
                raise
            logger.warning(error_msg)

    # Run conflict validation after all modules are loaded
    _validate_tool_conflicts(known_tools, override_policy)
    _validate_command_conflicts(strict_mode)
    return PluginLoadResult(loaded_count=loaded, failed=tuple(failures))


# ── Test helper ───────────────────────────────────────────────────────────────


def _reset_for_testing() -> None:
    """Clear all registries.  Call from test setUp / pytest fixtures only."""
    _commands.clear()
    _tools.clear()
    _pipeline_post.clear()
