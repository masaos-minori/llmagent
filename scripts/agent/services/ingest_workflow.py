"""agent/services/ingest_workflow.py
IngestWorkflowService — orchestrates crawl / split / ingest pipeline stages.

Extracted from _IngestMixin._cmd_ingest() so the workflow is testable
without a running REPL.  Returns IngestResult with a stage label so the
caller can render stage-specific error messages.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """Structured outcome of an ingest run."""

    stage: str  # "ok" | "crawl" | "split" | "ingest"
    error: str | None = None
    n_chunks: int = 0
    messages: list[str] = field(default_factory=list)


class IngestWorkflowService:
    """Orchestrate crawl, split, and ingest pipeline stages.

    Each stage failure is captured in IngestResult.stage so the
    command handler can render a stage-aware error message.
    """

    async def run(
        self,
        target: str,
        lang: str = "ja",
        snippets_only: bool = False,
    ) -> IngestResult:
        """Run the full crawl → split → ingest pipeline for target.

        target: URL (http/https) or local file path.
        Returns IngestResult with stage="ok" on success.
        """
        result = IngestResult(stage="ok")
        loop = asyncio.get_running_loop()

        # Stage 1: crawl
        crawl_ok = await self._crawl(target, lang, loop, result)
        if not crawl_ok:
            return result

        # Stage 2 & 3: split + ingest
        await self._split_and_ingest(loop, snippets_only, result)
        return result

    async def _crawl(
        self,
        target: str,
        lang: str,
        loop: asyncio.AbstractEventLoop,
        result: IngestResult,
    ) -> bool:
        """Crawl target and populate the staging area.  Returns False on failure."""
        try:
            from rag.ingestion.crawler import (
                WebCrawler as _WebCrawler,  # noqa: PLC0415 — lazy: heavy crawler deferred to crawl call
            )

            crawler = _WebCrawler()
            if target.startswith(("http://", "https://")):
                result.messages.append(f"[ingest] crawling {target} (lang={lang})...")
                await crawler.crawl_site(target, lang)
                result.messages.append("[ingest] crawl done")
            else:
                file_path = Path(target)
                if not file_path.exists():
                    result.stage = "crawl"
                    result.error = f"file not found: {file_path}"
                    return False
                result.messages.append(
                    f"[ingest] reading local file {file_path} (lang={lang})..."
                )
                count = await loop.run_in_executor(
                    None, crawler.crawl_file, file_path, lang
                )
                if count == 0:
                    result.stage = "crawl"
                    result.error = "failed to read local file"
                    return False
                result.messages.append("[ingest] file read done")
        except Exception as e:
            result.stage = "crawl"
            result.error = str(e)
            return False
        return True

    async def _split_and_ingest(
        self,
        loop: asyncio.AbstractEventLoop,
        snippets_only: bool,
        result: IngestResult,
    ) -> None:
        """Run ChunkSplitter and RagIngester; update result in place."""
        try:
            from rag.ingestion.chunk_splitter import (
                ChunkSplitter as _Splitter,  # noqa: PLC0415 — lazy: heavy splitter deferred to split call
            )

            result.messages.append("[ingest] splitting chunks...")
            if snippets_only:
                from shared.config_loader import (
                    ConfigLoader,  # noqa: PLC0415 — lazy: deferred to avoid circular import at module level
                )

                base_cfg = ConfigLoader().load("rag_pipeline.toml")
                base_cfg["md_index_enable"] = True
                splitter = _Splitter(config=base_cfg)
            else:
                splitter = _Splitter()
            result.n_chunks = await loop.run_in_executor(None, splitter.process_all)
            result.messages.append(f"[ingest] {result.n_chunks} chunks written")
        except Exception as e:
            result.stage = "split"
            result.error = str(e)
            return

        try:
            from rag.ingestion.ingester import (
                RagIngester as _Ingester,  # noqa: PLC0415 — lazy: heavy ingester deferred to ingest call
            )

            result.messages.append("[ingest] ingesting to DB...")
            ingester = _Ingester()
            await loop.run_in_executor(None, ingester.ingest_all)
            result.messages.append("[ingest] done — RAG DB updated")
        except Exception as e:
            result.stage = "ingest"
            result.error = str(e)
