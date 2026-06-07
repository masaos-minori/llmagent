"""Rerank stage for RAG pipeline."""

import logging

from rag.llm import RagLLM
from rag.repository import deduplicate_chunks
from rag.stage import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


async def _rerank(query: str, merged: list, cfg, llm: RagLLM) -> list:
    """Apply Cross-Encoder rerank then dedup; fall back to RRF order on error."""
    if not cfg.get("use_rerank", True):
        result = merged[: cfg.rag_top_k]
        return deduplicate_chunks(result, cfg.max_chunks_per_doc)
    try:
        result = await llm.cross_encoder_rerank(
            query,
            merged[: cfg.top_k_rerank],
            cfg.rag_top_k,
            rag_min_score=cfg.rag_min_score,
        )
        return deduplicate_chunks(result, cfg.max_chunks_per_doc)
    except Exception as e:
        logger.warning(f"Rerank failed, using RRF order: {e}")
        result = merged[: cfg.rag_top_k]
        return deduplicate_chunks(result, cfg.max_chunks_per_doc)


class RerankStage(PipelineStage):
    def __init__(self, cfg, llm) -> None:
        self._cfg = cfg
        self._llm = llm

    async def run(self, ctx: PipelineContext, **kwargs) -> None:
        ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
