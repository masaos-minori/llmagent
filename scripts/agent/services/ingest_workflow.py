"""agent/services/ingest_workflow.py
IngestWorkflowService — orchestrates crawl / split / ingest pipeline stages.

Extracted from _IngestMixin._cmd_ingest() so the workflow is testable
without a running REPL. Raises IngestStageError on stage failure.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from pathlib import Path

import httpx

from agent.services.enums import IngestStage
from agent.services.exceptions import IngestStageError
from agent.services.models import IngestOutcome

logger = logging.getLogger(__name__)


class IngestWorkflowService:
    """Orchestrate crawl, split, and ingest pipeline stages.

    Raises IngestStageError on any stage failure so the command handler
    can render a stage-specific error message.
    """

    async def run(
        self,
        target: str,
        lang: str = "ja",
        snippets_only: bool = False,
    ) -> IngestOutcome:
        """Run the full crawl → split → ingest pipeline for target.

        target: URL (http/https) or local file path.
        Returns IngestOutcome with stage=OK on success.
        Raises IngestStageError on any stage failure.
        """
        loop = asyncio.get_running_loop()
        messages = await self._crawl(target, lang, loop)
        n_chunks, messages = await self._split_and_ingest(loop, snippets_only, messages)
        return IngestOutcome(
            stage=IngestStage.OK, n_chunks=n_chunks, messages=tuple(messages)
        )

    async def _crawl(
        self,
        target: str,
        lang: str,
        loop: asyncio.AbstractEventLoop,
    ) -> list[str]:
        """Crawl target and populate the staging area."""
        messages: list[str] = []
        try:
            from rag.ingestion.crawler import (
                WebCrawler as _WebCrawler,  # noqa: PLC0415 — lazy: heavy crawler deferred to crawl call
            )

            crawler = _WebCrawler()
            if target.startswith(("http://", "https://")):
                messages.append(f"[ingest] crawling {target} (lang={lang})...")
                await crawler.crawl_site(target, lang)
                messages.append("[ingest] crawl done")
            else:
                file_path = Path(target)
                if not file_path.exists():
                    raise IngestStageError(
                        IngestStage.CRAWL, f"file not found: {file_path}"
                    )
                messages.append(
                    f"[ingest] reading local file {file_path} (lang={lang})..."
                )
                count = await loop.run_in_executor(
                    None, crawler.crawl_file, file_path, lang
                )
                if count == 0:
                    raise IngestStageError(
                        IngestStage.CRAWL, "failed to read local file"
                    )
                messages.append("[ingest] file read done")
        except IngestStageError:
            raise
        except (OSError, ValueError, httpx.RequestError, ImportError) as e:
            logger.exception("Ingest crawl stage failed for %r", target)
            raise IngestStageError(IngestStage.CRAWL, str(e)) from e
        return messages

    async def _split_and_ingest(
        self,
        loop: asyncio.AbstractEventLoop,
        snippets_only: bool,
        messages: list[str],
    ) -> tuple[int, list[str]]:
        """Run ChunkSplitter and RagIngester; return (n_chunks, messages)."""
        n_chunks = 0
        try:
            from rag.ingestion.chunk_splitter import (
                ChunkSplitter as _Splitter,  # noqa: PLC0415 — lazy: heavy splitter deferred to split call
            )

            messages.append("[ingest] splitting chunks...")
            if snippets_only:
                from shared.config_loader import (
                    ConfigLoader,  # noqa: PLC0415 — lazy: deferred to avoid circular import at module level
                )

                base_cfg = ConfigLoader().load("rag_pipeline.toml")
                base_cfg["md_index_enable"] = True
                splitter = _Splitter(config=base_cfg)
            else:
                splitter = _Splitter()
            n_chunks = await loop.run_in_executor(None, splitter.process_all)
            messages.append(f"[ingest] {n_chunks} chunks written")
        except IngestStageError:
            raise
        except (OSError, ValueError, RuntimeError, ImportError) as e:
            logger.exception("Ingest split stage failed")
            raise IngestStageError(IngestStage.SPLIT, str(e)) from e

        try:
            from rag.ingestion.ingester import (
                RagIngester as _Ingester,  # noqa: PLC0415 — lazy: heavy ingester deferred to ingest call
            )

            messages.append("[ingest] ingesting to DB...")
            ingester = _Ingester()
            await loop.run_in_executor(None, ingester.ingest_all)
            messages.append("[ingest] done — RAG DB updated")
        except IngestStageError:
            raise
        except (OSError, RuntimeError, sqlite3.Error, ImportError) as e:
            logger.exception("Ingest ingest stage failed")
            raise IngestStageError(IngestStage.INGEST, str(e)) from e

        return n_chunks, messages
