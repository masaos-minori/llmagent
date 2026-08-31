#!/usr/bin/env python3
"""scripts/rag/ingestion/cache_invalidation.py

Isolate cache management logic from ingester.py into CacheInvalidator class.

After ingestion completes, sends HTTP POST to RAG pipeline service URL
to invalidate stale semantic cache entries. Only triggered when at least
one URL group succeeded.
"""

import httpx
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/ingest.log")


class CacheInvalidator:
    """Invalidate RAG pipeline semantic cache after ingestion."""

    def __init__(self, http_client: httpx.Client) -> None:
        """Initialize with HTTP client for cache invalidation requests."""
        self._client = http_client

    def invalidate(self, rag_pipeline_service_url: str, has_success: bool) -> None:
        """Invalidate RAG pipeline semantic cache after ingestion (only when at least one URL group succeeded)."""
        if not has_success or not rag_pipeline_service_url:
            return
        try:
            resp = self._client.post(rag_pipeline_service_url + "/rag_invalidate_cache")
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning(f"Cache invalidation failed: {e}")
