#!/usr/bin/env python3
"""scripts/rag/ingestion/embedding.py

Isolate embedding logic from ingester.py into EmbeddingService class.

EmbeddingService owns the embed URL, retry count, worker count, and HTTP client —
these are configuration concerns, not orchestration concerns.
"""

import time
from pathlib import Path

import httpx
from rag.exceptions import IngestionFailureReason
from rag.ingestion.pipeline_utils import read_chunk_json
from rag.models_data import PreparedChunk
from rag.utils import floats_to_blob
from shared.json_utils import parse_http_json
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/ingest.log")


class EmbeddingService:
    """Generate embeddings for chunk files via external API."""

    def __init__(
        self,
        embed_url: str,
        retry_count: int,
        workers: int,
        http_client: httpx.Client,
    ) -> None:
        """Initialize with embedding configuration and HTTP client."""
        self._embed_url = embed_url
        self._retry_count = retry_count
        self._workers = workers
        self._client = http_client

    def get_embedding(self, text: str) -> list[float] | None:
        """Return embedding vector for text. Returns None on empty input or network failure."""
        if not text or not text.strip():
            return None
        for attempt in range(self._retry_count):
            try:
                resp = self._client.post(
                    self._embed_url,
                    json={"content": text},
                )
                resp.raise_for_status()
                data = parse_http_json(resp)
                embedding = data.get("embedding")
                if not isinstance(embedding, list) or not embedding:
                    raise ValueError("missing or empty 'embedding' field in response")
                return embedding
            except (
                httpx.RequestError,
                httpx.HTTPStatusError,
                ValueError,
            ) as e:
                logger.warning(
                    "embedding attempt %s/%s: %s",
                    attempt + 1,
                    self._retry_count,
                    e,
                )
                if attempt < self._retry_count - 1:
                    time.sleep(min(2**attempt, 10))
        return None

    def embed_and_store(
        self, doc_id: int, path: Path
    ) -> PreparedChunk | IngestionFailureReason:
        """Embed one chunk without DB access; returns PreparedChunk or failure reason."""
        try:
            data = read_chunk_json(path)
        except Exception:
            return IngestionFailureReason.PARSE_FAILED
        content: str = data.content
        nc_raw = data.normalized_content
        normalized_content: str | None = (
            nc_raw if isinstance(nc_raw, str) and nc_raw else None
        )
        idx = data.chunk_index
        chunk_type: str = data.chunk_type or ""
        source_file: str = data.source_file or ""
        # Embed original content; E5 understands raw Japanese.
        # normalized_content is for FTS only and not used for embedding.
        embedding = self.get_embedding(content)
        if embedding is None:
            chunk_url = data.url
            logger.warning(
                "embedding failed for %s: %r",
                path.name,
                content[:60],
                extra={
                    "doc_id": doc_id,
                    "url": chunk_url,
                    "source_type": "file",
                    "stage_name": "ingester",
                },
            )
            return IngestionFailureReason.EMBEDDING_FAILED
        return PreparedChunk(
            doc_id=doc_id,
            chunk_index=idx,
            content=content,
            normalized_content=normalized_content,
            embedding_blob=floats_to_blob(embedding),
            chunk_type=chunk_type,
            source_file=source_file,
        )
