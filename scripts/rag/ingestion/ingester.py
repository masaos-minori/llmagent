#!/usr/bin/env python3
"""scripts/rag/ingestion/ingester.py

Thin orchestrator delegating to 7 concern-specific classes:
  FileRouter, EmbeddingService, ChunkFactory, DocumentStore,
  TransactionManager, ChunkGroupingStrategy, CacheInvalidator

Pipeline position: Crawler.py -> ChunkSplitter.py -> RagIngester.py
"""

import argparse
from dataclasses import dataclass
from pathlib import Path

import httpx
from db.helper import SQLiteHelper
from db.models import RagConsistencyReport
from rag.exceptions import ChunkFormatError, IngestionFailureReason
from rag.ingestion.cache_invalidation import CacheInvalidator
from rag.ingestion.chunk_grouping import ChunkGroupingStrategy
from rag.ingestion.chunk_preparation import ChunkFactory
from rag.ingestion.document_manager import DocumentManager
from rag.ingestion.document_persistence import DocumentStore
from rag.ingestion.embedding import EmbeddingService
from rag.ingestion.file_routing import FileRouter
from rag.ingestion.pipeline_utils import read_chunk_json
from rag.ingestion.transaction_commit import TransactionManager
from rag.models_data import ChunkDocument
from rag.utils import validate_url
from shared.config_loader import ConfigLoader
from shared.llm_client import build_embed_url
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/ingest.log")

# ──────────────────────────────────────────────────────────────────────────────
# Type definitions
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class IngestUrlResult:
    """Per-URL ingestion outcome returned by ingest_url_group()."""

    url: str
    n_success: int
    n_failed: int
    skipped: bool
    n_embed_failed: int = 0
    failure_reason: IngestionFailureReason | None = None

    @staticmethod
    def skip(url: str) -> "IngestUrlResult":
        """Return a skipped result for a URL."""
        return IngestUrlResult(url=url, n_success=0, n_failed=0, skipped=True)

    @staticmethod
    def validation_failure(url: str, chunk_files: list[Path]) -> "IngestUrlResult":
        """Return a failure result when artifact validation fails."""
        return IngestUrlResult(
            url=url, n_success=0, n_failed=len(chunk_files), skipped=False
        )

    @staticmethod
    def unexpected_failure(url: str) -> "IngestUrlResult":
        """Return a failure result for unexpected errors."""
        return IngestUrlResult(
            url=url,
            n_success=0,
            n_failed=0,
            skipped=False,
            failure_reason=IngestionFailureReason.UNEXPECTED_FAILURE,
        )

    @staticmethod
    def log_ingestion_result(
        doc_id: int,
        url: str,
        inserted: int,
        total: int,
        failed: int,
        embed_failed: int,
    ) -> None:
        """Log the chunk ingestion result."""
        src_type = "file" if url.startswith("file://") else "http"
        logger.info(
            "inserted %s/%s chunks (%s failed, %s embed-failed): %s",
            inserted,
            total,
            failed,
            embed_failed,
            url,
            extra={"doc_id": doc_id, "source_type": src_type, "stage_name": "ingester"},
        )


# ──────────────────────────────────────────────────────────────────────────────
# RagIngester class
# ──────────────────────────────────────────────────────────────────────────────
class RagIngester:
    """Embeds chunk files produced by ChunkSplitter and inserts them into SQLite; chunks are grouped by URL and moved to registered/ after ingestion."""

    def __init__(self, config: dict | None = None) -> None:
        cfg: dict = config or ConfigLoader().load("ingester.toml")
        rag_src_dir = Path(cfg["rag_src_dir"])
        self._chunk_dir: Path = rag_src_dir / "chunk"
        self._registered_dir: Path = rag_src_dir / "registered"
        self._embed_url: str = build_embed_url(cfg["embed_url"])
        self._embed_retry: int = int(cfg["embed_retry"])
        self._embed_workers: int = int(cfg.get("embed_workers", 4))
        # DB settings stored explicitly to bypass build_db_config() / agent.toml
        self._rag_db_path: str = str(cfg.get("rag_db_path", ""))
        self._sqlite_vec_so: str = str(cfg.get("sqlite_vec_so", ""))
        self._sqlite_timeout: int = int(cfg.get("sqlite_timeout", 30))
        self._sqlite_busy_timeout_ms: int = int(
            cfg.get("sqlite_busy_timeout_ms", 30000)
        )
        self._rag_pipeline_service_url: str = cfg.get("rag_pipeline_service_url", "")
        self._client = httpx.Client(timeout=60)
        # Extracted classes
        self._embedding_service = EmbeddingService(
            self._embed_url, self._embed_retry, self._embed_workers, self._client
        )
        self._cache_invalidator = CacheInvalidator(self._client)
        self._chunk_grouping_strategy = ChunkGroupingStrategy()
        self._file_router = FileRouter(self._registered_dir, self._chunk_dir)
        # Note: DocumentStore and DocumentManager are created per-ingest
        # because they depend on the SQLite connection context.

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __del__(self) -> None:
        try:
            client = getattr(self, "_client", None)
            if client is not None:
                client.close()
        except OSError:
            pass

    # ── Public interface ──────────────────────────────────────────────────────

    def ingest_all(
        self,
        force: bool = False,
        on_ingest_complete=None,
    ) -> RagConsistencyReport | None:
        """Process all chunk files in chunk_dir grouped by URL; force=True deletes existing document records before re-inserting.

        Returns the post-ingestion consistency report, or None if the check failed.
        Callers that do not inspect the return value are unaffected.
        """
        chunk_files = sorted(self._chunk_dir.glob("*.json"))
        if not chunk_files:
            logger.info("No chunk files to process")
            return None
        url_groups = self._chunk_grouping_strategy.group(chunk_files)

        consistency_report: RagConsistencyReport | None = None
        with SQLiteHelper(
            db_path=self._rag_db_path,
            sqlite_vec_so=self._sqlite_vec_so,
            sqlite_timeout=self._sqlite_timeout,
            sqlite_busy_timeout_ms=self._sqlite_busy_timeout_ms,
        ).open(write_mode=True, row_factory=True) as db:
            doc_manager = DocumentManager(db)
            doc_store = DocumentStore(db, doc_manager)
            results = self._process_url_groups(
                doc_manager, db, doc_store, url_groups, force
            )
            consistency_report = doc_manager.check_consistency(
                embed_failed=sum(
                    r.n_embed_failed for r in results if r.n_embed_failed > 0
                ),
                on_ingest_complete=on_ingest_complete,
            )

        total_success = sum(r.n_success for r in results)
        total_failed = sum(r.n_failed for r in results if r.n_failed > 0)
        total_embed_failed = sum(
            r.n_embed_failed for r in results if r.n_embed_failed > 0
        )
        total_skipped = sum(1 for r in results if r.skipped)
        logger.info(
            "=== done: %s URLs processed (%d success, %d failed, %d embed-failed, %d skipped) ===",
            len(results),
            total_success,
            total_failed,
            total_embed_failed,
            total_skipped,
            extra={"stage_name": "ingester"},
        )
        if consistency_report is None:
            logger.warning("Consistency check failed after ingestion")
        elif consistency_report.issues:
            logger.warning(
                "Ingestion completed with %d inconsistency issue(s): %s",
                len(consistency_report.issues),
                "; ".join(consistency_report.issues),
            )
        # Invalidate RAG pipeline semantic cache after ingestion (only when at least one URL group succeeded)
        has_success = any(r.n_success > 0 for r in results)
        self._cache_invalidator.invalidate(self._rag_pipeline_service_url, has_success)
        return consistency_report

    def ingest_url_group(
        self,
        doc_mgr: DocumentManager,
        db: SQLiteHelper,
        doc_store: DocumentStore,
        url: str,
        chunk_files: list[Path],
        force: bool,
    ) -> IngestUrlResult:
        """Ingest all chunk files for one URL into SQLite in ascending chunk_index order; routes files based on success/failure."""
        if not chunk_files:
            return IngestUrlResult.skip(url)

        chunk_files = sorted(chunk_files, key=lambda p: p.stem)
        try:
            first_data = self._read_chunk_json(chunk_files[0])
        except ChunkFormatError:
            return IngestUrlResult.validation_failure(url, chunk_files)

        first_fields = (
            first_data.url,
            first_data.title,
            first_data.lang,
            first_data.fetched_at,
            first_data.etag,
            first_data.last_modified,
            first_data.source_file,
            first_data.chunking_strategy,
            first_data.chunk_type,
        )
        chunk_indices: set[int] = set()
        for cp in chunk_files:
            try:
                cd = self._read_chunk_json(cp)
            except ChunkFormatError:
                return IngestUrlResult.validation_failure(url, chunk_files)
            cf = (
                cd.url,
                cd.title,
                cd.lang,
                cd.fetched_at,
                cd.etag,
                cd.last_modified,
                cd.source_file,
                cd.chunking_strategy,
                cd.chunk_type,
            )
            if cf != first_fields:
                return IngestUrlResult(
                    url=url,
                    n_success=0,
                    n_failed=len(chunk_files),
                    skipped=False,
                    failure_reason=IngestionFailureReason.GROUP_VALIDATION_FAILED,
                )
            chunk_indices.add(cd.chunk_index)
        expected = set(range(len(chunk_files)))
        if chunk_indices != expected:
            return IngestUrlResult(
                url=url,
                n_success=0,
                n_failed=len(chunk_files),
                skipped=False,
                failure_reason=IngestionFailureReason.GROUP_VALIDATION_FAILED,
            )

        title = first_data.title
        lang = first_data.lang
        etag = first_data.etag
        last_modified = first_data.last_modified
        chunking_strategy = first_data.chunking_strategy

        doc_id, skip, replace = doc_store.get_or_create(
            db,
            url,
            title,
            lang,
            force,
            etag=etag,
            last_modified=last_modified,
            chunking_strategy=chunking_strategy,
            fetched_at=first_data.fetched_at,
        )
        if skip:
            logger.info("already registered, skipping", extra={"url": url})
            self._file_router.route(chunk_files, [])
            return IngestUrlResult.skip(url)

        effective_doc_id = doc_id if doc_id is not None else -1

        factory = ChunkFactory(self._embedding_service, self._embed_workers)
        prepared_chunks, prepared_paths, failed_paths, embed_failed = factory.prepare(
            effective_doc_id, chunk_files
        )

        if len(prepared_chunks) > 0 and len(failed_paths) == 0:
            tx_mgr = TransactionManager(db, doc_mgr, doc_store)
            tx_mgr.commit(
                url,
                doc_id,
                prepared_chunks,
                prepared_paths,
                force,
                replace,
                title,
                lang,
                etag=etag,
                last_modified=last_modified,
                chunking_strategy=chunking_strategy,
                fetched_at=first_data.fetched_at,
            )
            self._file_router.route(prepared_paths, [])
        else:
            failed_all = [
                (p, "embedding_partial_failure") for p in prepared_paths
            ] + failed_paths
            self._file_router.route([], failed_all)

        n_success = len(prepared_chunks) if len(failed_paths) == 0 else 0
        IngestUrlResult.log_ingestion_result(
            doc_id if doc_id is not None else -1,
            url,
            n_success,
            len(chunk_files),
            len(failed_paths),
            embed_failed,
        )
        return IngestUrlResult(
            url=url,
            n_success=n_success,
            n_failed=len(failed_paths),
            skipped=False,
            n_embed_failed=embed_failed,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _read_chunk_json(self, path: Path) -> ChunkDocument:
        """Read and validate a chunk JSON file; returns ChunkDocument."""
        return read_chunk_json(path)

    def _log_ingest_failure(self, doc_id: int, path: Path, e: Exception) -> None:
        """Log a chunk ingestion failure."""
        chunk_url = ""
        try:
            chunk_data = read_chunk_json(path)
            chunk_url = chunk_data.url or ""
        except ChunkFormatError:
            pass
        logger.error(
            "Failed to ingest %s: %s",
            path,
            e,
            extra={
                "doc_id": doc_id,
                "url": chunk_url,
                "source_type": "file",
                "stage_name": "ingester",
            },
        )

    def _process_url_groups(
        self,
        doc_mgr: DocumentManager,
        db: SQLiteHelper,
        doc_store: DocumentStore,
        url_groups: dict[str, list[Path]],
        force: bool,
    ) -> list[IngestUrlResult]:
        """Iterate over URL groups and ingest each; log exceptions without stopping."""
        results: list[IngestUrlResult] = []
        for url, paths in url_groups.items():
            try:
                results.append(
                    self.ingest_url_group(doc_mgr, db, doc_store, url, paths, force)
                )
            except (OSError, RuntimeError, ValueError):
                logger.exception("ingest_url_group failed: %s", url)
                results.append(IngestUrlResult.unexpected_failure(url))
        return results


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    """CLI entry point for embedding generation and database ingestion."""
    parser = argparse.ArgumentParser(
        description=(
            "Embedding generation and DB ingestion: rag-src/chunk/*.json -> SQLite -> rag-src/registered/"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force delete and re-ingest already registered URLs",
    )
    args = parser.parse_args()

    ingester = RagIngester()
    ingester.ingest_all(args.force)


if __name__ == "__main__":
    ConfigLoader.restrict_to("ingester.toml")
    main()
