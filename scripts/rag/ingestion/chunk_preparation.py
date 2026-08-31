#!/usr/bin/env python3
"""scripts/rag/ingestion/chunk_preparation.py

Isolate chunk creation logic from ingester.py into ChunkFactory class.

ChunkFactory owns the parallel embedding orchestration — it creates the executor,
dispatches work, and collects results.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx
from rag.exceptions import IngestionFailureReason
from rag.models_data import PreparedChunk
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/ingest.log")


class ChunkFactory:
    """Prepare chunks for insertion by embedding them in parallel."""

    def __init__(
        self,
        embed_service: object,
        workers: int,
    ) -> None:
        """Initialize with EmbeddingService and worker count."""
        self._embed_service = embed_service
        self._workers = workers

    def prepare(
        self, doc_id: int, chunk_files: list[Path]
    ) -> tuple[list[PreparedChunk], list[Path], list[tuple[Path, str]], int]:
        """Embed chunk files in parallel; returns (prepared_chunks, prepared_paths, failed_paths_with_reasons, embed_failed_count)."""
        prepared_chunks: list[PreparedChunk] = []
        prepared_paths: list[Path] = []
        failed_paths: list[tuple[Path, str]] = []
        embed_failed = 0
        with ThreadPoolExecutor(max_workers=self._workers) as executor:
            futures = {
                executor.submit(self._embed_and_store, doc_id, path): path
                for path in chunk_files
            }
            for future in as_completed(futures):
                path = futures[future]
                try:
                    result = future.result()
                    if isinstance(result, PreparedChunk):
                        prepared_chunks.append(result)
                        prepared_paths.append(path)
                    elif isinstance(result, IngestionFailureReason):
                        reason_str = (
                            result.value if hasattr(result, "value") else str(result)
                        )
                        if "embedding" in reason_str.lower():
                            embed_failed += 1
                        failed_paths.append((path, reason_str))
                    else:
                        failed_paths.append(
                            (path, f"unexpected result type: {type(result).__name__}")
                        )
                except (
                    httpx.HTTPStatusError,
                    httpx.RequestError,
                    OSError,
                    ValueError,
                    TypeError,
                ) as e:
                    self._log_ingest_failure(doc_id, path, e)
                    failed_paths.append((path, str(e)))
        return prepared_chunks, prepared_paths, failed_paths, embed_failed

    def _embed_and_store(
        self, doc_id: int, path: Path
    ) -> PreparedChunk | IngestionFailureReason:
        """Embed one chunk without DB access; returns PreparedChunk or failure reason."""
        return self._embed_service.embed_and_store(doc_id, path)

    def _log_ingest_failure(self, doc_id: int, path: Path, error: Exception) -> None:
        """Log an ingest failure with context."""
        logger.warning(
            "ingest failure %s: %s",
            path.name,
            error,
            extra={
                "doc_id": doc_id,
                "source_type": "file",
                "stage_name": "ingester",
            },
        )
