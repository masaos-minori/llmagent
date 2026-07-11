"""Rerank stage for RAG pipeline."""

from rag.llm_client import RagLLM  # noqa: F401 — re-exported for callers
from rag.llm_prompts import RagRerankError  # noqa: F401 — re-exported for callers
from rag.repository import RagHit, deduplicate_chunks
from rag.stage import PipelineContext, PipelineStage
from shared.types import RagConfig


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
    def __init__(self, cfg: RagConfig, llm: RagLLM) -> None:
        self._cfg = cfg
        self._llm = llm

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
