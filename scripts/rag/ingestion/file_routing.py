#!/usr/bin/env python3
"""scripts/rag/ingestion/file_routing.py

Isolate chunk destination routing from ingester.py into FileRouter class.

Chunk files are routed based on success/failure:
- Successful chunks → rag-src/registered/
- Failed chunks → rag-src/retry/ or rag-src/failed/ based on failure reason
- Error metadata (.error.json) written for failed chunks
"""

import datetime
from pathlib import Path

import orjson
from rag.exceptions import ChunkFormatError
from rag.ingestion.pipeline_utils import read_chunk_json
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/ingest.log")


class FileRouter:
    """Routes chunk files based on ingestion success/failure and writes error metadata."""

    def __init__(self, registered_dir: Path, chunk_dir: Path) -> None:
        """Initialize with directory paths for routing destinations."""
        self._registered_dir = registered_dir
        self._chunk_dir = chunk_dir

    def route(
        self, successful_paths: list[Path], failed_paths: list[tuple[Path, str]]
    ) -> None:
        """Route chunk files based on success/failure: successful→registered/, failed→retry/ or failed/."""
        self._registered_dir.mkdir(parents=True, exist_ok=True)
        retry_dir = self._chunk_dir.parent / "retry"
        retry_dir.mkdir(parents=True, exist_ok=True)
        failed_dir = self._chunk_dir.parent / "failed"
        failed_dir.mkdir(parents=True, exist_ok=True)

        for path in successful_paths:
            dest = self._registered_dir / path.name
            try:
                import shutil

                shutil.move(str(path), str(dest))
            except OSError as e:
                chunk_url = ""
                try:
                    chunk_data = read_chunk_json(path)
                    chunk_url = chunk_data.url or ""
                except ChunkFormatError:
                    pass
                logger.error(
                    "move failed %s → %s: %s",
                    path,
                    dest,
                    e,
                    extra={
                        "url": chunk_url,
                        "source_type": "file",
                        "stage_name": "ingester",
                    },
                )

        for path, reason in failed_paths:
            error_metadata = self.write_error_metadata(path, reason)
            if error_metadata is not None:
                error_path = failed_dir / f"{path.stem}.error.json"
                try:
                    error_path.write_bytes(orjson.dumps(error_metadata))
                except OSError as e:
                    logger.warning(
                        "Failed to write .error.json metadata for %s: %s",
                        path,
                        e,
                        extra={"stage_name": "ingester"},
                    )

            if "embedding" in reason.lower():
                dest = retry_dir / path.name
            else:
                dest = failed_dir / path.name
            try:
                import shutil

                shutil.move(str(path), str(dest))
            except OSError as e:
                logger.warning(
                    "Failed to move failed chunk %s → %s: %s",
                    path,
                    dest,
                    e,
                    extra={"stage_name": "ingester"},
                )

    def write_error_metadata(self, path: Path, failure_reason: str) -> dict | None:
        """Write .error.json metadata for a failed chunk."""
        try:
            chunk_data = read_chunk_json(path)
        except ChunkFormatError:
            return None

        metadata = {
            "schema_version": "1",
            "created_by": "rag_ingester",
            "failure_reason": failure_reason,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        }

        url = chunk_data.url or ""
        if url:
            metadata["url"] = url

        chunk_index_raw = chunk_data.chunk_index
        if chunk_index_raw is not None:
            metadata["chunk_index"] = str(chunk_index_raw)

        source_file = chunk_data.source_file or ""
        if source_file:
            metadata["source_file"] = source_file

        return metadata
