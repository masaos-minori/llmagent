"""Rerank stage for RAG pipeline."""

import logging

from rag.repository import deduplicate_chunks
from rag.stage import PipelineContext

logger = logging.getLogger(__name__)


class RerankStage:
    def __init__(self, cfg, llm) -> None:
        self._cfg = cfg
        self._llm = llm

    async def run(self, ctx: PipelineContext, **kwargs) -> None:
        rag_top_k: int = self._cfg.get("rag_top_k", 5)
        max_chunks_per_doc: int = self._cfg.get("max_chunks_per_doc", 3)
        if not self._cfg.get("use_rerank"):
            ctx.reranked = deduplicate_chunks(
                ctx.merged[:rag_top_k], max_chunks_per_doc
            )
            return
        try:
            result = await self._llm.cross_encoder_rerank(
                ctx.query,
                ctx.merged[: self._cfg.get("top_k_rerank", 20)],
                rag_top_k,
                rag_min_score=self._cfg.get("rag_min_score", 0.0),
            )
            ctx.reranked = deduplicate_chunks(result, max_chunks_per_doc)
        except Exception as e:
            logger.warning(f"Rerank failed, using RRF order: {e}")
            ctx.reranked = ctx.merged[:rag_top_k]
