"""scripts/rag/stages/search.py

Search stage for RAG pipeline."""

from __future__ import annotations

import asyncio
import sqlite3
import struct
from typing import TYPE_CHECKING, Any, Literal, cast

from rag.repository import RagRepository
from rag.stage import PipelineContext, PipelineStage

if TYPE_CHECKING:
    import httpx
    from db.helper import SQLiteHelper

from shared.logger import Logger
from shared.types import RagConfig, RawHit

from rag.models_result import SearchDiagnostics

logger = Logger(__name__, "/opt/llm/logs/search.log")

# Bounds in-flight embedding requests per search run.
_EMBED_CONCURRENCY = 8


async def _search_all_queries(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then independent per-leg DB searches.

    For each query the vector leg runs only when an embedding is available; the
    BM25 (FTS) leg always runs. A failure in one leg no longer suppresses the
    other, and `fts_errors` counts one per failed retrieval leg. Embeddings are
    fetched concurrently up to `_EMBED_CONCURRENCY`. Sequential DB access avoids
    shared-connection conflicts.
    """
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    async def _vector_leg(
        repo: RagRepository, embedding: list[float], top_k: int, query: str
    ) -> tuple[list[RawHit], bool]:
        """Return (hits, failed) for the vector leg; never raises past its leg."""
        try:
            hits = cast("list[RawHit]", repo.vector_search(embedding, top_k))
            return hits, False
        except (
            sqlite3.OperationalError,
            RuntimeError,
            ValueError,
            OverflowError,
            struct.error,
        ) as e:
            logger.warning("Vector search failed for '%s': %s", query, e)
            return [], True

    async def _fts_leg(
        repo: RagRepository, query: str, top_k: int
    ) -> tuple[list[RawHit], bool]:
        """Return (hits, failed) for the BM25 (FTS) leg; never raises past its leg."""
        try:
            hits = cast("list[RawHit]", repo.fts_search(query, top_k))
            return hits, False
        except (
            sqlite3.OperationalError,
            RuntimeError,
            ValueError,
            OverflowError,
            struct.error,
        ) as e:
            logger.warning("FTS search failed for '%s': %s", query, e)
            return [], True

    sem = asyncio.Semaphore(_EMBED_CONCURRENCY)

    async def _embed_limited(q: str) -> list[float]:
        async with sem:
            return await get_embedding(q, cast(_httpx.AsyncClient, http), embed_url)

    raw = await asyncio.gather(
        *(_embed_limited(q) for q in queries),
        return_exceptions=True,
    )
    all_results: list[list[RawHit]] = []
    repo = RagRepository(db)
    embed_ok = 0
    embed_failed = 0
    fts_errors = 0
    for q, result in zip(queries, raw):
        if isinstance(result, Exception):
            logger.warning("Embedding failed for '%s': %s", q, result)
            embed_failed += 1
        elif not isinstance(result, list):
            logger.warning("Unexpected embedding type for '%s': %s", q, type(result))
            embed_failed += 1
        else:
            embed_ok += 1
            vec_hits, vec_failed = await _vector_leg(repo, result, cfg.top_k_search, q)
            fts_errors += int(vec_failed)
            if vec_hits:
                all_results.append(vec_hits)
        # The FTS leg always runs, even when the embedding failed, so an embedding
        # outage still yields lexical hits for the query.
        fts_hits, fts_failed = await _fts_leg(repo, q, cfg.top_k_search)
        fts_errors += int(fts_failed)
        if fts_hits:
            all_results.append(fts_hits)
    # degraded reflects whether any embedding or FTS error occurred during this run.
    # This matches the calculation in rag.diagnostics.SearchDiagnostics.from_run_result().
    degraded = embed_failed > 0 or fts_errors > 0
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
        degraded=degraded,
    )


class SearchStage(PipelineStage):
    """Semantic + BM25 hybrid search stage across all expanded queries."""

    def __init__(
        self,
        cfg: RagConfig,
        http: httpx.AsyncClient | None = None,
        embed_url: str = "",
    ) -> None:
        """Initialize with RAG config, optional HTTP client, and embedding URL."""
        self._cfg = cfg
        self._http = http
        self._embed_url = embed_url

    def get_status(
        self, ctx: PipelineContext
    ) -> tuple[Literal["success", "fallback"], str | None]:
        """Return execution status of this stage with optional reason string."""
        if not ctx.search_results:
            return "fallback", "no search results"
        return "success", None

    async def run(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, db, self._cfg, self._http, self._embed_url
        )
        ctx.search_results = results
        ctx.search_diagnostics = diagnostics
        if diagnostics.embed_failed > 0:
            logger.warning(
                "search degraded: %d/%d queries lacked embedding",
                diagnostics.embed_failed,
                diagnostics.embed_ok + diagnostics.embed_failed,
            )
        if diagnostics.fts_errors > 0:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )
