"""rag/stages/search.py
Search stage for embedding + BM25 search.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from db.helper import SQLiteHelper

from rag.llm import get_embedding
from rag.repository import RagRepository
from rag.stage import PipelineContext

logger = logging.getLogger(__name__)


async def _search_all_queries(
    queries: list[str],
    db: SQLiteHelper,
    cfg: dict[str, Any],
    http: httpx.AsyncClient,
) -> list[list]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    raw = await asyncio.gather(
        *(get_embedding(q, http) for q in queries),
        return_exceptions=True,
    )
    all_results: list[list] = []
    repo = RagRepository(db)
    for q, result in zip(queries, raw):
        if isinstance(result, Exception):
            logger.warning(f"Embedding failed for '{q}': {result}")
            continue
        assert isinstance(result, list)
        try:
            vec_res = repo.vector_search(result, cfg.get("top_k_search", 100))
            fts_res = repo.fts_search(q, cfg.get("top_k_search", 100))
            if vec_res:
                all_results.append(vec_res)
            if fts_res:
                all_results.append(fts_res)
        except Exception as e:
            logger.warning(f"Search failed for '{q}': {e}")
    return all_results


class SearchStage:
    def __init__(self, cfg: dict[str, Any], http: httpx.AsyncClient) -> None:
        self._cfg = cfg
        self._http = http

    async def run(self, ctx: PipelineContext, db: SQLiteHelper, **kwargs: Any) -> None:
        """Run search stage."""
        ctx.search_results = await _search_all_queries(
            ctx.queries, db, self._cfg, self._http
        )
        # Notify observers
        for observer in ctx.observers:
            try:
                await observer.on_stage_complete("search", ctx)
            except Exception as e:
                logger.warning(f"Observer failed in Search stage: {e}")
