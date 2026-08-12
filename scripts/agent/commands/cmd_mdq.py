#!/usr/bin/env python3
"""scripts/agent/commands/cmd_mdq.py

MDQ (Markdown Query) slash-command mixin for CommandRegistry.

Provides _MdqMixin with:
  _cmd_mdq_status   — /mdq status: health and index statistics
  _cmd_mdq_index    — /mdq index <path> [--force]: index a path
  _cmd_mdq_refresh  — /mdq refresh <path>: refresh index for a path
  _cmd_mdq_search   — /mdq search <query>: search indexed content
  _cmd_mdq_outline  — /mdq outline <path>: get heading structure
  _cmd_mdq_get      — /mdq get <chunk_id>: retrieve a chunk
  _cmd_mdq_grep     — /mdq grep <pattern>: search with regex
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from agent.commands.mixin_base import MixinBase

if TYPE_CHECKING:
    from shared.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


def _parse_int_flag(parts: list[str], part: str) -> int | None:
    """Parse '--flag=N' or '--flag N' (space-separated) into int; None on failure."""
    try:
        return (
            int(part.split("=")[1])
            if "=" in part
            else int(parts[parts.index(part) + 1])
        )
    except (ValueError, IndexError):
        return None


class _MdqMixin(MixinBase):
    """MDQ slash-command handlers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the MDQ mixin via MixinBase constructor."""
        super().__init__(*args, **kwargs)

    def _require_tools(self) -> ToolExecutor | None:
        """Return ctx.services.tools if available; else write a not-available message and return None."""
        ctx = self._ctx
        if ctx.services is None or ctx.services.tools is None:
            self._out.write("MCP tool executor not available.")
            return None
        return ctx.services.tools

    async def _execute_mdq(
        self,
        tools: ToolExecutor,
        tool_name: str,
        tool_args: dict[str, Any],
        success_label: str,
    ) -> None:
        """Execute an MDQ tool call and write '[mdq] error: ...' or the success label + output."""
        result = await tools.execute(tool_name, tool_args)
        if result.is_error:
            self._out.write(f"[mdq] error: {result.output}")
            return
        self._out.write(f"[mdq] {success_label}")
        self._out.write(result.output)

    async def _cmd_mdq(self, args: str) -> None:
        """Dispatch /mdq subcommands.

        Usage:
          /mdq status
          /mdq index <path> [--force]
          /mdq refresh <path> [--force]
          /mdq search <query> [--limit N] [--path-prefix PATH] [--mode bm25|grep]
          /mdq outline <path> [--max-depth N]
          /mdq get <chunk_id> [--with-neighbors]
          /mdq grep <pattern> [--path PATH] [--max-chars N] [--context-before N] [--context-after N]
        """
        parts = args.strip().split(maxsplit=1)
        subcmd = parts[0] if parts else "status"
        rest = parts[1] if len(parts) > 1 else ""

        if subcmd == "status":
            await self._cmd_mdq_status()
            return
        if subcmd == "index":
            await self._cmd_mdq_index(rest)
            return
        if subcmd == "refresh":
            await self._cmd_mdq_refresh(rest)
            return
        if subcmd == "search":
            await self._cmd_mdq_search(rest)
            return
        if subcmd == "outline":
            await self._cmd_mdq_outline(rest)
            return
        if subcmd == "get":
            await self._cmd_mdq_get(rest)
            return
        if subcmd == "grep":
            await self._cmd_mdq_grep(rest)
            return
        self._out.write("Usage: /mdq status|index|refresh|search|outline|get|grep")

    async def _cmd_mdq_status(self) -> None:
        """Report health and index statistics.

        Usage: /mdq status
        """
        tools = self._require_tools()
        if tools is None:
            return
        await self._execute_mdq(tools, "stats", {}, "stats")

    async def _cmd_mdq_index(self, args: str) -> None:
        """Index a Markdown path into the MDQ store.

        Usage: /mdq index <path> [--force]
        """
        tools = self._require_tools()
        if tools is None:
            return

        parts = args.strip().split()
        if not parts:
            self._out.write("Usage: /mdq index <path> [--force]")
            return

        path = parts[0]
        force = "--force" in parts

        tool_args: dict[str, Any] = {"paths": [path]}
        if force:
            tool_args["force"] = True

        await self._execute_mdq(tools, "index_paths", tool_args, "index")

    async def _cmd_mdq_refresh(self, args: str) -> None:
        """Incrementally refresh the index for changed Markdown files.

        Usage: /mdq refresh <path> [--force]
        """
        tools = self._require_tools()
        if tools is None:
            return

        parts = args.strip().split()
        if not parts:
            self._out.write("Usage: /mdq refresh <path> [--force]")
            return

        path = parts[0]
        force = "--force" in parts

        tool_args: dict[str, Any] = {"paths": [path]}
        if force:
            tool_args["force"] = True

        await self._execute_mdq(tools, "refresh_index", tool_args, "refresh")

    async def _cmd_mdq_search(self, args: str) -> None:
        """Search indexed Markdown content.

        Usage: /mdq search <query> [--limit N] [--path-prefix PATH] [--mode bm25|grep]
        """
        tools = self._require_tools()
        if tools is None:
            return

        parts = args.strip().split()
        if not parts:
            self._out.write(
                "Usage: /mdq search <query> [--limit N] [--path-prefix PATH] [--mode bm25|grep]"
            )
            return

        query = parts[0]
        tool_args: dict[str, Any] = {"query": query}

        for part in parts[1:]:
            if part.startswith("--limit"):
                limit = _parse_int_flag(parts, part)
                if limit is not None:
                    tool_args["limit"] = limit
            elif part.startswith("--path-prefix"):
                tool_args["path_prefix"] = (
                    part.split("=", 1)[1]
                    if "=" in part
                    else parts[parts.index(part) + 1]
                )
            elif part in ("--mode",):
                tool_args["mode"] = (
                    parts[parts.index(part) + 1]
                    if parts.index(part) + 1 < len(parts)
                    else "bm25"
                )
            elif part.startswith("--mode="):
                tool_args["mode"] = part.split("=", 1)[1]

        await self._execute_mdq(tools, "search_docs", tool_args, "search")

    async def _cmd_mdq_outline(self, args: str) -> None:
        """Get the heading hierarchy of a Markdown file.

        Usage: /mdq outline <path> [--max-depth N]
        """
        tools = self._require_tools()
        if tools is None:
            return

        parts = args.strip().split()
        if not parts:
            self._out.write("Usage: /mdq outline <path> [--max-depth N]")
            return

        path = parts[0]
        tool_args: dict[str, Any] = {"path": path}

        for part in parts[1:]:
            if part.startswith("--max-depth"):
                max_depth = _parse_int_flag(parts, part)
                if max_depth is not None:
                    tool_args["max_outline_items"] = max_depth

        await self._execute_mdq(tools, "outline", tool_args, "outline")

    async def _cmd_mdq_get(self, args: str) -> None:
        """Retrieve a Markdown chunk by ID.

        Usage: /mdq get <chunk_id> [--with-neighbors]
        """
        tools = self._require_tools()
        if tools is None:
            return

        parts = args.strip().split()
        if not parts:
            self._out.write("Usage: /mdq get <chunk_id> [--with-neighbors]")
            return

        chunk_id = parts[0]
        tool_args: dict[str, Any] = {"chunk_id": chunk_id}

        if "--with-neighbors" in parts:
            tool_args["with_neighbors"] = True

        await self._execute_mdq(tools, "get_chunk", tool_args, "get")

    async def _cmd_mdq_grep(self, args: str) -> None:
        """Search Markdown chunks with a regex pattern.

        Usage: /mdq grep <pattern> [--path PATH] [--max-chars N] [--context-before N] [--context-after N]
        """
        tools = self._require_tools()
        if tools is None:
            return

        parts = args.strip().split()
        if not parts:
            self._out.write(
                "Usage: /mdq grep <pattern> [--path PATH] [--max-chars N] [--context-before N] [--context-after N]"
            )
            return

        pattern = parts[0]
        tool_args: dict[str, Any] = {"pattern": pattern}

        for part in parts[1:]:
            if part.startswith("--path"):
                path_val = (
                    part.split("=", 1)[1]
                    if "=" in part
                    else parts[parts.index(part) + 1]
                )
                if "paths" not in tool_args:
                    tool_args["paths"] = []
                tool_args["paths"].append(path_val)
            elif part.startswith("--max-chars"):
                max_chars = _parse_int_flag(parts, part)
                if max_chars is not None:
                    tool_args["max_chars_per_match"] = max_chars
            elif part.startswith("--context-before"):
                context_before = _parse_int_flag(parts, part)
                if context_before is not None:
                    tool_args["context_before"] = context_before
            elif part.startswith("--context-after"):
                context_after = _parse_int_flag(parts, part)
                if context_after is not None:
                    tool_args["context_after"] = context_after

        await self._execute_mdq(tools, "grep_docs", tool_args, "grep")
