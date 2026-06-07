"""Search stage for RAG pipeline."""

import asyncio
import logging

from rag.repository import RagRepository
from rag.stage import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


async def _search_all_queries(queries: list[str], db, cfg) -> list[list]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    from rag.llm import get_embedding

    raw = await asyncio.gather(
        *(get_embedding(q, db._http) for q in queries),
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
            vec_res = repo.vector_search(result, cfg.top_k_search)
            fts_res = repo.fts_search(q, cfg.top_k_search)
            if vec_res:
                all_results.append(vec_res)
            if fts_res:
                all_results.append(fts_res)
        except Exception as e:
            logger.warning(f"Search failed for '{q}': {e}")
    return all_results


class SearchStage(PipelineStage):
    def __init__(self, cfg) -> None:
        self._cfg = cfg

    async def run(self, ctx: PipelineContext, db=None, **kwargs) -> None:
        # Moves logic from RagPipeline.search_queries()
        ctx.search_results = await _search_all_queries(ctx.queries, db, self._cfg)
