#!/usr/bin/env python3
"""agent/commands/cmd_mdq.py
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

import logging
from typing import Any

from agent.commands.mixin_base import MixinBase

logger = logging.getLogger(__name__)


class _MdqMixin(MixinBase):
    """MDQ slash-command handlers."""

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
        ctx = self._ctx
        if ctx.services is None or ctx.services.tools is None:
            self._out.write("MCP tool executor not available.")
            return

        result = await ctx.services.tools.execute("stats", {})

        if result.is_error:
            self._out.write(f"[mdq] error: {result.output}")
            return

        self._out.write("[mdq] stats")
        self._out.write(result.output)

    async def _cmd_mdq_index(self, args: str) -> None:
        """Index a Markdown path into the MDQ store.

        Usage: /mdq index <path> [--force]
        """
        ctx = self._ctx
        if ctx.services is None or ctx.services.tools is None:
            self._out.write("MCP tool executor not available.")
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

        result = await ctx.services.tools.execute("index_paths", tool_args)

        if result.is_error:
            self._out.write(f"[mdq] error: {result.output}")
            return

        self._out.write("[mdq] index")
        self._out.write(result.output)

    async def _cmd_mdq_refresh(self, args: str) -> None:
        """Incrementally refresh the index for changed Markdown files.

        Usage: /mdq refresh <path> [--force]
        """
        ctx = self._ctx
        if ctx.services is None or ctx.services.tools is None:
            self._out.write("MCP tool executor not available.")
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

        result = await ctx.services.tools.execute("refresh_index", tool_args)

        if result.is_error:
            self._out.write(f"[mdq] error: {result.output}")
            return

        self._out.write("[mdq] refresh")
        self._out.write(result.output)

    async def _cmd_mdq_search(self, args: str) -> None:
        """Search indexed Markdown content.

        Usage: /mdq search <query> [--limit N] [--path-prefix PATH] [--mode bm25|grep]
        """
        ctx = self._ctx
        if ctx.services is None or ctx.services.tools is None:
            self._out.write("MCP tool executor not available.")
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
                try:
                    tool_args["limit"] = (
                        int(part.split("=")[1])
                        if "=" in part
                        else int(parts[parts.index(part) + 1])
                    )
                except (ValueError, IndexError):
                    pass
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

        result = await ctx.services.tools.execute("search_docs", tool_args)

        if result.is_error:
            self._out.write(f"[mdq] error: {result.output}")
            return

        self._out.write("[mdq] search")
        self._out.write(result.output)

    async def _cmd_mdq_outline(self, args: str) -> None:
        """Get the heading hierarchy of a Markdown file.

        Usage: /mdq outline <path> [--max-depth N]
        """
        ctx = self._ctx
        if ctx.services is None or ctx.services.tools is None:
            self._out.write("MCP tool executor not available.")
            return

        parts = args.strip().split()
        if not parts:
            self._out.write("Usage: /mdq outline <path> [--max-depth N]")
            return

        path = parts[0]
        tool_args: dict[str, Any] = {"path": path}

        for part in parts[1:]:
            if part.startswith("--max-depth"):
                try:
                    tool_args["max_outline_items"] = (
                        int(part.split("=")[1])
                        if "=" in part
                        else int(parts[parts.index(part) + 1])
                    )
                except (ValueError, IndexError):
                    pass

        result = await ctx.services.tools.execute("outline", tool_args)

        if result.is_error:
            self._out.write(f"[mdq] error: {result.output}")
            return

        self._out.write("[mdq] outline")
        self._out.write(result.output)

    async def _cmd_mdq_get(self, args: str) -> None:
        """Retrieve a Markdown chunk by ID.

        Usage: /mdq get <chunk_id> [--with-neighbors]
        """
        ctx = self._ctx
        if ctx.services is None or ctx.services.tools is None:
            self._out.write("MCP tool executor not available.")
            return

        parts = args.strip().split()
        if not parts:
            self._out.write("Usage: /mdq get <chunk_id> [--with-neighbors]")
            return

        chunk_id = parts[0]
        tool_args: dict[str, Any] = {"chunk_id": chunk_id}

        if "--with-neighbors" in parts:
            tool_args["with_neighbors"] = True

        result = await ctx.services.tools.execute("get_chunk", tool_args)

        if result.is_error:
            self._out.write(f"[mdq] error: {result.output}")
            return

        self._out.write("[mdq] get")
        self._out.write(result.output)

    async def _cmd_mdq_grep(self, args: str) -> None:
        """Search Markdown chunks with a regex pattern.

        Usage: /mdq grep <pattern> [--path PATH] [--max-chars N] [--context-before N] [--context-after N]
        """
        ctx = self._ctx
        if ctx.services is None or ctx.services.tools is None:
            self._out.write("MCP tool executor not available.")
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
                try:
                    tool_args["max_chars_per_match"] = (
                        int(part.split("=")[1])
                        if "=" in part
                        else int(parts[parts.index(part) + 1])
                    )
                except (ValueError, IndexError):
                    pass
            elif part.startswith("--context-before"):
                try:
                    tool_args["context_before"] = (
                        int(part.split("=")[1])
                        if "=" in part
                        else int(parts[parts.index(part) + 1])
                    )
                except (ValueError, IndexError):
                    pass
            elif part.startswith("--context-after"):
                try:
                    tool_args["context_after"] = (
                        int(part.split("=")[1])
                        if "=" in part
                        else int(parts[parts.index(part) + 1])
                    )
                except (ValueError, IndexError):
                    pass

        result = await ctx.services.tools.execute("grep_docs", tool_args)

        if result.is_error:
            self._out.write(f"[mdq] error: {result.output}")
            return

        self._out.write("[mdq] grep")
        self._out.write(result.output)
