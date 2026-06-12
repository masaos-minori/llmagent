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

import importlib.util
import logging
from collections.abc import Awaitable, Callable
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


def get_pipeline_post_stages() -> list[Callable[..., Any]]:
    """Return a snapshot of all registered post-rerank pipeline stage hooks."""
    return list(_pipeline_post)


# ── Plugin auto-discovery ─────────────────────────────────────────────────────


def load_plugins(plugin_dir: str | Path) -> int:
    """Import all *.py files from plugin_dir; returns count loaded; errors are logged and skipped."""
    plugin_path = Path(plugin_dir)
    if not plugin_path.is_dir():
        logger.debug("Plugin dir not found, skipping: %s", plugin_dir)
        return 0

    loaded = 0
    for py_file in sorted(plugin_path.glob("*.py")):
        try:
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                loaded += 1
                logger.info("Plugin loaded: %s", py_file.name)
        except (ImportError, SyntaxError, AttributeError) as e:
            logger.warning("Plugin load failed (%s): %s", py_file.name, e)
    return loaded


# ── Test helper ───────────────────────────────────────────────────────────────


def _reset_for_testing() -> None:
    """Clear all registries.  Call from test setUp / pytest fixtures only."""
    _commands.clear()
    _tools.clear()
    _pipeline_post.clear()
