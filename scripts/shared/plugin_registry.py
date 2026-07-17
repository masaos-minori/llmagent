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

Lifecycle contract:
  Startup:
    Call register_builtin_commands() before load_plugins() so conflict detection works.
    Call load_plugins(plugin_dir) once at process startup; calling it multiple times is
    allowed but each call replaces _last_load_result and ADDS to existing registries.
    Existing registrations are NOT cleared between calls.
  Repeated loads:
    Calling load_plugins() more than once is safe but accumulates registrations.
    Duplicate command/tool names registered by a later call silently overwrite earlier ones.
    _last_load_result reflects only the most recent call.
  Test isolation:
    Call _reset_for_testing() at the start of each test that loads plugins.
    This is the ONLY supported way to clear global registry state.
    Do not call _reset_for_testing() in non-test code.
  Reload:
    No hot-reload is implemented. Restarting the process is the intended upgrade path.
"""

from __future__ import annotations

import inspect
import logging
import typing
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Protocol, TypeVar, runtime_checkable

from shared.plugin_registries import (
    _builtin_command_names,
    _commands,
    _current_loading_module,
    _pipeline_post,
    _tools,
)
from shared.plugin_result import PluginLoadResult
from shared.types import RagHit

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


# ── Decorators ────────────────────────────────────────────────────────────────


def register_command(name: str, *, prefix: bool = False) -> Callable[[_F], _F]:
    """Register a slash-command plugin; name includes the leading slash; prefix=True allows trailing args."""

    def decorator(fn: _F) -> _F:
        _commands[name] = (fn, prefix, _current_loading_module[0])
        logger.debug("[plugin] command registered: %s", name)
        return fn

    return decorator


def register_tool(name: str) -> Callable[[_F], _F]:
    """Register a local async function as a tool handler; bypasses MCP entirely."""

    def decorator(fn: _F) -> _F:
        if not inspect.iscoroutinefunction(fn):
            raise ValueError(
                f"[plugin] tool contract violation: '{name}' handler must be "
                f"an async function (defined with 'async def')"
            )
        hints = typing.get_type_hints(fn)
        return_hint = hints.get("return")
        if return_hint is None:
            raise ValueError(
                f"[plugin] tool contract violation: '{name}' missing return type annotation (expected tuple[str, bool])"
            )
        if return_hint != tuple[str, bool]:
            raise ValueError(
                f"[plugin] tool contract violation: '{name}' expected return type 'tuple[str, bool]', got {return_hint}"
            )
        _tools[name] = (fn, _current_loading_module[0])
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
    fn_typed: Callable[..., Any] | None = fn
    return fn_typed


def iter_tools() -> dict[str, Callable[..., Any]]:
    """Return a snapshot of all registered plugin tools."""
    return {name: fn for name, (fn, _mod) in _tools.items()}


def register_builtin_commands(names: frozenset[str]) -> None:
    """Register built-in command names for conflict detection during plugin loading.

    Called by the agent layer at startup to provide the set of builtin command
    names.  This avoids a direct import from agent to shared, preserving the
    import architecture constraint (shared must not import from agent).
    """
    _builtin_command_names[0] = names


async def run_pipeline_stages(
    hooks: list[PipelineHook],
    hits: list[RagHit],
    query: str,
    *,
    strict: bool = False,
) -> list[RagHit]:
    """Execute all registered post-rerank hooks with error isolation.

    Iterates hooks; calls each hook with (hits, query).
    Supports both sync and async hooks (detected via inspect.iscoroutinefunction).
    Failed hooks are logged and skipped; strict=True re-raises the first failure.
    Returns the (possibly modified) hits list.
    """
    for hook in hooks:
        try:
            if inspect.iscoroutinefunction(hook):
                result = await hook(hits, query)
            else:
                result = hook(hits, query)  # type: ignore[assignment]
            if result is not None:
                hits = result
        except Exception as exc:  # noqa: BLE001 — plugin hook may raise any exception type
            msg = (
                f'Plugin hook "{getattr(hook, "__name__", repr(hook))}" failed on query "{query[:60]}": '
                f"{type(exc).__name__}: {exc}"
            )
            if strict:
                logger.error(msg)
                raise
            logger.warning(msg)
    return hits


# ── Plugin auto-discovery ─────────────────────────────────────────────────────


# Use lazy access so patches on shared.plugin_auto_discover propagate correctly.
def get_last_load_result() -> PluginLoadResult | None:  # noqa: F811 — replaces re-export
    """Return the most recent PluginLoadResult, or None before first load."""
    from shared.plugin_auto_discover import (
        get_last_load_result as _get,  # noqa: PLC0415
    )

    return _get()


def load_plugins(  # noqa: F811 — replaces re-export
    plugin_dir: str | Path,
    *,
    known_tools: frozenset[str] = frozenset(),
    override_policy: str = "reject",
    strict_mode: bool = False,
) -> PluginLoadResult:
    """Import all *.py files from plugin_dir; returns PluginLoadResult with success/failure details."""
    from shared.plugin_auto_discover import load_plugins as _load  # noqa: PLC0415

    return _load(
        plugin_dir,
        known_tools=known_tools,
        override_policy=override_policy,
        strict_mode=strict_mode,
    )


def _reset_for_testing() -> None:  # noqa: F811 — replaces re-export
    """Clear all registries and reset module-level state.

    For test use only. Do not call from production code.
    Call at the start (and optionally end) of each test that loads plugins
    or registers commands/tools directly. This is the only supported way
    to clear global registry state between tests.
    """
    from shared.plugin_auto_discover import (
        _reset_for_testing as _reset,  # noqa: PLC0415
    )

    _reset()
