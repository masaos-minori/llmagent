#!/usr/bin/env python3
"""agent/commands/cmd_ingest.py
Export, ingest, and compact mixin for CommandRegistry.

Provides _IngestMixin with:
  _cmd_export            — /export: dump conversation to Markdown or JSON
  _cmd_ingest            — /ingest: crawl/ingest a URL or local file
  _cmd_compact           — /compact: force immediate context compression
"""

import logging

from agent.commands.mixin_base import MixinBase
from agent.commands.utils import render_export, write_export

logger = logging.getLogger(__name__)


class _IngestMixin(MixinBase):
    """Export, ingest, and compact slash-command handlers."""

    def _cmd_export(self, args: str) -> None:
        """Export the current conversation history to Markdown or JSON.

        Usage: /export [md|json] [filename]
        """
        ctx = self._ctx
        parts = args.strip().split()
        fmt = "md"
        outfile: str | None = None
        for part in parts:
            if part in ("md", "json"):
                fmt = part
            else:
                outfile = part
        content = render_export(ctx.conv.history, fmt)
        write_export(content, outfile, len(ctx.conv.history))

    async def _cmd_ingest(self, args: str) -> None:
        """Crawl/ingest a URL or local file into the RAG DB from within the REPL.

        Usage: /ingest <url|path> [ja|en] [--snippets-only]
        --snippets-only forces heading-based Markdown snippet chunking.
        """
        from agent.services.ingest_workflow import (
            IngestWorkflowService,  # noqa: PLC0415 — lazy: heavy ingest pipeline deferred to /ingest call
        )

        parts = args.strip().split()
        if not parts:
            print("Usage: /ingest <url|path> [lang=ja|en] [--snippets-only]")
            return
        target = parts[0]
        lang = "ja"
        snippets_only = False
        for p in parts[1:]:
            if p in ("ja", "en"):
                lang = p
            elif p == "--snippets-only":
                snippets_only = True

        svc = IngestWorkflowService()
        result = await svc.run(target, lang=lang, snippets_only=snippets_only)
        for msg in result.messages:
            print(f"  {msg}")
        if result.error:
            logger.error(f"Ingest failed at stage={result.stage}: {result.error}")
            print(f"  [ingest] error ({result.stage}): {result.error}")

    async def _cmd_compact(self) -> None:
        """Force immediate compression of conversation history.

        Bypasses the context_char_limit threshold and compresses the oldest
        context_compress_turns pairs unconditionally.
        """
        ctx = self._ctx
        if ctx.services.hist_mgr is None:
            print("History manager not available.")
            return
        turn_msgs = [m for m in ctx.conv.history if m["role"] != "system"]
        # compress_turns * 2: each "turn" = 1 user + 1 assistant message
        n_compress = ctx.services.hist_mgr.compress_turns * 2
        if len(turn_msgs) <= n_compress:
            print("Nothing to compact: history too short.")
            return
        ctx.conv.history = await ctx.services.hist_mgr.force_compress(ctx.conv.history)
