"""agent/services/ingest_workflow.py
IngestWorkflowService — orchestrates crawl / split / ingest pipeline stages.

Extracted from _IngestMixin._cmd_ingest() so the workflow is testable
without a running REPL. Raises IngestStageError on stage failure.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any

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
        on_status: Callable[[str], None] | None = None,
    ) -> IngestOutcome:
        """Run the full crawl → split → ingest pipeline for target.

        target: URL (http/https) or local file path.
        on_status: optional callback invoked with each status message as it
            is generated, enabling real-time progress display.
        Returns IngestOutcome with stage=OK on success.
        Raises IngestStageError on any stage failure.
        """
        loop = asyncio.get_running_loop()
        messages = await self._crawl(target, lang, loop, on_status=on_status)
        n_chunks, messages, embed_failed = await self._split_and_ingest(
            loop, snippets_only, messages, on_status=on_status
        )
        return IngestOutcome(
            stage=IngestStage.OK,
            n_chunks=n_chunks,
            messages=tuple(messages),
            embed_failed=embed_failed,
        )

    async def _crawl(
        self,
        target: str,
        lang: str,
        loop: asyncio.AbstractEventLoop,
        on_status: Callable[[str], None] | None = None,
    ) -> list[str]:
        """Crawl target and populate the staging area."""
        try:
            from rag.ingestion.crawler import (
                WebCrawler as _WebCrawler,  # noqa: PLC0415 — lazy: heavy crawler deferred to crawl call
            )

            crawler = _WebCrawler()
            if target.startswith(("http://", "https://")):
                messages = await self._crawl_url(
                    crawler, target, lang, on_status=on_status
                )
            else:
                messages = await self._crawl_file(
                    crawler, Path(target), lang, loop, on_status=on_status
                )
        except IngestStageError:
            raise
        except (OSError, ValueError, httpx.RequestError, ImportError) as e:
            logger.exception("Ingest crawl stage failed for %r", target)
            raise IngestStageError(IngestStage.CRAWL, str(e)) from e
        return messages

    def _emit(self, msg: str, on_status: Callable[[str], None] | None) -> str:
        """Emit msg to on_status if set; return msg for message list collection."""
        if on_status is not None:
            on_status(msg)
        return msg

    async def _crawl_url(
        self,
        crawler: Any,
        url: str,
        lang: str,
        on_status: Callable[[str], None] | None = None,
    ) -> list[str]:
        """Crawl an HTTP URL and return status messages."""
        messages = [self._emit(f"[ingest] crawling {url} (lang={lang})...", on_status)]
        await crawler.crawl_site(url, lang)
        messages.append(self._emit("[ingest] crawl done", on_status))
        return messages

    async def _crawl_file(
        self,
        crawler: Any,
        file_path: Path,
        lang: str,
        loop: asyncio.AbstractEventLoop,
        on_status: Callable[[str], None] | None = None,
    ) -> list[str]:
        """Crawl a local file and return status messages."""
        if not file_path.exists():
            raise IngestStageError(IngestStage.CRAWL, f"file not found: {file_path}")
        messages = [
            self._emit(
                f"[ingest] reading local file {file_path} (lang={lang})...", on_status
            )
        ]
        count = await loop.run_in_executor(None, crawler.crawl_file, file_path, lang)
        if count == 0:
            raise IngestStageError(IngestStage.CRAWL, "failed to read local file")
        messages.append(self._emit("[ingest] file read done", on_status))
        return messages

    async def _split_and_ingest(
        self,
        loop: asyncio.AbstractEventLoop,
        snippets_only: bool,
        messages: list[str],
        on_status: Callable[[str], None] | None = None,
    ) -> tuple[int, list[str], int]:
        """Run ChunkSplitter and RagIngester; return (n_chunks, messages, embed_failed)."""
        n_chunks = 0
        try:
            splitter = self._build_splitter(snippets_only)
            messages.append(self._emit("[ingest] splitting chunks...", on_status))
            n_chunks = await loop.run_in_executor(None, splitter.process_all)
            messages.append(
                self._emit(f"[ingest] {n_chunks} chunks written", on_status)
            )
        except IngestStageError:
            raise
        except (OSError, ValueError, RuntimeError, ImportError) as e:
            logger.exception("Ingest split stage failed")
            raise IngestStageError(IngestStage.SPLIT, str(e)) from e

        try:
            messages, embed_failed = await self._ingest_to_db(loop, on_status=on_status)
        except IngestStageError:
            raise
        except (OSError, RuntimeError, sqlite3.Error, ImportError) as e:
            logger.exception("Ingest ingest stage failed")
            raise IngestStageError(IngestStage.INGEST, str(e)) from e

        return n_chunks, messages, embed_failed

    def _build_splitter(self, snippets_only: bool) -> Any:
        """Build a ChunkSplitter instance, optionally with md_index enabled."""
        from rag.ingestion.chunk_splitter import (  # noqa: PLC0415 — lazy: deferred
            ChunkSplitter as _Splitter,
        )

        if snippets_only:
            from shared.config_loader import (  # noqa: PLC0415 — lazy: deferred
                ConfigLoader,
            )

            base_cfg = ConfigLoader().load("rag_pipeline.toml")
            base_cfg["md_index_enable"] = True
            return _Splitter(config=base_cfg)
        return _Splitter()

    async def _ingest_to_db(
        self,
        loop: asyncio.AbstractEventLoop,
        on_status: Callable[[str], None] | None = None,
    ) -> tuple[list[str], int]:
        """Run RagIngester and return (status messages, embed_failed count)."""
        from rag.ingestion.ingester import (  # noqa: PLC0415 — lazy: deferred
            RagIngester as _Ingester,
        )

        messages = [self._emit("[ingest] ingesting to DB...", on_status)]
        ingester = _Ingester()
        report = await loop.run_in_executor(None, ingester.ingest_all)
        embed_failed = report.embed_failed if report else 0
        messages.append(self._emit("[ingest] done — RAG DB updated", on_status))
        if embed_failed > 0:
            messages.append(
                self._emit(
                    f"[warn] {embed_failed} chunk(s) failed embedding — "
                    "stored without vec index; FTS search still works",
                    on_status,
                )
            )
        if report and report.issues:
            for issue in report.issues:
                messages.append(self._emit(f"[warn] {issue}", on_status))
        return messages, embed_failed
