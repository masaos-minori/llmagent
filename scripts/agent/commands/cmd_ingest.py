#!/usr/bin/env python3
"""agent/commands/cmd_ingest.py
Export, ingest, and compact mixin for CommandRegistry.

Provides _IngestMixin with:
  _cmd_export            — /export: dump conversation to Markdown or JSON
  _cmd_ingest            — /ingest: crawl/ingest a URL or local file
  _cmd_compact           — /compact: force immediate context compression
  _cmd_rag               — /rag: search the RAG knowledge base
"""

import logging

from mcp.rag_pipeline.models import RagPipelineConfig, build_rag_cfg_adapter

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
        from agent.services.exceptions import (
            IngestStageError,  # noqa: PLC0415 — lazy: deferred to avoid import cost
        )
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
        try:
            result = await svc.run(target, lang=lang, snippets_only=snippets_only)
            for msg in result.messages:
                print(f"  {msg}")
        except IngestStageError as e:
            logger.error("Ingest failed at stage=%s: %s", e.stage, e.detail)
            print(f"  [ingest] error ({e.stage}): {e.detail}")

    async def _cmd_rag(self, args: str) -> None:
        """Search the RAG knowledge base with a query.

        Usage:
          /rag search <query>           Run RAG search and print context
          /rag search <query> --debug   Also print per-stage latency
        """
        from rag.pipeline import (
            RagPipeline,  # noqa: PLC0415 — lazy: heavy RAG module deferred to /rag call
        )
        from shared.config_loader import (
            ConfigLoader,  # noqa: PLC0415 — lazy: deferred to /rag call
        )

        ctx = self._ctx
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else ""
        if sub != "search" or len(parts) < 2:
            print("Usage: /rag search <query> [--debug]")
            return

        remainder = parts[1]
        debug = "--debug" in remainder
        query = remainder.replace("--debug", "").strip()
        if not query:
            print("Usage: /rag search <query> [--debug]")
            return

        if ctx.services is None or ctx.services.http is None:
            print("HTTP client not available.")
            return

        rag_cfg_dict = ConfigLoader().load("common.toml", "rag.toml")

        if not rag_cfg_dict.get("use_search", True):
            print("RAG search is disabled (use_search=false in config).")
            return

        rag_cfg = build_rag_cfg_adapter(RagPipelineConfig.from_dict(rag_cfg_dict))
        pipeline = RagPipeline(ctx.services.http, rag_cfg)
        context = await pipeline.augment(query)
        if not context:
            print("No results found.")
        else:
            print(context)

        if debug:
            timings = pipeline.last_timings
            if timings:
                print("\n--- Stage timings ---")
                for stage_name, elapsed in timings.items():
                    print(f"  {stage_name}: {elapsed * 1000:.1f} ms")

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
