"""Search stage for RAG pipeline."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from rag.repository import RagRepository
from rag.stage import PipelineContext, PipelineStage

if TYPE_CHECKING:
    import httpx
    from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


async def _search_all_queries(
    queries: list[str], db: SQLiteHelper, cfg: dict[str, Any]
) -> list[list]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    from rag.llm import get_embedding

    raw = await asyncio.gather(
        *(get_embedding(q, db._http) for q in queries),  # type: ignore[attr-defined]
        return_exceptions=True,
    )
    all_results: list[list] = []
    repo = RagRepository(db)
    for q, result in zip(queries, raw):
        if isinstance(result, Exception):
            logger.warning(f"Embedding failed for '{q}': {result}")
            continue
        if not isinstance(result, list):
            logger.warning(f"Unexpected embedding type for '{q}': {type(result)}")
            continue
        try:
            vec_res = repo.vector_search(result, cfg["top_k_search"])
            fts_res = repo.fts_search(q, cfg["top_k_search"])
            if vec_res:
                all_results.append(vec_res)
            if fts_res:
                all_results.append(fts_res)
        except Exception as e:
            logger.warning(f"Search failed for '{q}': {e}")
    return all_results


class SearchStage(PipelineStage):
    def __init__(
        self, cfg: dict[str, Any], http: httpx.AsyncClient | None = None
    ) -> None:
        self._cfg = cfg
        self._http = http

    async def run(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        # Moves logic from RagPipeline.search_queries()
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        ctx.search_results = await _search_all_queries(ctx.queries, db, self._cfg)
