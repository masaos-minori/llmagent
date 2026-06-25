"""Rerank stage for RAG pipeline."""

from shared.types import RagConfig

from rag.llm import RagLLM, RagRerankError  # noqa: F401 — re-exported for callers
from rag.repository import RagHit, deduplicate_chunks
from rag.stage import PipelineContext, PipelineStage


async def _rerank(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        result = merged[: cfg.rag_top_k]
        return deduplicate_chunks(result, cfg.max_chunks_per_doc)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    return deduplicate_chunks(result, cfg.max_chunks_per_doc)


class RerankStage(PipelineStage):
    def __init__(self, cfg: RagConfig, llm: RagLLM) -> None:
        self._cfg = cfg
        self._llm = llm

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
