#!/usr/bin/env python3
"""agent/commands/cmd_rag_export.py

Export and compact mixin for CommandRegistry.

Provides _RagExportMixin with:
  _cmd_export            — /export: dump conversation to Markdown or JSON
  _cmd_compact           — /compact: force immediate context compression
"""

import logging
from typing import Any

from agent.commands.mixin_base import MixinBase
from agent.history import HistoryCompressionError
from agent.services.export_formatter import render_export, write_export

logger = logging.getLogger(__name__)


class _RagExportMixin(MixinBase):
    """Export and compact slash-command handlers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

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

    async def _cmd_compact(self) -> None:
        """Force immediate compression of conversation history.

        Bypasses the context_char_limit threshold and compresses the oldest
        context_compress_turns pairs unconditionally.
        """
        ctx = self._ctx
        if ctx.services_required.hist_mgr is None:
            self._out.write("History manager not available.")
            return
        turn_msgs = [m for m in ctx.conv.history if m["role"] != "system"]
        # compress_turns * 2: each "turn" = 1 user + 1 assistant message
        n_compress = ctx.services_required.hist_mgr.compress_turns * 2
        if len(turn_msgs) <= n_compress:
            self._out.write("Nothing to compact: history too short.")
            return
        try:
            (
                ctx.conv.history,
                result,
            ) = await ctx.services_required.hist_mgr.force_compress(ctx.conv.history)
            if (
                result.compressed_count > 0
                or result.summary_added
                or result.is_fallback
            ):
                ctx.session.replace_messages(ctx.conv.history)
        except HistoryCompressionError as e:
            self._out.write_error(f"Compression failed: {e}")
            return
