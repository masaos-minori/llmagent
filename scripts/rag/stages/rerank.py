"""scripts/rag/stages/rerank.py

Rerank stage for RAG pipeline."""

import logging
from typing import Literal

from shared.types import RagConfig

from rag.llm_client import RagLLM
from rag.llm_prompts import RagRerankError
from rag.repository import RagHit, deduplicate_chunks
from rag.stage import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


async def _rerank(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


def _rerank_fallback(merged: list[RagHit], cfg: RagConfig) -> list[RagHit]:
    """Fallback reranking when use_rerank=False: slice + dedup."""
    result = merged[: cfg.rag_top_k]
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


class RerankStage(PipelineStage):
    """LLM-based reranking stage that reorders merged search results by relevance."""

    def __init__(self, cfg: RagConfig, llm: RagLLM) -> None:
        """Initialize with RAG configuration and LLM client for reranking."""
        self._cfg = cfg
        self._llm = llm

    def get_status(
        self, ctx: PipelineContext
    ) -> tuple[Literal["success", "fallback"], str | None]:
        """Return execution status of this stage with optional reason string."""
        if not self._cfg.use_rerank:
            return "fallback", "use_rerank=False"
        if ctx._fallback_reason == "rerank_exception":
            return "fallback", "rerank_exception"
        return "success", None

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")
