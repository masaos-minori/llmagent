#!/usr/bin/env python3
"""
agent_cmd_ingest.py
Export, ingest, and compact mixin for CommandRegistry.

Extracted from agent_commands.py.  Provides _IngestMixin with:
  _cmd_export            — /export: dump conversation to Markdown or JSON
  _run_split_and_ingest  — run ChunkSplitter + RagIngester in executor
  _cmd_ingest            — /ingest: crawl/ingest a URL or local file
  _cmd_compact           — /compact: force immediate context compression
"""

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import orjson
from config_loader import ConfigLoader

if TYPE_CHECKING:
    from agent_context import AgentContext

logger = logging.getLogger(__name__)


class _IngestMixin:
    """Export, ingest, and compact slash-command handlers."""

    if TYPE_CHECKING:
        _ctx: "AgentContext"

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

        content = (
            orjson.dumps(ctx.history, option=orjson.OPT_INDENT_2).decode()
            if fmt == "json"
            else self._render_history_md(ctx.history)  # type: ignore[attr-defined]  # provided by _RagMixin
        )

        if not outfile:
            print(content)
            return
        try:
            Path(outfile).write_text(content, encoding="utf-8")
            print(
                f"Exported {len(ctx.history)} messages to {outfile}"
                f" ({fmt.upper()}, {len(content)} chars)"
            )
            logger.info(f"Conversation exported to {outfile} ({fmt})")
        except OSError as e:
            print(f"Export failed: {e}")

    async def _run_split_and_ingest(
        self, loop: asyncio.AbstractEventLoop, snippets_only: bool = False
    ) -> None:
        """Run ChunkSplitter and RagIngester in a thread executor.

        snippets_only=True forces Markdown heading-based chunking regardless
        of the md_index_enable config value.
        """
        from chunk_splitter import ChunkSplitter as _ChunkSplitter  # noqa: PLC0415
        from rag_ingester import RagIngester as _RagIngester  # noqa: PLC0415

        print("  [ingest] splitting chunks...")
        if snippets_only:
            # Override md_index_enable so heading-based snippets are always used
            base_cfg = ConfigLoader().load("rag_pipeline.json")
            base_cfg["md_index_enable"] = True
            splitter = _ChunkSplitter(config=base_cfg)
        else:
            splitter = _ChunkSplitter()
        n_chunks = await loop.run_in_executor(None, splitter.process_all)
        print(f"  [ingest] {n_chunks} chunks written")

        print("  [ingest] ingesting to DB...")
        ingester = _RagIngester()
        await loop.run_in_executor(None, ingester.ingest_all)
        print("  [ingest] done — RAG DB updated")

    async def _cmd_ingest(self, args: str) -> None:
        """Crawl/ingest a URL or local file into the RAG DB from within the REPL.

        Usage: /ingest <url|path> [ja|en] [--snippets-only]
        --snippets-only forces heading-based Markdown snippet chunking.
        """
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
        loop = asyncio.get_running_loop()
        try:
            from web_crawler import WebCrawler as _WebCrawler  # noqa: PLC0415

            crawler = _WebCrawler()

            if target.startswith(("http://", "https://")):
                print(f"  [ingest] crawling {target} (lang={lang})...")
                await crawler.crawl_site(target, lang)
                print("  [ingest] crawl done")
            else:
                file_path = Path(target)
                if not file_path.exists():
                    print(f"  [ingest] error: file not found: {file_path}")
                    return
                print(f"  [ingest] reading local file {file_path} (lang={lang})...")
                count = await loop.run_in_executor(
                    None, crawler.crawl_file, file_path, lang
                )
                if count == 0:
                    print("  [ingest] error: failed to read local file")
                    return
                print("  [ingest] file read done")

            await self._run_split_and_ingest(loop, snippets_only=snippets_only)
        except Exception as e:
            logger.error(f"Ingest failed for {target}: {e}")
            print(f"  [ingest] error: {e}")

    async def _cmd_compact(self) -> None:
        """Force immediate compression of conversation history.

        Bypasses the context_char_limit threshold and compresses the oldest
        context_compress_turns pairs unconditionally.
        """
        ctx = self._ctx
        if ctx.services.hist_mgr is None:
            print("History manager not available.")
            return
        turn_msgs = [m for m in ctx.history if m["role"] != "system"]
        n_compress = ctx.services.hist_mgr.compress_turns * 2
        if len(turn_msgs) <= n_compress:
            print("Nothing to compact: history too short.")
            return
        # Temporarily clear char_limit so compress() proceeds unconditionally
        orig_limit = ctx.services.hist_mgr._char_limit
        ctx.services.hist_mgr._char_limit = 0
        try:
            ctx.history = await ctx.services.hist_mgr.compress(ctx.history)
        finally:
            ctx.services.hist_mgr._char_limit = orig_limit
