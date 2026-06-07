"""Search stage for RAG pipeline."""

import asyncio
import logging

from rag.llm import get_embedding
from rag.repository import RagRepository
from rag.stage import PipelineContext

logger = logging.getLogger(__name__)


class SearchStage:
    def __init__(self, cfg, http) -> None:
        self._cfg = cfg
        self._http = http

    async def run(self, ctx: PipelineContext, db=None, **kwargs) -> None:
        top_k = self._cfg.get("top_k_search", 10)
        raw = await asyncio.gather(
            *(get_embedding(q, self._http) for q in ctx.queries),
            return_exceptions=True,
        )
        all_results: list = []
        repo = RagRepository(db)
        for q, result in zip(ctx.queries, raw):
            if isinstance(result, Exception):
                logger.warning(f"Embedding failed for '{q}': {result}")
                continue
            assert isinstance(result, list)
            try:
                vec_res = repo.vector_search(result, top_k)
                fts_res = repo.fts_search(q, top_k)
                if vec_res:
                    all_results.append(vec_res)
                if fts_res:
                    all_results.append(fts_res)
            except Exception as e:
                logger.warning(f"Search failed for '{q}': {e}")
        ctx.search_results = all_results
